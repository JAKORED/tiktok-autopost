# Refonte FactVibes — direction artistique cinématographique (22/10/2026)

> Document de pilotage de la refonte. Il réunit l'**audit** du rendu historique, les
> **storyboards** des 10 nouveaux scénarios (G55→G64), et la **procédure** d'exploitation
> quotidienne du nouveau chemin « réalisateur » (`cinema.py`).

---

## 1. Audit du rendu historique (Phase 1)

L'audit a porté sur 4 vidéos réelles publiées (frames extraites via ffmpeg) et la lecture
complète de `factory.py`, `make_toon.py`, `toon_engine.py`, `studio.build_caption`, `config`.

**Diagnostic — pourquoi les vues décrochaient :**

| Défaut | Cause technique | Conséquence rétention |
|---|---|---|
| Image plate, zéro profondeur | Un seul plan (`bg_image`) + personnages fixes | Pas de mouvement → pas de stimulation |
| Titre jaune permanent | `title_card` affiché de bout en bout | Encombre l'image, vole l'attention au récit |
| Personnages figés | Aucun rig : pose unique du début à la fin | Aucun storytelling non-verbal |
| Boucle musicale identique | Une seule piste en boucle à volume constant | Fatigue auditive, pas de relief |
| Sous-titres fusionnés | Impact en faux-gras Cairo (glyphes collés) | Illisibilité → désabonnement silencieux |
| 0 plan, 0 transition | `make_toon.render` = 1 image/30 s statique | Aucun rythme de montage |

**Mesures avant/après** (`tests/metrics_compare.py`, ancien `auto_177` vs nouveau `auto_217`) :

| Indice | Ancien | Nouveau | Ratio |
|---|---|---|---|
| Mouvement inter-images (%) | 0,91 | 2,89 | **×3,2** |
| Changements de plan | 0 | 4 | **∞** |
| Dynamique audio p90−p10 (dB) | 11,8 | 18,5 | **+6,7 dB** |
| Crête audio p90 (dBFS) | −12,0 | −3,7 | **+8,3 dB** |

---

## 2. Architecture de la refonte

Séparation nette du contenu et de la présentation :

```
factory.py     → scénario (7 répliques, punch, question, hashtags, storyboard hints)
      │
      ├─ cinema.py      → réalisateur : plans, caméra, rig, sous-titres, fin
      ├─ artdir.py      → système graphique : palettes, lumière, typo, easings
      ├─ sets_v2.py     → décors en 3 couches parallaxe (far/mid/near)
      ├─ toon_engine.py → rig 2D des personnages (additif, ancien chemin intact)
      └─ audio_v2.py    → SFX + musiques par humeur + ambiances, synthétisés numpy
```

**Activation progressive** : le chemin « cinéma » ne se déclenche QUE si l'épisode porte un
champ `storyboard` (et pas de `bg_image`). Les 216 épisodes historiques passent donc par
l'ancien chemin `make_toon.render`/`mix_audio`, strictement inchangé (régression validée par
`tests/test_detection_doublon.py`).

---

## 3. Grammaire visuelle (nouveau chemin)

### 3.1 Décors — 3 couches parallaxe (`sets_v2.py`)
- **far** (0.55) : ville nocturne, fenêtres allumées ;
- **mid** (0.90) : mur, étagère, horloge vivante (aiguilles réelles) ;
- **near** (1.35) : bureau, objets de premier plan.
La fenêtre est percée via `OPERATOR_CLEAR` : on voit la couche *far* au travers — vraie
profondeur, pas un sticker.

### 3.2 Lumière (`artdir.py`)
Clé chaude en diagonale, contre-jour, poussières dans le faisceau, brouillard, grain,
vignettage, letterbox ciné (0→5,5 % à l'ouverture), flash sur la révélation.

### 3.3 Typographie
- Contour noir épais + **interlettrage proportionnel** (tracking 9 sur sous-titres) ;
- Police en graisse **NORMALE** (le faux-gras d'Impact fusionnait les glyphes) ;
- Titre révélé par **masque** puis évacué (plus de titre jaune permanent) ;
- Sous-titres mot-à-mot, **mot actif en jaune accent**, scrim sombre ;
- `keyword_slam` : le mot de la chute grossit d'un coup.

### 3.4 Caméra & plans (`cinema.py`)
- 1 réplique = 1 plan ; plans `wide` / `med` / `close` ;
- mouvements `push` / `pull` / `pan` / `drift` / `whip` avec easing (8 courbes, `spring`
  borné à 1,06 pour un rebound contrôlé) ;
- transitions `cut` / `dip` / `flash` / `wipe` ;
- rig calculé par plan : locuteur face caméra en punch, réacteur `facepalm`/`shrug` ;
- **fin** : cadre assombri (voile 62 %) + question de commentaire + « SUIS POUR LA SUITE ».

### 3.5 Personnages — rig 2D (`toon_engine.py`)
Tour de tête par écrasement latéral (yaw/lean, disparition de l'oreille lointaine), regard
(gaze_x/y), posture (shoulder), gestes (`point`/`shrug`/`crossed`/`facepalm`/`open`),
entrée en scène (`enter`, `alpha`, décalage latéral). 100 % vectoriel pycairo — aucun
sprite, aucun asset tiers.

### 3.6 Son (`audio_v2.py`)
SFX synthétisés : `riser`, `whoosh`, `stab`, `hit`, `tick`, `shimmer`, `sub_drop`.
Musiques par **humeur** suivant le récit : `curious` → `tension` → `light` → `reveal`.
Ambiances par décor (bureau, usine, magasin, scène). Mixage avec **ducking** (la musique
s'abaisse sous la voix) et creusement des silences → le silence devient un effet.

---

## 4. Les 10 scénarios v2 (G55→G64, auto_217→auto_226)

Un scénario = **UNE** vidéo (fini les 4 clones). Chacun porte : 7 répliques (dernière =
*punch*), question de commentaire réelle, 4 variantes d'accroche (`hooks`) pour tests A/B au
niveau de la légende, et un storyboard (plans / mouvements / transitions / mot-clé frappé).

| Famille | id | Titre | Construction |
|---|---|---|---|
| G55 | auto_217 | La télé qui répond avant ta phrase | objet connecté / devancement |
| G56 | auto_218 | Le badge qui pointe avant toi | institution / anticipation |
| G57 | auto_219 | La cafetière qui décide à ta place | objet connecté / surveillance |
| G58 | auto_220 | Le caddie qui fait ta liste | objet connecté / prédiction |
| G59 | auto_221 | Le mail parti tout seul | objet connecté / perte de contrôle |
| G60 | auto_222 | L'IA qui te remplace en réunion | institution / remplacement |
| G61 | auto_223 | La réforme appliquée d'avance | institution / anticipation 2 |
| G62 | auto_224 | Le ticket de caisse qui prédit | objet connecté / prédiction 2 |
| G63 | auto_225 | La montre qui parle à ta place | objet connecté / surveillance 2 |
| G64 | auto_226 | L'usine qui produit des pièces inutiles | institution / production inutile |

Les storyboards complets (hints par réplique : `kind`, `move`, `transition`, `slam`) sont
dans `factory.SCENARIOS_V2`. Exemple G55 :

```
0 : wide  push  dip    → accroche, on découvre le décor
3 : med   pan          → Fournier commente, caméra latérale
5 : close push  wipe   → Kevin inquiet, tension qui monte
6 : close push  flash  slam="DÎNER" → la chute, révélation
```

---

## 5. Procédure quotidienne

Rien ne change à l'exploitation — le pipeline reste :

```
python video_pipeline/studio.py render_new      # rend les épisodes READY
python video_pipeline/studio.py queue           # remplit le tampon
python video_pipeline/studio.py publish         # publie le plus ancien READY
```

`make_toon.build(id)` dispatche automatiquement :
- épisode **avec** `storyboard` → `cinema.render` + `audio_v2` (nouveau chemin) ;
- épisode **sans** `storyboard` (historique) → `make_toon.render` + `mix_audio` (ancien).

**ORDRE M permanent** : jamais d'identifiant `auto_XXX` visible dans la légende. La preuve de
présence repose sur « (épisode N) » + titre distinctif. `build_caption` v2 ajoute la question
du scénario + ses hashtags (5 max, jamais `#fyp`/`#viral`).

### Tests
```
python tests/test_cinema.py            # 6 familles de vérifications (scénarios, cinématique, rig, légendes, audio)
python tests/test_detection_doublon.py # régression anti-doublon (inchangée)
python tests/metrics_compare.py <ancien.mp4> <nouveau.mp4>
python tests/fake_lines.py             # épisode factice pour tester sans TTS (réseau)
```

### Remotion (`remotion/`)
Composition web optionnelle, même format 9:16 (1080×1920, 24 i/s) :
```
cd remotion
npx remotion still src/index.ts FactVibesTitle ../temp/t.png --frame=24
npm run render                          # FactVibesTitle → mp4
```
Le pipeline **pycairo reste le chemin de production par défaut** ; Remotion est une passerelle
pour itérer rapidement sur les titres/cartes sans relancer le rendu cairo.

---

## 6. Limites & suite

- **TTS edge-tts** : l'incident 429 (limite Microsoft, `wss://api.msedgeservices.com`) peut
  bloquer la génération de voix. La démo `auto_217_demo.mp4` a donc été produite avec une
  **voix synthétique hors-ligne** (`tests/fake_lines.py`) pour valider tout le rendu/mix/encodage.
  Réessayer le TTS réel dès que la limite se libère (4 réessais déjà codés).
- **Banque de scénarios** : G55→G64 comble le stock. Prévoir G65+ avant épuisement.
- **Rétention réelle** : les métriques ci-dessus sont **techniques** (mouvement, plans, audio).
  La rétention TikTok (courbe de vues) n'est mesurable qu'après publication — à comparer sur
  les prochaines sorties v2 vs historique dans TikTok Analytics.
