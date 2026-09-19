# cloud/kaggle — génération vidéo IA sur Kaggle

Documentation complète : **`docs/video-ai/KAGGLE.md`** (à lire d'abord). Ici : le mode d'emploi rapide.

## Utiliser sans comprendre le code
1. Kaggle : compte + vérification téléphone (une fois). *New Notebook → File → Import Notebook* → `cloud/kaggle_video_pipeline.ipynb`.
2. Settings : **GPU T4 x2**, **Internet On**. Cellule « Paramètres » : `PHASE = "episode1"`.
3. **Save Version → Save & Run All**. Fermer l'onglet.
4. Output → **Download All** → déposer dans `videos/incoming/` du projet → `python cloud/ingest_incoming.py`.
5. Regarder `videos/incoming/_review/<id>.png` et le fichier ; corriger si besoin ; **puis** `PHASE = "rest"`.

## Fichiers
| Fichier | Rôle |
|---|---|
| `../kaggle_video_pipeline.ipynb` | notebook autonome (projet embarqué en base64) — généré par `build_notebook.py` |
| `config.json` | réglages (phase, modèle, résolution, steps, dtype, budget, bible des personnages) |
| `setup.sh` | installation (pip, apt/cairo, cache modèles hors sortie) |
| `generate_shots.py` | **GPU** : probe → images de départ SDXL → test A/B → plans Wan 2.2, reprise, replis OOM, contrôle qualité |
| `render_episodes.py` | **CPU** : montage (voix, sous-titres, musique) + contrôle final ; meilleur effort |
| `restore_previous.py` | reprise depuis la sortie d'une exécution précédente |
| `plans/cloud_00N.json` | durées de plans calées sur la narration réelle |
| `build_notebook.py` | régénère le notebook après modification (`python cloud/kaggle/build_notebook.py`) |
| `../validate_video.py`, `../ingest_incoming.py` | contrôle d'un mp4 ; import des résultats vers `videos/ready/` |

## Commandes utiles (poste local)
```
python cloud/kaggle/generate_shots.py --phase episode1 --check     # liste les plans à générer (aucune génération)
python cloud/validate_video.py <fichier.mp4> --kind shot|final --frames
python cloud/ingest_incoming.py
python cloud/kaggle/build_notebook.py
```
Variables : `PHASE`, `TIME_BUDGET_HOURS`, `VIDEO_ROOT`, `HF_HOME` (aucun secret ; `HF_TOKEN` facultatif).
