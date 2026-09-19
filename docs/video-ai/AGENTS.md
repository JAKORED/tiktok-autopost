# AGENTS — rôles, lectures, sorties

## Protocole obligatoire pour tout agent (humain ou IA)
1. **LIRE avant d'agir** : `README.md`, `STATE.md`, `EXPERIMENTS.md`, `SOLUTIONS.md`, `ARCHITECTURE.md`, `NEXT_STEPS.md` (ce dossier).
2. **Ne pas refaire** un test déjà consigné sans raison écrite (nouvelle version, nouvelle condition).
3. **ÉCRIRE après** : code + résultat + documentation. Une tâche n'est finie que si `EXPERIMENTS.md`, `SOLUTIONS.md`, `STATE.md`
   et `NEXT_STEPS.md` sont à jour, puis commit clair (`docs(video): …`, `feat(video): …`). Jamais de secret dans un commit.
4. **Honnêteté** : distinguer VÉRIFIÉ (source lue / test réalisé) et NON VÉRIFIÉ. Ne jamais annoncer un fichier sans l'avoir contrôlé (`ffprobe` + image extraite).

## Agents utilisés (session du 19/09/2026)
Les agents étaient des sous-agents de recherche à lecture web (WebSearch/WebFetch) ; leurs rapports ont été **recoupés** par des tests
directs quand c'était possible (statut des Spaces, quotas, Comfy Cloud). Leurs sorties brutes ne sont pas versionnées :
les faits retenus sont dans `EXPERIMENTS.md` / `SOLUTIONS.md`.

### AGENT VIRAL / DIRECTEUR CRÉATIF / SOCIAL
- **Mission** : mécanismes communs des contenus à très forte audience → règles de production + accroches, boucles, hashtags.
- **Sorties** : `videos/research/trends_2026.md`, `videos/research/cartoon_trends.md`, règles ci-dessous, `cloud_episodes.py`.
- **Constats vérifiés** : Ballerina Cappuccina (19,5 M de vues en 3 semaines) et Tung Tung Sahur (42,5 M) — source Know Your Meme / Daily Dot ;
  franceinfo 17/06/2026 (chaînes de vidéos IA d'animaux, une vidéo à 232 M de vues, « un gagnant pour 10 000 »).
- **NON VÉRIFIÉ** : chiffres de rétention (estimations d'éditeurs d'outils), audiences de « Hasan Ai 202 » (blog tiers), micro-drames de chats (CGTN, sans source primaire).
- **Règles retenues (10)** : sujet+promesse dans la 1re phrase (≤ 12 mots) ; image 1 = personnage en plein cadre ; plan de 3 s en moyenne (5 s max) ;
  total 28–34 s, chute entre 24 et 30 s ; structure hook → escalade en 3 beats → retournement → chute ; dernière phrase qui reboucle sur la 1re ;
  sous-titres mot à mot, gros, mot-clé en couleur ; titre d'écran 3 lignes visible 0–2,5 s ; un son par gag + silence de 0,3 s avant la chute ;
  personnages et lieux constants (série). **Risque cité** : « chasse au slop » sur les contenus IA produits en masse.

### AGENT CLOUD GPU (2 passes)
- **Mission** : services GPU/crédits gratuits, conditions ACTUELLES (carte, téléphone, quota, automatisation).
- **Sorties (faits)** : voir `SOLUTIONS.md`. Aucun service testé n'offre de GPU automatisable **sans compte** ; toutes les pistes viables demandent
  une action humaine (compte, SMS ou session manuelle).
- **Lectures obligatoires** : `SOLUTIONS.md`, `EXPERIMENTS.md` (EXP-005, EXP-009, EXP-012).

### AGENT VIDEO AI (modèles)
- **Mission** : comparer Wan 2.x, LTX-2.x, MiniMax H3, HunyuanVideo 1.5, CogVideoX, Mochi, InfiniteTalk, Wan2GP.
- **Constats vérifiés (sources HF/GitHub)** : Wan 2.2 (Apache 2.0) est le dernier Wan open weights ; Wan 2.5+ = API seulement. Wan2GP est une interface
  multi-modèles (6–9 Go de VRAM annoncés). LTX-2.x = audio+vidéo natifs, licence communautaire. MiniMax H3 : licence avec restrictions UE/UK/Corée/USA.
- **NON VÉRIFIÉ** : VRAM/temps sur T4, qualité cartoon comparée.

### AGENT HUGGINGFACE + COLAB/KAGGLE
- **Mission** : Spaces réellement fonctionnels, quotas, notebooks. **Vérifié par test direct** : `Lightricks/ltx-video-distilled` et
  `zerogpu-aoti/wan2-2-fp8da-aoti-faster` répondent à un script sans compte (EXP-007/010).
- **Constats** : quotas ZeroGPU (doc officielle) anonyme 2 min/jour, compte gratuit 5 min/jour. Colab gratuit : automatisation « hors interface » interdite.
  Kaggle : `kaggle kernels push` + SMS. Notebooks existants : `Square-Zero-Labs/Wan2GP-on-Colab` (push 31/08/2026), `…-on-Kaggle` (24/05/2026) — interface Gradio.

### AGENT STOCKAGE / AUTOMATISATION / PAROLE
- **Mission** : stockage gratuit, lip-sync open source, schéma d'automatisation.
- **Constats** : Backblaze B2 10 Go sans carte (page d'inscription) ; GitHub Releases < 2 Go/fichier. Lip-sync candidats : InfiniteTalk (Apache 2.0),
  LatentSync, MuseTalk ; **aucun n'est prouvé sur personnages non réalistes**. API TikTok : `video.publish` exige un audit pour publier en public.

### AGENT WORKFLOW / OPTIMISATION / COMFYUI
- **Mission** : réduire le nombre de générations GPU.
- **Recommandation (raisonnement NON VÉRIFIÉ)** : 4 clips Wan 2.2 14B + Lightning par vidéo (~20 au total), 2 plans de montage par clip (large puis
  recadré ~140 %), upscale ×2 puis RIFE ×2, montage en 7 plans. Comfy Cloud apporte des workflows prêts (Lightning, FLF2V, GGUF).

### AGENT KEYFRAMES
- **Mission** : images de départ cohérentes sans quota. **Verdict** : personnages vectoriels (cohérence garantie) + décors IA (AI Horde vérifié en réel) ;
  Cloudflare FLUX-schnell possible mais demande un compte/token ; génération locale CPU = brouillon 512².

### AGENT QUALITY CONTROL (rôle tenu par l'agent principal)
- **Mission** : inspecter le **fichier final** (rythme, hook, cohérence, artefacts, audio, sous-titres, 9:16) et exiger la régénération d'un plan défectueux.
- **Méthode** : `ffprobe` (format/durée), `volumedetect` (niveau), images extraites à intervalles réguliers assemblées en planche (PIL), lecture visuelle.
- **Critères d'élimination** : mains/membres parasites, visage ou vêtement qui change, objet qui apparaît/disparaît, couleurs incohérentes, flicker.
- **Sortie** : verdict écrit dans `EXPERIMENTS.md` (jamais « professionnel » sans inspection du fichier final).
