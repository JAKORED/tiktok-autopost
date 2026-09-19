"""Scripts originaux de la série « FactVibes Toons » (personnages 100 % fictifs, aucune personne réelle).

Continuité de série : Kevin (l'employé) et Robo-Bob traversent plusieurs épisodes ; la « réunion »
est un gag récurrent. Humour = décalage / deadpan / répétition qui escalade (formats en vogue, cf.
videos/research/cartoon_trends.md).
"""

VOICES = {
    "kevin":    dict(voice="fr-FR-RemyMultilingualNeural", rate="+6%",  pitch="+2Hz"),
    "fournier": dict(voice="fr-FR-DeniseNeural",           rate="+8%",  pitch="+0Hz"),
    "ministre": dict(voice="fr-FR-HenriNeural",            rate="-2%",  pitch="-4Hz"),
    "josette":  dict(voice="fr-FR-EloiseNeural",           rate="-4%",  pitch="+7Hz"),
    "bob":      dict(voice="fr-FR-HenriNeural",            rate="-6%",  pitch="-28Hz", robot=True),
}

GENERIC_TAGS = ["#fyp", "#pourtoi", "#humour", "#dessinanime", "#cartoon", "#drole", "#FactVibesToons"]

EPISODES = [
    dict(
        id="toon_001", ep=1, set="office", left="kevin", right="fournier",
        accent=(255, 214, 64),
        headline="CETTE RÉUNION|AURAIT PU ÊTRE|UN MAIL",
        title="La réunion qui aurait pu être un mail",
        topic="travail / bureau",
        tags=["#travail", "#bureau", "#reunion", "#entreprise"],
        lines=[
            dict(who="fournier", emo="happy",   text="Bonjour à tous ! Merci d'être venus à cette réunion très importante."),
            dict(who="kevin",    emo="worried", text="C'est sur quoi, Madame Fournier ?"),
            dict(who="fournier", emo="happy",   text="Pour décider de la date de la prochaine réunion."),
            dict(who="kevin",    emo="neutral", text="Ça tenait dans un mail."),
            dict(who="fournier", emo="angry",   text="Non. Un mail, ça ne se planifie pas en réunion."),
            dict(who="kevin",    emo="worried", text="On vient de perdre une heure."),
            dict(who="fournier", emo="smug",    text="Je vous envoie un mail de synthèse. Après une réunion de suivi."),
            dict(who="kevin",    emo="neutral", text="Je démissionne. Par mail.", punch=True),
        ],
    ),
    dict(
        id="toon_002", ep=2, set="stage", left="ministre", right="josette",
        accent=(255, 120, 100),
        headline="LA PROMESSE|HISTORIQUE",
        title="La promesse historique du ministre",
        topic="politique (satire générique)",
        tags=["#politique", "#satire", "#promesse", "#societe"],
        lines=[
            dict(who="ministre", emo="happy",   text="Chers concitoyens, je vous fais une promesse historique : demain, tout ira mieux !"),
            dict(who="josette",  emo="neutral", text="Vous avez dit la même chose hier, monsieur le ministre."),
            dict(who="ministre", emo="happy",   text="Hier, c'était la promesse d'hier. Celle-ci est toute neuve."),
            dict(who="josette",  emo="worried", text="Et l'ancienne promesse, elle est où ?"),
            dict(who="ministre", emo="worried", text="Elle est en cours d'évaluation. Par un comité. Qui se réunira."),
            dict(who="josette",  emo="angry",   text="Quand ça ?"),
            dict(who="ministre", emo="smug",    text="Après les prochaines élections. Merci, bonne journée !", punch=True),
        ],
    ),
    dict(
        id="toon_003", ep=3, set="factory", left="bob", right="kevin",
        accent=(90, 230, 255),
        headline="LE ROBOT|VA TE REMPLACER",
        title="Le robot, l'IA et la réunion",
        topic="industrie / intelligence artificielle",
        tags=["#industrie", "#ia", "#robot", "#travail"],
        lines=[
            dict(who="bob",   emo="neutral", text="Bonjour Kevin. Cette heure, j'ai assemblé mille pièces."),
            dict(who="kevin", emo="neutral", text="Bravo Bob. Moi, j'ai réussi à ouvrir mon tableur."),
            dict(who="bob",   emo="neutral", text="Je ne dors pas, je ne mange pas, je ne prends jamais de pause."),
            dict(who="kevin", emo="angry",   text="Ça va, on a compris, tu es parfait !"),
            dict(who="bob",   emo="worried", text="Plus pour longtemps. Ils me remplacent lundi par une intelligence artificielle."),
            dict(who="kevin", emo="worried", text="Quoi ? Mais alors, nous aussi, on est remplacés !"),
            dict(who="bob",   emo="neutral", text="Non. Elle a déjà planifié une réunion pour en discuter.", punch=True),
        ],
    ),
    dict(
        id="toon_004", ep=4, set="supermarket", left="josette", right="kevin",
        accent=(255, 230, 90),
        headline="47 EUROS|POUR UNE TOMATE",
        title="Le prix de la tomate",
        topic="société / pouvoir d'achat",
        tags=["#societe", "#inflation", "#courses", "#pouvoirdachat"],
        lines=[
            dict(who="kevin",   emo="neutral", text="Ça fait quarante-sept euros, madame."),
            dict(who="josette", emo="worried", text="Pour un paquet de pâtes, un yaourt et une tomate ?"),
            dict(who="kevin",   emo="smug",    text="La tomate est en édition limitée."),
            dict(who="josette", emo="angry",   text="De mon temps, avec ce prix, on achetait le magasin !"),
            dict(who="kevin",   emo="neutral", text="De votre temps, le magasin coûtait vingt francs."),
            dict(who="josette", emo="happy",   text="Alors vous avez raison. Donnez-moi la tomate. Je la mets dans mon testament.", punch=True),
        ],
    ),
]
