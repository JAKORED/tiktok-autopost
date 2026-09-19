#!/usr/bin/env python3
"""Construit cloud/kaggle_video_pipeline.ipynb : un notebook Kaggle AUTONOME (aucun git clone, aucun dataset à envoyer).

Le code du projet est embarqué (zip en base64) dans une cellule ; le notebook l'extrait sous /kaggle/working/project.
À relancer après toute modification des scripts listés dans FILES :
    python cloud/kaggle/build_notebook.py
Sortie : cloud/kaggle_video_pipeline.ipynb (à importer dans Kaggle : File > Import Notebook).
"""
import base64
import io
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FILES = [
    "video_pipeline/cloud_episodes.py", "video_pipeline/compose_cloud.py", "video_pipeline/make_toon.py",
    "video_pipeline/toon_engine.py", "video_pipeline/toon_scripts.py",
    "cloud/validate_video.py",
    "cloud/kaggle/config.json", "cloud/kaggle/requirements.txt", "cloud/kaggle/setup.sh",
    "cloud/kaggle/generate_shots.py", "cloud/kaggle/render_episodes.py", "cloud/kaggle/restore_previous.py",
] + [f"cloud/kaggle/plans/cloud_00{i}.json" for i in range(1, 6)]


def bundle_b64():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            z.write(ROOT / rel, rel)
    raw = base64.b64encode(buf.getvalue()).decode()
    return "\n".join(raw[i:i + 100] for i in range(0, len(raw), 100)), len(buf.getvalue())


def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip("\n").splitlines(True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": text.strip("\n").splitlines(True)}


def build():
    b64, size = bundle_b64()
    cells = [
        md("""
# FactVibes Toons — génération vidéo IA (Wan 2.2) sur Kaggle

**Ce notebook est autonome** : il installe tout, vérifie le GPU, génère les plans vidéo, monte les épisodes, contrôle les fichiers.
Mémoire complète du projet : `docs/video-ai/KAGGLE.md` (dans le dépôt Git).

## À faire, dans l'ordre (actions humaines)
1. **Settings (à droite) → Accelerator : `GPU T4 x2`** et **Internet : On** (Kaggle demande une vérification par téléphone, une seule fois).
2. Cellule « Paramètres » ci-dessous : laisser `PHASE = "episode1"` pour le **premier passage** (1 seul épisode, contrôle qualité), puis
   plus tard `PHASE = "rest"` pour les épisodes 2 à 5.
3. **Save Version → Save & Run All (Commit)**, puis fermer l'onglet. Durée : voir les mesures affichées (`measurements.json`).
4. Récupérer le résultat : onglet **Output → Download All**, déposer dans `videos/incoming/` du projet, lancer `python cloud/ingest_incoming.py`.

## Reprise après interruption
Ajouter la **sortie de l'exécution précédente** (Add Data → Notebook Output → ce notebook) : les plans valides déjà générés sont repris,
rien n'est regénéré. Aucune identité, aucun token n'est nécessaire (modèles publics de Hugging Face).
"""),
        code('''
# ===== PARAMÈTRES (seule cellule à modifier) =====
PHASE = "episode1"          # "episode1" (premier passage), puis "rest" (épisodes 2-5), ou "all"
TIME_BUDGET_HOURS = 8.0     # arrêt propre avant la limite de session Kaggle (12 h max) ; la reprise est ensuite possible

import os
os.environ.update(PHASE=PHASE, TIME_BUDGET_HOURS=str(TIME_BUDGET_HOURS), VIDEO_ROOT="/kaggle/working/videos")
os.environ["HF_HOME"] = "/kaggle/temp/hf" if os.path.isdir("/kaggle/temp") else "/tmp/hf"   # 34 Go de modèles : hors de la sortie
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
print("PHASE =", PHASE, "| budget =", TIME_BUDGET_HOURS, "h | HF_HOME =", os.environ["HF_HOME"])
'''),
        code('''
# ===== 1. Vérification de l'environnement : GPU, CUDA, RAM, disque, Internet =====
!nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
!df -h /kaggle/working /kaggle/temp /tmp 2>/dev/null
!free -g | head -2
!curl -s -o /dev/null -w "Internet (huggingface.co) : HTTP %{http_code}\\n" --max-time 15 https://huggingface.co || echo "PAS D'INTERNET : activer Internet dans Settings"
import torch
print("torch", torch.__version__, "| CUDA :", torch.cuda.is_available(), "| GPU(s) :", torch.cuda.device_count())
assert torch.cuda.is_available(), "Aucun GPU : Settings > Accelerator > GPU T4 x2, puis relancer."
'''),
        code(f'''
# ===== 2. Fichiers du projet (embarqués dans ce notebook, {size // 1024} Ko) — NE PAS MODIFIER =====
import base64, io, zipfile
BUNDLE_B64 = """
{b64}
"""
zipfile.ZipFile(io.BytesIO(base64.b64decode("".join(BUNDLE_B64.split())))).extractall("/kaggle/working/project")
print("projet extrait dans /kaggle/working/project")
'''),
        code('''
# ===== 3. Installation des dépendances (CPU : téléchargements, pip, apt) =====
!bash /kaggle/working/project/cloud/kaggle/setup.sh
'''),
        code('''
# ===== 4. Reprise : reprend les plans valides d'une exécution précédente rattachée en entrée (sinon ne fait rien) =====
!python /kaggle/working/project/cloud/kaggle/restore_previous.py
'''),
        code('''
# ===== 5. GÉNÉRATION GPU : mesures -> images de départ -> test A/B -> plans (avec reprise et contrôle qualité) =====
# Les mesures (temps, VRAM, RAM, résolution, fps, steps) sont écrites dans /kaggle/working/videos/generated/measurements.json
!python -u /kaggle/working/project/cloud/kaggle/generate_shots.py --phase {PHASE}
'''),
        code('''
# ===== 6. MONTAGE (CPU) : narration + sous-titres animés + musique -> vidéos 1080x1920 =====
# Meilleur effort : si le montage est impossible ici, il se refait en local à partir des plans (voir KAGGLE.md).
!python -u /kaggle/working/project/cloud/kaggle/render_episodes.py --phase {PHASE}
'''),
        code('''
# ===== 7. CONTRÔLE et bilan : validation technique de chaque fichier + résumé lisible =====
import json, pathlib, subprocess, sys
sys.path.insert(0, "/kaggle/working/project/cloud")
import validate_video as V
root = pathlib.Path("/kaggle/working/videos")
lines = [f"# Bilan — PHASE {PHASE}", ""]
for kind, pattern in (("shot", "generated/*/shots/shot_*.mp4"), ("final", "ready/cloud_*.mp4")):
    for f in sorted(root.glob(pattern)):
        r = V.validate(f, kind)
        i = r["info"]
        lines.append(f"- {'OK ' if r['ok'] else 'KO '} {f.relative_to(root)} — {i.get('width')}x{i.get('height')} {i.get('fps')}fps {i.get('duration')}s"
                     + (f" | problèmes : {r['problems']}" if r["problems"] else ""))
m = root / "generated" / "measurements.json"
if m.exists():
    lines += ["", "## Mesures (extrait)"] + [f"- {json.dumps(x, ensure_ascii=False)}" for x in json.loads(m.read_text(encoding="utf-8"))[-25:]]
pathlib.Path("/kaggle/working/SUMMARY.md").write_text("\\n".join(lines), encoding="utf-8")
print("\\n".join(lines))
print("\\nFichiers de sortie :", sum(1 for _ in pathlib.Path("/kaggle/working").rglob("*") if _.is_file()), "(limite Kaggle : 500)")
'''),
    ]
    nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                       "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 4}
    out = ROOT / "cloud" / "kaggle_video_pipeline.ipynb"
    out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"notebook écrit : {out} ({out.stat().st_size // 1024} Ko, projet embarqué {size // 1024} Ko)")


if __name__ == "__main__":
    build()
