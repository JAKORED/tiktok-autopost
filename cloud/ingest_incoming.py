#!/usr/bin/env python3
"""Import des résultats Kaggle : videos/incoming/ -> validation -> videos/ready/ (ou plans -> montage local).

Procédure (voir docs/video-ai/KAGGLE.md) :
  1. Kaggle : onglet « Output » du notebook > « Download All » (zip).
  2. Déposer le zip (ou son contenu) dans  videos/incoming/
  3. python cloud/ingest_incoming.py
Il fait, sans jamais publier :
  - décompresse les .zip trouvés dans incoming/ ;
  - vidéos FINALES (…/ready/cloud_00N.mp4) : validation stricte 1080×1920 + audio ; si OK -> videos/ready/ + metadata/ ;
  - PLANS (…/generated/cloud_00N/shots/shot_XX.mp4) : validation -> videos/generated/<id>/shots/ ; puis indique la commande
    de montage local (compose_cloud.py <id> render) si la vidéo finale n'a pas été montée sur Kaggle ;
  - écrit une planche d'inspection (6 images) dans videos/incoming/_review/<id>.png pour le contrôle VISUEL obligatoire.
Usage : python cloud/ingest_incoming.py [--incoming videos/incoming] [--videos videos]
"""
import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_video as V  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    root = HERE.parent / "videos"
    ap.add_argument("--incoming", default=str(root / "incoming"))
    ap.add_argument("--videos", default=str(root))
    a = ap.parse_args()
    inc, vid = Path(a.incoming), Path(a.videos)
    inc.mkdir(parents=True, exist_ok=True)
    for z in inc.glob("*.zip"):
        out = inc / f"_unzipped_{z.stem}"
        if not out.exists():
            print(f"décompression {z.name} -> {out.name}")
            zipfile.ZipFile(z).extractall(out)
    (inc / "_review").mkdir(exist_ok=True)

    finals, shots = {}, {}
    for f in inc.rglob("cloud_*.mp4"):
        if "_review" in f.parts or ".rejected" in f.name or ".tmp" in f.name:
            continue
        finals[f.stem] = f
    for f in inc.rglob("shot_*.mp4"):
        m = re.search(r"(cloud_\d{3})", str(f))
        if m and ".rejected" not in f.name and ".tmp" not in f.name:
            shots.setdefault(m.group(1), []).append(f)

    ok_finals = 0
    for ep_id, f in sorted(finals.items()):
        rep = V.validate(f, "final", frames=False)
        files = V.extract_frames(f, inc / "_review" / f"{ep_id}_frames")
        sheet = V.contact_sheet(files, inc / "_review" / f"{ep_id}.png")
        print(f"{ep_id} FINAL : {'VALIDE' if rep['ok'] else 'INVALIDE'} {rep['info'].get('duration')}s "
              f"{rep['info'].get('width')}x{rep['info'].get('height')} | planche : {sheet}")
        for p in rep["problems"]:
            print("   PROBLÈME :", p)
        if rep["ok"]:
            (vid / "ready").mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, vid / "ready" / f"{ep_id}.mp4")
            meta = next(inc.rglob(f"{ep_id}.json"), None)
            if meta:
                (vid / "metadata").mkdir(parents=True, exist_ok=True)
                shutil.copy2(meta, vid / "metadata" / f"{ep_id}.json")
            else:
                print(f"   métadonnées absentes -> lancer : python video_pipeline/compose_cloud.py {ep_id} render")
            ok_finals += 1
        shutil.rmtree(inc / "_review" / f"{ep_id}_frames", ignore_errors=True)

    for ep_id, files in sorted(shots.items()):
        dst = vid / "generated" / ep_id / "shots"
        dst.mkdir(parents=True, exist_ok=True)
        good = bad = 0
        for f in sorted(files):
            if V.validate(f, "shot")["ok"]:
                shutil.copy2(f, dst / f.name)
                good += 1
            else:
                bad += 1
                print(f"   {ep_id} {f.name} : plan invalide, non importé")
        print(f"{ep_id} PLANS : {good} importés, {bad} rejetés -> {dst}")
        if ep_id not in finals:
            print(f"   montage local : python video_pipeline/compose_cloud.py {ep_id} prepare && "
                  f"python video_pipeline/compose_cloud.py {ep_id} render")
    if not finals and not shots:
        print("Rien à importer : déposer le zip Kaggle ou son contenu dans", inc)
    print(f"Terminé : {ok_finals} vidéo(s) finale(s) validée(s). RIEN n'a été publié. "
          "Inspecter les planches dans incoming/_review/ AVANT toute publication.")


if __name__ == "__main__":
    main()
