"""Publication via TikTok Studio (navigateur déjà connecté par QR — voir tiktok_login_qr.py).

Pilote le Chrome visible ouvert avec le profil config/chrome_tiktok_profile (port 9222 ; lancé
automatiquement s'il n'est pas ouvert). Envoie le mp4, saisit la légende des métadonnées, clique
« Publier », puis lit la liste « Contenu » de TikTok Studio : l'état de la file n'est mis à
PUBLISHED que si la vidéo y apparaît réellement avec le début de sa légende.

Usage : python video_pipeline/publish_studio.py <video_id> --confirm
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    StaleElementReferenceException, NoSuchElementException, WebDriverException)

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
PROFILE = ROOT / "config" / "chrome_tiktok_profile"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload"
CONTENT_URL = "https://www.tiktok.com/tiktokstudio/content"


def _cdp_ready(timeout=3):
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False


def ensure_chrome(timeout=90):
    """Chrome de debug (port 9222) déjà ouvert ? Sinon on le lance et on ATTEND le port.

    Le 30/09/2026 l'ancien « sleep(8) » ne suffisait pas : Chrome met 15-25 s à ouvrir
    9222 (et peut rester bloqué sur une boîte de premier lancement) -> publication
    cassée avec SessionNotCreatedException. On sonde donc le port réellement.
    """
    if not _cdp_ready():
        subprocess.Popen([CHROME, "--remote-debugging-port=9222", f"--user-data-dir={PROFILE}",
                          "--window-size=1200,950", "--no-first-run", "--no-default-browser-check",
                          UPLOAD_URL])
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _cdp_ready():
            break
        time.sleep(2)
    else:
        raise RuntimeError(
            f"Chrome debug injoignable sur le port 9222 après {timeout}s. "
            f"Lance à la main : \"{CHROME}\" --remote-debugging-port=9222 "
            f"--user-data-dir=\"{PROFILE}\" {UPLOAD_URL} (session TikTok déjà connectée "
            f"dans ce profil, pas besoin de rescanner le QR).")
    o = Options()
    o.debugger_address = "127.0.0.1:9222"
    return webdriver.Chrome(options=o)


def find_retry(d, by, val, tries=10, sleep=1.5):
    """Recherche d'élément robuste aux StaleElementReference (recharges de page TikTok)."""
    last = None
    for _ in range(tries):
        try:
            return d.find_element(by, val)
        except (StaleElementReferenceException, NoSuchElementException) as exc:
            last = exc
            time.sleep(sleep)
    raise last


def body_text(d, tries=10):
    """Texte de la page, ou None si la page se recharge (TikTokStudio la reconstruit sans
    arrêt pendant l'import) — les boucles d'attente traitent None en « pas encore ».

    16/10/2026 : lecture en JavaScript (`document.body.innerText`) et PLUS `.text` de
    Selenium. Sur ce Chrome, `element.text` renvoie une chaîne VIDE alors que la page
    affiche tout : TOUTES les détections deviennent fausses en cascade (« import non
    terminé », fenêtres « Publier maintenant » jamais cliquées -> « publication sans
    preuve »). `innerText` et `page_source` voient bien le texte (mesuré).
    """
    for _ in range(tries):
        try:
            txt = d.execute_script(
                "return document.body ? (document.body.innerText || '') : ''")
            if txt:
                return txt
            return None                      # page vide = en reconstruction
        except WebDriverException:
            time.sleep(0.5)
    return None


def page_says(d, *words):
    """True si au moins un des mots est dans la page (False si page illisible)."""
    body = body_text(d)
    if not body:
        return False
    return any(w in body for w in words)


def click_button(d, text):
    """Clique le bouton visible dont le INNERTEXT correspond (JS).

    16/10/2026 : `b.text` est vide sur ce Chrome (cf. body_text) — la comparaison ne
    fonctionnait plus et aucune fenêtre de confirmation n'était cliquée.
    """
    for _ in range(3):
        try:
            ok = d.execute_script("""
                var want = arguments[0];
                var els = document.querySelectorAll('button, [role="button"]');
                for (var i = 0; i < els.length; i++) {
                    var e = els[i], r = e.getBoundingClientRect();
                    if (r.width <= 0 || r.height <= 0) continue;
                    if (getComputedStyle(e).visibility === 'hidden') continue;
                    if ((e.innerText || '').trim() === want) { e.click(); return true; }
                }
                return false;
            """, text)
            if ok:
                time.sleep(1)
                return True
            return False
        except WebDriverException:
            time.sleep(0.5)
    return False


def _norm(s):
    return " ".join((s or "").split())


def _field_text(d):
    """Texte réel du champ description, lu en JS (innerText/textContent).

    16/10/2026 : `.text` Selenium renvoie '' ici aussi (cf. body_text) — la légende
    paraissait toujours absente et on réécrivait inutilement (risque d'abandon « légende
    non saisie »)."""
    ed = editor(d, timeout=8)
    if ed is None:
        return ""
    try:
        return d.execute_script(
            "return arguments[0] ? (arguments[0].innerText || "
            "arguments[0].textContent || '') : ''", ed) or ""
    except (StaleElementReferenceException, WebDriverException):
        return ""


def editor(d, timeout=0):
    """Attend et renvoie l'éditeur de description TikTok (parfois absent, parfois tardif).

    Le 30/09/2026 : l'élément disparaît puis réapparaît pendant que TikTok reconstruit le
    formulaire d'upload. On sait l'attendre au lieu de planter.
    Le 16/10/2026 : la visibilité se teste en JS — `is_displayed()` renvoie False sur ce
    Chrome même pour un élément visible (mesuré : 757x62 px, visibility:visible,
    is_displayed=False), ce qui empêchait de TOUTOUVER le champ description.
    """
    deadline = time.time() + max(0, timeout)
    while True:
        try:
            ed = d.execute_script("""
                var els = document.querySelectorAll('.public-DraftEditor-content');
                for (var i = 0; i < els.length; i++) {
                    var e = els[i], r = e.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0 &&
                        getComputedStyle(e).visibility !== 'hidden') return e;
                }
                return null;
            """)
        except WebDriverException:
            ed = None
        if ed is not None:
            return ed
        if time.time() >= deadline:
            return None
        time.sleep(1.5)


def _select_all(d, ed):
    """Sélectionne tout le contenu du champ description (SANS modifier le DOM).

    02/10/2026 — mesuré sur le vrai formulaire TikTok Studio :
      * `element.send_keys()` ne fait RIEN sur ce DraftEditor (même Ctrl+A / Suppr) ;
      * les touches CDP (Input.dispatchKeyEvent) sont également ignorées ;
      * en revanche `Input.insertText` (CDP) écrit, et REMPLACE la sélection.

    On sélectionne donc en JavaScript puis on écrit via CDP. Point important : le JS ne
    fait que poser la sélection — il ne supprime rien — donc l'état React du DraftEditor
    n'est pas désynchronisé (c'était le défaut du « filet de sécurité » du 30/09).
    """
    return d.execute_script("""
      var n = arguments[0];
      if (!n) return -1;
      n.focus();
      var r = document.createRange();
      r.selectNodeContents(n);
      var s = getSelection();
      s.removeAllRanges();
      s.addRange(r);
      return s.toString().length;
    """, ed)


def _insert_text(d, texte):
    """Écrit un texte dans le champ focused, en remplaçant la sélection (CDP)."""
    d.execute_cdp_cmd("Input.insertText", {"text": texte})


def ensure_caption(d, caption, tries=4, settle=5.0):
    """Saisit la légende et la VÉRIFIE strictement (égalité, plus simple « contient »).

    TikTok réécrit la description avec le nom du fichier tant que la couverture
    charge : après saisie on laisse la page se stabiliser et on revérifie, sinon on
    recommence. Sans ça, le post part avec « auto_022 » comme légende.
    """
    want = _norm(caption)
    probe = _norm(caption)[:25]

    for attempt in range(tries):
        # Ferme les fenêtres d'info. « J'ai compris » uniquement : « Annuler » annule
        # l'import en cours sur le formulaire TikTok Studio, détruit le champ description
        # et rend la légende impossible à saisir (c'est ce qui a fait échouer les 5 envois
        # du 01/10 au soir, tous avec « légende non saisie »).
        click_button(d, "J'ai compris")   # compare en innerText (JS), pas b.text (vide)

        got = _norm(_field_text(d))
        if got == want:
            return True

        ed = editor(d, timeout=25)   # l'éditeur peut réapparaître : on l'attend
        if ed is None:
            time.sleep(2)
            continue

        # TikTok remplit le champ avec le NOM DU FICHIER. On sélectionne tout (JS, sans
        # toucher au DOM) puis on écrit par CDP : insertText REMPLACE la sélection.
        try:
            _select_all(d, ed)
            time.sleep(0.4)
            _insert_text(d, caption)
        except WebDriverException as exc:
            print(f"[legende] écriture CDP refusée ({exc.__class__.__name__}) -> nouvel essai",
                  flush=True)
            time.sleep(1.5)
            continue
        time.sleep(2.0)
        # PAS de ESCAPE ici : sur le formulaire d'upload il fait perdre la publication
        # (30/09/2026 — la page repartait sur /content).

        # laisse TikTok finir de recharger la couverture, puis on revérifie strictement
        deadline = time.time() + settle
        while time.time() < deadline:
            time.sleep(1.0)
            if _norm(_field_text(d)) == want:
                return True
        if _norm(_field_text(d)) == want:
            return True
        print(f"[legende] champ non conforme après écriture (essai {attempt+1}/{tries}) "
              f"-> champ = {_field_text(d)[:60]!r}", flush=True)
        time.sleep(1.5)

    return _norm(_field_text(d)) == want or probe in _norm(_field_text(d))


def _cartes_contenu(d, tours=6):
    """Liste les publications du compte.

    TikTok Studio virtualise la page : chaque carte = un bloc contenant la durée puis
    la légende. On récupère le texte de chaque carte (c'est ce que voit le patron), ce
    qui permet de décider « est-ce que CE fichier est déjà en ligne ? ».
    """
    js = r"""
    var out = [], vus = {};
    document.querySelectorAll('span').forEach(function(el){
      var t = (el.innerText||'').trim();
      if (!/^\d{2}:\d{2}$/.test(t)) return;
      var p = el, meilleur = null;
      for (var i=0;i<12 && p;i++){
        p = p.parentElement; if (!p) break;
        var tx = (p.innerText||'');
        // On garde le PLUS PETIT ancêtre qui contient déjà une vraie légende : un
        // ancêtre plus haut englobe plusieurs publications, et on attribuerait alors
        // une légende à la mauvaise vidéo (faux « déjà en ligne » = vidéo perdue).
        if (tx.length >= 60 && /\d{1,2}:\d{2}/.test(tx)) { meilleur = p; break; }
      }
      if (!meilleur) return;
      var tx = (meilleur.innerText||'').replace(/\s+/g,' ').trim();
      // Un ancêtre peut engl PLUSIEURS publications (TikTok Studio imbrique les cartes
      // dans des lignes). Une carte n'a qu'une durée : on coupe donc le texte avant la
      // prochaine durée. Sans ça, la légende de la publication suivante atterrit dans
      // la carte précédente -> faux « déjà en ligne » = vidéo jamais publiée.
      // Piège : l'heure « 2 oct., 10:53 » a la forme d'une durée, ce n'en est pas une.
      var coupe = -1, re = /\d{2}:\d{2}/g, m;
      while ((m = re.exec(tx)) !== null) {
        if (m.index === 0) continue;                       // la durée de la carte
        var avant = tx.slice(Math.max(0, m.index - 24), m.index);
        if (/\d{1,2}\s+[^0-9:]{2,8}\s*$/.test(avant)) continue;   // « 2 oct., 10:53 » : heure
        coupe = m.index; break;
      }
      if (coupe > 0) tx = tx.slice(0, coupe).trim();
      // Deux ancêtres peuvent décrire la MÊME carte (l'un avec les statistiques, l'autre
      // sans) : on déduplique sur les 100 premiers caractères, jamais sur le texte entier.
      var cle = tx.slice(0, 100);
      if (tx.length < 8 || vus[cle]) return; vus[cle] = 1;
      out.push({duree: t, carte: tx.slice(0, 300)});
    });
    return JSON.stringify(out);
    """
    trouvees, vus = {}, set()
    try:
        d.set_script_timeout(25)   # le DOM du contenu grossit : pas de script qui bloque
    except Exception:
        pass
    for tour in range(tours):
        try:
            brut = d.execute_script(js) or "[]"
            for c in json.loads(brut):
                cle = c.get("carte") or ""
                if cle and cle not in vus:
                    vus.add(cle)
                    trouvees[cle] = c
        except WebDriverException:
            break
        try:
            d.execute_script("""
              window.scrollTo(0, document.body.scrollHeight);
              document.querySelectorAll('div').forEach(function(e){
                if (e.scrollHeight > e.clientHeight + 60) e.scrollTop = e.scrollHeight;
              });
            """)
        except WebDriverException:
            break
        time.sleep(2.2)
    return list(trouvees.values())


def _id_depuis_carte(carte):
    """Déduit le video_id d'une carte Contenu, via le marqueur « (épisode 69) ».

    La légende en ligne est le nom du fichier, qui contient toujours le numéro
    d'épisode. C'est la seule correspondance fiable : le HEADLINE, lui, est partagé
    par les 4 variantes d'un même scénario.
    """
    ep = re.search(r"\(épisode\s+(\d+)\s*\)", carte or "")
    if not ep:
        return None
    return f"auto_{int(ep.group(1)):03d}"


def _titre_distinctif(caption):
    """La partie de la légende qui distingue UNE variante d'une autre.

    La légende fait « HEADLINE — Titre (épisode N) ». Le headline est commun aux 4
    variantes d'un scénario : s'en servir comme sonde « vidéo déjà en ligne » revient
    à dire qu'une variante est en ligne dès qu'une autre l'est. C'est exactement ce qui
    est arrivé le 09/10/2026 : auto_070 a été reconnu « déjà en ligne » à cause de
    auto_069, et marqué PUBLISHED alors qu'il ne l'a jamais été.
    On ne compare donc que le TITRE, qui porte le paramètre de la variante.
    """
    if not caption:
        return ""
    m = re.search(r"—\s*(.+?)\s*\(épisode", caption)
    if not m:
        return ""
    return _norm(m.group(1))


def present_dans_contenu(video_id, caption=None, driver=None):
    """(Trouvé, extrait, video_id_en_ligne) si la vidéo est DÉJÀ publiée sur le compte.

    09/10/2026 — le contrôle par « 24 premiers caractères de la légende » produisait un
    faux positif : ces 24 caractères sont le HEADLINE, partagé par les 4 variantes d'un
    scénario. La base s'est alors désynchronisée du compte (auto_070 marquée PUBLISHED,
    auto_069 — réellement en ligne — restée FAILED), ce qui,a créé le 02/10 et entretenu
    les doublons du patron.

    On ne compare plus que des marqueurs propres à UNE vidéo :
      1. l'identifiant du fichier dans la légende (auto_041) — infaillible ;
      2. le numéro d'épisode « (épisode 41) » ↔ auto_041 ;
      3. le TITRE distinctif (la partie qui porte le paramètre de la variante).
    Le video_id réellement trouvé est renvoyé : s'il diffère, c'est qu'UNE AUTRE variante
    du même scénario est en ligne, et l'appelant doit le savoir (cf. studio.publish_next).
    """
    d = driver or ensure_chrome()
    try:
        d.get(CONTENT_URL)
    except WebDriverException as exc:
        print(f"[contenu] navigation impossible : {exc.__class__.__name__}", flush=True)
        return False, "", None
    time.sleep(9)

    mp4 = VIDEOS / "ready" / f"{video_id}.mp4"
    duree = ""
    if mp4.exists():
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", str(mp4)],
                capture_output=True, text=True, timeout=30)
            duree = "00:%02d" % round(float(out.stdout.strip()))
        except (ValueError, OSError, subprocess.SubprocessError):
            duree = ""

    cartes = _cartes_contenu(d)
    print(f"[contenu] {len(cartes)} publication(s) lue(s), durée visée {duree or '?'}",
          flush=True)
    titre = _titre_distinctif(caption)
    for c in cartes:
        carte = (c.get("carte") or "")
        if not carte:
            continue
        if video_id in carte:                       # 1. l'id du fichier est dans la légende
            return True, carte, video_id
        id_carte = _id_depuis_carte(carte)
        if id_carte and id_carte == video_id:       # 2. même numéro d'épisode
            return True, carte, id_carte
        if titre and len(titre) >= 12 and titre in _norm(carte):   # 3. titre distinctif
            return True, carte, id_carte or video_id
    # ALERTE (pas un blocage) : une publication de même durée à légende cassée peut être
    # un envoi déjà parti dont on n'a aucune trace. Deux vidéos peuvent durer 26 s sans
    # être la même : bloquer là-dessus empêcherait un post légitime, donc on se contente
    # de le signaler et l'homme tranche.
    if duree:
        for c in cartes:
            if c.get("duree") == duree and not re.search(r"\(épisode", c.get("carte") or ""):
                print(f"[contenu] ⚠ publication de même durée ({duree}) à légende cassée : "
                      f"{(c.get('carte') or '')[:80]}", flush=True)
                break
    return False, "", None
    # ALERSE (pas un blocage) : une publication de même durée à légende cassée peut être
    # un envoi déjà parti dont on n'a aucune trace. Deux vidéos peuvent durer 26 s sans
    # être la même : bloquer là-dessus empêcherait un post légitime, donc on se contente
    # de le signaler et l'homme tranche.
    if duree:
        for c in cartes:
            if c.get("duree") == duree and not re.search(r"\(épisode", c.get("carte") or ""):
                print(f"[contenu] ⚠ publication de même durée ({duree}) à légende cassée : "
                      f"{(c.get('carte') or '')[:80]}", flush=True)
                break
    return False, ""


def set_state(video_id, state, **fields):
    qf = VIDEOS / "queue.json"
    q = json.loads(qf.read_text(encoding="utf-8")) if qf.exists() else []
    e = next((x for x in q if x["video_id"] == video_id), None)
    if e is None:
        e = {"video_id": video_id, "file": f"ready/{video_id}.mp4"}
        q.append(e)
    e.update(state=state, **fields)
    qf.write_text(json.dumps(q, ensure_ascii=False, indent=2), encoding="utf-8")


def fs_caption(caption):
    """Légende rendue utilisable comme NOM DE FICHIER Windows.

    02/10/2026 — TikTok Studio recopie le nom du fichier dans la description. Or le
    champ description de cette page refuse TOUTE frappe (send_keys, touches CDP, clic
    souris : mesuré, aucun effet) et `Input.insertText` écrit dans le DOM sans mettre à
    jour l'état Draft.js — la vidéo partait donc avec « auto_041 » comme légende. La
    seule voie fiable est donc de nommer le fichier comme la légende.
    Windows interdit \\ / : * ? " < > | dans un nom de fichier : seul « ? » est
    remplacé (par « ? » pleine largeur, qui se lit pareil), le reste est sans effet.
    """
    txt = re.sub(r'[\\/:*"<>|]', '', caption or "")
    txt = txt.replace("?", "\uff1f")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt[:210]


def _fichier_a_envoyer(mp4, legende):
    """Copie la vidéo sous le nom de la légende, dans un chemin court (< MAX_PATH)."""
    for base in (Path(r"C:\jv"), Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "jv"):
        try:
            base.mkdir(parents=True, exist_ok=True)
            cible = base / f"{legende}.mp4"
            shutil.copy2(mp4, cible)
            if cible.exists() and len(str(cible)) < 250:
                return cible
        except OSError:
            continue
    return mp4


def publish(video_id, caption=None):
    meta = json.loads((VIDEOS / "metadata" / f"{video_id}.json").read_text(encoding="utf-8"))
    mp4 = VIDEOS / "ready" / f"{video_id}.mp4"
    if not caption:
        caption = meta["caption"]
    legende = fs_caption(caption)          # ce que TikTok affichera réellement
    d = ensure_chrome()
    d.get(UPLOAD_URL)
    time.sleep(5)
    a_envoyer = _fichier_a_envoyer(mp4, legende)
    print(f"[envoi] fichier : {a_envoyer.name[:70]}… ({len(str(a_envoyer))} car.)", flush=True)
    find_retry(d, By.CSS_SELECTOR, 'input[type="file"]', tries=12, sleep=2).send_keys(
        str(a_envoyer))

    for _ in range(60):  # attend la fin de l'import (max ~5 min)
        time.sleep(5)
        # La page est reconstruite en boucle pendant l'import : « illisible » = pas
        # encore prêt, on continue d'attendre au lieu de planter (cf. 30/09/2026).
        if page_says(d, "Importé", "Uploaded"):
            break
    else:
        set_state(video_id, "FAILED", error="import TikTok Studio non terminé")
        sys.exit("import non terminé")

    # Ferme les fenêtres d'info éventuelles. ATTENTION : on ne clique JAMAIS « Annuler »,
    # ce bouton annule l'import en cours sur le formulaire TikTok Studio — il détruit le
    # champ description et la vidéo part sans légende (01/10/2026, 19h24).
    for _ in range(3):
        if not click_button(d, "J'ai compris"):
            break

    # La description doit contenir la légende. Elle y est DÉJÀ : TikTok l'a recopiée
    # depuis le nom du fichier. On vérifie donc, et seulement si le champ a bougé on
    # tente une réécriture (sélection + Input.insertText).
    if not ensure_caption(d, legende):
        print(f"[legende] champ après 4 essais : {_field_text(d)[:150]!r}", flush=True)
        print(f"[legende] éditeur présent : "
              f"{bool(d.find_elements(By.CSS_SELECTOR, '.public-DraftEditor-content'))}",
              flush=True)
        set_state(video_id, "FAILED", error="légende non saisie (champ absent ou écrasé par TikTok)")
        sys.exit("légende non saisie")

    for _ in range(24):
        if not page_says(d, "Chargement"):
            break
        time.sleep(2.5)

    # dernière vérification stricte juste avant l'envoi (réécrit si TikTok a réécrit)
    if not ensure_caption(d, legende, tries=3):
        set_state(video_id, "FAILED", error="légende perdue juste avant Publier")
        sys.exit("légende perdue avant Publier")

    # Bouton Publier : clic sur le nœud VISIBLE (le premier `[data-e2e]` peut être un
    # doublon invisible -> clic « réussi » sans effet réel, d'où les « sans preuve » du
    # 15/10 soir) et surtout VÉRIFICATION de l'effet : URL/champ/confirmation/bouton
    # désactivé. Sans effet observable, on réessaie au lieu de croire à un succès.
    posted = False
    for _ in range(8):
        try:
            etat = d.execute_script("""
                var bs = document.querySelectorAll('[data-e2e="post_video_button"]');
                var btn = null;
                for (var i = 0; i < bs.length; i++) {
                    var r = bs[i].getBoundingClientRect();
                    if (r.width > 0 && r.height > 0 &&
                        getComputedStyle(bs[i]).visibility !== 'hidden') { btn = bs[i]; break; }
                }
                if (!btn) return 'absent';
                btn.scrollIntoView({block: 'center'});
                btn.click();
                return 'clic';
            """)
        except WebDriverException:
            time.sleep(1.5)
            continue
        if etat != "clic":
            time.sleep(1.5)
            continue
        time.sleep(3)
        # effet observable ? (navigation, bouton parti/désactivé, fenêtre de confirmation)
        effet = ("tiktokstudio/content" in d.current_url) or page_says(
            d, "Publier maintenant", "Publier quand même", "Continuer")
        if not effet:
            try:
                dispo = d.execute_script("""
                    var b = document.querySelector('[data-e2e="post_video_button"]');
                    if (!b) return false;                 // bouton parti = effet
                    var r = b.getBoundingClientRect();
                    if (r.width <= 0 || r.height <= 0) return false;
                    return b.disabled || b.getAttribute('aria-disabled') === 'true';
                """)
                # False = absent/invisible (effet) ; True = désactivé (envoi en cours, effet)
                # Seul « toujours visible et actif » = clic sans effet.
                effet = dispo is not None and dispo in (True, False) and not d.execute_script(
                    "var b=document.querySelector('[data-e2e=\"post_video_button\"]');"
                    "if(!b) return false;var r=b.getBoundingClientRect();"
                    "return r.width>0&&r.height>0&&!b.disabled&&"
                    "b.getAttribute('aria-disabled')!=='true';")
            except WebDriverException:
                effet = False
        if effet:
            posted = True
            break
        print("[publier] clic « Publier » sans effet visible -> nouvel essai", flush=True)
        time.sleep(2)
    if not posted:
        set_state(video_id, "FAILED", error="bouton Publier introuvable ou non cliquable")
        sys.exit("bouton Publier indisponible")
    time.sleep(4)
    # Confirmation éventuelle après « Publier » (ex. vérification de contenu / droits d'auteur)
    for label in ("Publier maintenant", "Publier quand même", "Continuer", "Publier"):
        if "tiktokstudio/content" in d.current_url:
            break
        if click_button(d, label):
            print(f"fenêtre de confirmation validée : {label}")
            time.sleep(3)

    # Preuve réelle : la vidéo doit figurer dans la liste Contenu de TikTok Studio.
    # La liste met parfois 30-60 s à afficher le nouveau post : on réessaie (30 × 6 s).
    # La recherche porte sur l'IDENTIFIANT du fichier, que la légende contient désormais,
    # et non sur les 25 premiers caractères (trop fragile : le 01/10/2026 une légende
    # tronquée a fait croire à une publication réussie).
    body, found = "", False
    for _ in range(30):
        time.sleep(6)
        if "tiktokstudio/content" not in d.current_url:
            d.get(CONTENT_URL)
            time.sleep(5)
        body = body_text(d) or ""
        if video_id in body or (caption and _norm(caption)[:24] in _norm(body)):
            found = True
            break
    if found:
        set_state(video_id, "PUBLISHED", error=None, caption=legende,
                  published_at_utc=datetime.now(timezone.utc).isoformat(),
                  published_evidence={"method": "tiktok studio (navigateur, connexion QR)",
                                      "confirmation": "vidéo présente dans Contenu de TikTok Studio",
                                      "en_examen": "examen" in body.lower()})
        (VIDEOS / "published").mkdir(exist_ok=True)
        shutil.copy2(mp4, VIDEOS / "published" / mp4.name)
        print(f"{video_id} PUBLISHED (présente dans Contenu ; en examen={'examen' in body.lower()})")
        try:
            if a_envoyer != mp4:
                a_envoyer.unlink(missing_ok=True)
        except OSError:
            pass
    else:
        # Le clic « Publier » a déjà été fait : la vidéo PEUT être partie même si la liste
        # ne l'affiche pas encore (ou l'a affichée avec une autre légende). On ne la
        # marque surtout pas FAILED — ce serait la republier plus tard, soit le doublon
        # récurrent du patron. État PUBLISHED_SUSPECT : ni republié, ni perdu.
        shot = VIDEOS / "failed" / f"{video_id}_studio.png"
        shot.parent.mkdir(parents=True, exist_ok=True)
        try:
            d.save_screenshot(str(shot))
        except Exception:
            pass
        set_state(video_id, "PUBLISHED_SUSPECT", error=None,
                  published_at_utc=datetime.now(timezone.utc).isoformat(),
                  published_evidence={
                      "method": "tiktok studio (navigateur, connexion QR)",
                      "confirmation": "clic Publier effectué, mais absente de Contenu après 3 min",
                      "capture": shot.name})
        print(f"{video_id} CLIC « Publier » effectué mais PAS de preuve dans Contenu.\n"
              f"  → état PUBLISHED_SUSPECT (jamais republié automatiquement).\n"
              f"  → capture : {shot}", flush=True)
        sys.exit("publication sans preuve — vérification manuelle requise")


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[2] != "--confirm":
        sys.exit(__doc__)
    publish(sys.argv[1])
