"""Moteur de génération CPU : Pillow (images) + edge-tts (voix FR) + ffmpeg (montage).

Une "scène" du concept est découpée en phrases. Chaque phrase = 1 image (titre + sous-titre)
+ 1 voix + 1 clip 9:16 1080x1920 dont la durée colle exactement à l'audio. Les clips sont
concaténés sans ré-encodage. Rien n'est simulé : chaque étape est vérifiée avec ffprobe.

Usage : python video_pipeline/generate.py [video_001 video_002 ...]
"""
import asyncio
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "videos"
CONCEPTS = json.loads((ROOT / "video_pipeline" / "concepts.json").read_text(encoding="utf-8"))

W, H = 1080, 1920
FPS = 30
TAIL = 0.35  # respiration après chaque phrase
FONT_BOLD = r"C:\Windows\Fonts\arialbd.ttf"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} a échoué:\n{r.stderr[-1500:]}")
    return r


def wrap_text(text, font, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = f"{cur} {word}".strip()
        if font.getbbox(test)[2] <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_block(draw, lines, font, y_start, line_h, fill):
    for i, ln in enumerate(lines):
        bbox = draw.textbbox((0, 0), ln, font=font)
        x = (W - (bbox[2] - bbox[0])) // 2
        y = y_start + i * line_h
        draw.text((x + 5, y + 5), ln, font=font, fill=(0, 0, 0))
        draw.text((x, y), ln, font=font, fill=fill)


def make_frame(headline, subtitle, bg, accent, out_path):
    bg, accent = tuple(bg), tuple(accent)
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    grad = np.array(bg, dtype=np.float32)[None, :] * (1 - 0.55 * t)
    arr = np.repeat(grad[:, None, :], W, axis=1).astype(np.uint8)
    img = Image.fromarray(arr, "RGB")
    draw = ImageDraw.Draw(img)

    big = ImageFont.truetype(FONT_BOLD, 118)
    draw_block(draw, wrap_text(headline, big, W - 200), big, int(H * 0.22), 145, accent)

    small = ImageFont.truetype(FONT_BOLD, 56)
    draw_block(draw, wrap_text(subtitle, small, W - 180), small, int(H * 0.62), 76, (255, 255, 255))

    for ypos in (int(H * 0.12), int(H * 0.90)):
        draw.rectangle([W * 0.08, ypos, W * 0.92, ypos + 14], fill=accent)
    img.save(out_path)


async def tts_all(jobs):
    import edge_tts

    for text, voice, path in jobs:
        await edge_tts.Communicate(text, voice, rate="+6%").save(str(path))


def probe_duration(path):
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(path)])
    return float(r.stdout.strip())


def split_sentences(text):
    return [p for p in re.split(r"(?<=[.!?…])\s+", text.strip()) if p]


def make_clip(frame, audio, dur, out_path):
    frames = int(dur * FPS) + 1
    vf = (f"zoompan=z='min(zoom+0.0007,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
          f"d={frames}:s={W}x{H}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loglevel", "error",
         "-i", str(frame), "-i", str(audio),
         "-vf", vf, "-af", "apad,aresample=44100",
         "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "aac", "-b:a", "128k", "-ac", "2",
         str(out_path)])


def concat_clips(clips, out_path):
    lst = out_path.with_suffix(".txt")
    lst.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out_path)])


def generate(concept):
    cid = concept["id"]
    work = VIDEOS / "generated" / cid
    work.mkdir(parents=True, exist_ok=True)

    segments = []
    for sc in concept["scenes"]:
        for sent in split_sentences(sc["voiceover"]):
            segments.append((sc["text"], sent, sc["bg"], sc["accent"]))

    tts_jobs, frames, audios = [], [], []
    for i, (head, sent, bg, acc) in enumerate(segments):
        fr, au = work / f"seg_{i:02d}.png", work / f"seg_{i:02d}.mp3"
        make_frame(head, sent, bg, acc, fr)
        frames.append(fr)
        audios.append(au)
        tts_jobs.append((sent, concept["audio_voice"], au))
    asyncio.run(tts_all(tts_jobs))

    clips = []
    for i, (fr, au) in enumerate(zip(frames, audios)):
        dur = probe_duration(au) + TAIL
        clip = work / f"clip_{i:02d}.mp4"
        make_clip(fr, au, dur, clip)
        clips.append(clip)
        print(f"  {cid} segment {i + 1}/{len(segments)} ok ({dur:.1f}s)", flush=True)

    final = work / f"{cid}.mp4"
    concat_clips(clips, final)

    # Contrôle qualité réel
    probe = json.loads(run(["ffprobe", "-v", "error", "-show_entries",
                            "stream=codec_type,codec_name,width,height,r_frame_rate",
                            "-of", "json", str(final)]).stdout)
    v = next(s for s in probe["streams"] if s["codec_type"] == "video")
    a = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
    total = probe_duration(final)
    assert (v["width"], v["height"]) == (W, H), f"format inattendu {v['width']}x{v['height']}"
    assert a is not None, "piste audio absente"
    assert total > 10, f"vidéo trop courte ({total:.1f}s)"

    meta = {
        "video_id": cid,
        "title": concept["title"],
        "hook": concept["hook"],
        "description": concept["description"],
        "hashtags": concept["hashtags"],
        "voice": concept["audio_voice"],
        "duration_sec": round(total, 2),
        "resolution": f"{v['width']}x{v['height']}",
        "fps": v["r_frame_rate"],
        "codecs": {"video": v["codec_name"], "audio": a["codec_name"]},
        "scenes": concept["scenes"],
        "engine": "pillow + edge-tts + ffmpeg (CPU) — Wan2GP/MiniMax non utilisables : aucun GPU",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READY",
        "caption": f"{concept['title']} — {concept['hook']} " + " ".join(concept["hashtags"]),
    }
    (VIDEOS / "metadata").mkdir(parents=True, exist_ok=True)
    (VIDEOS / "ready").mkdir(parents=True, exist_ok=True)
    (VIDEOS / "metadata" / f"{cid}.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (VIDEOS / "ready" / f"{cid}.mp4").write_bytes(final.read_bytes())
    return meta


def main():
    ids = sys.argv[1:] or [c["id"] for c in CONCEPTS["concepts"]]
    for concept in CONCEPTS["concepts"]:
        if concept["id"] in ids:
            m = generate(concept)
            print(f"OK {m['video_id']} {m['duration_sec']}s {m['resolution']}", flush=True)
    print("DONE")


if __name__ == "__main__":
    main()
