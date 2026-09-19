# NEXT_STEPS — tâches cochables (mettre à jour après CHAQUE étape)

## Fait
- [x] Tester Modal → rejeté (EXP-005)
- [x] Tester LTX ZeroGPU → limité (EXP-007/008/009)
- [x] Tester Wan 2.2 (Space HF) → meilleure qualité (EXP-010)
- [x] Tester Pollinations → rejeté (EXP-006)
- [x] Tester AI Horde → validé pour les décors (EXP-011)
- [x] Rechercher Comfy Cloud (sources lues, calcul crédits→plans→vidéos) (EXP-012)
- [x] Créer la mémoire du projet `docs/video-ai/` et protéger les secrets dans `.gitignore`
- [x] Écrire les 5 concepts (`cloud_episodes.py`) avec les règles virales
- [x] Produire un prototype hybride (option D) `proto_001` et le contrôler sur le fichier final (EXP-014) — verdict : propre, pas encore « pro »
- [x] Source de décors de qualité sans watermark : AI Horde (EXP-011)
- [x] Écrire le notebook Kaggle autonome + scripts (`cloud/kaggle/`), contrôle `validate_video.py`, import `ingest_incoming.py`, reprise `restore_previous.py` (EXP-015)
- [x] Tester localement montage / validation / reprise / import sur fichiers réels (EXP-015) — 6 bugs corrigés
- [x] Calculer les plans de narration réels des 5 épisodes (31 plans) et les embarquer dans le notebook

## À faire
- [ ] **(HUMAIN — seule action requise)** Kaggle : compte + vérification téléphone, importer le notebook, T4 x2 + Internet On, `PHASE="episode1"`, Save & Run All, télécharger l'Output dans `videos/incoming/`
- [ ] Tester Comfy Cloud réellement (crédits réels, Wan, API gratuite ?) — **bloqué : compte requis**
- [ ] Source d'images : décors = AI Horde (validé) ; **personnages animaux à produire** (étendre `toon_engine.py` ou référence IA)
- [ ] Finaliser la character sheet (visage, corps, vêtements, couleurs, accessoires, proportions, expressions, poses) — personnages vectoriels existants : Kevin, Fournier, Ministre, Josette, Bob
- [ ] Valider sur GPU le pilote Wan 2.2 5B (écrit dans `cloud/kaggle/generate_shots.py`, jamais exécuté) ; fallback moteur : i2v→t2v (fait), puis LTX / Comfy Cloud / ZeroGPU
- [ ] Comparer options A (IA), B (vectoriel), C (référence+Wan), D (hybride) : le test A/B du notebook (i2v vs t2v, même seed) + `proto_001` — consigner la mesure dans EXPERIMENTS.md
- [ ] Produire l'**épisode 1 « pro »** (24–30 s, hook→6 plans→chute→boucle) avec plans Wan sur accroche et chute
- [ ] Contrôler le fichier final de l'épisode 1 (rythme, cohérence, audio, sous-titres, 9:16) ; corriger/régénérer
- [ ] Produire les épisodes 2–5
- [ ] Valider `publish_studio.py` corrigé sur une publication réelle
- [ ] Connecter AutoPost : `publish_queue.py sync` (les vidéos `cloud_00N` entrent en READY)
- [ ] Stockage cloud des vidéos finales (candidat : GitHub Releases ou Backblaze B2 — action humaine si compte)

## Règles
- Cocher uniquement avec une preuve (fichier contrôlé, sortie de commande, capture).
- Ne jamais rayer une tâche échouée : la laisser cochée avec la mention « rejeté » et renvoyer à l'expérience.

## Recherche parallèle (ne pas s'arrêter à Kaggle)
- [ ] Autre Space Wan avec réservation GPU plus faible ; version quantifiée/GGUF du 5B pour T4 (aucun résultat vérifié à ce jour)
- [ ] Tester Comfy Cloud si un compte gratuit est créé (calcul crédits : ~11 crédits/plan de 5 s ; 400 crédits ≈ 36 plans, si l'offre est confirmée)
- [ ] Modèle plus léger (LTX-Video) en secours sur Kaggle si le 5B ne tient pas sur T4
