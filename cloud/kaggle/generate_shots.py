#!/usr/bin/env python3
"""Génération GPU des plans vidéo (Wan 2.2 TI2V-5B via diffusers) sur Kaggle (2×T4 16 Go).

⚠ STATUT : code écrit et vérifié statiquement + mode --check ; la génération GPU n'a PAS encore tourné sur Kaggle
(aucun accès GPU depuis le poste de développement). Toute mesure est produite au premier lancement et écrite dans
<VIDEO_ROOT>/generated/measurements.json. Voir docs/video-ai/KAGGLE.md.

Étapes (chacune tolère l'échec des étapes expérimentales, jamais celle des plans de production) :
  0. contrôle de l'environnement (GPU, CUDA, RAM, disque)
  1. probe    : choix du dtype (fp16 puis bf16), temps/VRAM à 480×832 puis 704×1280 (UNE variable : la résolution)
  2. keyframes: une image de départ par plan (SDXL) + images de référence des personnages
  3. ab_test  : même plan, même seed, UNE variable (image de départ vs texte seul)
  4. plans    : génération avec reprise (SKIP si le fichier existe et est valide), repli OOM, contrôle qualité, relances

Usage :
  python generate_shots.py --phase episode1|rest|all [--config config.json] [--root <VIDEO_ROOT>] [--check]
Entrées : plans/<id>.json (durées calées sur la narration).  Sorties : <root>/generated/<id>/{keyframes,shots}/…
Env : VIDEO_ROOT (racine de sortie), HF_HOME (cache des modèles), HF_TOKEN facultatif.
"""
import argparse
import gc
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # cloud/ -> validate_video
import validate_video as V  # noqa: E402

T0 = time.time()


def log(*a):
    print(f"[{(time.time() - T0) / 60:6.1f} min]", *a, flush=True)


# ------------------------------------------------------------------ configuration / chemins
def load_config(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_root(args):
    r = args.root or os.environ.get("VIDEO_ROOT")
    if not r:
        r = "/kaggle/working/videos" if Path("/kaggle/working").exists() else str(HERE.parent.parent / "videos")
    p = Path(r)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_plan(root, ep):
    for cand in (root / "generated" / ep / "shots_plan.json", HERE / "plans" / f"{ep}.json"):
        if cand.exists():
            return json.loads(cand.read_text(encoding="utf-8"))["shots"]
    raise FileNotFoundError(f"plan introuvable pour {ep} (cherché dans {root}/generated et {HERE}/plans)")


def measure(root, **kw):
    f = root / "generated" / "measurements.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    kw["t_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    data.append(kw)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log("MESURE", json.dumps(kw, ensure_ascii=False))


def ram_gb():
    try:
        import psutil
        return round(psutil.virtual_memory().used / 2**30, 1)
    except Exception:
        return None


def gpu_info():
    try:
        import torch
        if not torch.cuda.is_available():
            return {"cuda": False}
        p = torch.cuda.get_device_properties(0)
        return {"cuda": True, "count": torch.cuda.device_count(), "name": p.name,
                "vram_gb": round(p.total_memory / 2**30, 1), "capability": torch.cuda.get_device_capability(0),
                "torch": torch.__version__}
    except Exception as e:
        return {"cuda": False, "error": str(e)[:120]}


def prompt_with_bible(cfg, text):
    """Ajoute la description fixe d'un personnage (bible) si son nom apparaît dans le prompt : cohérence par le texte."""
    low = text.lower()
    extra = [d for k, d in cfg.get("character_bible", {}).items() if k in low]
    return text + (" Character design: " + "; ".join(extra) + "." if extra else "")


# ------------------------------------------------------------------ mode --check (aucune génération)
def check(cfg, root, phase):
    print("=== CHECK (aucune génération) ===")
    print("root :", root)
    print("GPU  :", gpu_info())
    print("RAM utilisée (Go) :", ram_gb())
    for d in ("/kaggle/temp", "/tmp", str(root)):
        try:
            print(f"disque libre {d} : {shutil.disk_usage(d).free / 2**30:.1f} Go")
        except Exception:
            pass
    total = todo = 0
    for ep in cfg["episodes_by_phase"][phase]:
        plan = load_plan(root, ep)
        for s in plan:
            total += 1
            dst = root / "generated" / ep / "shots" / f"shot_{s['index']:02d}.mp4"
            ok = dst.exists() and V.validate(dst, "shot")["ok"]
            todo += 0 if ok else 1
            print(f"  {ep} plan {s['index']} : {s['span']:.1f}s, {s['num_frames']} images -> {'SKIP (valide)' if ok else 'GENERATE'}")
    print(f"=== {todo}/{total} plans à générer ===")


# ------------------------------------------------------------------ étape 2 : images de départ (SDXL)
def generate_keyframes(cfg, root, jobs, refs):
    """jobs = [(chemin, prompt, seed)], refs = [(chemin, prompt, seed)] ; saute les fichiers existants."""
    import torch
    from diffusers import StableDiffusionXLPipeline
    todo = [j for j in jobs + refs if not Path(j[0]).exists()]
    if not todo:
        log("keyframes : tout existe déjà (SKIP)")
        return
    k = cfg["keyframe"]
    t = time.time()
    pipe = StableDiffusionXLPipeline.from_pretrained(cfg["model"]["keyframe_repo"], torch_dtype=torch.float16,
                                                     variant="fp16", use_safetensors=True).to("cuda")
    log(f"SDXL chargé en {time.time() - t:.0f}s ; {len(todo)} images à générer")
    for path, prompt, seed in todo:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        t = time.time()
        img = pipe(prompt=f"{k['style']} {prompt}", negative_prompt=k["negative_prompt"], width=k["width"],
                   height=k["height"], num_inference_steps=k["steps"], guidance_scale=k["guidance_scale"],
                   generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        img.save(path)
        log(f"keyframe {Path(path).name} en {time.time() - t:.0f}s")
    del pipe
    gc.collect()
    torch.cuda.empty_cache()


# ------------------------------------------------------------------ Wan 2.2
class Wan:
    def __init__(self, cfg, mode, dtype_name):
        import torch
        self.torch, self.cfg, self.mode, self.dtype_name = torch, cfg, mode, dtype_name
        self.dtype = {"fp16": torch.float16, "bf16": torch.bfloat16}[dtype_name]
        self.pipe = self._load()

    def _load(self):
        torch = self.torch
        from diffusers import AutoencoderKLWan
        repo = self.cfg["model"]["wan_repo"]
        t = time.time()
        vae = AutoencoderKLWan.from_pretrained(repo, subfolder="vae", torch_dtype=torch.float32)
        if self.mode == "i2v":
            from diffusers import WanImageToVideoPipeline as P
        else:
            from diffusers import WanPipeline as P
        pipe = P.from_pretrained(repo, vae=vae, torch_dtype=self.dtype)
        if self.cfg["wan"].get("vae_tiling"):
            try:
                pipe.vae.enable_tiling()
            except Exception as e:
                log("vae tiling indisponible :", e)
        if self.cfg["wan"]["offload"] == "sequential":
            pipe.enable_sequential_cpu_offload()
        else:
            pipe.enable_model_cpu_offload()
        log(f"Wan {self.mode} {self.dtype_name} chargé en {time.time() - t:.0f}s ; RAM utilisée {ram_gb()} Go")
        return pipe

    def run(self, prompt, width, height, frames, steps, seed, image_path=None):
        torch = self.torch
        kw = dict(prompt=prompt, negative_prompt=self.cfg["wan"]["negative_prompt"], height=height, width=width,
                  num_frames=frames, guidance_scale=self.cfg["wan"]["guidance_scale"],
                  num_inference_steps=steps, generator=torch.Generator("cpu").manual_seed(seed))
        if self.mode == "i2v":
            from PIL import Image
            kw["image"] = Image.open(image_path).convert("RGB")
        torch.cuda.reset_peak_memory_stats()
        t = time.time()
        frames_out = self.pipe(**kw).frames[0]
        return frames_out, time.time() - t, torch.cuda.max_memory_allocated() / 2**30

    def free(self):
        if hasattr(self, "pipe"):
            del self.pipe
        gc.collect()
        self.torch.cuda.empty_cache()


def frames_ok(frames):
    """Détecte NaN / image noire (piège connu du fp16)."""
    import numpy as np
    a = np.asarray(frames[len(frames) // 2], dtype="float32")
    if not np.isfinite(a).all():
        return False
    if a.max() <= 1.5:  # les pipelines Wan renvoient par défaut des flottants dans [0, 1]
        a = a * 255.0
    return bool(a.mean() > 6 and a.std() > 3)


def export(frames, path, fps):
    from diffusers.utils import export_to_video
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    export_to_video(frames, str(path), fps=fps)


def aligned(n, mod=4):  # Wan : 4k+1 images
    return ((n - 1) // mod) * mod + 1


# ------------------------------------------------------------------ étape 1 : probe
def probe(cfg, root, sample_image):
    """Choisit le dtype (premier valide de dtype_order) puis mesure temps/VRAM par résolution (variable unique)."""
    p, w = cfg["probe"], cfg["wan"]
    order = [w["dtype"]] if w["dtype"] in ("fp16", "bf16") else w["dtype_order"]
    mode = "i2v" if (w["mode"] == "i2v" and sample_image and Path(sample_image).exists()) else "t2v"
    chosen = None
    for dt in order:
        wan = None
        try:
            wan = Wan(cfg, mode, dt)
            frames, sec, vram = wan.run("a cartoon character talking, smooth animation", w["width"], w["height"],
                                        p["frames"], p["steps"], 1, sample_image)
            ok = frames_ok(frames)
            measure(root, stage="probe_dtype", dtype=dt, mode=mode, size=f"{w['width']}x{w['height']}",
                    frames=p["frames"], steps=p["steps"], seconds=round(sec, 1), vram_peak_gb=round(vram, 2),
                    ram_gb=ram_gb(), valid=ok)
            if ok:
                chosen = dt
                for (pw, ph) in p["sizes"][1:]:  # résolutions supérieures : information, pas de changement de production
                    try:
                        fr, s2, v2 = wan.run("a cartoon character talking, smooth animation", pw, ph, p["frames"],
                                             p["steps"], 1, sample_image)
                        measure(root, stage="probe_size", dtype=dt, size=f"{pw}x{ph}", frames=p["frames"],
                                steps=p["steps"], seconds=round(s2, 1), vram_peak_gb=round(v2, 2), valid=frames_ok(fr))
                    except Exception as e:
                        measure(root, stage="probe_size", dtype=dt, size=f"{pw}x{ph}", error=type(e).__name__ + ": " + str(e)[:160])
                wan.free()
                break
            wan.free()
        except Exception as e:
            measure(root, stage="probe_dtype", dtype=dt, mode=mode, error=type(e).__name__ + ": " + str(e)[:200])
            if wan is not None:
                try:
                    wan.free()
                except Exception:
                    pass
            import torch
            gc.collect()
            torch.cuda.empty_cache()
    return chosen, mode


def calibrate_steps(cfg, wan, root, sample_image, frames):
    """Temps par step mesuré à la taille réelle (différence 4 steps − 2 steps) -> nombre de steps compatible avec le budget."""
    w = cfg["wan"]
    if w["steps"] != "auto":
        return int(w["steps"])
    _, t2, _ = wan.run("calibration", w["width"], w["height"], frames, 2, 1, sample_image)
    _, t4, _ = wan.run("calibration", w["width"], w["height"], frames, 4, 1, sample_image)
    per_step = max((t4 - t2) / 2, 0.5)
    measure(root, stage="calibration", frames=frames, size=f"{w['width']}x{w['height']}", seconds_per_step=round(per_step, 2))
    return per_step  # converti en steps par l'appelant (dépend du budget restant)


# ------------------------------------------------------------------ étape 4 : plans de production
def produce(cfg, root, wan, episodes, dtype, steps_of, deadline):
    w = cfg["wan"]
    report = []
    for ep in episodes:
        plan = load_plan(root, ep)
        base = root / "generated" / ep
        for s in plan:
            i = s["index"]
            dst = base / "shots" / f"shot_{i:02d}.mp4"
            if dst.exists() and V.validate(dst, "shot")["ok"]:
                log(f"{ep} plan {i} : SKIP (fichier valide)")
                continue
            if time.time() > deadline:
                log(f"BUDGET DE TEMPS ATTEINT : arrêt propre avant {ep} plan {i} (reprise possible)")
                return report
            kf = base / "keyframes" / f"kf_{i:02d}.png"
            if wan.mode == "i2v" and not kf.exists():
                log(f"{ep} plan {i} : image de départ absente -> plan ignoré")
                report.append({"episode": ep, "shot": i, "status": "keyframe manquante"})
                continue
            prompt = prompt_with_bible(cfg, s["prompt"])
            frames_n = aligned(s["num_frames"])
            steps = steps_of(frames_n)
            best = None
            for attempt in range(w["max_retries"] + 1):
                seed = w["seed_base"] + i + 1000 * attempt
                try:
                    fr, sec, vram = wan.run(prompt, w["width"], w["height"], frames_n, steps, seed,
                                            kf if wan.mode == "i2v" else None)
                except Exception as e:
                    name = type(e).__name__
                    log(f"{ep} plan {i} tentative {attempt}: {name} {str(e)[:160]}")
                    if "OutOfMemory" in name or "out of memory" in str(e).lower():
                        import torch
                        gc.collect()
                        torch.cuda.empty_cache()
                        if attempt == 0:
                            try:  # repli 1 : tiling VAE (bug connu sur le 5B : NON VÉRIFIÉ)
                                wan.pipe.vae.enable_tiling()
                                log("repli OOM 1 : tiling VAE activé")
                            except Exception:
                                frames_n = aligned(int(frames_n * 0.75))
                                log(f"repli OOM 1b : {frames_n} images")
                        else:
                            frames_n = aligned(int(frames_n * 0.75))
                            log(f"repli OOM 2 : {frames_n} images")
                    continue
                tmp = dst.with_suffix(".tmp.mp4")
                export(fr, tmp, w["fps"])
                rep = V.validate(tmp, "shot")
                measure(root, stage="shot", episode=ep, shot=i, attempt=attempt, dtype=dtype, mode=wan.mode,
                        size=f"{w['width']}x{w['height']}", frames=frames_n, fps=w["fps"], steps=steps,
                        seconds=round(sec, 1), vram_peak_gb=round(vram, 2), ram_gb=ram_gb(), ok=rep["ok"],
                        problems=rep["problems"])
                if rep["ok"]:
                    tmp.replace(dst)
                    best = "ok"
                    break
                best = "problème"
                tmp.replace(dst.with_suffix(".rejected.mp4")) if attempt == w["max_retries"] else tmp.unlink(missing_ok=True)
            report.append({"episode": ep, "shot": i, "status": best or "échec"})
            log(f"{ep} plan {i} -> {best or 'ÉCHEC'}")
    return report


# ------------------------------------------------------------------ orchestration
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default=None)
    ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--root", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    cfg = load_config(args.config)
    phase = args.phase or os.environ.get("PHASE") or cfg["phase"]
    root = get_root(args)
    episodes = cfg["episodes_by_phase"][phase]
    log(f"phase={phase} épisodes={episodes} root={root}")
    if args.check:
        return check(cfg, root, phase)

    info = gpu_info()
    log("environnement :", info, "| RAM utilisée (Go) :", ram_gb())
    if not info.get("cuda"):
        sys.exit("ERREUR : aucun GPU CUDA. Notebook > Settings > Accelerator > GPU T4 x2, puis relancer.")
    budget = float(os.environ.get("TIME_BUDGET_HOURS") or cfg["time_budget_hours"]) * 3600
    deadline = T0 + budget
    w, kcfg = cfg["wan"], cfg["keyframe"]

    # 2) images de départ + références (avant Wan pour libérer SDXL avant de charger Wan)
    jobs, refs = [], []
    for ep in episodes:
        for s in load_plan(root, ep):
            jobs.append((root / "generated" / ep / "keyframes" / f"kf_{s['index']:02d}.png",
                         prompt_with_bible(cfg, s["prompt"].split("vertical composition.")[-1].strip()),
                         w["seed_base"] + s["index"]))
    if cfg["references"]["enabled"]:
        for j, (name, desc) in enumerate(cfg["character_bible"].items()):
            refs.append((root / "generated" / "_bible" / f"{name}.png", f"character reference sheet, full body, neutral pose, plain background: {desc}", 500 + j))
    if kcfg["enabled"] and w["mode"] == "i2v":
        try:
            generate_keyframes(cfg, root, jobs, refs)
        except Exception as e:
            measure(root, stage="keyframes", error=type(e).__name__ + ": " + str(e)[:200])
            log("keyframes en échec -> bascule en texte→vidéo (t2v)")
            w["mode"] = "t2v"

    sample = jobs[0][0] if jobs and Path(jobs[0][0]).exists() else None

    # 1) probe / choix du dtype
    dtype, mode = None, w["mode"]
    if cfg["probe"]["enabled"]:
        dtype, mode = probe(cfg, root, sample)
    if dtype is None:
        dtype = w["dtype_order"][-1] if w["dtype"] == "auto" else w["dtype"]
        log(f"probe sans résultat valide -> dtype par défaut {dtype}")
    if w["mode"] == "i2v" and mode != "i2v":
        log("i2v indisponible -> t2v")
    w["mode"] = mode

    # 4) production : un seul chargement du modèle pour tous les plans
    wan = Wan(cfg, w["mode"], dtype)
    frames_typ = aligned(int(sum(s["num_frames"] for e in episodes for s in load_plan(root, e)) /
                             max(1, sum(len(load_plan(root, e)) for e in episodes))))
    per_step = calibrate_steps(cfg, wan, root, sample, frames_typ)
    remaining = sum(1 for e in episodes for s in load_plan(root, e)
                    if not (root / "generated" / e / "shots" / f"shot_{s['index']:02d}.mp4").exists())

    def steps_of(frames_n):
        if isinstance(per_step, int):
            return per_step
        scale = (frames_n / max(frames_typ, 1)) ** 1.2
        avail = max(deadline - time.time(), 60) / max(remaining, 1) / 1.15  # 15 % de marge (encodage, retries)
        n = int(avail / (per_step * scale))
        return max(w["steps_min"], min(w["steps_max"], n))

    # 3) test A/B (une seule variable : image de départ ; même prompt, même seed, mêmes steps)
    ab = cfg["ab_test"]
    if ab["enabled"] and ab["episode"] in episodes and w["mode"] == "i2v":
        try:
            s = next(x for x in load_plan(root, ab["episode"]) if x["index"] == ab["shot"])
            kf = root / "generated" / ab["episode"] / "keyframes" / f"kf_{s['index']:02d}.png"
            out = root / "generated" / "_ab_test"
            fn = aligned(s["num_frames"])
            steps = steps_of(fn)
            pr = prompt_with_bible(cfg, s["prompt"])
            for label, img in (("i2v_keyframe", kf), ("t2v_texte_seul", None)):
                if img is None:
                    wan.free()
                    wan = Wan(cfg, "t2v", dtype)
                fr, sec, vr = wan.run(pr, w["width"], w["height"], fn, steps, w["seed_base"] + s["index"], img)
                export(fr, out / f"{label}.mp4", w["fps"])
                measure(root, stage="ab_test", variant=label, seconds=round(sec, 1), vram_peak_gb=round(vr, 2), steps=steps)
            wan.free()
            wan = Wan(cfg, "i2v", dtype)
        except Exception as e:
            measure(root, stage="ab_test", error=type(e).__name__ + ": " + str(e)[:200])
            wan.free()
            wan = Wan(cfg, w["mode"], dtype)  # la production ne doit jamais dépendre de l'étape expérimentale

    report = produce(cfg, root, wan, episodes, dtype, steps_of, deadline)
    (root / "generated" / "run_report.json").write_text(
        json.dumps({"phase": phase, "dtype": dtype, "mode": w["mode"], "elapsed_min": round((time.time() - T0) / 60, 1),
                    "report": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    log("TERMINÉ")


if __name__ == "__main__":
    main()
