#!/usr/bin/env python3
"""Reprise après interruption : recopie les plans / images / vidéos VALIDES d'une exécution précédente.

Principe Kaggle : la sortie d'un notebook (/kaggle/working) d'une exécution précédente est rattachée à la suivante via
« Add Data » > « Notebook Output » ; elle apparaît alors sous /kaggle/input/<nom>/… avec la même arborescence.
Ce script cherche dans /kaggle/input tout chemin `…/generated/<id>/{shots,keyframes}/…` (+ `_bible/`, `ready/`, `metadata/`)
et copie dans VIDEO_ROOT ce qui manque. Les mp4 de plans sont revalidés avant copie (jamais de fichier corrompu repris).
Ensuite generate_shots.py fait SKIP sur les plans déjà valides : rien n'est regénéré.

Usage : python restore_previous.py [--root <VIDEO_ROOT>] [--input /kaggle/input]
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import validate_video as V  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.environ.get("VIDEO_ROOT", "/kaggle/working/videos"))
    ap.add_argument("--input", default="/kaggle/input")
    a = ap.parse_args()
    root, src = Path(a.root), Path(a.input)
    if not src.exists():
        print("restore : pas de /kaggle/input -> rien à reprendre.")
        return 0
    copied = skipped = 0
    for f in src.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in (".mp4", ".png", ".json"):
            continue
        parts = f.parts
        anchor = next((i for i, p in enumerate(parts) if p in ("generated", "ready", "metadata")
                       and i > 0 and parts[i - 1] == "videos"), None)
        if anchor is None:
            continue
        rel = Path(*parts[anchor:])
        dst = root / rel
        name = f.name
        if name.endswith((".rejected.mp4", ".tmp.mp4")) or name in ("measurements.json", "run_report.json", "render_report.json"):
            continue  # rapports et fichiers rejetés : non repris
        if dst.exists():
            skipped += 1
            continue
        if f.suffix.lower() == ".mp4" and "shots" in rel.parts and not V.validate(f, "shot")["ok"]:
            print("restore : plan invalide ignoré", rel)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        copied += 1
    print(f"restore : {copied} fichier(s) repris, {skipped} déjà présent(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
