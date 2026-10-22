"""Métriques comparatives ancien rendu (plateau) vs nouveau rendu (réalisateur).

Mesure, sur deux fichiers mp4 (un historique publié + une vidéo « cinéma ») :
  1. mouvement moyen (différence absolue inter-images, en % de l'échelle) —
     détecte l'image « morte » qui faisait décrocher la rétention ;
  2. nombre de plans (changements de scène via scdet de ffmpeg, seuil 12) —
     le rythme de montage est le levier n°1 de rétention court format ;
  3. dynamique audio (RMS p10/p90) — un mix plat (boucle à volume constant)
     ne porte pas la voix ; le ducking crée du contraste.

Usage :
  python tests/metrics_compare.py <ancien.mp4> <nouveau.mp4>
Exemple (nécessite ffmpeg dans le PATH) :
  python tests/metrics_compare.py videos/generated/auto_178/auto_178.mp4 ^
                                  videos/generated/auto_217/auto_217_demo.mp4
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

# ------------------------------------------------------------------ helpers


def _runs(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, shell=False)
    if r.returncode != 0:
        raise RuntimeError(f"{' '.join(map(str, cmd))}\n{r.stderr[-600:]}")
    return r.stdout


def mouvement(path, max_frames=240):
    """Différence absolue moyenne entre images consécutives (% de l'échelle)."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path),
         "-vf", "scale=180:320,format=gray,fps=8",
         "-frames:v", str(max_frames), "-f", "rawvideo", "-"],
        capture_output=True).stdout
    buf = np.frombuffer(raw, dtype=np.uint8)
    n = len(buf) // (180 * 320)
    if n < 2:
        return 0.0
    imgs = buf[: n * 180 * 320].reshape(n, 320, 180).astype(np.float32)
    return float(np.abs(np.diff(imgs, axis=0)).mean() / 255.0 * 100.0)


def plans(path):
    """Nombre de changements de scène (seuil scdet=12)."""
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-vf", "select='gt(scene,0.12)',metadata=print",
         "-f", "null", "-"],
        capture_output=True, text=True)
    nb = sum(1 for l in r.stderr.splitlines() if "pts_time" in l)
    return nb


def dynamique_audio(path):
    """Plage dynamique audio : écart p90-p10 du RMS (dB)."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path),
         "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.float32)
    if len(a) < 16000:
        return 0.0, 0.0
    fen = 1600  # 100 ms
    n = len(a) // fen
    rms = np.sqrt((a[: n * fen].reshape(n, fen) ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-12)
    return float(np.percentile(db, 90) - np.percentile(db, 10)), float(np.percentile(db, 90))


def fiche(path):
    meta = json.loads(_runs([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-show_entries", "format=duration", "-of", "json", str(path)]))
    st = meta["streams"][0]
    return dict(duree=float(meta["format"]["duration"]),
                w=st["width"], h=st["height"], fps=st["r_frame_rate"])


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    anc, nou = Path(sys.argv[1]), Path(sys.argv[2])
    for p in (anc, nou):
        if not p.exists():
            print("introuvable :", p)
            sys.exit(2)
    fa, fn = fiche(anc), fiche(nou)
    print(f"{'':34}{'ANCIEN':>16}{'NOUVEAU':>16}")
    print(f"{'résolution':34}{str(fa['w'])+'x'+str(fa['h']):>16}{str(fn['w'])+'x'+str(fn['h']):>16}")
    print(f"{'durée (s)':34}{fa['duree']:>16.2f}{fn['duree']:>16.2f}")

    ma, mn = mouvement(anc), mouvement(nou)
    print(f"{'mouvement inter-images (%)':34}{ma:>16.2f}{mn:>16.2f}")
    pa, pn = plans(anc), plans(nou)
    print(f"{'changements de plan':34}{pa:>16}{pn:>16}")
    da, na = dynamique_audio(anc)
    db_, nb = dynamique_audio(nou)
    print(f"{'dynamique audio p90-p10 (dB)':34}{da:>16.1f}{db_:>16.1f}")
    print(f"{'crête audio p90 (dB)':34}{na:>16.1f}{nb:>16.1f}")
    print()
    if mn > ma * 1.25:
        print("> le nouveau rendu bouge significativement plus (moins d'image morte).")
    if pn > pa:
        print("> le nouveau rendu monte plus de plans (rythme + rétention).")
    if db_ > da:
        print("> le nouveau mix est plus dynamique (ducking des silences actif).")


if __name__ == "__main__":
    main()
