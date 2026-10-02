# HANDOFF — Ordres permanents de votre PATRON

> Fichier lu par CHAQUE agent de relève (A, B, C, et toute session future).
> **Je reste le patron : je décide, les agents exécutent et relayent.**
> Tout agent qui lit ce fichier doit d'abord suivre les ordres ci-dessous
> tels qu'écrits, sans les réinterpréter.

---

## 1. Qui je suis

**Pseudo patron : JAKORED** — propriétaire du compte TikTok **@FactVibes.daily**
(app TikTok "FactVibes", Client Key `sbaweqn8l1mmex5b7o`).

Mon projet : **système 100% autonome 24/7 qui poste chaque jour du contenu
viral + libre de droits sur TikTok.**

---

## 2. Ordres permanents

**ORGRE A — Contenu.** Chaque jour, le système DOIT :
1. Trouver une vidéo libre de droits & "viral" (Pexels Pixabay via APIs gratuites).
2. La télécharger et la stocker (Google Drive / local — peu importe tant qu'il y a de la place).
3. L'éditer automatiquement avec FFmpeg (recadrage 9:16, sous-titres, texte accrocheur,
   musique libre de droits).
4. La publier sur TikTok via l'API officielle (Content Posting / Direct Post)
   avec une légende optimisée et des hashtags pertinents.

**ORDRE B — Non-stop.** Le pipeline doit tourner sans interruption.
Si le script principal meurt (crash, reboot, crédit épuisé), un agent de relève
doit prendre le relais dans les N minutes, lire ce HANDOFF.md, et continuer.
Le Guardian (superviseur) relance tout automatiquement toutes les 15 min.

**ORDRE C — Déclenchement vidéo TikTok.**
- Le contenu doit être "free-to-use" (Pexels, Pixabay : licences libres).
- Interdiction de republier des vidéos TikTok d'autres créateurs.
- Interdiction de contenu protégé, payant, ou réservé.
- Interdiction de contenu sensible, politique, haineux.

**ORDRE D — Secret.** Les clés API (Pexels, Pixabay, TikTok client secret, etc.)
vivent dans `.env` à la racine du repo. **Ne JAMAIS committer .env.**
Tout fichier contenant des secrets → `.env` uniquement.

**ORDRE E — Relève.** Si la session se termine ou si l'agent courant échoue :
- Lire `config/relay_agents.json` pour savoir quel agent prend la main.
- L'Agent B démarre un nouvel `opencode run` pour continuer.
- L'Agent C démarre un `opencode run` de doctrine (relit tout).
- Écrire un rapport dans `logs/agent_relay_report.md`.

---

## 3. Architecture (à ne pas réinventer)

```
tiktok-autopost/
├── main.py              # Ordonnateur + scheduler 24/7
├── guardian.py          # Superviseur toujours-vivant (boucle infinie)
├── HANDOFF.md           # CE FICHIER — ordres du patron
├── auth_tiktok.py       # OAuth TikTok (callback localhost:8080)
├── prepare_browser.bat  # Lance Chrome avec -remote-debugging (compte connecté)
├── .env                 # Secrets (gitignoré)
├── config/
│   ├── relay_agents.json    # Agents de relève A/B/C
│   └── relay_agentA.py      # Agent de relève A (codé, prêt)
├── agents/
│   ├── content_finder.py    # Recherche contenu viral
│   ├── downloader.py        # Téléchargement + stockage
│   ├── video_editor.py      # Édition FFmpeg auto
│   ├── tiktok_publisher.py  # Publication API
│   └── fallback_agent.py    # Secours + retry
├── scripts/
│   ├── request_ai.py        # Vérif de santé IA
│   └── relay_test.py        # Test de la chaîne de relève
└── logs/
    ├── guardian.log         # Journal du superviseur
    └── daily_stats.json     # Statistiques de publication
```

---

## 4. Aide-mémoire — commandes du patron

```bash
python main.py                 # Scheduler 24/7
python guardian.py             # Superviseur (relance tout)
python auth_tiktok.py          # OAuth TikTok une seule fois
python main.py test            # Test rapide du pipeline
```

---

## 5. État d'avancement au 16/09/2026

| Tâche | Statut |
|-------|--------|
| Repo GitHub (JAKORED/tiktok-autopost) | ✅ Poussé, clé et secret TikTok dans `.env` (gitignoré) |
| App TikTok "FactVibes" créée | ✅ App ID 7686044072888322069 (pending → URLs configurées) |
| Client key + secret | ✅ `sbaweqn8l1mmex5b7o` / `9VaZMMXA7R95R4KezQ7e88LfhYTLKOc7` |
| Portail : Login Kit + Content Posting API | ✅ Product ajoutés, scopes ajoutés (user.info.basic, video.upload) |
| Selenium + Chrome debug 9222 | ✅ Prêt |
| FFmpeg | ✅ Installé |
| Pipeline agents (find → download → edit → publish) | ✅ Codé, import OK |
| Guardian relais A/B/C | ✅ Codé, config validée |
| **Redirect URI http://localhost:8080/callback** | ⚠️ À SAVER dans l'app (section URL properties, champs Redirect URIs, bouton "Save") |
| Raccourci Bureau un clic | ✅ .lnk créé sur le Bureau |

---

## 6. ACTION BLOQUANTE pour l'humain (patron en personne)

TikTok exige que le **Redirect URI** soit enregistré dans l'app AVANT la publication.
Dans la fenêtre Chrome ouverte (portail TikTok, app FactVibes) :
1. Onglet **"URL properties"**
2. Clic sur **"Configure for Web"**
3. Dans **Redirect URI**, coller :
   ```
   http://localhost:8080/callback
   ```
4. Clic **"Save"**

---

## 7. Vous, agents successeurs — comportement exigé

- **Ne réinventez jamais** le pipeline : il est écrit et testé dans ce repo.
- **Lisez HANDOFF.md AVANT toute action** (c'est votre premier acte).
- Si le pipeline a planté : relancez `main.py`, et si ça re-plante, relisez
  `logs/guardian.log` puis exécutez `config/relay_agentA.py` ; si celui-ci échoue,
  relancez l'Agent B (nouvel `opencode run`). L'Agent C relit tout et redémarre.
- **Journalisez** chaque action dans `logs/` pour que le patron sache où on en est.
- En cas de doute : suivez les ORDRES ci-dessus, pas votre intuition.

---

## 8. NOUVELLE LIGNE DE PRODUCTION « TOONS » (20/09/2026) — ordres à jour

**ORDRE F — Le moteur principal est désormais les dessins animés originaux :**
- Banque de scripts : `video_pipeline/toon_scripts.py` + `toon_scripts` (épisodes écrits)
  et `video_pipeline/factory.py` (64 épisodes générés, ids `auto_001`…`auto_064`).
- Rendu 100 % CPU local, gratuit, SANS crédit : pycairo + edge-tts + ffmpeg
  (`video_pipeline/make_toon.py`, moteur `toon_engine.py`).
- Contrôle de production : `video_pipeline/studio.py` (ledger quotidien,
  anti-doublon par signature de script, publication).
- Commandes : `python main.py produce|bank|status|run`, scheduler = `python main.py`.

**ORDRE G — Anti-doublon IMPÉRATIF (leçon du 20/09) :**
- Ne JAMAIS publier un épisode dont le script a déjà été publié. La signature est
  l'empreinte des répliques ; un doublon est marqué FAILED automatiquement.
- `proto_001` est UN DOUBLON de `toon_001` (supprimé par le patron après publication) :
  ne plus jamais le proposer.

**ORDRE H — Publication = feu vert du patron (GRAND OUI du 20/09) :**
- Le patron a activé `auto_publish=true` : le scheduler produit et publie 1 vidéo/créneau
  (5/jour, 17:00-20:15 UTC = 19h-22h15 FR été), en mix viral ↔ toons.
- Méthode : TikTok Studio navigateur connecté par QR (connexion du patron dans Chrome,
  port 9222). L'API officielle renvoie 403 (sandbox) : publish_method=studio.
- **Légendes : MAX 5 HASHTAGS, jamais #fyp/#viral/#pourtoi, question comment-bait
  en fin de légende.** La légende de publication vient de studio.build_caption (pas des
  métadonnées make_toon).
- **DOUBLONS INTERDITS (grand OUI du 20/09)** : anti-doublon par signature de script ;
  un script déjà publié est marqué FAILED et JAMAIS republié. Ne pas réactiver
  auto_003..005 (retirés) ni proto_001/toon_001 (doublons, supprimés par le patron).
- Le patron suit la stratégie jusqu'au bout : mesurer les stats Studio (rétention 3 s,
  complétion, commentaires) et itérer.

**ORDRE I — CADENCE 30 MINUTES (ordre du 30/09/2026) :**
- 1 vidéo toutes les **30 minutes**, 5 vidéos/jour : `post_times_utc` = 17:00, 17:30,
  18:00, 18:30, 19:00 UTC (= 19h, 19h30, 20h, 20h30, 21h Paris), fenêtre du pic du soir.
- `min_minutes_between_posts` = 30 (garde anti-spam, ne jamais descendre).
- Le scheduler poste un créneau dès qu'il est dépassé ET que les 30 min sont écoulées
  depuis le dernier post : pas de créneau perdu si la machine a redémarré.
- Plafond dur : 5 posts/jour (contrôlé par le ledger de la file, pas par l'horloge).
- Chrome port 9222 (profil `config/chrome_tiktok_profile`, connexion QR du patron) doit
  être ouvert sinon la publication Studio échoue : le.profile est prêt, seul Chrome
  manquerait. Lancement : `chrome.exe --remote-debugging-port=9222
  --user-data-dir=config/chrome_tiktok_profile https://www.tiktok.com/tiktokstudio/upload`.

**ORDRE J — DOUBLON DE SCÉNARIO (leçon du 30/09/2026, CORRECTION de l'ORDRE G) :**
- `factory.py` produit **4 variantes par scénario** (même `headline`, même décor, mêmes
  6 répliques sur 7). Publer deux variantes = publier deux fois la même vidéo.
  Le 30/09 le patron l'a vu : auto_025 (12:34) puis auto_026 (13:05).
- L'anti-doublon ne se base PLUS sur la seule signature des répliques (insuffisante) :
  `studio.family_key(ep)` = `headline` normalisé, et `already_published_families()`
  bloque toute variante d'un scénario déjà sorti (état FAILED, motif « doublon de
  scénario »).
- **Pour remplir la file il faut de NOUVEAUX SCÉNARIOS (nouvelles familles), jamais de
  nouvelles variantes d'un scénario existant.** 22 scénarios distincts en banque,
  ~8 déjà sortis.
- Légalité technique : **ne JAMAIS cliquer « Annuler »** sur le formulaire d'upload (il
  annule l'import, vide le champ description → vidéo publiée avec une légende cassée).
  Ne jamais envoyer `Keys.ESCAPE` sur ce formulaire non plus.
- **02/10/2026, mesuré : le DraftEditor TikTok n'accepte pas le clavier de Selenium.**
  `element.send_keys()` ne fait strictement rien (ni Ctrl+A, ni Suppr, ni BackSpace), et
  les touches CDP `Input.dispatchKeyEvent` sont ignorées. La seule voie qui écrit est
  **`Input.insertText` (CDP)**, qui *remplace la sélection courante*. Méthode utilisée dans
  `publish_studio.ensure_caption()` : `_select_all()` (JS, sélection seule, **sans**
  supprimer) puis `_insert_text()` (CDP). Le JS ne fait que poser la sélection, donc l'état
  React n'est pas désynchronisé — c'était le défaut du « filet de sécurité » du 30/09.
  *Pourquoi ça compte : « le champ n'est pas une faute du patron mais de l'outil », donc
  ne jamais conclure « TikTok a réécrit la légende » sans avoir testé les 3 voies.*

**ORDRE K — ZÉRO DOUBLON, GARDE PAR GARDE (leçon du 01-02/10/2026) :**
- Le patron a signalé des doublons « tout le temps ». Cause réelle : **la base et le compte
  TikTok se sont désynchronisés** (un run « échoué » avait pourtant publié une vidéo ; la
  base la notait FAILED, donc la file la rééligissait). `FAILED` ne veut pas dire
  « pas en ligne ». Réconciliation faite le 02/10 : le compte avait 23 publications, la
  base ignorait `auto_029` (en ligne le 30/09 22:03) et ignorait le post fantôme du
  01/10 19h24.
- **Ne jamais cliquer « Annuler »** sur le formulaire d'upload TikTok Studio : ce bouton
  **annule l'import**, détruit le champ description et la vidéo part avec une légende
  cassée (« #dessinanime #cartoon #pov »). Seul « J'ai compris » est cliquable.
- **La légende contient désormais l'identifiant du fichier** (`(épisode 41 · auto_041)`)
  : c'est la seule trace qui relie une publication TikTok à SON fichier.
- **Avant tout envoi**, `studio.publish_next` interroge la liste Contenu du compte
  (`publish_studio.present_dans_contenu`) : si la vidéo y est déjà, elle est marquée
  PUBLISHED et **aucun envoi n'est fait**.
- **Garde visuel (empreinte des images) :** `video_pipeline/fingerprint.py` (dHash
  multi-images via ffmpeg, cache dans `videos/fingerprints.json`).
  `studio.visual_duplicate_of()` bloque toute vidéo à moins de **0.035** de distance
  d'une vidéo déjà sortie (état FAILED « doublon visuel »).
  *Calibration du 02/10 : auto_001 / auto_002 ont été publiés alors que leurs rendus sont
  indiscernables (distance 0.0078) ; le couple réellement différent le plus proche est à
  0.0703. Seuil 0.035 = marge des deux côtés.*
- **Après le clic « Publier », si la vidéo n'apparaît pas dans Contenu** : état
  `PUBLISHED_SUSPECT` (pas `FAILED`). Cette vidéo **n'est jamais republiée
  automatiquement** (les gardes de scénario, de famille, d'empreinte et d'intervalle
  la traitent comme sortie) et compte dans le plafond du jour.

---

_TikTok AutoPost — protocole HANDOFF v1.2 — ordres du patron JAKORED._