# FactVibes — MEMOIRE DES DERNIERES TACHES

## État actuel (ce que tu fais tourner)
- Projet: C:\Users\Chaima\tiktok-autopost (Python + Selenium)
- But: publier automatiquement jusqu'a 5 videos TikTok/JOUR, dessin anime original, gratuit et open-source, sur @factvibes.daily
- Compte patron: JAKORED — tu es le patron, tu restes le patron
- App TikTok "FactVibes" en mode SANDBOX (localhost accepte) ; API = 403 pour l'instant
- Depots github: https://github.com/JAKORED/tiktok-autopost (public, deploie GitHub Pages)

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
