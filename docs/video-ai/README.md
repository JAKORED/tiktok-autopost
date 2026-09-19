# video-ai — mémoire du projet « machine vidéo TikTok »

**Point d'entrée obligatoire.** Ordre de lecture avant toute intervention : `README.md` → `STATE.md` → `EXPERIMENTS.md` →
`SOLUTIONS.md` → `ARCHITECTURE.md` → `AGENTS.md` → `NEXT_STEPS.md`. Après chaque test ou changement : mettre à jour ces fichiers, puis committer.

## Objectif
Produire **5 vidéos TikTok 9:16 professionnelles** (24–30 s) de la série « FactVibes Toons » (dessins animés narrés : humour/travail, société,
satire d'un royaume fictif, industrie), avec génération IA dans le cloud, **sans GPU local et sans carte bancaire**, puis les publier sur le compte
TikTok `FactVibes`. Contraintes : aucun mock, aucune fausse vidéo ; « professionnel » = jugé sur le **fichier final**, pas sur le fait qu'il existe.
Objectif viral : appliquer les mécanismes observés (hook, rétention, chute, boucle, série), **sans promettre** de millions de vues.

## État actuel (résumé — détail dans STATE.md)
- **Publié et vérifié** : 3 vidéos « psychologie » (video_001..003) via TikTok Studio.
- **Réalisé mais non publié** : 4 dessins animés vectoriels toon_001..004 (jugés trop basiques).
- **Moteur vidéo IA retenu (provisoire)** : Wan 2.2 14B image→vidéo sur Space Hugging Face ZeroGPU — **quota trop faible** pour ~30 plans.
- **Décors IA** : AI Horde (SDXL) validé. **Personnages** : vectoriels (cohérence garantie).
- **Prototype hybride `proto_001`** (décor IA AI Horde + personnages vectoriels + caméra cinématographique) : fichier réel, propre, **pas encore « pro »** (EXP-014). Aucune vidéo `cloud_001..005` avec plans Wan n'existe encore.

## Outils : validés / limités / rejetés (pourquoi → SOLUTIONS.md)
- **Validés** : pipeline CPU (ffmpeg/edge-tts), moteur vectoriel pycairo, TikTok Studio (Selenium), AI Horde pour les décors.
- **Limités** : HF ZeroGPU (120 s/jour anonyme), LTX-Video distillé.
- **Meilleur moteur testé** : Wan 2.2 14B I2V (Space HF).
- **Rejetés** : Modal (carte exigée), Pollinations (filigrane, 584×1009, déformé), API TikTok (403).
- **À tester (action humaine)** : Comfy Cloud gratuit, Kaggle, Colab.

## Quotas, coûts, limites (mesurés sauf « NV »)
- HF ZeroGPU anonyme : **120 s GPU/jour**, requête refusée si le reste < durée réservée (EXP-009). Compte gratuit : 5 min/jour (doc, NV).
- Comfy Cloud : **contradiction** 400 crédits/mois vs « 5 free runs » ; ~11 crédits par clip Wan 2.2 I2V de 5 s (EXP-012). API gratuite non confirmée.
- AI Horde : gratuit, ~2–5 min par image (priorité basse).
- Coût réel dépensé à ce jour : **0 €**.

## Fichiers importants
| Chemin | Rôle |
|---|---|
| `video_pipeline/generate.py` | vidéos « psychologie » CPU (EXP-001) |
| `video_pipeline/toon_engine.py`, `toon_scripts.py`, `make_toon.py` | dessins animés vectoriels + voix + sous-titres + musique ; épisode `proto_001` = mode `cinematic` avec `bg_image` (décor IA) |
| `video_pipeline/cloud_episodes.py` | **5 épisodes originaux** (beats = 1 phrase/plan, prompts de plan, chutes) |
| `video_pipeline/compose_cloud.py` | narration, plan de génération, montage final avec plans IA |
| `cloud/hf_shots.py` | génération de plans sur Space HF (T2V LTX ; **le pilote Wan I2V reste à écrire**) |
| `cloud/horde_image.py` | images/décors SDXL via AI Horde (clé anonyme publique) |
| `cloud/modal_video.py`, `cloud/modal_gpu_probe.py` | **historique** — Modal rejeté, conservés comme preuve du test |
| `video_pipeline/publish_studio.py`, `tiktok_login_qr.py`, `publish_queue.py` | publication + file d'attente |
| `videos/research/` | recherches de tendances |
| `videos/metadata/*.json`, `videos/queue.json` | métadonnées et état de la file (versionnés) ; les binaires sont ignorés par Git |

## Référence des scripts (rôle · commande · entrée → sortie · env · secours)
- **`cloud/hf_shots.py`** — plans via Hugging Face. `python cloud/hf_shots.py <episode> [--only 0,3] [--seed 7] [--space <id>]`.
  Entrée : `videos/generated/<id>/shots_plan.json`. Sortie : `…/shots/shot_XX.mp4`. Env : `HF_TOKEN` (facultatif, quota 5 min/jour).
  Reprise automatique ; s'arrête proprement si quota épuisé. **Limite** : appelle `/text_to_video` de LTX ; Wan I2V à ajouter.
- **`cloud/horde_image.py`** — `python cloud/horde_image.py "<prompt>" sortie.png [--w 704 --h 1216 --seed 5 --model "AlbedoBase XL (SDXL)"]`.
  Aucun secret (clé anonyme publique). User-Agent explicite obligatoire (sinon Cloudflare 1010) ; ne rien contourner.
- **`video_pipeline/compose_cloud.py`** — `python video_pipeline/compose_cloud.py <id> prepare` (voix + plan) puis `… render` (montage).
  Entrée : `cloud_episodes.py` + `shots/`. Sortie : `videos/ready/<id>.mp4` + `metadata/<id>.json`. **`render` n'a jamais tourné sur de vrais plans : NON VALIDÉ.**
- **`video_pipeline/make_toon.py`** — `python video_pipeline/make_toon.py toon_001 [--png 4.0 | --seconds 6]`. Sortie : `videos/ready/toon_00N.mp4`.
- **`video_pipeline/publish_studio.py`** — `python video_pipeline/publish_studio.py <id> --confirm`. Prérequis : `tiktok_login_qr.py` exécuté une fois
  (scan du QR par l'utilisateur). Effet : **publie réellement** sur TikTok. Correctif de légende non validé en réel.
- **`video_pipeline/publish_queue.py`** — `status | sync | schedule <id> <ISO> | publish <id> --confirm | verify` (voie API, 403 actuel).
- Variables : voir `.env.example` (`HF_TOKEN`, `COMFY_API_KEY`, `TIKTOK_*`). **Ne jamais committer de valeurs.**

## Prochaines étapes → NEXT_STEPS.md
Action humaine à choisir (une seule suffit) : créer le compte gratuit **Comfy Cloud**, ou faire la vérification SMS **Kaggle**, ou fournir un `HF_TOKEN`
gratuit. En attendant : construire le prototype hybride de l'épisode 1 (décors AI Horde + personnages vectoriels + montage) et écrire le pilote Wan I2V.
