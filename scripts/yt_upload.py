#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publie des vidéos de videos/ready sur YouTube (chaîne Phrazia) via Chrome CDP.

Chrome doit tourner avec le port 9222 (prepare_browser.bat) et YouTube Studio
doit être connecté. Usage :

    python scripts/yt_upload.py toon_002 toon_003
"""

import base64
import io
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from cdp import Tab, list_pages, open_tab  # noqa: E402

UPLOAD_URL = ("https://studio.youtube.com/channel/UCfRGgDMtWpsmd7LmBEY2_Lg"
              "/videos/upload")
HISTORY = os.path.join(ROOT, "logs", "youtube_posts.json")
QUEUE = os.path.join(ROOT, "videos", "queue.json")

# Verrou de lancement : DEUX yt_upload.py sur le MEME Chrome se marchent dessus
# (le second navigue l'onglet au milieu du wizard du premier → « aucune-boite »,
# « target navigated or closed », et vidéos publiées non détectées).
# Leçon du 21/10/2026 (voir docs/PROCEDURE_YOUTUBE.md §5).
LOCK = os.path.join(ROOT, "videos", ".yt_publish.lock")
LOCK_TTL = 1800            # 30 min : au-delà, le verrou est considéré orphelin
CDP_HTTP = "http://127.0.0.1:9222"


def verrou_acquerir(force=False):
    """Prend le verrou de lancement ; refuse si un autre lot tourne."""
    if os.path.exists(LOCK):
        age = time.time() - os.path.getmtime(LOCK)
        if age < LOCK_TTL and not force:
            raise SystemExit(
                f"un autre yt_upload.py tourne deja (verrou {LOCK}, "
                f"age {int(age)} s). Attendez sa fin, ou relancez avec --force "
                f"si vous etes sur qu'il est mort.")
        print(f"[verrou] ancien verrou ignore (age {int(age)} s)")
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    with io.open(LOCK, "w", encoding="utf-8") as f:
        json.dump({"pid": os.getpid(),
                   "debut_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
                  f)


def verrou_lacher():
    try:
        if os.path.exists(LOCK):
            os.remove(LOCK)
    except OSError:
        pass


def fermer_onglet_studio():
    """Ferme l'onglet Studio au niveau navigateur (HTTP), même si le renderer
    est gelé — contournement du 19/10/2026. Inoffensif si absent."""
    try:
        for p in list_pages():
            if "studio.youtube.com" in (p.get("url") or ""):
                req = urllib.request.Request(
                    CDP_HTTP + "/json/close/" + p["id"], method="PUT")
                urllib.request.urlopen(req, timeout=10).read()
    except Exception:
        pass

# Cadence imposée par le patron : lot d'essai puis 6 vidéos/jour max.
QUOTA_INITIAL = 6          # dès le 1er jour (ordre du boss : 6/jour)
QUOTA_INITIAL_DATE = "2026-10-15"
QUOTA_JOUR = 6             # à partir du lendemain

JS_CLICK_IMPORT = """(() => {
  const b = [...document.querySelectorAll('button')].find(e => /importer des vid/i.test(e.innerText || ''));
  if (!b) return 'absent';
  b.click();
  return 'ok';
})()"""

JS_FILE_COUNT = ('document.querySelectorAll("input[type=file]").length')

JS_WAIT_TITLE = ('!!document.querySelector("#title-textarea #textbox")')

JS_FILL = """(() => {
  function setBox(sel, text) {
    const el = document.querySelector(sel);
    if (!el) return 'absent';
    el.focus();
    el.textContent = text;
    el.dispatchEvent(new InputEvent('input', {bubbles: true, data: text, inputType: 'insertText'}));
    el.dispatchEvent(new Event('change', {bubbles: true}));
    return 'ok';
  }
  const t = setBox('#title-textarea #textbox', __TITLE__);
  const d = setBox('#description-textarea #textbox', __DESC__);
  const link = document.querySelector('#video-link');
  return JSON.stringify({t: t, d: d,
    title: (document.querySelector('#title-textarea #textbox') || {}).textContent || '',
    link: link ? link.href : null});
})()"""

JS_KIDS = """(() => {
  const find = () => [...document.querySelectorAll('tp-yt-paper-radio-button')]
    .find(o => /Non, elle n'est pas con/i.test(o.getAttribute('aria-label') || o.innerText || ''));
  const target = find();
  if (!target) return 'introuvable';
  if (target.checked === true || target.classList.contains('iron-selected')) return 'deja-ok';
  target.click();
  return new Promise(res => setTimeout(() => {
    const now = find();
    res(now && (now.checked === true || now.classList.contains('iron-selected'))
      ? 'ok' : 'pas-retenu');
  }, 900));
})()"""

JS_NEXT = """(() => {
  const dlg = [...document.querySelectorAll('tp-yt-paper-dialog')]
    .find(d => d.querySelector('[id=step-title-0]'));
  if (!dlg) return 'dialog-absent';
  const label = r => (r.getAttribute('aria-label') || r.innerText || '').trim();
  // étape Visibilité = radios Privée / Non répertoriée / Publique présentes
  const vis = [...dlg.querySelectorAll('tp-yt-paper-radio-button')]
    .some(r => label(r).toLowerCase().startsWith('priv'));
  if (vis) return 'au-visibilite';
  const b = [...dlg.querySelectorAll('ytcp-button')].find(x => {
    const t = (x.innerText || '').trim();
    return t === 'Suivant' && x.getBoundingClientRect().width > 0 &&
      !(x.disabled === true || x.getAttribute('aria-disabled') === 'true');
  });
  if (!b) return 'attente';
  b.click();
  return 'suivant';
})()"""

JS_SET_PUBLIC = """(() => {
  const dlg = [...document.querySelectorAll('tp-yt-paper-dialog')]
    .find(d => d.querySelector('[id=step-title-0]'));
  if (!dlg) return null;                       // -> wait_js réessaie
  const label = r => (r.getAttribute('aria-label') || r.innerText || '').trim();
  const radios = [...dlg.querySelectorAll('tp-yt-paper-radio-button')];
  const pub = radios.find(r => label(r).toLowerCase().startsWith('publique'));
  if (!pub) return null;                       // -> wait_js réessaie
  pub.click();
  return new Promise(res => setTimeout(() => {
    const now = [...dlg.querySelectorAll('tp-yt-paper-radio-button')]
      .find(r => label(r).toLowerCase().startsWith('publique'));
    const btns = [...dlg.querySelectorAll('ytcp-button')]
      .map(x => ({t: (x.innerText || '').trim(),
                  w: Math.round(x.getBoundingClientRect().width),
                  dis: x.disabled === true || x.getAttribute('aria-disabled') === 'true'}))
      .filter(x => x.w > 0);
    res(JSON.stringify({ok: !!(now && (now.checked === true || now.classList.contains('iron-selected'))),
                        btns: btns}));
  }, 900));
})()"""

JS_PUBLISH = """(() => {
  const dlg = [...document.querySelectorAll('tp-yt-paper-dialog')]
    .find(d => d.querySelector('[id=step-title-0]'));
  if (!dlg) return 'dialog-absent';
  const b = [...dlg.querySelectorAll('ytcp-button')].find(x => {
    const t = (x.innerText || '').trim();
    return t === 'Publier' && x.getBoundingClientRect().width > 0 &&
      !(x.disabled === true || x.getAttribute('aria-disabled') === 'true');
  });
  if (!b) return 'absent';
  b.click();
  return 'ok';
})()"""

JS_CONFIRM = """(() => {
  const vis = [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog')]
    .filter(x => x.getBoundingClientRect().width > 0);
  // cas 1 : « Vidéo mise en ligne » avec le lien
  let d = vis.find(x => /Vidéo mise en ligne/.test(x.innerText || ''));
  if (d) {
    const link = [...d.querySelectorAll('a[href]')]
      .map(a => a.href).find(h => /youtu\\.(be|com)\\//.test(h)) || null;
    const fermer = [...d.querySelectorAll('ytcp-button')]
      .some(x => (x.innerText || '').trim() === 'Fermer' && x.getBoundingClientRect().width > 0);
    return JSON.stringify({ok: true, type: 'online', link: link, fermer: fermer});
  }
  // cas 2 : « Traitement de la vidéo » = publié, deviendra publique après le
  // traitement SD (l'écran dit explicitement « pour que la vidéo soit publiée »)
  d = vis.find(x => /Traitement de la vidéo/.test(x.innerText || ''));
  if (d) {
    const fermer = [...d.querySelectorAll('ytcp-button')]
      .some(x => (x.innerText || '').trim() === 'Fermer' && x.getBoundingClientRect().width > 0);
    return JSON.stringify({ok: true, type: 'processing', link: null, fermer: fermer});
  }
  return false;
})()"""

JS_CLOSE_CONFIRM = """(() => {
  const d = [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog')]
    .find(x => /(Vidéo mise en ligne|Traitement de la vidéo)/.test(x.innerText || '')
      && x.getBoundingClientRect().width > 0);
  if (!d) return 'absent';
  const b = [...d.querySelectorAll('ytcp-button')]
    .find(x => (x.innerText || '').trim() === 'Fermer' && x.getBoundingClientRect().width > 0);
  if (!b) return 'pas-de-fermer';
  b.click();
  return 'ok';
})()"""


# --------------------------------------------------------------------------- #
#  utilitaires
# --------------------------------------------------------------------------- #
def get_tab():
    """Onglet YouTube Studio sur la page d'import (ouvert au besoin) + connexion CDP.

    Priorité : un onglet déjà sur /videos/upload ; sinon on réutilise un onglet
    Studio existant et on le NAVIGUE vers la page d'import (la page d'import
    est le seul endroit où le bouton « Importer des vidéos » et le champ fichier
    existent — une page /edit ne les a pas)."""
    page = None
    for p in list_pages():
        if ("studio.youtube.com" in p.get("url", "")
                and "/videos/upload" in p.get("url", "")):
            page = p
            break
    if page is None:
        for p in list_pages():
            if "studio.youtube.com" in p.get("url", ""):
                page = p
                break
    if page is None:
        page = open_tab(UPLOAD_URL)
        time.sleep(8)
    tab = Tab(page["webSocketDebuggerUrl"])
    if "/videos/upload" not in (page.get("url") or ""):
        tab.evaluate("location.href = " + json.dumps(UPLOAD_URL) + "; 'nav'")
        time.sleep(10)
    return tab


def wait_js(tab, expr, timeout=40, poll=1.0, desc=""):
    """Attend que l'expression JS retourne une valeur truthy."""
    end = time.time() + timeout
    last = None
    while time.time() < end:
        try:
            last = tab.evaluate(expr)
        except Exception:
            last = None
        if last:
            return last
        time.sleep(poll)
    raise RuntimeError(
        f"timeout ({timeout}s) en attendant : {desc or expr[:70]} "
        f"(dernier retour : {last!r})")


def shot(tab, name):
    try:
        tab.call("Page.enable")
        res = tab.call("Page.captureScreenshot", {"format": "png"})
        path = os.path.join(ROOT, "temp", name)
        with open(path, "wb") as f:
            f.write(base64.b64decode(res["data"]))
        return path
    except Exception:
        return None


def build_texts(meta, vid):
    """Titre (<=100 car.) + description propres, sans identifiant interne."""
    title = (meta.get("title") or vid).strip()
    ep = meta.get("episode")
    tags = [h for h in (meta.get("hashtags") or [])
            if h.lower() not in ("#fyp", "#pourtoi")]
    head = (f"{title} — épisode {ep} de FactVibes Toons." if ep else title)
    desc = head + "\n\n" + " ".join(tags + ["#shorts"])
    return (title + " #shorts")[:100], desc


def load_history():
    if os.path.exists(HISTORY):
        with io.open(HISTORY, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(hist):
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    with io.open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)


CHANNEL_ID = "UCfRGgDMtWpsmd7LmBEY2_Lg"


def rss_videos():
    """Vidéos PUBLIÉES sur la chaîne — source de vérité absolue (flux RSS public,
    visible en quelques secondes après publication, brouillons exclus)."""
    import urllib.request
    import xml.etree.ElementTree as ET
    url = ("https://www.youtube.com/feeds/videos.xml?channel_id=" + CHANNEL_ID)
    with urllib.request.urlopen(url, timeout=15) as r:
        data = r.read()
    ns = {"a": "http://www.w3.org/2005/Atom",
          "yt": "http://www.youtube.com/xml/schemas/2015"}
    root = ET.fromstring(data)
    out = {}
    for e in root.findall("a:entry", ns):
        vid = e.find("yt:videoId", ns).text
        titre = (e.find("a:title", ns).text or "")
        out[vid] = {"title": titre, "norm": normalize_title(titre)}
    return out


def attend_rss(titre, timeout=150, poll=10):
    """Attend que le titre apparaisse dans le RSS public ; retourne l'URL
    canonique, ou None si la vidéo n'est pas en ligne."""
    norm = normalize_title(titre)
    fin = time.time() + timeout
    while time.time() < fin:
        try:
            for vid, info in rss_videos().items():
                if info["norm"] == norm:
                    return "https://youtube.com/shorts/" + vid
        except Exception:
            pass
        time.sleep(poll)
    return None


# --------------------------------------------------------------------------- #
#  sélection anti-doublon
# --------------------------------------------------------------------------- #
JS_GET_TITLES = """(() => {
  const norm = s => (s || '').toLowerCase()
    .replace(/#shorts/g, '')
    .replace(/[\\u{1F300}-\\u{1FAFF}\\u{2600}-\\u{27BF}]/gu, '')
    .replace(/[^a-z0-9à-ÿ]+/g, ' ').trim();
  const out = {};
  const anchors = [...document.querySelectorAll('a[href*="/video/"]')];
  for (const a of anchors) {
    const parts = (a.getAttribute('href') || '').split('/').filter(Boolean);
    const i = parts.indexOf('video');
    const id = i >= 0 ? parts[i + 1] : null;
    if (!id || out[id]) continue;
    let card = a;
    for (let k = 0; k < 8 && card; k++) {
      if ((card.innerText || '').length > 40) break;
      card = card.parentElement;
    }
    if (!card) continue;
    const lines = (card.innerText || '').split('\\n')
      .map(s => s.trim()).filter(Boolean)
      .filter(s => !/^\\d+:\\d+$/.test(s));        // retire la durée
    if (lines.length) out[id] = {title: lines[0], norm: norm(lines[0])};
  }
  return JSON.stringify(out);
})()"""


def normalize_title(t):
    """Même normalisation que JS_GET_TITRES (comparaison anti-doublon)."""
    import re
    t = (t or "").lower().replace("#shorts", "")
    t = re.sub(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]", "", t)
    return re.sub(r"[^a-z0-9à-ÿ]+", " ", t).strip()


def tiktok_published():
    """Vidéos PUBLISHED sur TikTok (source : videos/queue.json), tri ancien->récent."""
    if not os.path.exists(QUEUE):
        return []
    with io.open(QUEUE, encoding="utf-8") as f:
        q = json.load(f)
    pub = [e for e in q if e.get("state") == "PUBLISHED"]
    pub.sort(key=lambda e: str(e.get("published_at_utc") or ""))
    return [e["video_id"] for e in pub]


def quota_restant(hist, date_utc=None):
    """Combien de vidéos on a le droit de poster aujourd'hui."""
    from collections import Counter
    jour = date_utc or time.strftime("%Y-%m-%d", time.gmtime())
    deja = Counter(str(v.get("published_utc", ""))[:10] for v in hist.values())
    limite = QUOTA_INITIAL if jour == QUOTA_INITIAL_DATE else QUOTA_JOUR
    return max(0, limite - deja[jour]), limite


def select_candidates(hist, channel_titles=None, limit=1):
    """Candidates = postées TikTok - déjà sur YouTube (par id ET par titre)."""
    yt_norms = {normalize_title(v.get("title") or "") for v in hist.values()}
    if channel_titles:
        yt_norms |= {c["norm"] for c in channel_titles.values() if c.get("norm")}
    out = []
    for vid in tiktok_published():
        if vid in hist:                       # déjà postée (id)
            continue
        mpath = os.path.join(ROOT, "videos", "metadata", vid + ".json")
        if not os.path.exists(mpath):
            continue
        with io.open(mpath, encoding="utf-8") as f:
            title = json.load(f).get("title") or ""
        if normalize_title(title) in yt_norms:  # déjà postée (titre)
            continue
        out.append(vid)
        if len(out) >= limit:
            break
    return out


def get_channel_titles(tab):
    """Titres des vidéos déjà en ligne sur la chaîne (anti-doublon live)."""
    try:
        raw = tab.evaluate(JS_GET_TITLES)
        return json.loads(raw) if raw else {}
    except Exception:
        return {}


# --------------------------------------------------------------------------- #
#  publication d'une vidéo
# --------------------------------------------------------------------------- #
def publish_one(tab, vid, timeout_upload=90):
    video_path = os.path.join(ROOT, "videos", "ready", vid + ".mp4")
    meta_path = os.path.join(ROOT, "videos", "metadata", vid + ".json")
    if not os.path.exists(video_path):
        raise FileNotFoundError(video_path)
    meta = {}
    if os.path.exists(meta_path):
        with io.open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    title, desc = build_texts(meta, vid)

    # 0. fermer une éventuelle fenêtre de confirmation résiduelle
    tab.evaluate(JS_CLOSE_CONFIRM)
    time.sleep(1)

    # 1. ouvrir la fenêtre d'import (inutile si déjà ouverte)
    base = tab.evaluate(JS_FILE_COUNT) or 0
    if base == 0:
        if (tab.evaluate(JS_CLICK_IMPORT) or '') == 'absent':
            print("   (bouton Importer absent, la fenêtre est peut-être déjà ouverte)")
        try:
            wait_js(tab, f'{JS_FILE_COUNT} > {base}', timeout=25, poll=0.7,
                    desc="apparition du champ fichier")
        except RuntimeError:
            if not (tab.evaluate(JS_FILE_COUNT) or 0):
                shot(tab, "upload_error_import.png")
                raise
    else:
        print("   (fenêtre d'import déjà ouverte)")

    # 2. envoyer le fichier
    tab.set_file_inputs([video_path.replace("\\", "/")])
    print(f"   fichier envoyé : {os.path.basename(video_path)}")

    # 3. attendre le formulaire, remplir
    wait_js(tab, JS_WAIT_TITLE, timeout=timeout_upload, poll=1.5,
            desc="formulaire de détails")
    fill = json.loads(tab.evaluate(
        JS_FILL.replace("__TITLE__", json.dumps(title))
               .replace("__DESC__", json.dumps(desc))))
    if fill.get("t") != "ok" or fill.get("d") != "ok":
        raise RuntimeError(f"remplissage incomplet: {fill}")
    print(f"   titre : {fill['title']}")
    link = fill.get("link")

    # 4. audience : pas conçu pour les enfants
    kids = wait_js(tab, JS_KIDS, timeout=15, poll=1.0, desc="choix audience")
    print(f"   audience : {kids}")
    time.sleep(1)

    # 5. avancer jusqu'à l'étape Visibilité
    #    (le bouton "Suivant" reste désactivé pendant l'import : parfois
    #     plusieurs minutes. On patiente jusqu'à 10 min et on journalise
    #     la progression pour diagnostiquer.)
    JS_STATUS = """(() => {
      const d = [...document.querySelectorAll('tp-yt-paper-dialog, ytcp-dialog')]
        .find(x => x.getBoundingClientRect().width > 0 &&
                   (x.querySelector('[id=step-title-0]') || /Détails/.test(x.innerText||'')));
      if (!d) return 'aucune-boite';
      const t = (d.innerText || '').replace(/\\s+/g, ' ');
      const m = t.match(/(\\d{1,3})\\s?%/);
      if (/Importation/i.test(t)) return m ? ('import ' + m[1] + '%') : 'import';
      if (/Traitement/i.test(t)) return 'traitement';
      return 'formulaire';
    })()"""
    steps = 0
    last_state = None
    vu_dialogue = False            # la boîte d'import a été vue au moins une fois
    sans_boite = 0                 # itérations consécutives sans aucune boîte
    for i in range(300):           # ~300 × 2 s = 10 min max
        r = tab.evaluate(JS_NEXT)
        if r != last_state:
            print(f"   [nav {i}] {r}")
            last_state = r
        if r in ("attente", "suivant", "au-visibilite"):
            vu_dialogue = True
            sans_boite = 0
        elif r == "aucune-boite":
            sans_boite += 1
            # La boîte avait été vue puis a disparu : l'assistant a été volé par
            # un AUTRE yt_upload (navigation de l'onglet) ou le renderer est gelé.
            # Inutile d'attendre 10 min : on sort et on laisse la vérification
            # RSS décider (la vidéo peut être partie quand même — cas auto_012).
            if vu_dialogue and sans_boite > 45:     # ~90 s sans aucune boîte
                raise RuntimeError(
                    "assistant d'import disparu (onglet repris par un autre "
                    "processus ou renderer gelé) — vérification RSS obligatoire")
        if r == "suivant":
            steps += 1
            time.sleep(2.5)
            continue
        if r == "au-visibilite":
            break                   # étape Visibilité atteinte
        if i % 15 == 0:             # ~toutes les 30 s : log de progression
            try:
                print(f"   [nav {i}] état : {tab.evaluate(JS_STATUS)}")
            except Exception:
                pass
        time.sleep(2)               # bouton absent/désactivé : on réessaie
    else:
        shot(tab, "upload_error_nav.png")
        raise RuntimeError("étape Visibilité jamais atteinte")
    if steps == 0:
        raise RuntimeError("aucun clic Suivant n'a abouti")

    # 6. visibilité publique
    pub = json.loads(wait_js(tab, JS_SET_PUBLIC, timeout=20, poll=1.0,
                             desc="étape visibilité"))
    if not pub.get("ok"):
        shot(tab, "upload_error_visibility.png")
        raise RuntimeError(f"visibilité publique non sélectionnée: {pub}")

    # 7. publier
    wait_js(tab, JS_PUBLISH, timeout=20, poll=1.0, desc="bouton Publier")
    print("   clic sur Publier…")

    # 8. confirmation « Vidéo mise en ligne » — DEUX signaux acceptés :
    #    le dialogue de confirmation, OU la navigation vers l'état « d=ud »
    #    (upload done) de la page d'import. Cas réel du 18/10 : via_002
    #    publiée mais dialogue non détecté → rejetée à tort.
    JS_CONFIRM2 = JS_CONFIRM.replace(
        "(() => {",
        "(() => {\n  if ((location.href || '').indexOf('d=ud') > -1)"
        " return JSON.stringify({ok: true, type: 'd-ud', link: null});",
        1)
    try:
        conf = json.loads(wait_js(tab, JS_CONFIRM2, timeout=120, poll=2.0,
                                  desc="confirmation de publication"))
        link = conf.get("link") or link
        print(f"   confirmation : {conf.get('type') or 'dialogue'}")
        tab.evaluate(JS_CLOSE_CONFIRM)
    except RuntimeError:
        u = tab.evaluate("location.href") or ""
        if "d=ud" not in u:
            raise
        print("   confirmation : état d=ud (upload done)")
    time.sleep(2)
    return link or "?"


def main():
    import atexit
    verrou_acquerir(force="--force" in sys.argv)
    atexit.register(verrou_lacher)

    vids = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not vids:
        print(__doc__)
        return 1

    hist = load_history()
    tab = get_tab()

    # mode quotidien : on ne choisit PAS, on prend les candidates anti-doublon
    # dans l'ordre chronologique TikTok, dans la limite du quota du jour.
    if "--daily" in sys.argv:
        restant, limite = quota_restant(hist)
        print(f"Quota du jour : {restant}/{limite} restant(s)")
        if restant == 0:
            print("Objectif du jour déjà atteint — rien à publier.")
            return 0
        # --limit N : ne publier que N vidéos de ce lot (le reste plus tard ;
        # le quota journalier reste global et tient compte de ce qui est déjà en ligne)
        if "--limit" in sys.argv:
            try:
                restant = min(restant, int(sys.argv[sys.argv.index("--limit") + 1]))
            except (ValueError, IndexError):
                pass
        # on rafraîchit d'abord les titres de la chaîne (doublons live)
        try:
            tab.evaluate("location.href = location.href; 'reload'")
            time.sleep(6)
        except Exception:
            pass
        chan = get_channel_titles(tab)
        # vérité absolue en plus : le RSS public (publié seulement,
        # brouillons exclus) — indépendant de l'état de l'interface Studio
        try:
            for vid_yt, info in rss_videos().items():
                chan[vid_yt] = {"title": info["title"], "norm": info["norm"]}
            print(f"Anti-doublon : {len(chan)} titres vérifiés (Studio + RSS public)")
        except Exception as exc:
            print(f"RSS public indisponible ({exc}) : dédup limitée à Studio + historique")
        vids = select_candidates(hist, chan, limit=restant)
        print(f"Candidates retenues ({len(vids)}) : {', '.join(vids) or 'aucune'}")
        if not vids:
            print("Plus rien à publier (tout est déjà en ligne).")
            return 0
    else:
        vids = [a for a in sys.argv[1:] if not a.startswith("-")]
        if not vids:
            print(__doc__)
            return 1

    failures = 0
    for vid in vids:
        if hist.get(vid, {}).get("url"):
            print(f"[skip] {vid} déjà publiée : {hist[vid]['url']}")
            continue
        mpath = os.path.join(ROOT, "videos", "metadata", vid + ".json")
        title = ""
        if os.path.exists(mpath):
            with io.open(mpath, encoding="utf-8") as f:
                title = json.load(f).get("title") or ""

        # état propre : on (re)navigue vers la page d'import et on ferme les
        # boîtes résiduelles — l'état laissé par le wizard précédent empoisonne
        # le suivant (constaté le 18/10 : via_001 bloqué, via_003 sans champ).
        try:
            tab.evaluate("location.href = " + json.dumps(UPLOAD_URL) + "; 'nav'")
            time.sleep(10)
            tab.evaluate(JS_CLOSE_CONFIRM)
            time.sleep(2)
        except Exception:
            pass

        print(f"[start] {vid}")
        url = None
        try:
            url = publish_one(tab, vid)
        except Exception as exc:
            print(f"[echec-interface] {vid} : {exc}")
            # On ne RÉUTILISE jamais un onglet qui a lâché en cours de route :
            # il a été volé par un autre processus ou son renderer est gelé.
            print("   (fermeture de l'onglet Studio + ouverture d'un onglet neuf)")
            fermer_onglet_studio()
            time.sleep(3)
            tab = get_tab()

        # VÉRITÉ RSS : publié = présent dans le flux public, quelle que soit
        # la parole de l'interface. Une confirmation « perdue » n'est donc
        # plus un échec si la vidéo est réellement en ligne.
        # 240 s au lieu de 60 quand l'interface a échoué : une vidéo peut
        # apparaître en RSS plusieurs minutes après (cas mesuré auto_012, 21/10).
        url_rss = attend_rss(title, timeout=150 if url else 240)
        if url_rss:
            url_final = url_rss if url in (None, "?") else url
            if url in (None, "?"):
                print("   confirmé via RSS (l'interface n'avait pas confirmé)")
            hist[vid] = {"url": url_final, "title": title,
                         "published_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                        time.gmtime())}
            save_history(hist)
            print(f"[ok] {vid} -> {url_final}")
        elif url and url != "?":
            # dialogue de confirmation vu mais RSS pas encore à jour :
            # on enregistre quand même (preuve forte), RSS complétera
            hist[vid] = {"url": url, "title": title,
                         "published_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                        time.gmtime()),
                         "note": "confirmation interface ; RSS à confirmer"}
            save_history(hist)
            print(f"[ok?] {vid} -> {url} (RSS pas encore à jour)")
        else:
            failures += 1
            print(f"[echec] {vid} : pas en ligne (RSS) — brouillon possible à nettoyer")
        time.sleep(3)

    print(f"\nTerminé : {len(vids) - failures}/{len(vids)} publié(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
