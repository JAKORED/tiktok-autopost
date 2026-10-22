"""Pack d'audit TikTok — prepare un dossier/zipe a televerser a ChatGPT (lecture seule).

Capture 3 ecrans (profil public, statistiques Studio, liste Contenu) + leurs textes,
puis ecrit un dossier d audit a partir de videos/queue.json (66 publications).

  python scripts/pack_audit.py            # dossier audit_factivibes_<date>
  python scripts/pack_audit.py --zip      # + archive .zip (a glisser dans ChatGPT)

Aucune publication, aucune ecriture sur le compte : uniquement lecture + captures.
"""
import argparse
import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CDP = "http://127.0.0.1:9222"
TODAY = datetime.now().strftime("%Y%m%d")
PACK = ROOT / "audit_factivibes_2210"
CAPTURES = PACK / "04_CAPTURES"
VIDEOS = PACK / "03_EXEMPLES_VIDEOS"

ECRANS = [
    ("profil_public", "https://www.tiktok.com/@factivibeparano"),
    ("stats_studio", "https://www.tiktok.com/tiktokstudio/analytics"),
    ("liste_contenu", "https://www.tiktok.com/tiktokstudio/content"),
]

# une carte de la liste Contenu commence par sa duree (mm:ss) sur sa propre ligne
DUREE = re.compile(r"^\d{2}:\d{2}$")


def _http(path, method="GET"):
    req = urllib.request.Request(CDP + path, method=method)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


class Tab:
    def __init__(self, ws_url):
        import websocket
        self.ws = websocket.create_connection(ws_url, timeout=120, suppress_origin=True)
        self.mid = 0

    def call(self, method, params=None):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": method,
                                 "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"].get("message", "erreur CDP"))
                return msg.get("result", {})

    def evaluate(self, expr):
        res = self.call("Runtime.evaluate", {"expression": expr,
                                             "returnByValue": True,
                                             "awaitPromise": True})
        return (res.get("result") or {}).get("value")


def capture(nom, url, attente=12):
    """Ouvre un onglet propre, capture l ecran + le texte, puis FERME l onglet."""
    p = _http("/json/new?" + urllib.parse.quote(url, safe=":/?&="), method="PUT")
    tid = p["id"]
    print(f"[capture] {nom} -> {url}")
    try:
        tab = Tab(p["webSocketDebuggerUrl"])
        tab.call("Page.enable")
        time.sleep(attente)
        # certains blocs (bandeau cookies, onglet non actif) demandent un second temps
        texte = tab.evaluate(
            "document.body ? (document.body.innerText||'').slice(0,6000) : ''") or ""
        (PACK / "04_CAPTURES" / f"{nom}.txt").write_text(texte, encoding="utf-8")
        tab.call("Page.bringToFront")
        time.sleep(2)
        res = tab.call("Page.captureScreenshot", {"format": "png"})
        import base64
        (CAPTURES / f"{nom}.png").write_bytes(base64.b64decode(res["data"]))
        print(f"[capture] OK {nom}.png ({len(texte)} car. de texte)")
        return texte
    except Exception as exc:
        print(f"[capture] ECHEC {nom} : {exc}", file=sys.stderr)
        return ""
    finally:
        try:
            _http(f"/json/close/{tid}", method="PUT")
        except Exception:
            pass


def publications():
    q = json.loads((ROOT / "videos" / "queue.json").read_text(encoding="utf-8"))
    pub = [e for e in q if e.get("state") in ("PUBLISHED", "PUBLISHED_SUSPECT")]
    pub.sort(key=lambda e: str(e.get("published_at_utc") or ""))
    return pub, q


def ecrire_markdown(pub, q, textes):
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    sch = cfg.get("posting_schedule", {})

    demande = f"""# DEMANDE A CHATGPT — Audit de la chaine TikTok FactVibes

Tu examines une chaine TikTok de dessins animes originaux, publiee de facon
automatisee par un pipeline Python (non, pas pour le dire : pour comprendre
les contraintes techniques decrites plus bas).

**Ce qu on veut de toi, AVANT qu on produise de nouvelles videos :**

1. Un DIAGNOSTIC honnete de la chaine : positionnement, accroche, constance,
   format (28-31 s), rythme, points faibles visibles dans les donnees.
2. Une liste CHIFFREE et PRIORISEE de CHANGEMENTS a faire (legende, hook des
   3 premieres secondes, structure du gag, format, horaires de publication,
   hashtags, serie/continuite, identite visuelle, appels a l interaction).
3. Ce qu on ne doit PAS changer (ce qui marche deja).
4. Un PLAN CONCRET pour les 10 prochaines videos (sujets, hooks, dur\u00e9es cibles).

**Fichiers joints** (dans ce meme dossier) :
- `01_CHAINE.md` — qui on est, regles de publication, contraintes techniques
- `02_PUBLICATIONS.md` — les {len(pub)} videos publiees (dates, legendes, hashtags)
- `02B_PERFORMANCE_RECENTE.md` — **vues / likes / commentaires** des dernieres videos
- `03_EXEMPLES_VIDEOS/` — {len(list(VIDEOS.glob('*.mp4')))} videos reelles a regarder (mp4) + leurs metadonnees
- `04_CAPTURES/` — captures d ecran {len(list(CAPTURES.glob('*.png')))} ecrans (profil, statistiques 7 jours, liste des contenus)
- `05_STATS/STATISTIQUES.md` — followers, vues, likes, sources de trafic, recherches

Reponds en francais, sois direct, et ne te contente pas de conseils generiques :
appuie-toi sur les legendes et les videos que tu vois.
"""
    (PACK / "00_DEMANDE_A_CHATGPT.md").write_text(demande, encoding="utf-8")

    chaine = f"""# La chaine — FactVibes (TikTok)

- Compte : **@factivibeparano** — https://www.tiktok.com/@factivibeparano
- Concept : **dessins animes originaux courts** (humour de bureau / quotidien),
  rendus 100 % en local (pycairo + edge-tts + ffmpeg), 100 % libres de droits.
- Duree des videos : **26 a 31 secondes** (format court, gag unique).
- Compteur de publications au {datetime.now().strftime('%d/%m/%Y')} : **{len(pub)}**
  marquees publiees en base (le compteur du compte TikTok Studio affiche lui
  **{_compteur_publications(_lecture('liste_contenu'))}** — ecart connu, la file
  locale n est qu une approximation : voir 05_STATS/STATISTIQUES.md).
- Performances des 7 derniers jours + vues par video : **02B_PERFORMANCE_RECENTE.md**
  et **05_STATS/STATISTIQUES.md** (c est la que se trouve l information utile).
- Volume : jusqu'a **{sch.get('posts_per_day', 3)} videos par jour**, une toutes les
  {sch.get('min_minutes_between_posts', 30)} minutes, creneaux
  {', '.join(sch.get('post_times_utc', []))} UTC (= 19h-20h Paris).
- Publications par jour depuis le 16/09/2026, tres peu de jours sans post.

## Regles de legende (ecrites par le proprietaire, a ne pas casser)
- Format : `HOOK MAJUSCULES — titre (episode N). question #tags`
- Maximum 5 hashtags, **jamais #fyp / #viral / #pourtoi**
- Une question en fin de legende (comment-bait)
- **Jamais d identifiant interne** (`auto_XXX`) visible : risque de ban
  (l algo TikTok lit ca comme du contenu automatise).

## Contraintes techniques (elles limitent ce qu on peut changer)
- Publication via TikTok Studio dans un Chrome pilote en CDP ; le champ de
  legende n accepte pas le clavier -> **le nom du fichier du mp4 devient la
  legende** (d ou le format ci-dessus).
- Anti-doublon severe : 1 seul scenario = 1 seule video (4 variantes identiques
  existent en interne, toutes bloquees sauf une), empreinte visuelle, signature
  de script. Toute video deja sortie n est jamais republiee.
- Banque de scenarios : {len({e.get('video_id','') for e in q})} videos produites
  au total dans la base, {len(pub)} publiees.

## Situation actuelle
- Tampon de videos pretes : **0** (tous les scenarios G1..G54 sont sortis) :
  il faut ecrire de NOUVEAUX scenarios avant de produire a nouveau.
- Derniers posts du {datetime.now().strftime('%d/%m/%Y')} : 3 videos (voir 02).
"""
    (PACK / "01_CHAINE.md").write_text(chaine, encoding="utf-8")

    lignes = ["# Les videos publiees (ordre chronologique)",
              "",
              "| # | date (UTC) | duree | legende publiee |",
              "|---|---|---|---|"]
    for i, e in enumerate(pub, 1):
        cap = (e.get("caption") or "").replace("|", "/").replace("\n", " ")
        duree = ""
        lignes.append(f"| {i} | {str(e.get('published_at_utc'))[:16]} | {duree} | {cap} |")
    lignes += ["", "## Videos les plus recentes (avec URL publique)",
               "", "Voir `04_CAPTURES/liste_contenu.txt` et les URLs dans "
                   "`05_STATS/audit_publications.json`."]
    (PACK / "02_PUBLICATIONS.md").write_text("\n".join(lignes), encoding="utf-8")


def copier_exemples(pub):
    VIDEOS.mkdir(parents=True, exist_ok=True)
    meta = ROOT / "videos" / "metadata"
    choisis = pub[-4:]
    for e in choisis:
        src = ROOT / "videos" / e["file"]
        if src.exists():
            shutil.copy2(src, VIDEOS / src.name)
        m = meta / f"{e['video_id']}.json"
        if m.exists():
            shutil.copy2(m, VIDEOS / (e["video_id"] + ".json"))
        print("[videos]", e["video_id"], "->", src.name if src.exists() else "ABSENT")


def copier_stats():
    stats = PACK / "05_STATS"
    stats.mkdir(parents=True, exist_ok=True)
    for nom in ("audit_publications.json", "daily_stats.json"):
        s = ROOT / "logs" / nom
        if s.exists():
            shutil.copy2(s, stats / nom)
    research = ROOT / "videos" / "research"
    if (research / "PRODUCTION_PLAN.md").exists():
        shutil.copy2(research / "PRODUCTION_PLAN.md", stats / "PRODUCTION_PLAN.md")


def _lecture(nom):
    f = CAPTURES / f"{nom}.txt"
    return f.read_text(encoding="utf-8") if f.exists() else ""


def _est_chiffre(s):
    return bool(s) and s.replace(",", "").replace(".", "").replace(" ", "") \
        .replace("K", "").replace("%", "").replace("+", "-").lstrip("-").isdigit()


def _chiffre(txt, mot):
    """Chiffre associe a un libelle TikTok (l ordre change selon la page : le
    profil met le NOMBRE AVANT le libelle, les stats le mettent APRES)."""
    lignes = [l.strip() for l in txt.splitlines() if l.strip()]
    for i, l in enumerate(lignes):
        if l.lower() == mot.lower():
            if i > 0 and _est_chiffre(lignes[i - 1]):
                return lignes[i - 1]
            for suite in lignes[i + 1:i + 3]:
                if _est_chiffre(suite):
                    return suite
    return "?"


def _entre(txt, debut, fin=None):
    """Ligne qui commence par `debut` et finit par `fin` (ex. 'Publications 66')."""
    for l in txt.splitlines():
        l = l.strip()
        if l.startswith(debut) and (fin is None or l.endswith(fin)):
            return l
    return ""


def _compteur_publications(txt):
    """'Publications 66' -> '66' (compteur du compte lu dans la liste Contenu)."""
    m = re.search(r"(\d[\d\s,.]*)", _entre(txt, "Publications"))
    return m.group(1).strip() if m else "?"


def ecrire_stats():
    """05_STATS/STATISTIQUES.md + 02B_PERFORMANCE_RECENTE.md a partir des captures."""
    stats = PACK / "05_STATS"
    stats.mkdir(parents=True, exist_ok=True)
    profil, analytics, contenu = _lecture("profil_public"), _lecture("stats_studio"), \
        _lecture("liste_contenu")

    md = ["# Statistiques de la chaine (recopies des captures 04_CAPTURES)", "",
          f"_Capture du {datetime.now().strftime('%d/%m/%Y %H:%M')}_", "",
          "## Profil public (@factivibeparano)", ""]
    if profil:
        jaime = _chiffre(profil, "J'aime")
        bio = next((l.strip() for l in profil.splitlines()
                    if "FactVibes Toons" in l), "")
        md += [f"- Followers : **{_chiffre(profil, 'Followers')}**",
               f"- J'aime (total) : **{jaime}**",
               f"- Suivis : {_chiffre(profil, 'Suivis')}",
               "- Bio : " + bio]
    md += ["", "## TikTok Studio — 7 derniers jours", ""]
    md += ["```", analytics.strip() or "(capture vide)", "```", "",
           "## A retenir pour l audit", "",
           "- Trafic : quasi 100 % « Pour toi » (decouverte), presque rien en recherche",
           "- Commentaires ~0 sur la fenetre : l engagement est le point faible",
           "- Quelques videos sortent nettement (700-800 vues), la majorite reste < 300"]
    (stats / "STATISTIQUES.md").write_text("\n".join(md), encoding="utf-8")

    # --- performance video par video (cartes de la liste Contenu)
    cartes, lignes = [], [l.rstrip() for l in contenu.splitlines()]
    i = 0
    while i < len(lignes):
        if DUREE.fullmatch(lignes[i]):
            duree = lignes[i]
            j = i + 1
            bloc = []
            while j < len(lignes) and not DUREE.fullmatch(lignes[j]):
                bloc.append(lignes[j])
                j += 1
            # bloc = [legende, date, "Tout le monde", vues, j'aime, commentaires]
            k = bloc.index("Tout le monde") if "Tout le monde" in bloc else -1
            if k >= 0 and len(bloc) >= k + 4:
                cartes.append({"duree": duree, "legende": bloc[0], "date": bloc[1],
                               "vues": bloc[k + 1], "likes": bloc[k + 2],
                               "coms": bloc[k + 3]})
            i = j
        else:
            i += 1

    perf = ["# Performance des dernieres videos (fenetre lue dans TikTok Studio)", "",
            "| date | duree | vues | likes | coms | legende |",
            "|---|---|---|---|---|---|"]
    for c in cartes:
        perf.append(f"| {c['date']} | {c['duree']} | **{c['vues']}** | {c['likes']} | "
                    f"{c['coms']} | {c['legende'][:90]}... |")
    perf += ["", f"_Compteur Publications du compte : "
                 f"{_compteur_publications(contenu)} (la file locale en marque 69 : "
                 f"ecart connu, la file n est qu une approximation)._"]
    (PACK / "02B_PERFORMANCE_RECENTE.md").write_text("\n".join(perf), encoding="utf-8")
    print(f"[stats] STATISTIQUES.md + 02B_PERFORMANCE_RECENTE.md ({len(cartes)} cartes)")



def zipper():
    out = ROOT / f"audit_factivibes_{TODAY}.zip"
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PACK.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(PACK.parent))
    print(f"[zip] {out.name} = {out.stat().st_size/1e6:.1f} Mo")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true")
    ap.add_argument("--sans-ecrans", action="store_true")
    ap.add_argument("--recapture", action="store_true",
                    help="refait les captures meme si elles existent deja")
    a = ap.parse_args()

    if PACK.exists():
        # on conserve les captures deja faites (elles coutent une navigation Chrome)
        for child in list(PACK.iterdir()):
            if child.name == "04_CAPTURES":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
    CAPTURES.mkdir(parents=True, exist_ok=True)

    textes = {}
    if not a.sans_ecrans:
        try:
            _http("/json/version")
        except Exception:
            print("Chrome 9222 injoignable : captures ignorees", file=sys.stderr)
        else:
            for nom, url in ECRANS:
                dest = CAPTURES / f"{nom}.png"
                if dest.exists() and not a.recapture:
                    print(f"[capture] {nom} deja la, conservee")
                    continue
                textes[nom] = capture(nom, url)

    pub, q = publications()
    copier_exemples(pub)
    ecrire_markdown(pub, q, textes)
    ecrire_stats()
    copier_stats()
    print(f"[pack] {PACK} pret : {len(pub)} publications ecrites")
    if a.zip:
        zipper()


if __name__ == "__main__":
    main()
