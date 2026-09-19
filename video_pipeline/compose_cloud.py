"""Assemblage d'une vidéo TikTok : plans vidéo IA (générés sur GPU cloud) + narration + sous-titres.

Étapes (chaque phase peut être relancée seule) :
  python video_pipeline/compose_cloud.py <id> prepare  # voix (edge-tts), timings, plan des plans -> shots_plan.json
  (GPU)        cloud/kaggle/generate_shots.py (notebook Kaggle) ou cloud/hf_shots.py   # produit shots/shot_XX.mp4
  python video_pipeline/compose_cloud.py <id> render   # montage 9:16 + sous-titres + musique -> ready/

Les plans sont calés sur la narration : un plan par phrase, durée = durée de la phrase (+ respiration).
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_toon as M  # noqa: E402  (voix, timings mot à mot, musique synthétisée, mixage)
import toon_engine as E  # noqa: E402  (sous-titres animés, titre)
from cloud_episodes import EPISODES, NARRATORS, GENERIC_TAGS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = Path(os.environ.get("VIDEO_ROOT", ROOT / "videos"))  # VIDEO_ROOT : surcharge (Kaggle, tests)
FPS, SR = 24, M.SR
LEAD_IN, GAP, TAIL = 0.15, 0.22, 1.7
MAX_FRAMES = 121  # Wan 2.2 TI2V-5B : 121 images à 24 fps ≈ 5 s


def wan_frames(seconds):
    n = int(round(seconds * FPS))
    n = max(33, min(MAX_FRAMES, n))
    return ((n - 1) // 4) * 4 + 1  # Wan exige 4k+1 images


def prepare(ep):
    work = VIDEOS / "generated" / ep["id"]
    work.mkdir(parents=True, exist_ok=True)
    cfg = NARRATORS[ep["narrator"]]
    lines, t0 = [], LEAD_IN
    for i, b in enumerate(ep["beats"]):
        mp3 = work / f"line_{i:02d}.mp3"
        words = asyncio.run(M.tts_line(b["text"], cfg, mp3))
        a = M.decode(mp3)
        dur = len(a) / SR
        lines.append(dict(who="narrator", emo="neutral", text=b["text"], start=t0, dur=dur, audio=a,
                          punch=b.get("punch", False),
                          words=[(w, t0 + o, t0 + o + d) for (w, o, d) in words]))
        t0 += dur + GAP
    total = lines[-1]["start"] + lines[-1]["dur"] + TAIL
    plan = []
    for i, ln in enumerate(lines):
        start = 0.0 if i == 0 else ln["start"]
        end = total if i == len(lines) - 1 else lines[i + 1]["start"]
        span = end - start
        plan.append(dict(index=i, span=round(span, 3), num_frames=wan_frames(span),
                         prompt=f"{ep['style']} {ep['beats'][i]['shot']}"))
    (work / "shots_plan.json").write_text(json.dumps(
        dict(episode=ep["id"], total=round(total, 3), shots=plan), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{ep['id']} : {len(lines)} plans, durée {total:.1f}s -> {work / 'shots_plan.json'}")
    for p in plan:
        print(f"  plan {p['index']}: {p['span']:.1f}s -> {p['num_frames']} images")
    return work, lines, total


def render(ep):
    work, lines, total = prepare(ep)  # recalcule à l'identique (voix déjà en cache disque non, mais déterministe)
    plan = json.loads((work / "shots_plan.json").read_text(encoding="utf-8"))["shots"]
    shots_dir = work / "shots"
    missing = [p["index"] for p in plan if not (shots_dir / f"shot_{p['index']:02d}.mp4").exists()]
    if missing:
        sys.exit(f"plans vidéo manquants : {missing} (générer d'abord les plans : voir docs/video-ai/KAGGLE.md)")

    # 1) chaque plan est calé à sa durée exacte, redimensionné en 1080x1920, concaténé
    fitted = []
    for p in plan:
        src = shots_dir / f"shot_{p['index']:02d}.mp4"
        out = work / f"fit_{p['index']:02d}.mp4"
        M.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
               "-vf", f"tpad=stop_mode=clone:stop_duration=4,scale={E.W}:{E.H}:force_original_aspect_ratio=increase:flags=lanczos,"
                      f"crop={E.W}:{E.H},fps={FPS},"
                      f"unsharp=5:5:0.6,format=yuv420p",
               "-t", f"{p['span']:.3f}", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", str(out)])
        fitted.append(out)
    lst = work / "fit_list.txt"
    lst.write_text("\n".join(f"file '{f.as_posix()}'" for f in fitted), encoding="utf-8")
    base = work / "base.mp4"
    M.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
           "-c", "copy", str(base)])

    # 2) audio : narration + musique + effets
    wav = M.mix_audio(lines, total, work)
    groups = M.build_caption_groups(lines)

    # 3) surimpressions (titre d'accroche, sous-titres animés, appel à suivre)
    out = work / f"{ep['id']}.mp4"
    n_frames = int(total * FPS)
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(base), "-f", "rawvideo",
                            "-pix_fmt", "bgra", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
                            "-s", f"{E.W}x{E.H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                            "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "160k",
                            "-t", f"{n_frames / FPS:.3f}", "-movflags", "+faststart", str(out)],
                           stdin=subprocess.PIPE)
    fsize = E.W * E.H * 4
    t_start = time.time()
    for f in range(n_frames):
        buf = dec.stdout.read(fsize)
        if len(buf) < fsize:
            break
        surf = cairo.ImageSurface.create_for_data(bytearray(buf), cairo.FORMAT_ARGB32, E.W, E.H)
        ctx = cairo.Context(surf)
        ctx.set_antialias(cairo.ANTIALIAS_BEST)
        t = f / FPS
        E.stroked_text(ctx, f"FACTVIBES TOONS  •  ÉPISODE {ep['ep']}", E.W / 2, 150, 32, (255, 255, 255),
                       ow=7, family="Arial Black")
        if t < 4.0:  # titre d'accroche : seulement au début (les 3 premières secondes décident)
            ctx.push_group()
            E.draw_headline(ctx, ep["headline"], "", ep["accent"], t)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(1.0 if t < 3.4 else max(0.0, (4.0 - t) / 0.6))
        for g in groups:
            if g[0][1] - 0.02 <= t < g[-1][2] + 0.12:
                now = -1
                for i, w in enumerate(g):
                    if w[1] <= t:
                        now = i
                E.draw_caption(ctx, g, now, t, ep["accent"])
                break
        if t > total - 1.5:
            import math
            pulse = 1 + 0.05 * math.sin(t * 8)
            ctx.save(); ctx.translate(E.W / 2, 1600); ctx.scale(pulse, pulse)
            E.stroked_text(ctx, "SUIS POUR LA SUITE", 0, 0, 64, ep["accent"], ow=12)
            ctx.restore()
        enc.stdin.write(surf.get_data())
        if f % 96 == 0:
            print(f"  image {f}/{n_frames} ({time.time() - t_start:.0f}s)", flush=True)
    enc.stdin.close()
    dec.stdout.close()
    if enc.wait() != 0:
        raise RuntimeError("encodage ffmpeg échoué")

    v, a, dur, mean = M.qc(out)
    hashtags = ep["tags"] + GENERIC_TAGS
    meta = {
        "video_id": ep["id"], "series": "FactVibes Toons", "episode": ep["ep"], "title": ep["title"],
        "topic": ep["topic"], "hook": ep["headline"].replace("|", " "),
        "description": " ".join(b["text"] for b in ep["beats"][:2]), "hashtags": hashtags,
        "duration_sec": round(dur, 2), "resolution": f"{v['width']}x{v['height']}", "fps": v["r_frame_rate"],
        "codecs": {"video": v["codec_name"], "audio": a["codec_name"]}, "mean_volume": mean,
        "beats": [{"text": b["text"], "shot": b["shot"]} for b in ep["beats"]],
        "engine": "Wan 2.2 (plans IA générés sur GPU cloud) + edge-tts + ffmpeg/cairo",
        "ai_generated_content": True, "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READY", "caption": f"{ep['title']} — épisode {ep['ep']} " + " ".join(hashtags),
    }
    (VIDEOS / "metadata").mkdir(exist_ok=True)
    (VIDEOS / "ready").mkdir(exist_ok=True)
    (VIDEOS / "metadata" / f"{ep['id']}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (VIDEOS / "ready" / f"{ep['id']}.mp4").write_bytes(out.read_bytes())
    print(f"OK {ep['id']} {dur:.1f}s {v['width']}x{v['height']} volume moyen {mean}")


if __name__ == "__main__":
    ep = next(e for e in EPISODES if e["id"] == sys.argv[1])
    {"prepare": prepare, "render": render}[sys.argv[2]](ep)
