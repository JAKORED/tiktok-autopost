# KAGGLE — pipeline de génération vidéo IA (Wan 2.2) sur GPU gratuit

> **Statut de validation (19/09/2026) — à lire d'abord.** Le notebook est écrit, cohérent et testé **localement** pour tout ce qui ne demande pas de GPU
> (voir tableau ci-dessous). La **génération GPU n'a jamais tourné sur Kaggle** : aucun accès GPU depuis le poste de développement. Tous les temps ci-dessous
> sont des **estimations de calcul**, pas des mesures ; le premier lancement les mesure et les écrit dans `measurements.json`.

| Élément | Testé | Comment |
|---|---|---|
| `cloud/validate_video.py` | **Oui** (réel) | fichier valide (proto_001), plan IA Wan réel, fichier tronqué, fichier absent ; 1 bug trouvé et corrigé |
| Montage `render_episodes.py` + `compose_cloud.py` | **Oui** (réel) | 6 vrais clips IA en plans de substitution → vidéo 1080×1920, 23,1 s, −15,4 dB ; 2 bugs trouvés et corrigés (récursion de police, étirement 480×832) |
| `restore_previous.py` | **Oui** (réel) | plan valide repris, plan corrompu refusé, plan rejeté ignoré |
| `cloud/ingest_incoming.py` | **Oui** (réel) | zip → validation → `ready/` + `metadata/` + import des plans |
| `generate_shots.py --check` | **Oui** | liste les 7 plans de l'épisode 1 (durées, images) sans générer |
| Notebook (syntaxe des 8 cellules, paquet embarqué) | **Oui** | `ast.parse`, intégrité du zip, tous les .py compilent |
| **Génération GPU (SDXL, Wan 2.2 5B, probe, A/B)** | **NON** | à valider au premier passage Kaggle — voir « Ce qui peut échouer » |

## Pourquoi Kaggle
- Seule piste **sans carte bancaire** avec une vraie capacité GPU (≈ 30 h/semaine annoncées, source secondaire) et une automatisation possible sans que
  je manipule tes identifiants : tu cliques « Save & Run All », je traite le résultat. Modal exige une carte (EXP-005) ; ZeroGPU = 120 s/jour (EXP-009) ;
  Colab gratuit interdit de contourner l'interface (FAQ officielle).
- **Action humaine unique** : compte Kaggle + vérification téléphone (Internet dans les notebooks). Aucun mot de passe/token à me donner.

## Configuration GPU (faits vérifiés par l'agent infra, sources dans AGENTS.md)
- Kaggle propose désormais **2×T4 (16 Go chacun)** ; le **P100 a été retiré le 15/09/2026**. 4 CPU, 29 Go de RAM, session 12 h max, sortie 20 Go,
  **500 fichiers de sortie maximum**, ≈ 60 Go de scratch (`/kaggle/temp`).
- **T4 = pas de bf16 matériel.** Le notebook teste **fp16 puis bf16** (17 images, 8 steps) et garde le premier dtype valide (ni NaN, ni image noire).
- `enable_model_cpu_offload` n'utilise **qu'un GPU** ; un seul processus est lancé (deux processus chargeraient 2 × ~20 Go en RAM > 29 Go).

## Modèle
- **Vidéo** : `Wan-AI/Wan2.2-TI2V-5B-Diffusers` (Apache 2.0), 34,2 Go à télécharger (transformer ≈ 20 Go stocké en fp32, text-encoder UMT5 ≈ 11,4 Go, VAE 2,8 Go).
  Officiellement « ≥ 24 Go de VRAM » ; pic connu de 26 Go au décodage VAE à 1280×704×121 images (issue diffusers #12097) → **risque OOM sur T4 16 Go**,
  d'où un repli automatique (tiling VAE puis −25 % d'images) et une résolution de production réduite (480×832).
- **Image de départ** : `stabilityai/stable-diffusion-xl-base-1.0` (fp16, licence OpenRAIL++, usage commercial permis).
- **Pourquoi pas le 14B du test EXP-010** : il ne tient pas sur T4 16 Go ; le 5B est le seul Wan 2.2 plausible. **La qualité du 5B n'est pas connue** :
  c'est une des inconnues que le premier passage (épisode 1 + A/B) tranche.

## Paramètres (`cloud/kaggle/config.json`)
| Paramètre | Valeur | Origine |
|---|---|---|
| Résolution production | 480×832 (multiples de 32) | coût ; identique au test réussi EXP-010 (résolution) |
| fps | 24 (natif du 5B) ; le test EXP-010 (14B) était à 16 | le 5B est natif 24 fps |
| Images par plan | 4k+1, calé sur la narration (57 à 121) | `plans/cloud_00N.json` |
| Steps | `auto` (20–40) : mesuré à 2 puis 4 steps à la taille réelle, ajusté au budget de temps | évite de deviner sans mesure |
| Guidance | 5,0 | valeur officielle |
| Mode | `i2v` (image de départ SDXL) ; repli automatique `t2v` | cohérence des personnages (EXP-008/010) |
| VAE tiling | **désactivé** | bug documenté sur le 5B (issue #12529) ; utilisé seulement en repli OOM |
| Budget | 8 h (arrêt propre) | session max 12 h |
| Personnages | `character_bible` : description fixe injectée dans chaque prompt qui cite l'animal + image de référence par personnage | cohérence par le texte + contrôle visuel |

**Règle expérimentale** : jamais plusieurs variables à la fois. Le probe ne fait varier que la résolution ; le test A/B ne fait varier que l'image de départ
(`i2v_keyframe` vs `t2v_texte_seul`, même prompt, même seed, mêmes steps) ; les deux mp4 sortent dans `generated/_ab_test/` pour comparaison visuelle.

## Installation / lancement (actions humaines, dans l'ordre)
1. Compte Kaggle + vérification téléphone (une fois).
2. Kaggle → **Create → New Notebook → File → Import Notebook** → `cloud/kaggle_video_pipeline.ipynb`.
3. **Settings** : Accelerator **GPU T4 x2** ; **Internet On**.
4. Cellule « Paramètres » : `PHASE = "episode1"` (premier passage).
5. **Save Version → Save & Run All (Commit)**. Fermer l'onglet.
6. Quand c'est terminé : onglet **Output → Download All** → déposer dans `videos/incoming/` → `python cloud/ingest_incoming.py`.
(Régénérer le notebook après modification du code : `python cloud/kaggle/build_notebook.py`.)

## Entrées
Plans de narration `cloud/kaggle/plans/cloud_00N.json` (durée de chaque plan = durée de la phrase, calculée avec la vraie voix), prompts de `video_pipeline/cloud_episodes.py`,
`config.json`. Modèles publics Hugging Face (aucun token).

## Sorties (dans `/kaggle/working`, < 500 fichiers)
```
videos/generated/<id>/keyframes/kf_XX.png        images de départ
videos/generated/<id>/shots/shot_XX.mp4          plans validés (nom déterministe)
videos/generated/_bible/<personnage>.png         images de référence
videos/generated/_ab_test/{i2v_keyframe,t2v_texte_seul}.mp4
videos/generated/measurements.json               temps/plan, VRAM, RAM, résolution, fps, steps, dtype
videos/generated/{run_report,render_report}.json
videos/ready/<id>.mp4 + <id>_review.png          épisode monté + planche d'inspection (si le montage a fonctionné sur Kaggle)
videos/metadata/<id>.json ; SUMMARY.md
```
Les fichiers intermédiaires du montage (voix, plans recalés…) restent hors sortie (`/kaggle/temp`).

## Temps estimé (ESTIMATION de calcul, non mesurée)
- Téléchargements : ≈ 34 Go + 7 Go : 15–40 min.  Images de départ (SDXL, 768×1344, 24 steps) : ≈ 0,5 min/image sur T4 → ≈ 15 min pour l'épisode 1.
- 5B à 480×832 : ≈ 390 tokens vidéo par image latente (32×32 px par token), ≈ 10 000 tokens pour un plan de 97 images ; à ~8–10 TFLOPs effectifs sur T4, avec CFG et 30 steps : **≈ 10–20 min par plan** (calcul, non mesuré) → **épisode 1 (7 plans) ≈ 1,5–2,5 h** ; 31 plans ≈ 6–10 h (2 sessions).
- **Le premier passage mesure ces chiffres** ; `steps: auto` les ajuste au budget. Si un plan dépasse 25 min, réduire résolution/steps (une variable à la fois) et consigner.

## Ce qui peut échouer (et ce que le code fait)
| Risque | Comportement |
|---|---|
| OOM au décodage VAE | repli 1 : tiling VAE (bug possible sur le 5B) ; repli 2 : −25 % d'images ; sinon le plan est marqué échec et le suivant continue |
| fp16 → NaN / image noire | le probe le détecte (`frames_ok`) et bascule en bf16 (plus lent sur T4, émulé) |
| Classe I2V incompatible avec le 5B | bascule automatique `t2v` (journalisé) |
| SDXL / keyframes en échec | bascule `t2v` |
| Plan noir / figé / corrompu | `validate_video` le rejette, jusqu'à 2 relances avec une autre seed, puis `*.rejected.mp4` |
| Session coupée / budget atteint | arrêt propre ; reprise (ci-dessous) |
| apt/cairo indisponible | montage ignoré avec message ; montage local possible |

## Reprise après interruption
Nom de fichier déterministe (`shot_XX.mp4`). Le notebook fait **SKIP** de tout plan déjà valide. Pour reprendre après une session coupée : nouveau notebook → **Add Data → Notebook Output**
→ l'exécution précédente ; la cellule 4 (`restore_previous.py`) recopie les plans/images valides ; la génération ne refait que le manquant. Un épisode terminé n'est jamais refait.

## Procédure d'import dans le projet
```
Kaggle Output ─download→ videos/incoming/ ─python cloud/ingest_incoming.py→ validation (final 1080×1920 + audio, plans) → videos/ready/ + metadata/
                                                                          └→ planche d'inspection : videos/incoming/_review/<id>.png  (à REGARDER)
puis :  python video_pipeline/publish_queue.py sync   →   publication seulement sur ordre explicite : publish_studio.py <id> --confirm
```
Si seuls les plans sont revenus : `python video_pipeline/compose_cloud.py <id> prepare && … render` en local (montage CPU).

## Plan de contrôle qualité (avant de lancer les épisodes 2–5)
1. `PHASE="episode1"` → télécharger → `ingest_incoming.py` → **regarder** planche + fichier : mains/membres, visages, vêtements, couleurs, flicker, rythme, hook, chute.
2. Comparer `_ab_test/i2v_keyframe.mp4` et `t2v_texte_seul.mp4` (variable unique) et les images `_bible/` → consigner dans `EXPERIMENTS.md`.
3. Comparer aux alternatives (vectoriel `proto_001`, Wan 14B EXP-010) et **décider** ; corriger `config.json` (une variable) ; régénérer uniquement les plans défectueux.
4. Seulement alors `PHASE="rest"`.
