# FactVibes — MEMOIRE DES DERNIERES TACHES

## 13/10/2026 — ORDRE M DU PATRON : « EVITE DE METTRE AUTO DANS LA DESCRIPTION, SINON L'ALGORITHME BAN »
- Le patron a vu / redoute que `auto_XXX` dans la description fasse prendre les vidéos
  pour du contenu automatisé => risque de bannissement. Ordre permanent reçu en cours
  de session : JAMAIS `auto_...` dans les légendes visibles.
- `studio.build_caption` mettait `(épisode 90 · auto_090)` dans la légende (c'est aussi
  le nom du fichier recopié par TikTok). CORRIGÉ : la légende est désormais
  `hook — titre (épisode N). question #tags`, SANS l'identifiant. L'identifiant reste
  interne (métadonnées) ; la preuve de présence dans Contenu s'appuie sur
  `(épisode N)` ↔ `auto_N` et sur le titre distinctif (tests mis à jour, OK).
- NOTE : `auto_090` est partie ce matin 10:20 Paris AVEC ` · auto_090` dans sa légende
  (post au format ancien). Le post est en ligne ; la légende n'a pas été éditée
  (édition manuelle risquée) — signaler au patron.

## 13/10/2026 — RETOUR À LA PUBLICATION : edge-tts migré (403) + premier post après 3 jours de silence
- Microsoft a migré edge-tts : l'ancien WebSocket `speech.platform.bing.com` renvoyait
  403. `make_toon.py` corrigé : nouvelle URL
  `wss://api.msedgeservices.com/tts/cognitiveservices/websocket/v1?Ocp-Apim-Subscription-Key=TRUSTED_CLIENT_TOKEN`
  + retry sur 403/429. Vérifié sur les 4 voix françaises.
- `studio.render_new` ignorait déjà les familles publiées (`families_a_eviter`) mais
  brûlait du budget sur des VARIANTES de scénarios déjà sortis : corrigé (une seule
  variante par famille par lot, familles déjà en tampon écartées aussi).
- 5 épisodes neufs rendus pour les familles fraîches : G22 (auto_086), G23 (auto_090),
  G24 (auto_094), G27 (auto_105), G28 (auto_109).
- **auto_090 PUBLIÉE le 13/10 à 10:20 Paris** (1/5 du jour) — le silence de 3 jours est
  brisé. La queue redonne la main : RATTRAPAGE + GARANTIES HORAIRES
  (12:00→2, 15:00→3, 21:00→5) puis créneaux 17:00-19:00 UTC, intervalle 30 min respecté.
- `auto_085` (import) / `auto_086` (légende non saisie — champ absent/écrasé ce matin)
  / `auto_089` (import) / `auto_093` (sans preuve) : échecs sans doublon (RIEN n'est
  parti). auto_086 n'a JAMAIS été en ligne (vérifié par réconciliation + familles) :
  remise en READY le 13/10 pour passer ce jour avec le nouveau format de légende.
- Orchestrateur relancé après le fix captions pour charger le nouveau build_caption.

## 09/10/2026 — LE PATRON : « aucune vidéo postée depuis 3-4 jours, programme le posting auto, 3 vidéos aujourd'hui, attention aux doublons »
- COMPTE MUET 129 h (dernier post 03/10 23:41 UTC). Cause : RIEN ne lançait le pipeline.
  Aucun process Python, et aucune tâche Windows — le dossier de démarrage, jamais alimenté.
- Chrome figé depuis le 30/09 : port 9222 en LISTENING mais connexions REFUSÉES (netstat
  ment). `auto_poster.chrome_vif()` teste une VRAI requete HTTP, pas la presence du port.
- `main.py run_scheduler` n'attrape RIEN le matin (creneaux 17:00-19:00 UTC, rien de
  depasse a 9 h) => un compte muet attend 6 jours de plus. Corrige dans auto_poster.py.
- NOUVEAUX FICHIERS : `auto_poster.py` (orchestrateur 24/7), `superviseur.py` (relance),
  `scripts\installer_demarrage.ps1` (installe sans droits admin), `scripts\installer_taches.ps1`
  (tache Windows, ADMIN requis). Installer au demarrage : le dossier Demarrage est
  choisi parce que Chrome a besoin d'un bureau pour TikTok Studio.
- CHAIN : dossier Demarrage -> superviseur.py -> auto_poster.py (tour de 120 s) ->
  Chrome vivant ? -> production tampon -> decision -> studio.publish_next().
  auto_poster ne decide QUE DU QUAND ; tous les garde anti-doublon restent dans studio.
- DOUBLONS : `family_key` lisait le `headline`, et G2/G16 y mettaient le PARAMETRE
  ("LE PRIX DES PATES", "DU BEURRE", "DU CAFE", "DU PAIN") => 4 variantes vues comme 4
  scenarios differents. Mesure : auto_061/auto_062 = 0.0187, auto_061/auto_063 = 0.0219
  (seuil 0.035) = la MEME video. Corrige : le GROUPE de fabrication est le scenario
  (champ `family` = `G<n>` dans factory.py), 4 variantes par groupe, G1..G36.
- BANQUE : 10 scénarios neufs ajoutes (G27..G36 : ascenseur, reunion de 4 h, appli de
  livraison, puces a l'oral, IA a cote, rapport automatique faux, attente au comptoir,
  decret télétravail, « c'est noté », abonnement résilié). 51 scenarios, 21 jamais
  publies = **4,2 jours** a 5/jour. Il faudra G37, G38... bientot.
- 1er post du 09/10 : `auto_057` (g15, inédit) publie 09:17 UTC, present dans Contenu,
  legende complete. Les 5 nouveaux episodes (auto_085/089/093/097/101) sont rendus.

## Etat actuel (ce que tu fais tourner)
- Projet: C:\Users\Chaima\tiktok-autopost (Python + Selenium)
- But: publier automatiquement jusqu'a 5 videos TikTok/JOUR, dessin anime original, gratuit et open-source, sur @factvibes.daily
- Compte patron: JAKORED — tu es le patron, tu restes le patron
- App TikTok "FactVibes" en mode SANDBOX (localhost accepte) ; API = 403 pour l'instant
- Depots github: https://github.com/JAKORED/tiktok-autopost (public, deploie GitHub Pages)
- ETAT : publication automatique ACTIVE (superviseur + auto_poster demarrés, dossier
  Demarrage installe). Pilotage : `python auto_poster.py --status`

## NOUVEAU (20/09/2026) — LIGNE "TOONS" ACTIVEE
- Moteur principal = dessins animes originaux 100% CPU local, GRATUIT, SANS aucun credit externe
- Banque: 5 episodes ecrits (toon) + 64 generes en parametrique (`video_pipeline/factory.py`)
- Rendu: `python main.py produce` -> `video_pipeline/make_toon.py` (edge-tts + pycairo + ffmpeg)
- Controle: `video_pipeline/studio.py` — ledger quotidien, anti-doublon par signature, publication
- Commandes patrou: `python main.py status|bank|produce|run`
- Etat: 5 episodes READY (auto_001..auto_005), 5 en reserve, aucun poste — EN ATTENTE DU FEU VERT
- Publication = validation humaine dans TikTok Studio via Chrome connecte (QR) ; auto_publish=false
- VERROU: ne JAMAIS publier un script deja publie (doublon = FAILED auto). La publication sans l'accord du patron est interdit depuis le 20/09.

## Ce qui a ete FAIT (dernieres taches, a garder en memoire)
1. App TikTok FactVibes creee sur developers.tiktok.com (sandbox)
2. URL properties configurees et VALIDEES (Production -> Sandbox -> Web)
3. Redirect URI http://localhost:8080/callback enregistre et SAUVE
4. Pipeline complet compilable: main.py, guardians, agents (content_finder, downloader, video_editor, tiktok_publisher, fallback)
5. Fichier .env rempli avec client key + secret TikTok
6. Desktop shortcuts crees: "FactVibes - Projet.lnk" et "FactVibes - Guardian.lnk"
7. Connexion de test au dashboard TikTok automatisable (Selenium CDP 9222)
8. 3 videos API publiees le 16/09 ; 3 autres via TikTok Studio le 19/09 (video_001..003)
9. 20/09 : garde anti-doublon ajoutee apres publication accidentelle de proto_001 (doublon de toon_001, supprimee par le patron)

## 24/09/2026 — POST DU JOUR (ordre du patron : au moins 2 videos)
1. Production: auto_013..017 rendus (5/5 budget, ledger OK)
2. Publication auto_013 via Studio navigateur -> PUBLISHED 24/09 10:45 (presente dans Contenu)
3. auto_012 = DOUBLON (marquee FAILED par le patron) -> verrouillee, jamais republier
4. Portail dev: page "No access / login requis" (non connecte) ; API officielle = 403 sandbox
   -> methode Studio navigateur = seule valable (confirmee)
5. Attention: les 2 posts de ce matin sont partis avec la legendes = nom de fichier + hashtags
   (l'editeur .public-DraftEditor-content n'existe plus / apparait trop tard sur TikTok Studio).
   Prochaines publications : bien verifier legendes avant de cliquer Publier.

## 24/09 — SCHEDULER RECALIBRE (horaires UTC corriges)
- BUG CORRIGE dans main.py run_scheduler : post_times_utc etait applique en heure LOCALE via
  datetime.now().replace() -> la publication aurait eu lieu 4h trop tot (17:00 local = 15:00 UTC).
  Desormais chaque creneau est un datetime aware UTC compare a now.astimezone(timezone.utc).
  -> 17:00 UTC = 19h Paris, 20:15 UTC = 22h15 Paris (soiree FR).
- Scheduler REDEMARRE (ancien PID 3932 arrete, nouveau lancé) pour charger le correctif.
  Il postera auto_014..017 ce soir (19h-22h15) puis continue automatiquement chaque jour.
- Chrome/QR toujours connecte sur @factivibeparano ; editeur Studio vide, pret pour upload.
- Bio mise a jour 24/09 : "FactVibes Toons 🎬 Dessins animés originaux chaque jour. Qui a déjà vécu ça ?"

## 30/09/2026 — CADENCE 30 MINUTES (ordre du patron)
- 1 post toutes les 30 min, 5/jour : 17:00 / 17:30 / 18:00 / 18:30 / 19:00 UTC = 19h-21h Paris.
- config.json : post_times_utc remplace l'ancienne grille (17h/18h/19h/19h30/20h15).
- Le scheduler n'a pas ete modifie : il poste deja un creneau des qu'il est depasse ET que
  min_minutes_between_posts (30) est ecoule. Aucun creneau perdu si la machine redemarre.
- Chrome debug 9222 etait FERME (port muet) => premiere tentative de post en echec
  (SessionNotCreatedException). Relance manuelle de Chrome avec le profil TikTok :
  les 7 videos READY (auto_024..auto_030) sont intactes, aucune perdue.
- File au 30/09 : 49 produites, 21 PUBLISHED, 21 FAILED (historique), 7 READY, 0 doublon.
- Rappel : les posts du 24-27/09 sont partis avec le NOM DE FICHIER comme legende.
  publish_studio.ensure_caption (corrige le 27/09) verifie strictement la legende avant
  de cliquer Publier et marque FAILED plutot que de publier une legende bidon.

## 30/09/2026 — DOUBLONS : LE PIEGE DES VARIANTES (leçon du patron)
- Le patron a repere : « C'EST LA MEME VIDEO PUBLIE IL Y A UNE DEMI-HEURE ». C'etait
  auto_025 (publie 12:34) puis auto_026 (publie 13:05) : meme scenario, meme decor,
  memes 6 premieres repliques sur 7 -> visuellement la MEME video.
- CAUSE : `factory.py` genere 4 VARIANTES par scenario (meme `headline`, meme `set`).
  L'anti-doublon ne comparait que la SIGNATURE DES REPLIQUES : les variantes passaient.
- CORRECTIF (studio.py) : nouvelle fonction `family_key(ep)` = `headline` normalise
  (repli : titre avant la parenthese) + `already_published_families()`. Au moment de
  publier, toute variante d'un scenario deja sorti est marquee FAILED
  (« doublon de scenario ») et le studio passe a la suivante.
- Effet : auto_027 / auto_028 desormais BLOQUES (variantes de « VOTRE BANQUE VOUS
  PROTEGE ») ; la file passe a auto_029.
- 22 scenarios auto_ distincts dans la banque, ~8 deja sortis => ~14 videos neuves
  disponibles (~3 jours a 5/jour). Pour tenir dans la durée il faut de NOUVEAUX
  scenarios (nouvelles familles dans factory.py), pas de nouvelles variantes.

## 30/09/2026 — PUBLICATION auto_025 / auto_026 REUSSIE
- 2 bugs de saisie de legendre corriges dans publish_studio.py (voir HANDOFF ORDRE J) :
  le « filet de securite » JS (createRange + selectNodeContents) desynchronisait l'etat
  React du DraftEditor => l'editeur se demontait et la page repartait sur /content ;
  et le `Keys.ESCAPE` envoye apres saisie faisait perdre la publication.
- auto_025 : publie 30/09 12:34 Paris (legende verifiee dans l'interface, 4 hashtags).
- auto_026 : publie 30/09 13:05 Paris via la boucle `publish_when_allowed` (attente
  de la garde de 30 min, jamais de force).
- 23 videos PUBLISHED au total, 4 READY (auto_029, auto_030 + les nouvelles rendues).

## 02/10/2026 — LE CHAMP LEGENDE NE PRENAIT PAS LE CLAVIER (cause des 5 echecs d'hier soir)
- Mesure sur le vrai formulaire TikTok Studio : `element.send_keys()` ne fait RIEN sur le
  `.public-DraftEditor-content` (meme Ctrl+A puis Suppr). Les touches CDP
  (`Input.dispatchKeyEvent`) sont ignorees aussi. Seul **`Input.insertText` (CDP) ecrit**,
  et il **remplace la selection courante**.
- Methode retenue : poser la selection en JS (`createRange` + `selectNodeContents`, SANS
  supprimer) puis `_insert_text()` par CDP. Le JS ne fait que selectionner, donc pas de
  desynchronisation React (c'etait le defaut du « filet de securite » du 30/09).
- Corrigé aussi : plus jamais de clic sur « Annuler » (il annule l'import et vide le champ).
- Après le clic « Publier », absence de preuve dans Contenu => etat `PUBLISHED_SUSPECT`
  (jamais republié automatiquement), plus `FAILED` qui provoquait les doublons.

## 02/10/2026 — LES DOUBLONS DU PATRON : cause racine trouvee
- La base et le compte TikTok etaient desynchronises : `auto_029` etait en ligne
  (30/09 22:03) mais note FAILED ; un post fantome du 01/10 19h24 (legende cassee) n'etait
  connu de personne. `FAILED` ne veut pas dire « pas en ligne ».
- `auto_001` et `auto_002` sont publies alors que leurs rendus sont INDISCERNABLES
  (distance d'empreinte 0.0078) : voila les doublons que le patron voit.
- 5 garde-fous installes (voir HANDOFF ORDRE K) : reconciliation avant envoi, id de fichier
  dans la legende, empreinte visuelle (seuil 0.035), PUBLISHED_SUSPECT, plus de « Annuler ».
- 10 scenarios NEUFS ajoutes dans factory.py (G17..G26) : badge, ticket de caisse, panne
  annoncee, conference de presse, salaire en retard, « a base de », collegue robot,
  decret retire, mot de passe 123456, file du drive. 40 episodes, 10 scenarios publiables.
- Piege repete : **ne jamais mettre le parametre dans le `headline`**, sinon les variantes
  d'un meme scenario passent pour des scenarios differents (cf. G16 « le prix des pates »).

## Prochaines etapes (quand tu es pret)
- `python main.py run` (apres accord du patron) pour publier le plus ancien READY via Studio navigateur
- OU passer `auto_publish=true` dans config.json APRÈS le feu vert du patron
- Augmenter la banque (factory.py : nouveaux resumes/situations) quand on en a besoin

## Commande pour relancer le gardien 24/7
- double-clic ou: python guardian.py

## 02/10/2026 - TROIS VIDEOS EN LIGNE, ET UNE DECOUVERTE SUR L'INTERFACE
- Etat reel du compte : **26 publications** (etait 23 avant ce matin). Les 3 nouvelles :
  `auto_041` (10:16, legende cassee -> a supprimer par le patron),
  `auto_049` (10:33) et `auto_045` (10:53, legende complete et correcte).
- **Le nom de fichier marche** : la legende en ligne de `auto_045` est bien le nom du
  fichier copie dans C:\jv, avec la question et les 4 hashtags. Plus aucune saisie clavier.
- DECOUVERTE IMPORTANTE : `auto_049` est partie en ligne a 10:33 **sans aucun clic de ma
  part** : c'etait l'upload d'une sonde de test (`test_nom2.py`) laisse ouvert sur le
  formulaire. Consequence : sur le vrai compte, un formulaire d'upload jamais ferme peut
  partir tout seul. Regle : toute sonde de test termine par quitter la page /content.
- Deux sondes ne doivent jamais tourner en meme temps qu'une publication : ajout d'un
  **verrou `videos/.publish.lock`** dans `publish_next` (refuse un second envoi si un
  premier est en cours, le libere apres 15 min s'il est perime).
- Bug de lecture du DOM corrige : une carte du bloc Contenu pouvait englober DEUX
  publications. Consequence : une legende attribuee a la mauvaise video, donc des
  « deja en ligne » a tort, donc des videos jamais publiees. On coupe maintenant chaque
  carte avant la duree suivante (en ignorant l'heure « 2 oct., 10:53 ») et on dedoublonne
  sur les 100 premiers caracteres.

## 15/10/2026 - YOUTUBE : lot d'essai de 3 shorts poste sur la chaine Phrazia
- Nouveaux outils : `scripts/cdp.py` (client CDP sur Chrome port 9222 : list/open/eval/
  snap/file/shot, origine desactivee pour passer le rejet --remote-allow-origins) et
  `scripts/yt_upload.py` (publication YouTube Studio automatique a partir de
  videos/ready + videos/metadata) + `scripts/yt_wait.py` (attend la fin du traitement).
- Lot d'essai PUBLIKE en public : toon_001 -> shorts/cp0QhFdEWkc, toon_002 ->
  shorts/-DTTO7T_bpw, toon_003 -> shorts/r2hgR0cxFvU. Historique :
  `logs/youtube_posts.json` (lu par yt_upload.py pour ne PAS republier un meme fichier).
- Réglages retenus : titre = meta title + " #shorts" (100 car. max), description =
  "meta - episode N de FactVibes Toons." + hashtags utiles (sans #fyp/#pourtoi) +
  #shorts, audience = "Non, pas concue pour les enfants" (YouTube présellectionne OUI),
  visibilite = Publique. JAMAIS d'identifiant interne (auto_/toon_) dans le texte visible.
- Pieges : le bouton "Suivant" est brievement inactif apres chaque sauvegarde (reessayer
  90 s avant d'abandonner) ; la confirmation "Video mise en ligne" n'apparait pas si le
  traitement SD est encore en cours (boite "Traitement de la video" a la place, la video
  passe publique seule) ; le champ input[file] n'existe qu'apres le clic "Importer des
  videos" et n'est remplissable que via DOM.setFileInputFiles (jamais par JS).
- Commande : `python scripts/yt_upload.py toon_004 auto_137 ...` (Chrome + port 9222 +
  session YouTube Studio connectes).

## 15/10/2026 - ORDRE DU PATRON : CROSS-POST TikTok -> YouTube (Phrazia), 3/jour puis 6/jour
- RÈGLE : ne JAMAIS créer de nouvelles vidéos pour YouTube. Réutiliser UNIQUEMENT celles
  d�j� pr�par�es et POST�ES sur TikTok (FactVibes). Z�ro doublon.
- Cadence : 3/jour minimum le premier jour (lot d'essai, FAIT : toon_001/002/003),
  puis 6 videos/jour.
- Source de v�rit� TikTok : `videos/queue.json` (state=PUBLISHED, 49 au 15/10).
  Candidates = PUBLISHED - d�j� sur YouTube (`logs/youtube_posts.json`).
- ANTI-DOUBLON DOUBLE : par video_id ET par titre normalis� (emoji/punct/#shorts
  retir�s) compar� aussi aux titres live de la chaîne YouTube (onglet Studio).
- `python scripts/yt_upload.py --daily` : respecte le quota du jour (3 le 15/10,
  6 ensuite), choisit les candidates automatiquement, met � jour l'historique.
- �CART CONSTAT� : TikTok Studio live affiche 46 publications, la file locale 49
  PUBLISHED. Ex. auto_122 est EN LIGNE sur TikTok mais marqu�e FAILED localement
  (« publication sans preuve »). Cons�quence : la file locale est une approximation ;
  v�rifier sur TikTok Studio avant d'affirmer qu'une vid�o n'est pas en ligne.


## 15/10/2026 - YOUTUBE : objectif 6/jour ATTEINT (6 shorts publies sur Phrazia)
- Bilan du jour : toon_001, toon_002, toon_003 (lot du matin) + video_003, video_002,
  video_001 (lot de l apres-midi, ordre du patron « trois autres = 6/jour »).
  Tous en Publique / Non concue pour les enfants, visibles dans Studio.
- URLs : cp0QhFdEWkc, -DTTO7T_bpw, r2hgR0cxFvU, fIpIfXNBs6k, ZiMNrG_9RGQ, ag24BKdI0rI
  (tout dans logs/youtube_posts.json, 6 entrees = anti-doublon operationnel).
- QUOTA mis a jour dans scripts/yt_upload.py : QUOTA_INITIAL = 6 (des le 1er jour).
- LECON TECHNIQUE : le bouton « Suivant » reste DESACTIVE pendant l import / le
  traitement, parfois plus de 5 minutes. La boucle de navigation attend desormais
  10 min max (300x2 s) et journalise la progression ([nav i] etat : import X%).
- Astuce fermeture : la boite « Video mise en ligne » se ferme via le bouton texte
  « Fermer » ; le formulaire d upload via le bouton icone « Enregistrer et fermer »
  (aria-label exact).
- 46 candidates restantes ; les 6 prochaines (demain) : auto_001, auto_002, via_000,
  toon_004, via_001, via_002. Lancer avec : python scripts/yt_upload.py --daily

## 16/10/2026 (soir) — CAUSE RACINE DES ECHECS TIKTOK + CADENCE 3/JOUR

**Bug Chrome/Selenium trouve (apres minuit 15->16/10)** : `element.text` renvoie VIDE
et `is_displayed()` rend False sur des elements pourtant visibles (mesure : body 1647
car. en innerText vs .text vide ; editeur 757x62 visible + is_displayed=False).
Cascade : "import non terminé" (page_says toujours faux) + fenetres "Publier maintenant"
jamais cliquees + clic Publier sur un doublon invisible -> "publication sans preuve".

**Correctifs (video_pipeline/publish_studio.py)** :
- body_text / _field_text : lecture en JS `innerText` (JS execute_script) ;
- click_button : matching + clic via JS sur libelle visible ;
- editor() : visibilite testee en JS (rect>0 + visibility) ;
- clic "Publier" : noeud VISIBLE choisi + verification d'effet reel (navigation,
  bouton parti/desactive, fenetre de confirmation), sinon reessai ;
- studio.py : PUBLISHED_SUSPECT n'est PLUS ecrase en FAILED (securite anti-doublon).

**Cadence TikTok portee a 3/jour** (ordre du patron) : config.json -> posts_per_day=3,
creneaux 17:00/17:30/18:00 UTC, garanties horaires 1 a 12:00 / 2 a 15:00 / 3 a 21:00.

**Banque enrichie** : 6 scenarios NEUFS G37-G42 dans factory.py (auto_145 -> auto_168) :
thermostat guerre froide / formulaire pour obtenir un formulaire / ministre inaugure
une salle inexistante / distributeur qui garde la monnaie / carte de fidélité /
repondeur "votre appel est important". Sujets verifies 1 par 1 contre G1-G36 (aucun
doublon de scenario). 24 episodes, 1 variante publiable par famille (doublon visuel).

**Posts du 16/10 (3/3, preuve "presente dans Contenu")** :
- 19:17 auto_145 "LE THERMOSTAT EST EN GUERRE FROIDE" (G37)
- 19:50 auto_149 "POUR AVOIR UN FORMULAIRE IL FAUT UN FORMULAIRE" (G38)
- 20:23 auto_153 "L'INAUGURATION DE QUELQUE CHOSE QUI N'EXISTE PAS" (G39, en examen)
Buffer demain : auto_157 (G40) / auto_161 (G41) / auto_165 (G42) deja rendus en READY.

**Reconciliation** : auto_122 repasse PUBLISHED (etait echoue a tort).

**YouTube** : toon_004 reste en BROUILLON (quota 6/jour atteint) — a publier demain.
Questions ouvertes au patron : video_001/002/003 supprimes de YouTube par ses soins ?

## 18/10/2026 — Recyclage TikTok → YouTube (ordre du patron : 3 matin + 3 après-midi, zéro doublon)

**Procédure enregistrée sur GitHub** : commit `235efa2` (docs/PROCEDURE_YOUTUBE.md + outillage
yt_upload/cdp/orchestrateur), puis `7c4895a` (durcissement anti-panne : RSS = vérité).

**Inventaire** : 48 vidéos TikTok éligibles sans aucun doublon (identifiant + titre normalisé,
confrontés à l'historique ET au contenu live de la chaîne ET au RSS public).

**Corrections faites aujourd'hui**
- toon_004 « Le prix de la tomate » : en ligne depuis le 16/10 avec le titre brut « toon 004 »
  et aucune description (règle des identifiants violée) → titre + description corrigés,
  vérifié publiquement (RSS + oEmbed).
- auto_002 « Le mail du vendredi (le planning) » : confirmée SUPPRIMEE de YouTube (page
  d'édition en erreur après rechargement + absente de la liste Contenu, deux vérifications) →
  marquée SUPPRIMEE comme video_001/002/003. → Question au patron : est-ce toi qui supprimes ?
  Si oui, je ne republie pas ; si non, remise en ligne possible (demande de validation).

**Lot du MATIN — 3/3 publiées et vérifiées publiquement**
- via_001 « Le message à 23 h 43 » → https://youtube.com/shorts/Oj6ahifC27U
- via_002 « POV : le voleur du frigo de bureau » → https://youtube.com/shorts/z6FpiZoKOyM (164 vues)
- via_003 « 3 h du matin au bureau » → https://youtube.com/shorts/SgmjZX7ZCTM

**Incidents du jour (tous résolus, correctifs poussés)**
1. Premier lancement `--daily` bloqué 15 min : get_tab() réutilisait le premier onglet Studio
   trouvé (ici une page /edit sans bouton d'import) ; de plus la liste Shorts Studio fait
   parfois geler le renderer. → navigation systématique vers /videos/upload avant chaque vidéo.
2. via_002 publiée par l'assistant MAIS la confirmation n'a pas été détectée (dialogue non
   visible) → rejetée à tort. → double signal (dialogue ou état « d=ud ») + VÉRIFICATION RSS
   publique après chaque tentative : le flux public est la seule vérité.
3. via_001 (1er essai) bloqué dans l'assistant, via_003 sans champ fichier : état empoisonné
   par le wizard précédent → état propre (re-navigation + fermeture des boîtes) entre chaque vidéo.

**Lot de l'APRÈS-MIDI programmé ~14h45** : via_004 « La dernière note vocale », via_005
« La voyante du dimanche », via_006 « Le Ministre plat-iste » (résultat à confirmer).

État en cours de journée : chaîne Phrazia = 9 vidéos publiées. Quota YouTube du jour : 3/6 consommés.

## 19/10/2026 — Journée complète : TikTok 3/3 + YouTube 3/3

**CONTEXTE** : banque TikTok épuisée (0 post le matin, alerte « la BANQUE est épuisée » en boucle). Ordre du soir du patron : poster des vidéos TikTok en vérifiant mille fois l'absence de doublons.

**NOUVEAUX SCÉNARIOS (G43-G48, 24 épisodes)** — 6 situations inédites vérifiées une à une contre les 82 sujets déjà produits : parking « cinq minutes » depuis 3 h, cantine et plat du jour fantôme, logiciel de pointage en retard avant l'arrivée, collègue « tu as deux secondes ? », imprimante sans toner, dernière modification à 18 h. Vérification anti-doublon multi-couches (titres usine + métadonnées + légendes TikTok publiées + scripts + familles + unicité interne) : AUCUN DOUBLON. Poussé GitHub d373fd2.

**BUG CORRIGÉ** : le scénario G46 utilisait le personnage « josette » sur le décor OFFICE (casting autorisé : kevin + fournier) → KeyError à chaque tentative de rendu, ce qui bloquait auto_181 et privait toute la famille d'un tour. Réparé (fournier à la place), poussé GitHub 941d37a. Preuve : auto_181 rendu → prêt.

**TIKTOK 19/10 : 3/3 publiés, audit live du compte OK**
- 19:20 — auto_169 « LE PARKING « CINQ MINUTES » DEPUIS TROIS HEURES » — https://www.tiktok.com/@factivibeparano/video/7698429964554669334
- 19:53 — auto_173 « LE PLAT DU JOUR N'EXISTE PLUS DEPUIS HIER » — https://www.tiktok.com/@factivibeparano/video/7698438489725046038
- 20:27 — auto_177 « LE LOGICIEL DE POINTAGE ME MET EN RETARD » — https://www.tiktok.com/@factivibeparano/video/7698447366508088598
- Légendes propres (aucun identifiant interne). Tampon pour demain : 3 vidéos prêtes (auto_181, auto_185, auto_189).

**YOUTUBE : lot de l'après-midi du 18/10 rattrapé, 3/3 publiés et vérifiés publics (oEmbed)**
- via_004 « La dernière note vocale #shorts » — https://youtube.com/shorts/X_6HbFm6EJE
- via_005 « La voyante du dimanche #shorts » — https://youtube.com/shorts/-WVgMfOxCJY
- via_006 « Le Ministre plat-iste #shorts » — https://youtube.com/shorts/zHKXyn2m0NI
- Incident : premier essai avorté (onglet Studio gelé, renderer figé — incident connu). via_004 était resté en brouillon non publié (donc aucun doublon public possible). Onglet fermé, lot relancé sur onglet neuf : 3/3 OK. Un brouillon orphelin de via_004 subsiste dans le Studio (hygiène seule, le contrôle RSS en rend la publication impossible deux fois).

**QUESTION TOUJOURS EN ATTENTE (posée le 18/10)** : est-ce toi qui supprimes les vidéos YouTube (video_001/002/003 + auto_002, marquées SUPPRIMÉES dans l'historique) ? Si oui, je ne les republie jamais. Si non, dis-moi et je les remonte.
