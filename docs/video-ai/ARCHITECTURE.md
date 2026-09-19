# ARCHITECTURE — pipeline de production vidéo

Objectif : 5 vidéos TikTok 9:16 de 24–30 s (série « FactVibes Toons »), sans GPU local ni carte bancaire.
Le pipeline est **modulaire** : chaque étape écrit un fichier ; on peut changer de moteur sans tout reconstruire.

```
RECHERCHE VIRALE → CONCEPT → SCRIPT → CHARACTER DESIGN → KEYFRAME → IMAGE-TO-VIDEO → VOICE
→ SOUND DESIGN → MONTAGE → SUBTITLES → QUALITY CONTROL → EXPORT → TIKTOK AUTOPOST
```

| # | Étape | Outil / script | Entrée | Sortie | Dépendances | Secours |
|---|---|---|---|---|---|---|
| 1 | Recherche virale | WebSearch/WebFetch (agents) ; `videos/research/*.md` | sujet, plateformes | règles de production (README) | accès web | relecture des rapports existants |
| 2 | Concept + script | `video_pipeline/cloud_episodes.py` (6–7 plans/épisode, 1 phrase = 1 plan) | règles §1 | `EPISODES` (texte, prompt de plan, chute `punch`) | — | `toon_scripts.py` (dialogues vectoriels) |
| 3 | Character design | `video_pipeline/toon_engine.py` (5 personnages vectoriels) | descriptions | personnages **identiques** à chaque image | pycairo | image de référence IA (AI Horde) |
| 4 | Keyframe / décor | `cloud/horde_image.py` (SDXL, sans compte) ou rendu `toon_engine` | prompt de décor | PNG 704×1216 sans filigrane | réseau, ~2–5 min/image | décors vectoriels de `toon_engine.draw_set` |
| 5 | Image→vidéo | **`cloud/kaggle/generate_shots.py`** (notebook Kaggle ; Wan 2.2 **5B** en i2v, SDXL pour les images de départ, repli t2v) ; `cloud/hf_shots.py` (Space HF, quota) en secours | keyframe + prompt de mouvement | `videos/generated/<id>/shots/shot_XX.mp4` | quota ZeroGPU (120 s/jour anonyme) ; `HF_TOKEN` facultatif | Comfy Cloud / Kaggle / Colab (voir NEXT_STEPS) ; animation vectorielle |
| 6 | Voix | `video_pipeline/compose_cloud.py prepare` (edge-tts fr-FR, timings mot à mot) | beats | `line_XX.mp3`, `shots_plan.json` | `edge-tts` | autre voix Neural fr-FR |
| 7 | Sound design | `make_toon.py` (`make_music`, `bwomp`, `pop`, ducking) | timeline | `mix.wav` (musique synthétisée, sans droits) | numpy | — |
| 8 | Montage | `compose_cloud.py render` (calage des plans à la durée des phrases, 1080×1920, concat) | shots + timeline | `base.mp4` | ffmpeg | plans en Ken Burns si un plan manque |
| 9 | Sous-titres / titre | `toon_engine.draw_caption` / `draw_headline` (mot actif surligné, titre 0–3,4 s) | timings mot à mot | frames incrustées | pycairo | — |
| 10 | Quality control | inspection **manuelle des images extraites** du fichier final (montage ffmpeg+PIL) + `ffprobe` + `volumedetect` | mp4 final | verdict, liste de plans à régénérer | — | régénérer uniquement le plan défectueux |
| 11 | Export | `compose_cloud.render` (H.264+AAC, loudnorm −15 LUFS, faststart) | — | `videos/ready/<id>.mp4` + `videos/metadata/<id>.json` | ffmpeg | — |
| 12 | Publication | `video_pipeline/publish_studio.py <id> --confirm` (Chrome connecté par QR) | `metadata/<id>.json` | preuve dans « Contenu » TikTok Studio, `videos/queue.json` = PUBLISHED | Chrome + `tiktok_login_qr.py` (1 fois) | `publish_queue.py publish` (API, 403 actuel) |

## Règles de conception
1. **Peu de plans GPU, beaucoup de montage** : 6–8 plans de ~4 s ; recadrage ~140 % maximum en 480p ; ralenti 0,75× ; sous-titres,
   coupes rythmées et sound design portent la richesse (source : agent workflow, raisonnement NON VÉRIFIÉ).
2. **Cohérence** : personnage = une seule image de référence réutilisée (vectoriel ou IA) ; ne jamais régénérer un personnage par plan.
3. **PUBLISHED = preuve** : jamais marqué sans que la vidéo apparaisse dans TikTok Studio.
4. **Fallback moteur** : A = HF Wan 2.2 → B = HF LTX → C = Comfy Cloud/Kaggle/Colab (action humaine) → D = animation vectorielle locale.
5. **Aucun secret dans Git** : variables listées dans `.env.example`.

## Modèles et réglages retenus (mesurés)
- Wan 2.2 14B I2V (Space `zerogpu-aoti/wan2-2-fp8da-aoti-faster`) : `steps=6`, `duration_seconds≤5`, 480×832, 16 fps.
- Upscale prévu : lanczos + netteté légère sur CPU (`compose_cloud.render`) ; Real-ESRGAN/RIFE = option sur T4 (NON TESTÉ).

## Chemin Kaggle → projet (détail : KAGGLE.md)
```
notebook autonome ─Kaggle T4x2─ generate_shots.py (GPU : probe, SDXL keyframes, A/B, Wan 5B, contrôle par plan)
      └─ render_episodes.py (CPU : voix, sous-titres, musique, 1080×1920) ─→ Output (≤ 500 fichiers)
Output ─download→ videos/incoming/ ─ingest_incoming.py→ validate_video.py (final + plans) → videos/ready/ + metadata/
      └─ planche d'inspection (0,20,…,100 %) à REGARDER → publish_queue.py sync → publish_studio.py <id> --confirm
```
Reprise : noms de plans déterministes `shot_XX.mp4` ; SKIP si valide ; `restore_previous.py` recopie la sortie d'une exécution précédente.
Contrôle : `cloud/validate_video.py` (technique + intégrité + noir/figé + planche) ne remplace pas l'inspection visuelle.
