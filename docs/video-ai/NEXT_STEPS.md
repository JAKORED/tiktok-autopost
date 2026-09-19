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

## À faire
- [ ] **(HUMAIN — un seul choix)** Créer le compte gratuit Comfy Cloud, ou vérifier Kaggle (SMS), ou fournir `HF_TOKEN`
- [ ] Tester Comfy Cloud réellement (crédits réels, Wan, API gratuite ?) — **bloqué : compte requis**
- [ ] Source d'images : décors = AI Horde (validé) ; **personnages animaux à produire** (étendre `toon_engine.py` ou référence IA)
- [ ] Finaliser la character sheet (visage, corps, vêtements, couleurs, accessoires, proportions, expressions, poses) — personnages vectoriels existants : Kevin, Fournier, Ministre, Josette, Bob
- [ ] Écrire le pilote Wan 2.2 image→vidéo (`cloud/`) avec fallback moteur A→B→C
- [ ] Comparer options A (IA), B (vectoriel), C (référence+Wan), D (hybride) sur un même plan — consigner la mesure
- [ ] Produire le **prototype épisode 1** (24–30 s, hook→6 plans→chute→boucle)
- [ ] Contrôler le fichier final de l'épisode 1 (rythme, cohérence, audio, sous-titres, 9:16) ; corriger/régénérer
- [ ] Produire les épisodes 2–5
- [ ] Valider `publish_studio.py` corrigé sur une publication réelle
- [ ] Connecter AutoPost : `publish_queue.py sync` (les vidéos `cloud_00N` entrent en READY)
- [ ] Stockage cloud des vidéos finales (candidat : GitHub Releases ou Backblaze B2 — action humaine si compte)

## Règles
- Cocher uniquement avec une preuve (fichier contrôlé, sortie de commande, capture).
- Ne jamais rayer une tâche échouée : la laisser cochée avec la mention « rejeté » et renvoyer à l'expérience.
