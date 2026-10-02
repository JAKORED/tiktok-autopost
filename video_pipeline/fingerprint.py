"""Empreinte visuelle d'une vidéo (dHash multi-images) pour détecter les doublons.

Pourquoi : le même scénario rendu 4 fois donne 4 fichiers différents (donc pas de
« même nom ») mais une vidéo visuellement identique. Et deux scénarios différents
partagés le même décor + les mêmes personnages. Le nom de fichier ne suffit pas :
on compare le contenu réel des images.

Méthode (ffmpeg, aucune dépendance Python) :
  - on extrait une image toutes les ~6 s, réduite à 9x8 niveaux de gris ;
  - dHash : on compare chaque pixel au voisin de droite -> 64 bits par image ;
  - l'empreinte d'une vidéo = la liste de ses dHash ;
  - distance = Hamming moyen normalisé (0 = identique, 1 = sans rapport).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

W, H = 9, 8
FRAME_SECONDS = 6
MAX_FRAMES = 6


def _ffmpeg(path: Path) -> list[bytes]:
    """Octets bruts des images reductions (W*H par image, suite concatenée)."""
    cmd = [
        "ffmpeg", "-v", "error", "-i", str(path),
        "-vf", f"fps=1/{FRAME_SECONDS},scale={W}:{H},format=gray",
        "-frames:v", str(MAX_FRAMES),
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if out.returncode != 0 or not out.stdout:
        return []
    raw, size = out.stdout, W * H
    return [raw[i:i + size] for i in range(0, len(raw) - size + 1, size)]


def _dhash(frame: bytes) -> int:
    bits = 0
    for y in range(H):
        row = y * W
        for x in range(W - 1):
            bits = (bits << 1) | (1 if frame[row + x] > frame[row + x + 1] else 0)
    return bits


def video_hash(path) -> list[int]:
    """Empreinte d'une vidéo = [dHash de chaque image échantillonnée]."""
    path = Path(path)
    if not path.exists():
        return []
    return [_dhash(f) for f in _ffmpeg(path) if len(f) == W * H]


def _popcount(x: int) -> int:
    return bin(x).count("1")


def distance(a: list[int], b: list[int]) -> float:
    """Distance de Hamming moyenne normalisée entre deux vidéos (0..1)."""
    if not a or not b:
        return 1.0
    n = min(len(a), len(b))
    bits = sum(_popcount(a[i] ^ b[i]) for i in range(n)) / (64.0 * n)
    return round(bits, 4)


# ------------------------------------------------------------------ cache disque
# Calculer une empreinte prend 5-13 s (ffmpeg) : on ne le fait qu'une fois par fichier,
# en se fiant à sa taille + date de modification. Sans ça, le garde-fou coûterait
# 3 minutes à chaque publication.
CACHE_FILE = Path(__file__).resolve().parent.parent / "videos" / "fingerprints.json"


def _cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            return {}
    return {}


def _stamp(path: Path) -> str:
    st = path.stat()
    return f"{st.st_size}-{int(st.st_mtime)}"


def cached_hash(path) -> list[int]:
    """Empreinte d'une vidéo, mise en cache sur la base de taille+mtime."""
    path = Path(path)
    key = path.name
    if not path.exists():
        return []
    data = _cache()
    entry = data.get(key)
    if entry and entry.get("stamp") == _stamp(path):
        return entry.get("hash", [])
    h = video_hash(path)
    data[key] = {"stamp": _stamp(path), "hash": h}
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError:
        pass
    return h
