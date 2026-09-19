# EXPERIMENTS — journal des expériences réelles

> Règle : on n'efface jamais une entrée, même un échec. Une nouvelle expérience = une nouvelle entrée `EXP-0NN`
> en bas du fichier. Chaque valeur ci-dessous a été **mesurée** (fichier, sortie de commande ou capture) sauf mention
> « NON VÉRIFIÉ ». Environnement de départ : Windows 11, Celeron N4120, 3,8 Go RAM, **aucun GPU**.

---

## EXP-001 — Pipeline CPU « faits de psychologie » (Pillow + edge-tts + ffmpeg)
- **Date** : 19/09/2026
- **Objectif** : produire de vraies vidéos 9:16 sans GPU.
- **Solution** : `video_pipeline/generate.py` (3 concepts de `concepts.json`), voix `edge-tts` fr-FR, sous-titres par phrase.
- **Configuration** : 1080×1920, 30 fps, H.264+AAC, un clip par phrase puis concat.
- **Résultat** : 3 fichiers réels — video_001 35,1 s, video_002 44,0 s, video_003 40,8 s. Contrôle `ffprobe` OK.
- **Erreurs corrigées** : `fill=accent` (liste au lieu de tuple), `queue.py` masquait le module standard `queue`
  (renommé `publish_queue.py`), directive `silence` invalide dans le concat ffmpeg, mauvais dossier `published`.
- **Coût / quota** : 0 €. **Décision** : conservé comme base technique ; visuellement trop simple (texte sur fond).

## EXP-002 — Publication TikTok par l'API officielle (Content Posting)
- **Date** : 19/09/2026 — **Objectif** : publier video_001 via `agents/tiktok_publisher.py`.
- **Résultat** : `401 Unauthorized` puis, après rafraîchissement automatique du token, `403 Forbidden` sur `/post/publish/video/init/`.
  `creator_info/query` répond 200 (compte `FactVibes`, niveaux de confidentialité PUBLIC/MUTUAL/SELF_ONLY).
- **Cause du 403** : **inconnue** (la requête de diagnostic a été refusée par le garde-fou du poste, non contournée).
  Hypothèses NON VÉRIFIÉES : scope `video.publish` manquant ou application non auditée.
- **Décision** : ne plus utiliser l'API ; passer par TikTok Studio (EXP-003). **Alternative** : demander l'audit TikTok.

## EXP-003 — Publication via TikTok Studio (Selenium, connexion par QR code)
- **Date** : 19/09/2026 — **Solution** : `tiktok_login_qr.py` (Chrome visible, l'utilisateur scanne le QR, cookies sauvegardés)
  + `publish_studio.py` (Chrome sur le port 9222, profil `config/chrome_tiktok_profile`).
- **Résultat** : video_001, video_002, video_003 **publiées**, vérifiées dans « Contenu » de TikTok Studio.
  Après examen TikTok : « Tout le monde », 49 / 82 / 35 vues au moment du contrôle (19/09, ~1 h après).
- **Particularités** : TikTok affiche une fenêtre « Publier maintenant » après le clic (gérée) ; les fenêtres
  « Activer les vérifications automatiques » (on clique Annuler) et « J'ai compris » sont fermées ; nouvel éditeur Draft.js.
- **Bug** : la description est **écrasée par le nom du fichier** tant que la couverture charge (« Chargement… ») →
  échec sur toon_001..004 (légende non saisie). **Correctif écrit** (`ensure_caption` : attendre la fin du chargement,
  retaper, revérifier avant « Publier ») — **NON VALIDÉ en publication réelle** depuis le correctif.
- **Décision** : voie de publication retenue.

## EXP-004 — Dessins animés vectoriels (pycairo) toon_001..004
- **Date** : 19/09/2026 — **Solution** : `toon_engine.py` + `make_toon.py` + `toon_scripts.py`.
- **Contenu** : 5 personnages originaux (Kevin, Mme Fournier, Ministre, Josette, Robo-Bob), 4 décors, synchro labiale sur
  l'amplitude réelle de la voix, sous-titres mot à mot (timings edge-tts), musique synthétisée, loudnorm −15 dB.
- **Résultat** : 4 fichiers réels 26,7–35,1 s, 1080×1920 (contrôlés). Rendu ~1,3× le temps réel sur ce CPU.
- **Verdict utilisateur** : « trop basique ». **Décision** : NON publiés. Le moteur reste utile comme source de
  **personnages cohérents** (référence pour image→vidéo) et comme repli.

## EXP-005 — Modal (GPU cloud)
- **Date** : 19/09/2026 — **Solution** : `cloud/modal_video.py` (Wan 2.2 TI2V-5B sur L40S), `cloud/modal_gpu_probe.py`.
- **Configuration** : compte créé par l'utilisateur (workspace `phraziashop`), `modal token new` OK, build d'image 70 s.
- **Erreur** : `InvalidError: Please add a payment method to use L40S GPU functions.` — identique pour **T4, L4, A10G**.
- **Coût / quota** : impossible sans carte bancaire.
- **Décision** : **REJETÉ** (contrainte utilisateur : pas de carte). Voir SOLUTIONS.md.

## EXP-006 — Pollinations (images gratuites sans compte)
- **Date** : 19/09/2026 — **Objectif** : keyframes cartoon 9:16.
- **Résultat** : 3 images de test (paon, robot, lion) — **584×1009 px**, filigrane « pollinations.ai » incrusté
  (le paramètre `nologo` est ignoré en anonyme), rendu sombre et déformé (le paon ressemble à un perroquet rouge).
- **Note d'honnêteté** : le téléchargement de test a utilisé un User-Agent de type navigateur ; à ne plus faire (voir EXP-011).
- **Décision** : **REJETÉ** pour les keyframes. **Alternative** : AI Horde (EXP-011), vectoriel (EXP-004).

## EXP-007 — LTX-Video distillé, texte→vidéo (Space HF ZeroGPU, anonyme)
- **Date** : 19/09/2026 — **Solution** : Space `Lightricks/ltx-video-distilled`, `gradio_client`, `/text_to_video`.
- **Configuration** : 704×1216, `duration_ui=3`, seed 7, prompt « paon en costume présentant un graphique ».
- **Résultat** : fichier réel 704×1216, 30 fps, 89 images, 2,97 s, généré en **21 s**. Personnage stable, bec qui bouge.
  Défauts : mouvement faible, style plat 2D (pas 3D malgré le prompt), le graphique et les confettis demandés sont absents.
- **Décision** : utilisable, qualité moyenne. Non retenu comme moteur principal.

## EXP-008 — LTX-Video image→vidéo avec référence vectorielle
- **Date** : 19/09/2026 — **Solution** : `/image_to_video`, image = décor de bureau + Kevin + Mme Fournier rendus par `toon_engine.py`.
- **Résultat** : fichier réel 704×1216, 2,97 s, 19 s. **Cohérence des personnages : bonne** (visages, vêtements, décor conservés,
  expressions animées). **Défauts** : mains et manches orange **inventées** au bord de l'image, couleurs ternies.
- **Décision** : cohérence prouvée, artefacts inacceptables → régénération nécessaire (cadrage plus serré, pas de bord de table).

## EXP-009 — Quota anonyme Hugging Face ZeroGPU
- **Date** : 19/09/2026 — **Mesure** : après EXP-007 et EXP-008 (~63 s de quota consommées), une 3e requête est refusée :
  `You have exceeded your ZeroGPU quota (120s requested vs. 57s left). Try again in 23:56:37.`
- **Conclusion mesurée** : quota anonyme = **120 s de GPU/jour** ; chaque requête en **réserve** une durée (120 s pour ce Space)
  et est refusée si le reste est inférieur. ≈ 4 clips/jour maximum. Un compte gratuit passe à 5 min/jour (doc officielle,
  non testé). **Insuffisant** pour ~30 plans.

## EXP-010 — Wan 2.2 14B image→vidéo (Space `zerogpu-aoti/wan2-2-fp8da-aoti-faster`)
- **Date** : 19/09/2026 — **Configuration** : image = même référence que EXP-008, `steps=6`, `duration_seconds=3`, guidance 1/1.
- **Résultat** : fichier réel **480×832, 16 fps, 49 images, 3,06 s**, ~60 s de temps total. Qualité **nettement meilleure que LTX** :
  aucune main parasite, personnages et couleurs conservés, bouches et bras animés naturellement.
  Limites : 480p / 16 fps (à upscaler), image→vidéo uniquement, 5 s max.
- **Note** : la requête a été acceptée avec ~57 s de quota restant → ce Space réserve moins de GPU par appel que LTX.
- **Décision** : **meilleur moteur vidéo testé**. Frein = quota (cf. EXP-009).

## EXP-011 — AI Horde (images SDXL, clé anonyme publique)
- **Date** : 19/09/2026 — **1re tentative** : `HTTP 403 error code: 1010` (protection Cloudflare sur la signature par défaut
  de `urllib`). **Correction légitime** : User-Agent explicite `factvibes-toons/1.0 (+https://github.com/JAKORED)` (aucun contournement).
- **Résultat** : décor « salle de réunion vide » 704×1216, modèle AlbedoBase XL, **fichier réel, sans filigrane**, illustration
  propre et cohérente. Temps total **276 s** (attente en file, priorité basse anonyme). Défauts mineurs : horloge dupliquée.
- **Décision** : **VALIDÉ pour les décors**. Prévoir 2–5 min par image ; lancer les demandes en parallèle.

## EXP-012 — Comfy Cloud (recherche seulement, pas de test réel)
- **Date** : 19/09/2026 — **Sources lues** : blog `blog.comfy.org/p/free-tier-arrives-in-comfy-cloud`, page `comfy.org/pricing`.
- **Faits** : sans carte bancaire ; GPU RTX PRO 6000 ; Wan disponible ; facturation à la seconde GPU (736,39 crédits/h) ;
  « environ 11 crédits » pour une vidéo Wan 2.2 I2V de 5 s (81 images, 18 fps, 640×640, 4 steps) ≈ 54 s de GPU.
- **CONTRADICTION NON RÉSOLUE** : le blog annonce **400 crédits/mois** (non reportés), la page tarifaire annonce
  **« 5 free runs »**. L'accès API sur l'offre gratuite n'est **pas indiqué** (les limites « concurrent workflows (API) »
  n'apparaissent que pour les offres payantes).
- **Calcul (si 400 crédits réels)** : 400 ÷ 11 ≈ **36 plans/mois**, soit 36 ÷ 6 plans par vidéo = **6 vidéos/mois**.
  Si « 5 runs » : **5 plans**, soit moins d'une vidéo. Offre Standard (payante, 20 $/mois) : 4 200 crédits ≈ 380 plans.
- **Test réel** : **impossible sans compte** (action humaine). **Décision** : « À TESTER APRÈS CRÉATION DE COMPTE ».

## EXP-013 — Recherches d'agents (synthèse, non testées)
Voir `AGENTS.md`. Points clés : Kaggle (SMS requis, ~30 h GPU/sem., T4×2/P100), Colab gratuit (sans téléphone, session manuelle,
interdit de contourner l'interface), Lightning AI (crédits, SMS), Cloudflare Workers AI FLUX-schnell (compte requis),
Gemini/Imagen (aucun accès image gratuit), stockage : Backblaze B2 10 Go sans carte.

## EXP-014 — Prototype hybride « proto_001 » (option D : décor IA + personnages vectoriels + caméra)
- **Date** : 19/09/2026 — **Objectif** : mesurer si un décor IA réel et une vraie mise en scène améliorent nettement le rendu, sans GPU ni quota.
- **Solution** : décor AI Horde (EXP-011, converti WEBP→PNG, flou de profondeur de champ 2,2 px, vignette) + personnages `toon_engine.py`
  (Kevin, Mme Fournier) + caméra « cinématographique » dans `make_toon.py` (`cinematic=True` : plan large sur la 1re réplique, plan moyen ×1,3
  sur celui qui parle, gros plan ×1,85 + secousse sur la chute, lissage exponentiel) + titre d'accroche effacé à 3,6 s (règle virale).
- **Résultat (fichier réel)** : `videos/ready/proto_001.mp4` — **1080×1920, 24 fps, H.264+AAC, 30,17 s, 4,8 Mo, volume moyen −15,3 dB
  (pic −1,2 dB)**. Rendu en **36 s** (≈ 1,2× plus rapide que le temps réel). Dialogues identiques à toon_001.
- **Contrôle du fichier final** (8 images extraites de 0,6 s à 27 s + 5 images autour de 6,5 s et 18,5 s) :
  + décor illustré cohérent et propre, profondeur de champ, alternance large/moyen/gros plan lisible, expressions (goutte de sueur, veine de colère),
    sous-titres mot actif surligné, titre visible seulement au début, fin sur gros plan de la chute ;
  − **fausse alerte** : un « chevauchement des personnages » vu sur la planche était un artefact de montage de la planche (bords de vignettes
    juxtaposées), pas un défaut du fichier ; les images isolées sont correctes ;
  − personnages toujours **plats** (mouvement limité à bouche, clignements, gestes du bras) ; ~25 % du cadre bas = comptoir vide (zone masquée
    par l'interface TikTok, acceptable) ; aucune animation de fond.
- **Verdict qualité** : nettement supérieur à toon_001 (fond plat) — **« propre et correct », PAS encore « pro/viral »** : il manque le mouvement riche
  et l'expressivité que donnerait une génération vidéo IA (Wan). Non publié (non demandé).
- **Coût** : 0 €, 0 s de quota GPU. **Décision** : option D **validée comme repli local** ; l'objectif « pro » passe par des plans Wan sur les moments forts
  (accroche + chute) dès qu'une capacité GPU sans quota bloquant existe (voir NEXT_STEPS, action humaine).

<!-- Nouvelle expérience : copier le modèle ci-dessous à la suite, incrémenter le numéro. -->
<!--
## EXP-0NN — Titre
- **Date** :  **Objectif** :  **Solution** :  **Configuration** :  **Résultat** :  **Erreur** :
- **Temps** :  **Coût** :  **Quota** :  **Décision** :  **Pourquoi** :
-->
