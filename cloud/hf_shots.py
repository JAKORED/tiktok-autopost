"""Génère les plans d'un épisode sur un Space Hugging Face ZeroGPU (LTX-Video distillé), sans carte.

Usage :
  python cloud/hf_shots.py <episode_id> [--only 0,3] [--seed 7] [--space Lightricks/ltx-video-distilled]

- lit videos/generated/<id>/shots_plan.json (produit par compose_cloud.py prepare)
- écrit videos/generated/<id>/shots/shot_XX.mp4 ; saute les plans déjà présents (reprise possible)
- s'arrête proprement si le quota GPU du jour est épuisé (affiche le délai avant réinitialisation)
- HF_TOKEN (optionnel, compte gratuit) : passe le quota anonyme (2 min/jour) à 5 min/jour
"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

from gradio_client import Client

ROOT = Path(__file__).resolve().parent.parent
SPACE = "Lightricks/ltx-video-distilled"
NEGATIVE = ("worst quality, inconsistent motion, blurry, jittery, distorted, extra limbs, extra hands, "
            "floating hands, deformed, text, watermark, subtitles, logo, low resolution")
H, W = 1216, 704


def main():
    ep = sys.argv[1]
    only = None
    seed = 7
    space = SPACE
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    if "--seed" in sys.argv:
        seed = int(sys.argv[sys.argv.index("--seed") + 1])
    if "--space" in sys.argv:
        space = sys.argv[sys.argv.index("--space") + 1]
    work = ROOT / "videos" / "generated" / ep
    plan = json.loads((work / "shots_plan.json").read_text(encoding="utf-8"))["shots"]
    out_dir = work / "shots"
    out_dir.mkdir(exist_ok=True)
    token = os.environ.get("HF_TOKEN") or None
    client = Client(space, token=token) if token else Client(space)
    print(f"Space {space} — {'compte HF (token)' if token else 'anonyme'}", flush=True)

    for p in plan:
        i = p["index"]
        dst = out_dir / f"shot_{i:02d}.mp4"
        if (only is not None and i not in only) or (dst.exists() and only is None):
            continue
        dur = round(min(8.0, max(2.0, p["span"] + 0.3)), 1)
        t0 = time.time()
        for attempt in (1, 2):
            try:
                vid, used_seed = client.predict(
                    prompt=p["prompt"], negative_prompt=NEGATIVE, input_image_filepath=None,
                    input_video_filepath=None, height_ui=H, width_ui=W, mode="text-to-video",
                    duration_ui=dur, ui_frames_to_use=9, seed_ui=seed + i, randomize_seed=False,
                    ui_guidance_scale=1, improve_texture_flag=True, api_name="/text_to_video")
                src = vid["video"] if isinstance(vid, dict) else vid
                shutil.copy(src, dst)
                print(f"plan {i}: OK {dur}s en {time.time() - t0:.0f}s -> {dst.name}", flush=True)
                break
            except Exception as e:
                msg = str(e)
                if "quota" in msg.lower() or "GPU" in msg and "exceeded" in msg.lower():
                    m = re.search(r"(\d+:\d+:\d+|\d+ ?[hm][^\s]*)", msg)
                    print(f"plan {i}: QUOTA GPU ÉPUISÉ — {msg[:220]}", flush=True)
                    print("Arrêt propre : relancer plus tard (reprise automatique) ou fournir HF_TOKEN.", flush=True)
                    return
                print(f"plan {i}: erreur tentative {attempt} — {type(e).__name__}: {msg[:200]}", flush=True)
                time.sleep(5)
        else:
            print(f"plan {i}: ÉCHEC après 2 tentatives", flush=True)
    print("FINI", flush=True)


if __name__ == "__main__":
    main()
