# Procédure de publication YouTube — chaîne « Phrazia »

> Ordre du patron (18/10/2026) : republier sur YouTube les vidéos **déjà publiées sur
> TikTok** (chaîne FactVibes), sans aucun doublon, par lots de **3 le matin + 3
> l'après-midi** (max 6/jour). Aucune création de contenu YouTube : on ne fait que
> recycler ce qui existe déjà sur TikTok.

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

## 6. Outillage

| Élément | Rôle |
|---------|------|
| `scripts/yt_upload.py` | Publication + sélection anti-doublon + historique (`--daily --limit N`, ou liste d'IDs explicite) |
| `scripts/cdp.py` | Mini-client Chrome CDP port 9222 (`list`, `open`, `eval`, `snap`, `cmd`) |
| `prepare_browser.bat` | Lancement de Chrome avec port 9222 (ne jamais fermer Chrome par automation) |
| `logs/youtube_posts.json` | Historique YouTube (clé = identifiant vidéo, y compris `SUPPRIMEE`) |
| `videos/queue.json` | État TikTok — source de sélection (uniquement `PUBLISHED`) |
| `videos/ready/`, `videos/metadata/` | Fichiers MP4 et métadonnées (titre, hashtags, épisode) |

## 7. Rythme de publication

- **Matin** : lot de 3 (avant 14 h)
- **Après-midi** : lot de 3 (à partir de ~15 h)
- Maximum strict : 6 vidéos/jour ; le lendemain reprend la file là où elle s'est
  arrêtée (ordre chronologique TikTok, sans jamais repasser sur un titre publié).
