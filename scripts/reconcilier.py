"""Réconciliation base <-> compte TikTok (lecture seule par défaut).

09/10/2026 — la désynchronisation base / compte est la cause historique des doublons
vécus par le patron : une vidéo réellement en ligne reste notée FAILED (elle sera
relancée), et une vidéo jamais envoyée se retrouve notée PUBLISHED (elle ne le sera
jamais). Les deux cas sont arrivés le 09/10 (auto_069 en ligne mais FAILED ; auto_070
déclarée PUBLISHED alors que c'était auto_069).

Ce script lit la liste « Contenu » de TikTok Studio et aligne la file sur ce qui est
RÉELLEMENT en ligne. Il ne publie rien.

  python scripts/reconcilier.py            # rapport seul, n'écrit rien
  python scripts/reconcilier.py --appliquer  # corrige réellement la file

Limite assumée : TikTok Studio ne charge qu'une poignée de cartes (~7). L'absence d'une
vidéo dans la fenêtre lue ne prouve donc RIEN. On ne rétrograde jamais un PUBLISHED sur
la seule foi de son absence ; on ne remonte en PUBLISHED que ce qu'on a VU en ligne.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "video_pipeline"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import studio  # noqa: E402
import publish_studio as ps  # noqa: E402

MOIS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.",
           "août", "sept.", "oct.", "nov.", "déc."]


def date_de_la_carte(carte, annee=None):
    """« 9 oct., 12:45 » -> datetime UTC (l'heure affichée est celle du compte TikTok).

    Le fuseau du compte est celui du patron (Paris) ; on applique le décalage local du
    poste, mesuré sur les posts déjà réconciliés (09/10 : 12:08 affichées = 10:08 UTC).
    """
    m = re.search(r"(\d{1,2})\s+([a-zéû]+\.?),\s*,?\s*(\d{1,2}):(\d{2})", carte)
    if not m:
        return None
    jour, mois_txt, h, mi = int(m.group(1)), m.group(2), int(m.group(3)), int(m.group(4))
    mois = next((i for i, nom in enumerate(MOIS_FR) if nom.startswith(mois_txt[:3].lower())
                 or nom.lower().startswith(mois_txt[:3].lower())), None)
    if mois is None:
        return None
    annee = annee or datetime.now().year
    local = datetime(annee, mois + 1, jour, h, mi)
    return local.astimezone().astimezone(timezone.utc)


def main():
    ap = argparse.ArgumentParser(description="Aligner la file sur le compte TikTok")
    ap.add_argument("--appliquer", action="store_true",
                    help="écrire réellement les corrections dans videos/queue.json")
    args = ap.parse_args()

    d = ps.ensure_chrome()
    d.get(ps.CONTENT_URL)
    import time
    time.sleep(8)
    cartes = ps._cartes_contenu(d, tours=6)
    print(f"{len(cartes)} carte(s) lue(s) dans Contenu TikTok\n")

    queue = studio.load_queue()
    par_id = {e["video_id"]: e for e in queue}
    vus, corrections = {}, []

    for c in cartes:
        carte = c.get("carte") or ""
        vid = ps._id_depuis_carte(carte)
        if not vid:
            print(f"  (sans numéro d'épisode, ignorée) {carte[:60]}")
            continue
        vus[vid] = carte
        e = par_id.get(vid)
        if e is None:
            corrections.append((vid, "ABSENTE_DE_LA_FILE",
                                "en ligne sur le compte mais inconnue de la base"))
        elif e.get("state") != "PUBLISHED":
            corrections.append((vid, e.get("state"),
                                "en ligne sur le compte -> PUBLISHED (réconciliation)"))
    # La liste est virtualisée : seule une fenêtre est lue. On ne rétrograde rien sur
    # la seule absence d'une carte — ce serait recreer le bug à l'envers.
    print(f"{len(vus)} vidéo(s) identifiée(s) en ligne : "
          f"{', '.join(sorted(vus))}\n")

    # ---- rétrogradation prouvée ----------------------------------------
    # Un PUBLISHED obtenu par « reconciliation » porte dans sa preuve la carte TikTok
    # qui a matché. On en relit le numéro d'épisode : s'il ne correspond pas au video_id,
    # la carte était celle d'UNE AUTRE vidéo — le faux positif du 09/10 (auto_070 marquée
    # PUBLISHED grâce à la carte de auto_069). La preuve est dans la base : rien à deviner.
    for e in queue:
        ev = e.get("published_evidence") or {}
        if e.get("state") != "PUBLISHED":
            continue
        if "conciliation" not in str(ev.get("method", "")):
            continue
        id_carte = ps._id_depuis_carte(str(ev.get("carte") or ""))
        if id_carte and id_carte != e["video_id"]:
            corrections.append((e["video_id"], "PUBLISHED",
                                "preuve invalide : la carte stockée est celle de "
                                + id_carte + " -> faux positif, à rétrograder"))

    if corrections:
        print("CORRECTIONS A APPROUUVOIR :")
        for vid, etat, why in corrections:
            print(f"  {vid} : {etat} -> {why}")
    else:
        print("Aucune correction : la file est alignée sur ce qui est visible.")

    # Contrôle de cohérence : des PUBLISHED du jourRecent introuvables dans la fenêtre.
    recents = [e for e in queue if e.get("state") == "PUBLISHED"
               and str(e.get("published_at_utc") or "")[:7] == datetime.now(timezone.utc).strftime("%Y-%m")]
    invisibles = [e["video_id"] for e in recents if e["video_id"] not in vus]
    if invisibles:
        print(f"\nNote : {len(invisibles)} PUBLISHED récent(s) hors de la fenêtre lue "
              f"({len(cartes)} cartes) : {', '.join(invisibles[:8])}")
        print("      ce n'est PAS une anomalie — TikTok Studio ne charge que ~7 cartes.")

    if not corrections:
        return
    if not args.appliquer:
        print("\n(relancer avec --appliquer pour écrire)")
        return

    for vid, etat, why in corrections:
        e = par_id.get(vid)
        retrograder = etat == "PUBLISHED" and "preuve invalide" in why
        if e is not None and retrograder:
            # Jamais publiée : on le dit clairement, et on garde la trace de la carte
            # qui avait induit l'erreur (utile pour comprendre, pas pour republier).
            e.update(state="FAILED", error="rétrogradé le 09/10/2026 : " + why,
                     published_at_utc=None,
                     published_evidence={"note": "légende réellement en ligne",
                                         "carte": (e.get("published_evidence") or {}).get("carte", "")})
            print(f"  écrit : {vid} FAILED (rétrogradé — jamais publiée)")
            continue
        if e is None:
            e = {"video_id": vid, "state": "PUBLISHED", "file": f"ready/{vid}.mp4",
                 "caption": None, "hashtags": [], "created_utc": studio.now_utc(),
                 "scheduled_for_utc": None, "publish_id": None, "published_at_utc": None,
                 "published_evidence": None, "error": None}
            queue.append(e)
            par_id[vid] = e
        ts = date_de_la_carte(vus.get(vid, ""))
        e.update(state="PUBLISHED", error=None,
                 published_at_utc=(ts.isoformat() if ts else studio.now_utc()),
                 published_evidence={"method": "réconciliation TikTok Studio",
                                     "confirmation": why,
                                     "carte": vus.get(vid, "")[:120]})
        print(f"  écrit : {vid} PUBLISHED")
    studio.save_queue(queue)
    print("\nFile réconciliée.")


if __name__ == "__main__":
    main()