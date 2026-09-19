# SOLUTIONS — registre des outils et services

> Chaque ligne renvoie à une expérience (`EXP-…`) ou à une source. Statuts : **VALIDÉ**, **LIMITÉ**, **TESTÉ**, **À TESTER**,
> **REJETÉ**. Carte = carte bancaire exigée. Une valeur supposée est marquée « NV » (non vérifié).

| Solution | Type | Gratuit | Carte | Quota mesuré / annoncé | Qualité (mesurée) | Statut |
|---|---|---|---|---|---|---|
| Pipeline CPU Pillow+edge-tts+ffmpeg | Montage local | Oui | Non | illimité | Basique (texte sur fond) | VALIDÉ (base technique) — EXP-001 |
| Moteur vectoriel pycairo | Personnages/animation locale | Oui | Non | illimité, ~1,3× temps réel | Propre mais « basique » (jugement utilisateur) | VALIDÉ pour cohérence — EXP-004 |
| TikTok Studio via Selenium | Publication | Oui | Non | — | Fonctionne (3 vidéos publiées) | VALIDÉ — EXP-003 |
| TikTok API Content Posting | Publication | Oui | Non | — | 403 à l'init | REJETÉ (cause inconnue) — EXP-002 |
| Modal | GPU cloud | 30 $/mois annoncés | **Oui** (mesuré) | aucun GPU sans carte | — | **REJETÉ** — EXP-005 |
| HF ZeroGPU — LTX-Video distillé | Vidéo T2V/I2V | Oui | Non | 120 s/jour anonyme, 5 min/jour compte gratuit (doc) | Moyenne, mains parasites en I2V | **LIMITÉ** — EXP-007/008/009 |
| HF ZeroGPU — Wan 2.2 14B I2V (Lightning) | Vidéo I2V | Oui | Non | même quota HF | **Bonne** (propre, cohérente), 480p/16 fps | **TESTÉ — meilleur moteur** — EXP-010 |
| Pollinations | Images | Oui | Non | non mesuré | 584×1009, filigrane, déformé | **REJETÉ** — EXP-006 |
| AI Horde (clé anonyme) | Images SDXL | Oui | Non | file d'attente, priorité basse | Bonne pour décors, 276 s/image | **VALIDÉ (décors)** — EXP-011 |
| Comfy Cloud gratuit | ComfyUI cloud (Wan) | Oui | Non | 400 crédits/mois **ou** 5 runs (contradiction) | NV | **À TESTER** (compte requis) — EXP-012 |
| Kaggle | GPU notebook | Oui | Non | ~30 h/sem. (source secondaire, NV), SMS obligatoire ; **2×T4 uniquement (P100 retiré le 15/09/2026)**, 29 Go RAM, 12 h/session, 500 fichiers de sortie | NV (Wan 2.2 5B sur T4 jamais mesuré) | **PRÉPARÉ, non exécuté** — notebook prêt (KAGGLE.md), action humaine requise |
| Google Colab gratuit | GPU notebook | Oui | Non | non publié, session manuelle | NV | À TESTER (action humaine) |
| Lightning AI | GPU notebook | Crédits | Non | ~15 crédits/mois (NV), SMS | NV | NV |
| Cloudflare Workers AI FLUX-schnell | Images | Oui | Non (annoncé) | 10 000 neurons/jour | NV (compte + token requis) | NV |
| Gemini / Imagen | Images | Non | — | « Not available » en gratuit | — | REJETÉ (source officielle) |
| Backblaze B2 | Stockage S3 | 10 Go | Non (annoncé) | 10 Go | — | Candidat stockage — NV |
| GitHub Releases | Stockage | Oui | Non | 2 Go/fichier | — | Candidat stockage — NV |

## Décisions expliquées (un futur agent ne doit pas refaire ces tests sans raison)

### Modal — REJETÉ
- **RAISON** : le compte exige un moyen de paiement pour tout GPU.
- **TEST** : `modal run` avec `gpu="L40S"`, puis sondes séparées T4, L4, A10G (`cloud/modal_gpu_probe.py`, variable `PROBE_GPU`).
- **RÉSULTAT** : `Please add a payment method to use <GPU> GPU functions.` pour chacun.
- **ALTERNATIVE** : HF ZeroGPU (EXP-010), Comfy Cloud (à tester), Kaggle/Colab (action humaine).

### Pollinations — REJETÉ pour les keyframes
- **RAISON** : résolution 584×1009, logo incrusté, images sombres/déformées.
- **TEST** : 3 prompts cartoon (paon, robot, lion), `model=flux`, seed 5.
- **RÉSULTAT** : inutilisable comme base d'image→vidéo (le logo serait animé, les personnages incohérents).
- **ALTERNATIVE** : AI Horde pour les décors ; personnages vectoriels pour la cohérence.

### LTX-Video distillé — LIMITÉ (pas moteur principal)
- **RAISON** : mouvement faible, artefacts (mains inventées) en image→vidéo, style plat, quota de 120 s/jour.
- **TEST** : EXP-007, EXP-008. **ALTERNATIVE** : Wan 2.2 14B (EXP-010).

### API TikTok — REJETÉE
- **RAISON** : 403 à l'initialisation malgré token valide. **TEST** : EXP-002. **ALTERNATIVE** : TikTok Studio (EXP-003).

### Kaggle — RETENU comme piste principale (non encore exécuté)
- **RAISON** : seule option sans carte avec vraie capacité GPU et automatisation sans identifiants partagés (le propriétaire lance « Save & Run All »).
- **TEST** : aucun test GPU possible depuis le poste ; tout ce qui est testable localement l'a été (montage, validation, reprise, import — voir KAGGLE.md).
- **RÉSULTAT ATTENDU / RISQUES** : Wan 2.2 5B exige officiellement 24 Go de VRAM (T4 = 16 Go) ; fp16 sur T4 non vérifié ; qualité du 5B inconnue.
- **ALTERNATIVE** si le 5B échoue sur T4 : LTX-Video (moins bon mais léger), Comfy Cloud (compte), HF ZeroGPU quotidien (1 vidéo/jour).
