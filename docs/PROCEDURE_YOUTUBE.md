# Procédure de publication YouTube — chaîne « Phrazia »

> Ordre du patron (18/10/2026, cadence confirmée le 21/10/2026) : republier sur YouTube
> les vidéos **déjà publiées sur TikTok** (chaîne FactVibes), sans aucun doublon, par lots
> de **3 le matin + 3 le soir** (max 6/jour). Aucune création de contenu YouTube : on ne
> fait que recycler ce qui existe déjà sur TikTok.

## 1. Principe directeur

**Zéro doublon** — règle absolue sur les deux plateformes. Une vidéo n'est téléversée
que si elle est absente des deux sources de vérité :

1. `logs/youtube_posts.json` (historique local, clé = identifiant vidéo) ;
2. le **contenu réel en ligne** de la chaîne (liste Studio → Contenu → Shorts,
   extraite par `scripts/yt_upload.py::get_channel_titles`).

Le test porte sur **l'identifiant de vidéo** ET sur le **titre normalisé**
(minuscules, sans emojis, sans `#shorts`, ponctuation réduite à des espaces).

Toute vidéo de l'historique marquée `SUPPRIMEE` reste exclue de la sélection :
une vidéo retirée n'est jamais re-téléversée sans ordre explicite du patron
(on signale, on ne recrée pas).

## 2. Format des textes (aucun identifiant interne visible)

Règle permanente : **jamais** d'identifiant interne (`auto_XXX`, `toon_XXX`,
`via_XXX`) dans un titre, une description ou une légende visible.

- **Titre** : titre de la métadonnée + ` #shorts` (100 caractères max)
- **Description** : `Titre — épisode N de FactVibes Toons.` + hashtags de la
  métadonnée (sans `#fyp` ni `#pourtoi`) + `#shorts`

Exemple :
```
Titre :       Le message à 23 h 43 #shorts
Description :  Le message à 23 h 43 — épisode 1 de FactVibes Toons.

#travail #ia #mail #nuit #humour #dessinanime #cartoon #drole #FactVibesToons #shorts
```

## 3. Déroulé d'un lot

1. **Prérequis** : Chrome ouvert avec le port CDP 9222 (`prepare_browser.bat`),
   session YouTube Studio connectée sur la chaîne Phrazia
   (`UCfRGgDMtWpsmd7LmBEY2_Lg`), vidéos sources présentes dans `videos/ready/`.
2. **Sélection anti-doublon** : `python scripts/yt_upload.py --daily --limit 3`
   prend les vidéos `PUBLISHED` de `videos/queue.json` (donc déjà en ligne sur
   TikTok) dans l'ordre chronologique ancien → récent, en excluant tout
   identifiant ou titre déjà côté YouTube. `--limit 3` n'en publie que 3 dans le
   lot ; les autres attendent le lot suivant.
3. **Publication** : le script pilote Studio via CDP (import du fichier, titre,
   description, déroulé « Suivant », visibilité Publique, clic « Publier »).
   Entre chaque vidéo : re-navigation vers la page d'import + fermeture des
   boîtes résiduelles (l'état laissé par le wizard précédent empoisonne le
   suivant — constaté le 18/10). La réussine n'est validée qu'après **effet
   réel** : confirmation « Vidéo mise en ligne » **ou** navigation vers l'état
   « d=ud » (upload done) de la page d'import.
4. **Vérification finale = flux RSS public** : après chaque tentative (succès
   ou erreur d'interface), le script interroge
   `https://www.youtube.com/feeds/videos.xml?channel_id=UCfRGgDMtWpsmd7LmBEY2_Lg`.
   Une vidéo **est publiée si et seulement si** elle apparaît dans ce flux
   (brouillons exclus) ; l'URL canonique du flux fait foi. Une confirmation
   d'interface « perdue » n'est donc plus un échec, et une vidéo déclarée
   publiée mais absente du flux est signalée. Repli : endpoint oEmbed
   (`youtube.com/oembed?url=...&format=json`), insensible au cache du RSS.
5. **Enregistrement** : chaque vidéo publiée est ajoutée immédiatement à
   `logs/youtube_posts.json` (URL canonique, titre, date UTC, note). C'est cet
   historique qui protège les lots suivants.
6. **Rapport** : liste des vidéos publiées + URLs au patron (dans `memoire.md`
   et en réponse de session).

## 4. Contrôles et cas particuliers

- **Avant chaque lot** : inventaire live de la chaîne (titres + IDs) confronté
  à l'historique. Toute vidéo de l'historique absente du live est marquée
  `SUPPRIMEE` dans `logs/youtube_posts.json` (vérification par rechargement de
  sa page d'édition Studio, pour écarter les erreurs de chargement transitoires).
- **Lancement unique (verrou)** : `yt_upload.py` prend `videos/.yt_publish.lock`
  à démarrage et refuse de tourner si un autre lot est en cours (< 30 min).
  Deux lanceurs sur le même Chrome se volent l'onglet l'un à l'autre et
  publient des vidéos que l'autre déclare échouées (incident du 21/10).
  `--force` ne s'utilise que si on sait que l'autre processus est mort.
  En cas d'échec d'interface, l'onglet Studio est fermé au niveau navigateur et
  remplacé par un onglet neuf (jamais de réutilisation d'un onglet suspect).
- **Brouillons** : un brouillon oublié en Studio est d'abord cherché avant tout
  téléversement (risque de doublon). S'il correspond à une vidéo de la sélection,
  on corrige ses textes et on le publie au lieu de re-téléverser.
- **Titre interne détecté en ligne** : toute vidéo déjà en ligne avec un titre
  brut ou une description vide est **corrigée** immédiatement via la page
  d'édition Studio (voir §5).
- **Quota** : 6 téléversements/jour maximum (`QUOTA_JOUR = 6`). `--daily` refuse
  de démarrer si le quota du jour est déjà consommé.

## 5. Historique des corrections

| Date | Élément | Action |
|------|---------|--------|
| 18/10 | `toon_004` « Le prix de la tomate » | En ligne depuis le 16/10 avec le titre brut **« toon 004 »** et aucune description (violation de la règle d'identifiants) → titre + description corrigés via Studio ; vidéo ajoutée à l'historique. |
| 18/10 | `auto_002` « Le mail du vendredi (le planning) » | Confirmée **supprimée** de YouTube (page d'édition en erreur après rechargement + absente de la liste Contenu) → marquée `SUPPRIMEE`, comme `video_001/002/003`. |
| 18/10 | premier lancement `--daily` | Bloqué 15 min sans sortie : l'onglet réutilisé n'était pas sur la page d'import, et la liste Shorts Studio fait parfois geler le renderer. Correctifs : navigation systématique vers `/videos/upload`, état propre par vidéo, dédup enrichie par RSS public. |
| 18/10 | `via_002` « POV : le voleur du frigo » | Publiée par l'assistant **sans que la confirmation ne soit détectée** (dialogue non visible) → ratée à tort par le 1er lot. D'où la vérification RSS systématique : le flux public est la seule vérité. |
| 18/10 | `via_001`/`via_003` | 1er passage avorté (wizard empoisonné par l'état de `via_001`) → repassés avec état propre : publiés et vérifiés (RSS + oEmbed). |
| 19/10 | onglet Studio figé en plein lot | Le renderer de l'onglet d'import s'est gelé en cours d'envoi de `via_004` : `Runtime.evaluate` ne répond plus, `cmd` et `Page.close` bloquent aussi (websocket morte). Le fichier s'est téléversé (état `d=ud`) mais le wizard n'a jamais cliqué « Publier » → la vidéo est restée **brouillon**, donc absente du RSS (aucun doublon public). **Contournement** : fermeture au niveau navigateur via l'API HTTP — `Invoke-RestMethod -Method Put http://127.0.0.1:9222/json/close/<targetId>` (le navigateur répond même quand le renderer est mort), puis relance du lot sur un onglet neuf. Le lot a été perdu de 3/3. Leçon confirmée : `d=ud` seul ne prouve pas la publication si le wizard a calé avant le clic « Publier » — le RSS reste l'unique vérité. |
| 20/10 | Chrome trouvé éteint au réveil | Vérifier `http://127.0.0.1:9222/json/version` **avant** chaque lot ; si absent, relancer `prepare_browser.bat` (la chaîne TikTok a aussi besoin de Chrome pour les créneaux du soir). |
| 21/10 | Lot du matin 3/3 mais pilotage à deux | **Symptôme** : « aucune-boite » pendant 10 min puis, à l'instant où le bouton « Suivant » réapparaît, `Inspected target navigated or closed` — l'assistant disparaît alors que la vidéo part quand même en ligne. **Cause** : deux processus ont piloté **le même onglet** Studio en même temps (un second `yt_upload.py` a navigué l'onglet au milieu du wizard du premier ; il a publié `auto_025` à 13:28 alors que le premier le déclarait échoué). Règle : **un seul lanceur `yt_upload.py` à la fois** — avant de lancer un lot, vérifier `Get-CimInstance Win32_Process -Filter "Name='python.exe'"` (aucun `yt_upload` ne doit tourner) et dire au patron qu'une autre session/terminal pilote le même Chrome. |
| 21/10 | `auto_012` publiée non détectée | La vidéo est en ligne (RSS + oEmbed) alors que l'interface n'a rien confirmé → l'historique a été réconcilié à la main. **Avant chaque relance : interroger le RSS public** ; une vidéo « déclarée échouée » peut être en ligne. |
| 21/10 | Renderer Studio gelé en cours de lot | `Page.captureScreenshot` et `Runtime.evaluate` ne répondent plus (page d'import + ~90 workers TikTok dans le même Chrome). Contournement : fermer l'onglet au niveau navigateur (`Invoke-RestMethod -Method Put http://127.0.0.1:9222/json/close/<targetId>`) puis ouvrir un onglet neuf — jamais « réutiliser » un onglet gelé. |
| 20/10 | lot programmé 02:04 (auto_012/022/025) | Le shell d'arrière-plan a été tué au redémarrage/session : **le lot n'a jamais tourné** (historique toujours à 19). Les 3 vidéos restent dues ; un shell d'arrière-plan meurt à chaque redémarrage → **toujours vérifier l'issue** (`logs/youtube_posts.json` + RSS) avant de re-lancer. |
| 21/10 | méconnaissance des profils Chrome | **3 profils coexistent** : `FactVibesDebug` (créé le 20/10 par l'ancien `prepare_browser.bat`, **aucun cookie** — inutile), le profil par défaut de l'utilisateur (jamais utilisable : Chrome ≥136 refuse le port de débogage sur le profil par défaut), et **`config/chrome_tiktok_profile` = LE vrai** (sessions TikTok (QR) + YouTube, relancé par l'autoposter lui-même, parent logique du port 9222). `prepare_browser.bat` a été réécrit pour ce profil. Ne plus jamais toucher aux autres. |
| 21/10 | `cdp.py eval <tab-id>` « introuvable » | `find_tab` matche sur **titre + URL**, jamais sur le GUID de l'onglet : toujours passer un sous-chaîne d'URL (`tiktokstudio/upload`, `example.com`…). Les « évaluations bloquées » du 20-21/10 étaient en fait des recherches d'onglet qui échouaient. |
| 21/10 | « bouton Publier indisponible » = **faux négatif** | 5 vidéos (181, 189, 190-192) marquées FAILED le 20/10 alors que **181 et 189 étaient en ligne** (vérification d'effet qui rate la confirmation de TikTok). La **réconciliation au démarrage** du poster les a reclassées PUBLISHED et a bloqué 190-192 (« doublon de scénario »). **Règle absolue : ne jamais réarmer un FAILED sans contrôle live/réconciliation** — le réarmer aurait pu rejouer une vidéo déjà publiée. Le 20/10 était en réalité 3/3 (185+181+189). |
| 21/10 | `auto_033` « WhatsApp/Tonton » : FAILED = **faux négatif** | Marquée FAILED par `auto_upload` (WinError 10053 sur la connexion au débogage pendant la détection de confirmation) alors qu'elle était **en ligne** (`xubm_CTcR-Y`, publiée 11:41:44Z) → vérifiée RSS + oEmbed, ajoutée à l'historique, aucune relance. Même famille que « bouton Publier indisponible » : **la confirmation d'interface qui rate ne prouve rien, seul le RSS tranche**. Les WinError 10053 du 21/10 coïncidaient avec l'activité du patron dans le même Chrome (transitoires). |
| 21/10 | `auto_029` relancé après échec à `[start]` | Échoué au démarrage (WinError 10053, aucun brouillon créé, quota non consommé) → relancé seul `python scripts/yt_upload.py auto_029` : publié `mM9NIawYx4k` (oEmbed + historique). Quota du jour final : 5/6 (012, 022, 025, 033, 029). |
| 21/10 | Brouillons orphelins doublons en Studio | **4 brouillons** de la liste Contenu doublonnent des vidéos déjà publiées (auto_025 ×2, auto_013, via_004) = risque latent de doublon. 1 supprimé sur 2 (« Annuler l'importation » + confirmation), **3 restent** (« La banque », micro-ondes, note vocale). La campagne a calé sur les handlers morts de la liste après re-rendu : la **case à cocher de sélection**, « Supprimer la vidéo » et « Annuler l'importation » n'ouvrent plus rien (contenu de dialogue zombie `offsetHeight=0`, zéro événement JS), seul « Modifier le brouillon » navigue. Leçons : (a) **survol requis** — les boutons d'action sont `ytcp-button { display:none }` révélés au hover de la ligne ; (b) les cellules `position:relative` (« Vues ») passent au-dessus → `position:relative + z-index` sur les ancêtres + `elementFromPoint` **avant** tout clic réel ; (c) après échec, **repartir d'une navigation propre** (un `location.href`/`history.back()` purge les dialogues zombies) ; (d) si rien ne répond → supprimer manuellement via l'UI du patron. Ne JAMAIS les publier (leurs titres sont déjà dans l'historique → la dédup les bloque de toute façon). |

| Élément | Rôle |
|---------|------|
| `scripts/yt_upload.py` | Publication + sélection anti-doublon + historique (`--daily --limit N`, ou liste d'IDs explicite) |
| `scripts/cdp.py` | Mini-client Chrome CDP port 9222 (`list`, `open`, `eval`, `snap`, `cmd`) — cible = **sous-chaîne titre/URL** |
| `prepare_browser.bat` | Relance de Chrome **profil `config/chrome_tiktok_profile`** port 9222 (inutile si le port répond déjà ; ne jamais fermer Chrome par automation) |
| `logs/youtube_posts.json` | Historique YouTube (clé = identifiant vidéo, y compris `SUPPRIMEE`) |
| `videos/.yt_publish.lock` | Verrou de lancement : un seul `yt_upload.py` à la fois (posé/release automatiquement, TTL 30 min) |
| `videos/queue.json` | État TikTok — source de sélection (uniquement `PUBLISHED`) |
| `videos/ready/`, `videos/metadata/` | Fichiers MP4 et métadonnées (titre, hashtags, épisode) |

## 7. Rythme de publication

- **Matin** : lot de 3 (avant 14 h) — lancé à réveil de l'agent, jamais après 14 h
- **Soir** : lot de 3 (à partir de ~19 h, fin de journée) — cadence ordonnée par le
  patron le 21/10/2026 (remplace « 3 l'après-midi »)
- Maximum strict : 6 vidéos/jour ; le lendemain reprend la file là où elle s'est
  arrêtée (ordre chronologique TikTok, sans jamais repasser sur un titre publié).
