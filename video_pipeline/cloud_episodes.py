"""5 épisodes originaux « FactVibes Toons » — plans vidéo IA (Wan 2.2 sur GPU cloud) + narration.

Choix de conception (voir videos/research/cartoon_trends.md) :
- personnages ANIMAUX : plus faciles à garder cohérents d'un plan à l'autre, format qui marche
  (cf. Chikn Nuggit : animaux à personnalité, humour absurde/décalé) ;
- un plan par phrase, ~30-40 s, hook dans les 3 premières secondes, chute finale ;
- sujets mêlés : travail/humour, société, politique (satire d'un royaume fictif), industrie.
Aucune personne réelle, aucun parti, aucun personnage protégé.
"""

NARRATORS = {
    "remy":     dict(voice="fr-FR-RemyMultilingualNeural",     rate="+7%", pitch="+0Hz"),
    "henri":    dict(voice="fr-FR-HenriNeural",                rate="+2%", pitch="-3Hz"),
    "denise":   dict(voice="fr-FR-DeniseNeural",               rate="+8%", pitch="+0Hz"),
    "vivienne": dict(voice="fr-FR-VivienneMultilingualNeural", rate="+8%", pitch="+0Hz"),
}

GENERIC_TAGS = ["#fyp", "#pourtoi", "#humourfr", "#dessinanime", "#animationia", "#drole", "#FactVibesToons"]

STYLE = ("Pixar-style 3D animated cartoon, vibrant saturated colors, soft cinematic lighting, "
         "expressive characters, smooth fluid motion, high quality, vertical composition.")

EPISODES = [
    dict(
        id="cloud_001", ep=1, narrator="remy", accent=(255, 214, 64), style=STYLE,
        headline="LES 5 COLLÈGUES|DE CHAQUE RÉUNION",
        title="Les 5 collègues de chaque réunion", topic="travail / humour",
        tags=["#travail", "#bureau", "#reunion", "#entreprise"],
        beats=[
            dict(text="Dans chaque réunion, il y a cinq collègues. Tu les connais tous.",
                 shot="wide shot of a bright modern meeting room, five cartoon animals sitting around a table: a sloth, an owl, a peacock, a shark in a suit and a hamster, camera slowly pushing in"),
            dict(text="Le paresseux dort les yeux ouverts, et il hoche la tête quand même.",
                 shot="close-up of a sleepy cartoon sloth in a shirt nodding slowly with half-closed eyes in a meeting room"),
            dict(text="Le hibou pose une question qui prolonge la réunion d'une heure.",
                 shot="cartoon owl with round glasses raising a wing, dramatic dolly zoom, meeting room, wall clock hands spinning fast"),
            dict(text="Le paon présente ses résultats. Personne n'a rien demandé.",
                 shot="proud cartoon peacock in a suit presenting a colorful chart, spreading his tail feathers, confetti falling"),
            dict(text="Le requin dit : point rapide. Et parle quarante minutes.",
                 shot="cartoon shark in a business suit talking energetically at a whiteboard, clock hands spinning quickly"),
            dict(text="Le hamster note tout, dans un carnet que personne ne lira jamais.",
                 shot="cute cartoon hamster scribbling furiously in a tiny notebook, close-up, pencil moving fast"),
            dict(text="Et toi, tu es celui qui regarde l'heure.", punch=True,
                 shot="cartoon character glancing at a wrist watch in a boring meeting, deadpan face, slow camera zoom"),
        ],
    ),
    dict(
        id="cloud_002", ep=2, narrator="henri", accent=(120, 230, 255), style=STYLE,
        headline="L'INFLATION|EXPLIQUÉE|PAR UN PIGEON",
        title="L'inflation expliquée par un pigeon", topic="société / pouvoir d'achat",
        tags=["#societe", "#inflation", "#pouvoirdachat", "#economie"],
        beats=[
            dict(text="Une miette coûtait une miette. Puis vint l'inflation.",
                 shot="close-up of a chubby cartoon pigeon wearing a tiny tie standing on a city bench, talking to the camera, warm sunset"),
            dict(text="Aujourd'hui, la même miette coûte trois miettes.",
                 shot="cartoon pigeon shocked looking at a price sign with three crumbs in front of a bakery window, comedic"),
            dict(text="Le boulanger dit que c'est à cause de la conjoncture.",
                 shot="cartoon baker cat in an apron shrugging behind a bakery counter full of pastries, bright cozy shop"),
            dict(text="La conjoncture, c'est un mot compliqué pour dire : c'est comme ça.",
                 shot="cartoon pigeon making air quotes with its wings, sarcastic face, close-up"),
            dict(text="Moi, j'ai trouvé la solution : je vole les sandwichs des touristes.",
                 shot="cartoon pigeon swooping down to grab a sandwich from a tourist's hand, dynamic action, city street"),
            dict(text="Pas légal, mais rentable. Demain, la miette coûtera peut-être… une miette.", punch=True,
                 shot="cartoon pigeon flying away triumphantly with a sandwich, sunset skyline, slow motion"),
        ],
    ),
    dict(
        id="cloud_003", ep=3, narrator="denise", accent=(255, 120, 100), style=STYLE,
        headline="LE COMITÉ POUR|CRÉER|UN COMITÉ",
        title="Le comité pour créer un comité", topic="politique (satire d'un royaume fictif)",
        tags=["#satire", "#royaumedesanimaux", "#lionroi", "#administration"],
        beats=[
            dict(text="La rivière déborde, dit le lion roi. Créons un comité.",
                 shot="majestic cartoon lion wearing a golden crown in a flooded animal kingdom, river overflowing, dramatic stormy sky"),
            dict(text="Un comité pour étudier le problème.",
                 shot="cartoon lion signing a huge scroll with a feather pen while ministers animals watch, grand hall"),
            dict(text="Un comité pour choisir les membres du comité.",
                 shot="cartoon fox and badger ministers arguing over a very long list, tower of papers, comedic"),
            dict(text="Un comité pour attendre le rapport du comité.",
                 shot="cartoon animals sitting around a huge table with mountains of paperwork, one falling asleep"),
            dict(text="Pendant ce temps, la rivière continue de monter.",
                 shot="cartoon water rising inside the hall, animals on the table lifting their feet, humorous"),
            dict(text="Un an plus tard, le rapport arrive : il y avait une rivière.", punch=True,
                 shot="cartoon lion reading a thick report with a deadpan expression while standing in water, slow zoom in"),
        ],
    ),
    dict(
        id="cloud_004", ep=4, narrator="vivienne", accent=(90, 230, 255), style=STYLE,
        headline="BOB|NE DORT|JAMAIS",
        title="Bob, le robot qui ne dort jamais", topic="industrie / robots",
        tags=["#industrie", "#robot", "#usine", "#travail"],
        beats=[
            dict(text="Bob n'a jamais dormi. Aujourd'hui, on le remplace.",
                 shot="friendly cartoon industrial robot with a square head and glowing blue eyes on a factory floor, orange sparks"),
            dict(text="Il soude, il visse, il emballe. Mille pièces par heure.",
                 shot="cartoon factory robot with several arms assembling products on a fast conveyor belt, sparks, dynamic camera"),
            dict(text="Ses collègues humains, eux, prennent des pauses.",
                 shot="cartoon factory workers laughing with coffee cups at a break table, robot working in the background, warm light"),
            dict(text="La direction annonce un robot plus récent.",
                 shot="cartoon factory robot looking up at a sleek shiny new robot descending on a platform, dramatic light"),
            dict(text="Bob range ses outils, sans rien dire, comme toujours.",
                 shot="cartoon robot placing tools into a small box, slow sad movement, close-up of glowing blue eyes dimming"),
            dict(text="Le nouveau robot demande une pause dès le premier jour.", punch=True,
                 shot="shiny new cartoon robot sitting on a chair sipping a tiny cup while the old robot stares surprised, comedic"),
        ],
    ),
    dict(
        id="cloud_005", ep=5, narrator="remy", accent=(255, 170, 90), style=STYLE,
        headline="MON CHAT|EN VISIO",
        title="Mon chat en visio", topic="humour / télétravail",
        tags=["#teletravail", "#chat", "#visio", "#chatorange"],
        beats=[
            dict(text="Ma visio commence dans une minute. Mon chat a d'autres plans.",
                 shot="cartoon orange cat sitting on a desk next to a laptop showing a video call, cozy home office, morning light"),
            dict(text="Il marche sur le clavier. Trente-quatre lignes de q.",
                 shot="cartoon cat walking across a laptop keyboard, close-up of paws on the keys, comedic"),
            dict(text="Il montre son derrière à toute l'équipe.",
                 shot="cartoon cat turning around with its tail up in front of a laptop camera, comedic, home office"),
            dict(text="Mon chef demande : qui est-ce ? Je réponds : mon assistant.",
                 shot="cartoon cat wearing a tiny headset sitting seriously at a desk, deadpan expression, close-up"),
            dict(text="Il a fait plus de choses en trois minutes que moi en une semaine.",
                 shot="cartoon cat knocking a coffee mug off the desk in slow motion, dramatic, home office"),
            dict(text="Lui est en pause. Moi, je suis en retard.", punch=True,
                 shot="cartoon cat sleeping curled on a warm laptop keyboard peacefully, close-up, soft light"),
        ],
    ),
]
