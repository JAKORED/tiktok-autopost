"""Contrôle automatique d'un fichier vidéo : technique + intégrité + signaux de qualité + images d'inspection.

Ne remplace PAS l'inspection visuelle : il élimine les fichiers cassés, noirs ou figés et produit une planche
d'images (0, 20, 40, 60, 80, 100 %) à regarder avant de déclarer une vidéo bonne.

Usage :
  python cloud/validate_video.py <fichier.mp4> [--kind shot|final] [--frames] [--json]
Sortie : rapport lisible (ou JSON) ; code de sortie 0 = valide, 1 = invalide.
Dépendances : ffmpeg + ffprobe dans le PATH ; Pillow (facultatif, pour les signaux de qualité et la planche).
Fonctionne sous Windows et Linux/Kaggle (aucun chemin en dur).
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Exigences par type de fichier. « shot » = plan IA brut ; « final » = vidéo montée prête pour TikTok.
RULES = {
    "shot": dict(min_dur=1.5, max_dur=12.0, min_w=320, min_h=480, audio=False, min_kb=20),
    "final": dict(min_dur=20.0, max_dur=60.0, exact_size=(1080, 1920), min_fps=23, max_fps=31,
                  audio=True, min_kb=300, min_volume_db=-30.0),
}


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    r = _run(["ffprobe", "-v", "error", "-show_entries",
              "stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames:format=duration,size",
              "-of", "json", str(path)])
    if r.returncode != 0:
        return None
    return json.loads(r.stdout)


def _fps(text):
    try:
        a, b = text.split("/")
        return float(a) / float(b) if float(b) else 0.0
    except Exception:
        return 0.0


def decodes_cleanly(path):
    """Décode tout le fichier ; toute erreur ffmpeg = fichier corrompu."""
    r = _run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "null", "-"])
    return (r.returncode == 0 and not r.stderr.strip()), r.stderr.strip()[:300]


def mean_volume_db(path):
    r = _run(["ffmpeg", "-i", str(path), "-af", "volumedetect", "-vn", "-f", "null", "-", "-hide_banner"])
    for line in r.stderr.splitlines():
        if "mean_volume" in line:
            try:
                return float(line.split("mean_volume:")[1].split("dB")[0])
            except Exception:
                return None
    return None


def extract_frames(path, outdir, n=6, width=270):
    """Extrait n images à 0, 20, …, 100 % de la durée. Retourne la liste des fichiers."""
    info = probe(path)
    dur = float(info["format"]["duration"]) if info else 0.0
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    files = []
    for i in range(n):
        t = max(0.0, min(dur - 0.05, dur * i / (n - 1))) if dur else 0.0
        f = outdir / f"frame_{i * 100 // (n - 1):03d}pct.png"
        _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(path),
              "-frames:v", "1", "-vf", f"scale={width}:-2", str(f)])
        if f.exists():
            files.append(f)
    return files


def contact_sheet(files, out):
    from PIL import Image
    ims = [Image.open(f) for f in files]
    if not ims:
        return None
    w = sum(i.width for i in ims)
    sheet = Image.new("RGB", (w, max(i.height for i in ims)))
    x = 0
    for im in ims:
        sheet.paste(im, (x, 0))
        x += im.width
    sheet.save(out)
    return out


def quality_signals(files):
    """Luminance, contraste et mouvement entre images échantillonnées (détecte noir / figé)."""
    try:
        from PIL import Image, ImageChops, ImageStat
    except ImportError:
        return {}
    if not files:
        return {}
    grays = [Image.open(f).convert("L").resize((64, 114)) for f in files]
    lum = [ImageStat.Stat(g).mean[0] for g in grays]
    std = [ImageStat.Stat(g).stddev[0] for g in grays]
    motion = [ImageStat.Stat(ImageChops.difference(a, b)).mean[0] for a, b in zip(grays, grays[1:])]
    return {"mean_luminance": round(sum(lum) / len(lum), 1), "mean_contrast": round(sum(std) / len(std), 1),
            "mean_motion": round(sum(motion) / len(motion), 2) if motion else 0.0}


def validate(path, kind="shot", frames=False):
    """Retourne un dict {ok, problems, info}. `problems` vide = fichier valide techniquement."""
    path = Path(path)
    rule = RULES[kind]
    problems, info = [], {"file": str(path), "kind": kind}
    if not path.exists() or path.stat().st_size == 0:
        return {"ok": False, "problems": ["fichier absent ou vide"], "info": info}
    info["size_kb"] = round(path.stat().st_size / 1024)
    if info["size_kb"] < rule["min_kb"]:
        problems.append(f"fichier trop petit ({info['size_kb']} Ko < {rule['min_kb']} Ko)")
    meta = probe(path)
    if not meta:
        return {"ok": False, "problems": problems + ["ffprobe ne lit pas le fichier"], "info": info}
    v = next((s for s in meta["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in meta["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        return {"ok": False, "problems": problems + ["aucune piste vidéo"], "info": info}
    dur = float(meta["format"].get("duration", 0) or 0)
    fps = _fps(v.get("r_frame_rate", "0/1"))
    info.update(codec=v["codec_name"], width=v["width"], height=v["height"], fps=round(fps, 2),
                duration=round(dur, 2), audio=(a["codec_name"] if a else None))
    if not (rule["min_dur"] <= dur <= rule["max_dur"]):
        problems.append(f"durée {dur:.1f}s hors plage [{rule['min_dur']}, {rule['max_dur']}]")
    if "exact_size" in rule and (v["width"], v["height"]) != rule["exact_size"]:
        problems.append(f"résolution {v['width']}x{v['height']} ≠ {rule['exact_size'][0]}x{rule['exact_size'][1]}")
    if "min_w" in rule and (v["width"] < rule["min_w"] or v["height"] < rule["min_h"]):
        problems.append(f"résolution trop faible {v['width']}x{v['height']}")
    if v["height"] <= v["width"]:
        problems.append("format non vertical (9:16 attendu)")
    if "min_fps" in rule and not (rule["min_fps"] <= fps <= rule["max_fps"]):
        problems.append(f"fps {fps:.1f} hors [{rule['min_fps']}, {rule['max_fps']}]")
    if rule["audio"]:
        if not a:
            problems.append("piste audio absente")
        else:
            vol = mean_volume_db(path)
            info["mean_volume_db"] = vol
            if vol is None or vol < rule["min_volume_db"]:
                problems.append(f"audio trop faible ou illisible ({vol} dB)")
    ok_dec, err = decodes_cleanly(path)
    if not ok_dec:
        problems.append(f"erreur de décodage : {err}")
    outdir = (path.parent / (path.stem + "_frames")) if frames else Path(tempfile.mkdtemp(prefix="vv_"))
    files = extract_frames(path, outdir)
    if not files:
        problems.append("aucune image extractible (fichier corrompu ?)")
    sig = quality_signals(files)
    info.update(sig)
    if sig:
        if sig["mean_luminance"] < 12:
            problems.append("image quasi noire")
        if kind == "shot" and sig["mean_motion"] < 0.5:
            problems.append("plan quasi figé (mouvement très faible)")
    if frames and files:
        sheet = contact_sheet(files, outdir / "contact_sheet.png")
        info["frames_dir"] = str(outdir)
        info["contact_sheet"] = str(sheet) if sheet else None
    return {"ok": not problems, "problems": problems, "info": info}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    kind = args[args.index("--kind") + 1] if "--kind" in args else "shot"
    res = validate(args[0], kind=kind, frames="--frames" in args)
    if "--json" in args:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(("VALIDE" if res["ok"] else "INVALIDE"), "—", args[0])
        for k, v in res["info"].items():
            print(f"  {k}: {v}")
        for p in res["problems"]:
            print(f"  PROBLÈME : {p}")
    sys.exit(0 if res["ok"] else 1)
