"""Génération vidéo IA sur GPU cloud (Modal) — test réel Wan 2.2 TI2V-5B, format vertical.

Usage (depuis la racine du repo) :
  python -m modal run cloud/modal_video.py --prompt "..." --out videos/generated/cloud_test/clip.mp4

Le modèle est téléchargé une seule fois dans un Volume Modal (cache), puis réutilisé.
Chaque exécution affiche le temps de génération pour estimer le coût (GPU facturé à la seconde).
"""
import time

import modal

app = modal.App("factvibes-video")
cache = modal.Volume.from_name("factvibes-hf-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "torch", "torchvision", "diffusers>=0.35.0", "transformers", "accelerate",
        "sentencepiece", "ftfy", "imageio", "imageio-ffmpeg", "numpy", "huggingface_hub[hf_transfer]",
    )
    .env({"HF_HOME": "/cache", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

MODEL = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
NEGATIVE = ("blurry, low quality, distorted face, extra fingers, deformed hands, static, still image, "
            "worst quality, jpeg artifacts, text, watermark, subtitles")


@app.function(image=image, gpu="L40S", timeout=2400, volumes={"/cache": cache})
def generate(prompt: str, width: int = 704, height: int = 1280, num_frames: int = 81,
             steps: int = 30, seed: int = 7, fps: int = 24) -> dict:
    import tempfile

    import torch
    from diffusers import AutoencoderKLWan, WanPipeline
    from diffusers.utils import export_to_video

    t0 = time.time()
    vae = AutoencoderKLWan.from_pretrained(MODEL, subfolder="vae", torch_dtype=torch.float32)
    pipe = WanPipeline.from_pretrained(MODEL, vae=vae, torch_dtype=torch.bfloat16)
    pipe.to("cuda")
    t_load = time.time() - t0

    t1 = time.time()
    frames = pipe(
        prompt=prompt, negative_prompt=NEGATIVE, height=height, width=width,
        num_frames=num_frames, guidance_scale=5.0, num_inference_steps=steps,
        generator=torch.Generator("cuda").manual_seed(seed),
    ).frames[0]
    t_gen = time.time() - t1

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        export_to_video(frames, f.name, fps=fps)
        data = open(f.name, "rb").read()
    cache.commit()
    return {"mp4": data, "load_s": round(t_load, 1), "gen_s": round(t_gen, 1),
            "frames": num_frames, "size": f"{width}x{height}", "steps": steps}


@app.local_entrypoint()
def main(prompt: str = "", out: str = "videos/generated/cloud_test/clip.mp4"):
    import os

    prompt = prompt or (
        "2D animated cartoon, flat colors, clean outlines. A tired young employee with messy brown hair "
        "and an orange hoodie sits at an office desk and talks to a manager with round glasses and a "
        "teal blazer. Expressive faces, smooth character animation, gentle camera push-in, bright "
        "office background, vertical composition."
    )
    res = generate.remote(prompt)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "wb").write(res.pop("mp4"))
    print("OK", out, res)
