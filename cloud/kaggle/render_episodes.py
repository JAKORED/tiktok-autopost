#!/usr/bin/env python3
"""Montage CPU des épisodes (narration, sous-titres animés, musique, 1080×1920) à partir des plans générés.

Meilleur effort : si cairo/ffmpeg/Internet manquent sur Kaggle, l'épisode est IGNORÉ avec un message clair — le montage se
refait alors en local (`python video_pipeline/compose_cloud.py <id> render`) à partir des plans rapportés dans videos/incoming/.

Les fichiers intermédiaires (voix, plans recalés, mix.wav…) vont dans un dossier de travail HORS de la sortie du notebook
(Kaggle limite la sortie à 500 fichiers / 20 Go). Seuls sortent : ready/<id>.mp4, metadata/<id>.json, ready/<id>_review.png.

Usage : python render_episodes.py --phase episode1|rest|all [--root <VIDEO_ROOT>] [--work <dossier>]
"""
import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # cloud/ -> validate_video
import validate_video as V  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default=os.environ.get("PHASE", "episode1"))
    ap.add_argument("--root", default=os.environ.get("VIDEO_ROOT", "/kaggle/working/videos"))
    ap.add_argument("--work", default=None)
    args = ap.parse_args()
    cfg = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    root = Path(args.root)
    scratch = Path("/kaggle/temp") if Path("/kaggle/temp").exists() else Path(tempfile.gettempdir())
    work = Path(args.work) if args.work else scratch / "render_work"
    os.environ["VIDEO_ROOT"] = str(work)  # lu à l'import de compose_cloud
    os.environ.setdefault("HF_HOME", str(scratch / "hf"))
    sys.path.insert(0, str(HERE.parent.parent / "video_pipeline"))
    try:
        import compose_cloud as C  # noqa: E402
    except Exception as e:  # cairo/numpy/edge-tts absents
        print(f"MONTAGE IGNORÉ ({type(e).__name__}: {e}).")
        print("-> montage à faire en local : télécharger les plans (videos/incoming/) puis "
              "`python video_pipeline/compose_cloud.py <id> render`.")
        return 0

    results = {}
    for ep_id in cfg["episodes_by_phase"][args.phase]:
        ep = next((e for e in C.EPISODES if e["id"] == ep_id), None)
        shots = root / "generated" / ep_id / "shots"
        plan = json.loads((HERE / "plans" / f"{ep_id}.json").read_text(encoding="utf-8"))["shots"]
        missing = [s["index"] for s in plan if not (shots / f"shot_{s['index']:02d}.mp4").exists()]
        bad = [s["index"] for s in plan if (shots / f"shot_{s['index']:02d}.mp4").exists()
               and not V.validate(shots / f"shot_{s['index']:02d}.mp4", "shot")["ok"]]
        if ep is None or missing or bad:
            results[ep_id] = f"IGNORÉ (plans manquants {missing}, invalides {bad})"
            print(f"{ep_id} : {results[ep_id]}")
            continue
        dst_shots = work / "generated" / ep_id / "shots"
        dst_shots.mkdir(parents=True, exist_ok=True)
        for f in shots.glob("shot_*.mp4"):
            shutil.copy2(f, dst_shots / f.name)
        try:
            C.render(ep)  # écrit work/ready/<id>.mp4 et work/metadata/<id>.json
        except SystemExit as e:
            results[ep_id] = f"ÉCHEC montage : {e}"
            print(results[ep_id])
            continue
        except Exception as e:
            results[ep_id] = f"ÉCHEC montage : {type(e).__name__}: {e}"
            print(results[ep_id])
            continue
        (root / "ready").mkdir(parents=True, exist_ok=True)
        (root / "metadata").mkdir(parents=True, exist_ok=True)
        final = root / "ready" / f"{ep_id}.mp4"
        shutil.copy2(work / "ready" / f"{ep_id}.mp4", final)
        shutil.copy2(work / "metadata" / f"{ep_id}.json", root / "metadata" / f"{ep_id}.json")
        rep = V.validate(final, "final", frames=True)
        # une seule planche d'inspection en sortie (pas 6 fichiers) : limite Kaggle de 500 fichiers
        review = final.parent / f"{ep_id}_frames"
        sheet = review / "contact_sheet.png"
        if sheet.exists():
            shutil.copy2(sheet, final.parent / f"{ep_id}_review.png")
        shutil.rmtree(review, ignore_errors=True)
        results[ep_id] = "OK" if rep["ok"] else f"MONTÉ mais INVALIDE : {rep['problems']}"
        print(f"{ep_id} : {results[ep_id]}")
    (root / "generated").mkdir(parents=True, exist_ok=True)
    (root / "generated" / "render_report.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
