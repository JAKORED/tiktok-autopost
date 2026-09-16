# TikTok AutoPost

Système automatisé 24/7 qui cherche du contenu viral libre de droits, le télécharge, l'édite, et le publie sur TikTok tous les jours.

## Architecture (6 agents)

```
┌─────────────────────────────────────────────────────────┐
│                    main.py (Scheduler)                  │
│            Tourne 24/7 - planifie les posts             │
└─────────────────────────────────────────────────────────┘
                          │
    ┌─────────────────────┼─────────────────────┐
    ▼                     ▼                     ▼
┌──────────┐      ┌──────────────┐      ┌──────────────┐
│  Agent 1 │      │   Agent 2    │      │   Agent 3    │
│ Content  │ ───► │  Downloader  │ ───► │ Video Editor │
│  Finder  │      │  (cloud)     │      │  (FFmpeg)    │
└──────────┘      └──────────────┘      └──────────────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │   Agent 4    │
                                          │    TikTok    │
                                          │  Publisher   │
                                          └──────────────┘
                                                 │
                                      ┌──────────┴─────────┐
                                      ▼                    ▼
                                ┌────────────┐    ┌─────────────┐
                                │  Agent 5   │    │   Agent 6   │
                                │  Fallback  │    │ Scheduler & │
                                │  (secours) │    │ Redondance  │
                                └────────────┘    └─────────────┘
```

## Installation locale

### 1. API Keys (gratuites)

| Service | Lien | Usage |
|---------|------|-------|
| **Pexels** | https://www.pexels.com/api/ | Vidéos libre de droits ✔ |
| **Pixabay** | https://pixabay.com/api/docs/ | Vidéos libre de droits ✔ |
| **TikTok** | https://developers.tiktok.com/ | Publication (approbation requise) |

### 2. Installer tout

```bash
cd tiktok-autopost
python setup.py
```

Le script `setup.py` te guide étape par étape pour configurer tes clés API.

### 3. Installer FFmpeg (pour l'édition vidéo)

- Télécharge : https://ffmpeg.org/download.html
- Sur Windows : décompresse, ajoute `bin/` au PATH

### 4. Tester

```bash
python main.py test
```

### 5. Publier une vidéo

```bash
python main.py run
```

### 6. Lancer en continu (scheduler 24/7)

```bash
python main.py
```

## Publication TikTok - 2 méthodes

### Méthode A : API officielle (recommandée mais approbation requise)

1. Va sur https://developers.tiktok.com/
2. Crée un compte développeur + une app
3. Active le produit **Content Posting API**
4. Soumets ton app pour **audit** (approbation)
5. Obtiens ton `client_key`, `client_secret`, `access_token`, `refresh_token`
6. Mets-les dans ton `.env`

**Avant approbation** : la visibilité est limitée à "privé".
**Après approbation** : publications publiques.

### Méthode B : Selenium (sans API, nécessite installation Chrome + cookies)

```bash
pip install selenium playwright
playwright install chromium
```

1. Connecte-toi manuellement à TikTok une fois dans Chrome
2. Exporte tes cookies dans `config/tiktok_cookies.json`
3. Le système poste automatiquement ensuite

## Déploiement gratuit 24/7 (Oracle Cloud)

Le meilleur hébergement **gratuit à vie** pour ce type de script :

1. Crée un compte : https://www.oracle.com/cloud/free/
2. Crée une VM `Ampere A1` ou `VM.Standard.E2.1.Micro` (gratuit)
3. Connecte-toi en SSH
4. Exécute :

```bash
# Sur la VM (Ubuntu)
sudo apt update && sudo apt install -y python3-pip ffmpeg git
pip install requests python-dotenv schedule Pillow pydub
git clone https://github.com/ton-repo/tiktok-autopost.git
cd tiktok-autopost
python3 setup.py
nohup python3 main.py > logs/nohup.log 2>&1 &
```

Le script tourne alors 24/7 sans interruption.

## Commandes utiles

```bash
python main.py            # Scheduler 24/7
python main.py run        # Un run complet (test manuel)
python main.py test       # Test la recherche de contenu
python main.py queue      # Publie les vidéos en attente
python main.py health     # Rapport de santé des agents
python main.py stats      # Statistiques journalières
```

## Fichiers de logs

```
logs/
├── autopost_20240916.log      # Logs journaliers
├── posted_videos.json         # Historique des contenus téléchargés
├── post_history.json          # Historique des publications
├── post_queue.json            # File d'attente (si échec)
├── agent_health.json          # Santé des agents
└── daily_stats.json           # Statistiques quotidiennes
```

## Structure

```
tiktok-autopost/
├── main.py                    # Ordonnateur principal (scheduler)
├── setup.py                   # Configuration initiale guidée
├── config.json                # Configuration du système
├── .env                       # API keys (à remplir)
├── agents/
│   ├── content_finder.py      # Agent 1 - Recherche
│   ├── downloader.py          # Agent 2 - Téléchargement
│   ├── video_editor.py        # Agent 3 - Édition
│   ├── tiktok_publisher.py    # Agent 4 - Publication
│   └── fallback_agent.py      # Agent 5 - Secours
├── temp/                      # Fichiers temporaires
├── output/                    # Vidéos finales
└── logs/                      # Journaux
```

## Limites légales importantes

- **ToS TikTok** : la publication automatisée est autorisée **uniquement** via l'API officielle. Le Selenium est une zone grise.
- **Contenu** : les vidéos de Pexels/Pixabay sont libres de droits mais TikTok favorise le contenu original. Ajoute ton propre texte/effet pour rester dans l'esprit de la plateforme.
- **IA générée** : si tu génères du contenu avec IA, TikTok exige le flag `is_aigc`.