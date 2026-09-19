#!/usr/bin/env bash
# Installation des dépendances dans le notebook Kaggle (Internet activé requis).
# Chaque étape est « best effort » : un échec du montage (cairo) ne doit pas empêcher la génération GPU.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
echo "== setup.sh — $(date -u +%FT%TZ)"

# Cache des modèles hors de /kaggle/working (limité et repris dans la sortie du notebook)
# /kaggle/temp (~60 Go) si présent : le poids des modèles (34 Go) ne doit PAS aller dans /kaggle/working (20 Go, repris en sortie)
SCRATCH=/tmp; [ -d /kaggle/temp ] && SCRATCH=/kaggle/temp
export HF_HOME="${HF_HOME:-$SCRATCH/hf}"
export HF_HUB_ENABLE_HF_TRANSFER=1
mkdir -p "$HF_HOME"
echo "HF_HOME=$HF_HOME  |  disque libre : $(df -h "$SCRATCH" | tail -1 | awk '{print $4}')"

echo "== 1/3 paquets Python (GPU + montage)"
python -m pip install -q -r "$HERE/requirements.txt" 2>&1 | tail -3 || echo "AVERTISSEMENT : pip a signalé une erreur (voir ci-dessus)"

echo "== 2/3 bibliothèques système pour le dessin vectoriel (cairo) — montage uniquement"
( apt-get update -qq && apt-get install -y -qq libcairo2-dev pkg-config fonts-dejavu-core ffmpeg ) >/tmp/apt.log 2>&1 \
  && echo "apt OK" || echo "AVERTISSEMENT : apt indisponible — le montage sur Kaggle sera ignoré (à faire en local)"
python -m pip install -q pycairo 2>&1 | tail -1 || true

echo "== 3/3 vérifications"
python - <<'PY'
import importlib
for m in ("torch", "diffusers", "transformers", "accelerate", "edge_tts", "cairo", "PIL"):
    try:
        mod = importlib.import_module(m)
        print(f"  {m:14s} OK  {getattr(mod, '__version__', '')}")
    except Exception as e:
        print(f"  {m:14s} ABSENT ({type(e).__name__})")
try:
    import torch
    print("  CUDA disponible :", torch.cuda.is_available(), "| GPU(s) :", torch.cuda.device_count())
except Exception:
    pass
PY
which ffmpeg ffprobe || echo "AVERTISSEMENT : ffmpeg/ffprobe introuvables"
echo "== setup terminé"
