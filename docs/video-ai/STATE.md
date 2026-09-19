# CURRENT STATE

Dernière mise à jour : 19/09/2026 — Agent : Claude (session « machine vidéo »)

## Fonctionne (prouvé par fichier ou capture)
- Publication TikTok Studio : video_001, 002, 003 publiées et visibles (EXP-003).
- Moteur vectoriel + voix + sous-titres + musique : toon_001..004 rendus (EXP-004).
- Wan 2.2 14B image→vidéo sur Space HF : clip 480×832 propre et cohérent (EXP-010).
- AI Horde : décor 704×1216 sans filigrane, 276 s (EXP-011).
- **Prototype hybride proto_001** (décor IA + personnages vectoriels + caméra) : fichier réel 30,2 s 1080×1920, contrôlé — propre mais pas « pro/viral » (EXP-014).

## Échec / rejeté
- Modal : carte bancaire exigée même pour un T4 (EXP-005).
- Pollinations : 584×1009, logo, déformé (EXP-006).
- API TikTok : 403 à l'initialisation (EXP-002).
- HF ZeroGPU anonyme : 120 s/jour → ~4 clips/jour, insuffisant (EXP-009).
- LTX-Video : mains inventées, mouvement faible (EXP-007/008).

## En cours / bloqué
- **Comfy Cloud** : recherche faite, sources contradictoires (400 crédits vs 5 runs), API gratuite non confirmée ; **test impossible sans compte**.
- Pilote Wan I2V : à écrire (le prototype hybride existe, voir ci-dessus). `compose_cloud.py render` : jamais exécuté sur de vrais plans.
- Correctif de légende de `publish_studio.py` : écrit, non validé en publication réelle.

## Prochaine action
1. (Agent) Écrire le pilote Wan 2.2 I2V + fallback, et remplacer les moments forts (accroche, chute) de proto_001 par des plans Wan dès qu'une capacité GPU existe.
2. (Humain, une seule) Créer un compte gratuit Comfy Cloud **ou** valider Kaggle par SMS **ou** fournir un `HF_TOKEN` gratuit.

## Objectif
Produire 5 vidéos professionnelles 9:16 (24–30 s), gratuitement, publiées sur TikTok.
