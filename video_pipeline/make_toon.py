"""Génère un épisode de dessin animé parlant (voix edge-tts + moteur toon_engine + ffmpeg).

Usage :
  python video_pipeline/make_toon.py toon_001            # épisode complet -> videos/ready/
  python video_pipeline/make_toon.py toon_001 --png 9.5  # une seule image à t=9.5s (contrôle visuel)
  python video_pipeline/make_toon.py toon_001 --seconds 6 # aperçu court (test de vitesse)
"""
import asyncio
import json
import math
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cairo
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import toon_engine as E  # noqa: E402
from toon_scripts import EPISODES, GENERIC_TAGS, VOICES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = Path(os.environ.get("VIDEO_ROOT", ROOT / "videos"))  # VIDEO_ROOT : surcharge (Kaggle, tests)
FPS = 24
SR = 24000
LEAD_IN, GAP, TAIL = 0.7, 0.3, 1.8


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} : {r.stderr[-800:]}")
    return r


# ------------------------------------------------------------------ voix
# 13/10/2026 — PANNE MICROSOFT : depuis le 10/10, Read Aloud a migré de
# speech.platform.bing.com vers api.msedgeservices.com et REFUSE (403) l'ancien point
# d'entrée WebSocket que utilise edge-tts 7.2.8. Conséquence visible : plus AUCUN rendu
# possible, et le compte s'est tu faute de vidéos prêtes. Le jeton client est inchangé :
# il suffit de rediriger l'URL WebSocket. Le nouveau point d'entrée limite plus durement
# (429 « too many requests »), d'où les réessais ci-dessous.
EDGE_WSS_V2 = "wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1"


def _utiliser_nouveau_point_tts():
    """Redirige edge-tts vers le point d'entrée Microsoft actuel (idempotent).

    On modifie `edge_tts.communicate.WSS_URL` et NON `edge_tts.constants.WSS_URL` : la
    bibliothèque fait `from .constants import WSS_URL`, elle garde donc sa propre copie
    et n'utiliserait pas notre changement autrement.
    """
    from edge_tts import communicate
    from edge_tts.constants import TRUSTED_CLIENT_TOKEN
    if "msedgeservices" not in communicate.WSS_URL:
        communicate.WSS_URL = (f"{EDGE_WSS_V2}"
                               f"?Ocp-Apim-Subscription-Key={TRUSTED_CLIENT_TOKEN}")


async def tts_line(text, cfg, path):
    import edge_tts
    from aiohttp import ClientResponseError

    _utiliser_nouveau_point_tts()
    derniere = None
    for essai in range(4):
        words = []
        try:
            com = edge_tts.Communicate(text, cfg["voice"], rate=cfg["rate"],
                                       pitch=cfg["pitch"], boundary="WordBoundary")
            with open(path, "wb") as f:
                async for ch in com.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append((ch["text"], ch["offset"] / 1e7,
                                      ch["duration"] / 1e7))
            return words
        except (ClientResponseError, Exception) as exc:   # 403/429, réseau, « no audio »
            derniere = exc
            await asyncio.sleep(2 * (essai + 1))
    raise derniere


def decode(path):
    r = run(["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "f32le", "-ac", "1",
             "-ar", str(SR), "-"])
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def robotize(a):
    t = np.arange(len(a)) / SR
    mod = 0.65 + 0.35 * np.sin(2 * np.pi * 62 * t)
    return (a * mod * 1.15).astype(np.float32)


# ------------------------------------------------------------------ musique + sfx (synthèse maison)
def make_music(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    bpm, beat = 92, 60 / 92
    chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
    out = np.zeros(n, dtype=np.float32)
    bar = beat * 4
    for i in range(int(dur / bar) + 1):
        s, e = int(i * bar * SR), min(n, int((i + 1) * bar * SR))
        if s >= n:
            break
        tt = np.arange(e - s) / SR
        env = np.minimum(1, tt / 0.15) * np.exp(-tt * 0.5)
        for f in chords[i % 4]:
            out[s:e] += (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2 * f * tt)) * env * 0.06
        for b in range(4):  # kick + charleston discrets
            ks = s + int(b * beat * SR)
            kl = int(0.18 * SR)
            if ks + kl < n:
                kt = np.arange(kl) / SR
                out[ks:ks + kl] += np.sin(2 * np.pi * (58 + 60 * np.exp(-kt * 30)) * kt) * np.exp(-kt * 16) * 0.20
            hs = s + int((b + 0.5) * beat * SR)
            hl = int(0.04 * SR)
            if hs + hl < n:
                rng = np.random.default_rng(b + i)
                out[hs:hs + hl] += rng.standard_normal(hl).astype(np.float32) * np.exp(-np.arange(hl) / SR * 90) * 0.03
    return out


def bwomp():
    l = int(0.45 * SR)
    tt = np.arange(l) / SR
    return (np.sin(2 * np.pi * np.cumsum(420 * np.exp(-tt * 7) + 70) / SR) * np.exp(-tt * 6) * 0.35).astype(np.float32)


def pop():
    l = int(0.12 * SR)
    tt = np.arange(l) / SR
    return (np.sin(2 * np.pi * (300 + 700 * np.exp(-tt * 40)) * tt) * np.exp(-tt * 30) * 0.18).astype(np.float32)


# ------------------------------------------------------------------ épisode
def prepare(ep):
    work = VIDEOS / "generated" / ep["id"]
    work.mkdir(parents=True, exist_ok=True)
    lines, t0 = [], LEAD_IN
    for i, ln in enumerate(ep["lines"]):
        cfg = VOICES[ln["who"]]
        mp3 = work / f"line_{i:02d}.mp3"
        words = asyncio.run(tts_line(ln["text"], cfg, mp3))
        a = decode(mp3)
        if cfg.get("robot"):
            a = robotize(a)
        dur = len(a) / SR
        hop = SR // FPS
        rms = np.array([np.sqrt(np.mean(a[j:j + hop] ** 2)) if j < len(a) else 0
                        for j in range(0, len(a) + hop, hop)])
        ref = np.percentile(rms[rms > 0.005], 92) if (rms > 0.005).any() else 1.0
        lines.append(dict(**ln, start=t0, dur=dur, audio=a, rms=np.clip(rms / max(ref, 1e-6), 0, 1),
                          words=[(w, t0 + o, t0 + o + d) for (w, o, d) in words]))
        t0 += dur + GAP
    total = lines[-1]["start"] + lines[-1]["dur"] + TAIL
    return work, lines, total


def mix_audio(lines, total, work):
    n = int(total * SR)
    voice = np.zeros(n, dtype=np.float32)
    sfx = np.zeros(n, dtype=np.float32)
    for ln in lines:
        s = int(ln["start"] * SR)
        voice[s:s + len(ln["audio"])] += ln["audio"][: n - s]
        if ln.get("punch"):
            b = bwomp()
            e = int((ln["start"] + ln["dur"]) * SR)
            sfx[e:e + len(b)] += b[: max(0, n - e)]
        p = pop()
        sfx[s:s + len(p)] += p[: max(0, n - s)]
    music = make_music(total)
    env = np.convolve(np.abs(voice), np.ones(int(0.12 * SR)) / int(0.12 * SR), mode="same")
    duck = 1 - 0.65 * np.clip(env * 9, 0, 1)
    fade = np.minimum(1, np.arange(n) / (SR * 0.5)) * np.minimum(1, (n - np.arange(n)) / (SR * 1.2))
    mixed = voice * 1.0 + sfx + music * duck * fade
    peak = np.max(np.abs(mixed))
    mixed = mixed / peak * 0.89 if peak > 0.89 else mixed
    wav = work / "mix.wav"
    import wave
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mixed * 32767).astype(np.int16).tobytes())
    return wav


def build_caption_groups(lines):
    groups = []
    for li, ln in enumerate(lines):
        cur = []
        for w in ln["words"]:
            cur.append(w)
            chars = sum(len(x[0]) for x in cur) + len(cur)
            if len(cur) >= 4 or chars >= 24 or w[0].endswith((".", "!", "?")):
                groups.append(cur); cur = []
        if cur:
            groups.append(cur)
    return groups


def render(ep, lines, total, wav, out_path, png_at=None, seconds=None):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, E.W, E.H)
    ctx = cairo.Context(surf)
    ctx.set_antialias(cairo.ANTIALIAS_BEST)

    bg = cairo.ImageSurface(cairo.FORMAT_ARGB32, E.W, E.H)
    bctx = cairo.Context(bg)
    counter = E.draw_set(bctx, ep["set"], ep.get("bg_image"))
    vignette = E.make_vignette() if ep.get("cinematic") else None
    cam = dict(z=1.0, fx=E.W / 2, fy=900.0)

    chars = {"L": E.Toon(ep["left"], E.LEFT_X, 1), "R": E.Toon(ep["right"], E.RIGHT_X, 2)}
    side_of = {ep["left"]: "L", ep["right"]: "R"}
    groups = build_caption_groups(lines)
    n_frames = int((seconds if seconds else total) * FPS)

    ff = None
    if png_at is None:
        ff = subprocess.Popen(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgra",
             "-s", f"{E.W}x{E.H}", "-r", str(FPS), "-i", "-", "-i", str(wav),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p",
             "-af", "loudnorm=I=-15:TP=-1.5:LRA=9", "-c:a", "aac", "-b:a", "160k", "-t", f"{n_frames / FPS:.3f}", "-movflags", "+faststart",
             str(out_path)], stdin=subprocess.PIPE)

    frames = [int(png_at * FPS)] if png_at is not None else range(n_frames)
    t_start = time.time()
    prev_t = 0.0
    for f in frames:
        t = f / FPS
        dt = max(t - prev_t, 1 / FPS)
        prev_t = t
        speaker, cur = None, None
        for ln in lines:
            if ln["start"] <= t < ln["start"] + ln["dur"] + 0.08:
                speaker, cur = ln, ln
        energy = {"L": 0.0, "R": 0.0}
        if speaker:
            idx = min(int((t - speaker["start"]) * FPS), len(speaker["rms"]) - 1)
            energy[side_of[speaker["who"]]] = float(speaker["rms"][max(idx, 0)])
        for s in "LR":
            chars[s].update(energy[s], dt)

        # caméra : léger zoom + secousse sur la chute
        shake_dx = shake_dy = 0.0
        for ln in lines:
            if ln.get("punch"):
                d = t - (ln["start"] + ln["dur"] - 0.1)
                if 0 <= d < 0.45:
                    k = (1 - d / 0.45)
                    shake_dx, shake_dy = math.sin(d * 80) * 14 * k, math.cos(d * 71) * 10 * k
        if ep.get("cinematic") and speaker:
            li = lines.index(speaker)
            sx = E.LEFT_X if side_of[speaker["who"]] == "L" else E.RIGHT_X
            kind = "close" if speaker.get("punch") else ("wide" if li == 0 else "med")
            tz, tfx, tfy = {"wide": (1.0, E.W / 2, 900.0), "med": (1.3, sx, 930.0), "close": (1.85, sx, 880.0)}[kind]
        else:
            tz, tfx, tfy = 1.0 + 0.035 * t / total, E.W / 2, 900.0
        kk = 1 - math.exp(-dt * 9)
        cam["z"] += (tz - cam["z"]) * kk
        cam["fx"] += (tfx - cam["fx"]) * kk
        cam["fy"] += (tfy - cam["fy"]) * kk
        z = cam["z"]
        fx = min(max(cam["fx"], E.W / (2 * z)), E.W - E.W / (2 * z))
        fy = min(max(cam["fy"], E.H / (2 * z)), E.H - E.H / (2 * z))

        ctx.set_source_rgba(0, 0, 0, 1)
        ctx.paint()
        ctx.save()
        ctx.translate(E.W / 2 + shake_dx, E.H / 2 + shake_dy)
        ctx.scale(z, z)
        ctx.translate(-fx, -fy)
        ctx.set_source_surface(bg, 0, 0)
        ctx.paint()
        order = ["L", "R"]
        if speaker:
            order = [s for s in "LR" if s != side_of[speaker["who"]]] + [side_of[speaker["who"]]]
        for s in order:
            ch = chars[s]
            is_speaking = bool(speaker and side_of[speaker["who"]] == s)
            intro = E.ease_out_back((t - (0.10 if s == "L" else 0.25)) / 0.45)
            pop_ = intro * (0.985 if not is_speaking else 1.0)
            if is_speaking:
                pop_ *= 1 + 0.045 * max(0.0, 1 - (t - speaker["start"]) / 0.25) * (1 if t >= speaker["start"] else 0)
            emo = speaker["emo"] if is_speaking else ("worried" if speaker and speaker["emo"] == "angry" else "neutral")
            if not is_speaking and speaker and speaker["emo"] == "happy":
                emo = "neutral"
            ch.draw(ctx, t, is_speaking, emo, +1 if s == "L" else -1, pop=max(pop_, 0.001),
                    reacting=not is_speaking)
        E.draw_counter(ctx, counter)
        ctx.restore()
        if vignette is not None:
            ctx.set_source_surface(vignette, 0, 0)
            ctx.paint()

        # surimpressions fixes
        E.stroked_text(ctx, f"FACTVIBES TOONS  •  ÉPISODE {ep['ep']}", E.W / 2, 150, 32, (255, 255, 255), ow=7, family="Arial Black")
        if not ep.get("cinematic") or t < 4.0:  # règle virale : titre visible seulement au début
            if ep.get("cinematic"):
                ctx.push_group()
            E.draw_headline(ctx, ep["headline"], "", ep["accent"], t)
            if ep.get("cinematic"):
                ctx.pop_group_to_source()
                ctx.paint_with_alpha(1.0 if t < 3.4 else max(0.0, (4.0 - t) / 0.6))
        for g in groups:
            g_start, g_end = g[0][1], g[-1][2] + 0.12
            if g_start - 0.02 <= t < g_end:
                now = -1
                for i, w in enumerate(g):
                    if w[1] <= t:
                        now = i
                E.draw_caption(ctx, g, now, t, ep["accent"])
                break
        if t > total - 1.6:
            pulse = 1 + 0.05 * math.sin(t * 8)
            ctx.save(); ctx.translate(E.W / 2, 1600); ctx.scale(pulse, pulse)
            E.stroked_text(ctx, "SUIS POUR LA SUITE", 0, 0, 64, ep["accent"], ow=12)
            ctx.restore()

        if png_at is not None:
            surf.write_to_png(str(out_path))
            return
        ff.stdin.write(surf.get_data())
        if f % 48 == 0:
            el = time.time() - t_start
            print(f"  {ep['id']} image {f}/{n_frames} ({el:.0f}s écoulées)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg a échoué à l'encodage")


def qc(path):
    r = run(["ffprobe", "-v", "error", "-show_entries",
             "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration",
             "-of", "json", str(path)])
    info = json.loads(r.stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    assert (v["width"], v["height"]) == (E.W, E.H), "format inattendu"
    assert a is not None, "audio absent"
    assert 20 < dur < 60, f"durée hors plage ({dur:.1f}s)"
    vol = run(["ffmpeg", "-i", str(path), "-af", "volumedetect", "-f", "null", "-", "-hide_banner"])
    mean = [l for l in vol.stderr.decode(errors="ignore").splitlines() if "mean_volume" in l]
    return v, a, dur, (mean[0].split("mean_volume:")[1].strip() if mean else "?")


def build(ep_id, seconds=None, png_at=None):
    """Construit un épisode complet (TTS -> mix -> render -> QC -> ready/) et renvoie ses métadonnées.

    - png_at  : génère UNE image de contrôle et renvoie son chemin (aucun mp4).
    - seconds : génère un aperçu court (test) et renvoie son chemin.
    Renvoie le dict de métadonnées (déjà écrit dans videos/metadata/ et copié dans videos/ready/).
    """
    ep = next(e for e in EPISODES if e["id"] == ep_id)
    work, lines, total = prepare(ep)
    print(f"{ep['id']} : {len(lines)} répliques, durée {total:.1f}s", flush=True)
    wav = mix_audio(lines, total, work)
    if png_at is not None:
        out = work / f"frame_{png_at:.1f}.png"
        render(ep, lines, total, wav, out, png_at=png_at)
        print(out)
        return out
    out = work / (f"{ep['id']}_preview.mp4" if seconds else f"{ep['id']}.mp4")
    t0 = time.time()
    render(ep, lines, total, wav, out, seconds=seconds)
    print(f"rendu en {time.time() - t0:.0f}s", flush=True)
    if seconds:
        return out
    v, a, dur, mean = qc(out)
    hashtags = (ep["tags"] + ["#FactVibesToons"])[:5]  # 5 hashtags max, jamais #fyp/#viral
    meta = {
        "video_id": ep["id"], "series": "FactVibes Toons", "episode": ep["ep"],
        "title": ep["title"], "topic": ep["topic"],
        "hook": ep["headline"].replace("|", " "),
        "description": " / ".join(l["text"] for l in lines[:2]),
        "hashtags": hashtags, "duration_sec": round(dur, 2),
        "resolution": f"{v['width']}x{v['height']}", "fps": v["r_frame_rate"],
        "codecs": {"video": v["codec_name"], "audio": a["codec_name"]},
        "mean_volume": mean,
        "lines": [{"who": l["who"], "emo": l["emo"], "text": l["text"]} for l in lines],
        "engine": "pycairo (dessin vectoriel) + edge-tts + ffmpeg — CPU, personnages et musique originaux",
        "ai_generated_content": True,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READY",
        "caption": f"{ep['title']} — épisode {ep['ep']} " + " ".join(hashtags),
    }
    (VIDEOS / "metadata").mkdir(exist_ok=True)
    (VIDEOS / "ready").mkdir(exist_ok=True)
    (VIDEOS / "metadata" / f"{ep['id']}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (VIDEOS / "ready" / f"{ep['id']}.mp4").write_bytes(out.read_bytes())
    print(f"OK {ep['id']} {dur:.1f}s {v['width']}x{v['height']} volume moyen {mean}")
    return meta


def main():
    args = sys.argv[1:]
    ep_id = args[0]
    png_at = float(args[args.index("--png") + 1]) if "--png" in args else None
    seconds = float(args[args.index("--seconds") + 1]) if "--seconds" in args else None
    build(ep_id, seconds=seconds, png_at=png_at)


if __name__ == "__main__":
    main()
