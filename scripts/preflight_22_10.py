"""Preflight anti-doublon avant les 3 posts du 22/10/2026 (lecture seule).

Verifie, pour chaque READY, les 5 couches de garde decrites dans HANDOFF.md (ORDRE G/J/K/L):
  1. signature de script deja publiee ?
  2. famille / scenario deja publie ?   (4 variantes = 1 seule video)
  3. empreinte visuelle proche d'une sortie ? (seuil 0.035)
  4. caption construite : jamais d'identifiant interne (ORDRE M) ?
  5. unicite interne entre les candidates du lot
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "video_pipeline"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import studio  # noqa: E402

q = studio.load_queue()
eps = {x["id"]: x for x in studio.bank()}
cands = [e for e in q if e["state"] == "READY"]
done_fams = studio.already_published_families(q)
done_sigs = studio.already_published_scripts(q)
sorties = [e["video_id"] for e in q
           if e.get("state") in ("PUBLISHED", "SCHEDULED", "DELETED", "PUBLISHED_SUSPECT")]

print("READY au lot :", [e["video_id"] for e in cands])
print("familles deja publiees :", len(done_fams),
      "| scripts publies :", len(done_sigs),
      "| sorties cumulees :", len(sorties))

lignes = []
probleme = False
for e in cands:
    vid = e["video_id"]
    ep = eps.get(vid)
    fam = studio.family_key(ep)
    mp = studio.META_DIR / (vid + ".json")
    sig = None
    if mp.exists():
        lines = json.loads(mp.read_text(encoding="utf-8")).get("lines", [])
        sig = "|".join(l["text"].strip().lower() for l in lines)
    legende = studio.build_caption(ep) if ep else (e.get("caption") or "")
    dup = studio.visual_duplicate_of(vid, sorties)
    ok_fam = fam not in done_fams
    ok_sig = sig not in done_sigs
    ok_vis = dup is None
    ok_leg = vid not in legende and "auto_" not in legende
    if not (ok_fam and ok_sig and ok_vis and ok_leg):
        probleme = True
    print("--- %s" % vid)
    print("    famille  : %-60s %s" % (fam, "OK (jamais publiee)" if ok_fam else "BLOQUE"))
    print("    signature: %s" % ("OK (inedite)" if ok_sig else "BLOQUE (script deja sorti)"))
    print("    visuel   : %s" % ("OK (distinct)" if ok_vis else "BLOQUE %s" % (dup,)))
    print("    legende  : %s" % legende)
    print("    legende propre (sans auto_) : %s" % ("OK" if ok_leg else "BLOQUE"))
    lignes.append((vid, fam, legende))

# unicite interne du lot (aucune famille en double parmi les 3 candidates)
fam_lot = [f for _, f, _ in lignes]
if len(set(fam_lot)) != len(fam_lot):
    probleme = True
    print("!! DOUBLON INTERNE AU LOT (2 memes familles) :", fam_lot)

print("\nRESULTAT :", "PROBLEME DETECTE" if probleme else "LOT PROPRE, 0 DOUBLON")
for vid, fam, leg in lignes:
    print("  %s | %s" % (vid, leg))
