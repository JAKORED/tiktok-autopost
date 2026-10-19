"""Banque de scripts paramétriques « FactVibes Toons ».

Génère des dizaines d'épisodes originaux de la série (mêmes personnages, décors et voix
que toon_scripts.py : Kevin, Mme Fournier, le Ministre, Mamie Josette, Robo-Bob).
Humour : deadpan / décalage / escalade qui se retourne (formats en vogue 2026, cf.
videos/research/cartoon_trends.md + PRODUCTION_PLAN.md).

Aucun personnage réel, aucune source protégée : tout est rédigé ici.
Chaque épisode dure ~25-40 s, 7-8 répliques, hook dans la première ligne.
L'ordre des épisodes est déterministe : le render est reproductible.
"""

OFFICE = ("kevin", "fournier")
STAGE = ("ministre", "josette")
FACTORY = ("bob", "kevin")
MARKET = ("josette", "kevin")

ACCENTS = {
    "kevin_fournier": (255, 214, 64),
    "ministre_josette": (255, 120, 100),
    "bob_kevin": (90, 230, 255),
    "josette_kevin": (255, 230, 90),
}
SETS = {
    "kevin_fournier": "office",
    "ministre_josette": "stage",
    "bob_kevin": "factory",
    "josette_kevin": "supermarket",
}
GENERIC = ["fyp", "pourtoi", "humour", "dessinanime", "cartoon", "drole", "FactVibesToons"]


# Nombre de variantes produites par scénario. TOUS les groupes G1..G26 font exactement
# 4 variantes : même décor, mêmes personnages, mêmes 6 répliques sur 7 — visuellement
# c'est LA MÊME vidéo. Le groupe est donc l'identité du scénario (champ `family`).
VARIANTES_PAR_SCENARIO = 4


def _ep(no, pair, headline, title, topic, tags, lines, family=None):
    key = f"{pair[0]}_{pair[1]}"
    return dict(
        id=f"auto_{no:03d}", ep=no, family=family, set=SETS[key],
        left=pair[0], right=pair[1],
        accent=ACCENTS[key], headline=headline, title=title, topic=topic,
        tags=[f"#{t}" for t in tags], lines=[
            dict(who=w, emo=e, text=t, **({"punch": True} if p else {}))
            for (w, e, t, p) in lines
        ],
    )


def l_(who, emo, text, punch=False):
    return (who, emo, text, punch)


def build_factory_episodes():
    """Toutes les variantes de la banque (deterministe). id = auto_XXX."""
    eps, no = [], 0

    def add(e):
        nonlocal no
        no += 1
        # Identité du SCÉNARIO = le groupe de fabrication, PAS le headline.
        # Certains groupes mettaient le paramètre dans le headline (G2 « LA MACHINE À
        # CAFÉ EN PANNE/EN MAINTENANCE », G16 « LE PRIX DES PÂTES / DU BEURRE / DU CAFÉ /
        # DU PAIN ») : les 4 variantes passaient alors pour 4 scénarios différents et
        # sortaient en série. C'est exactement le doublon visuel que le patron a signalé.
        groupe = (no - 1) // VARIANTES_PAR_SCENARIO + 1
        eps.append(_ep(no, *e, family=f"G{groupe}"))

    # --- G1 : le mail du vendredi 17 h 59 ---
    for (obj, jour) in [
        ("le budget", "lundi"),
        ("le planning", "mardi"),
        ("la présentation", "mercredi"),
        ("le tableau des congés", "jeudi"),
    ]:
        add((
            OFFICE, "LE MAIL DU|VENDREDI|17 h 59",
            f"Le mail du vendredi que tu redoutes ({obj})", "travail / bureau",
            ["travail", "bureau", "mail", "weekend"],
            [
                l_("fournier", "happy", "Très bien, dernier mail de la semaine. Je vous envoie le dossier."),
                l_("kevin", "worried", "Il est dix-sept heures cinquante-neuf, Madame Fournier."),
                l_("fournier", "smug", "Exactement. Envoyé à la dernière seconde : c'est plus sérieux."),
                l_("kevin", "neutral", f"{obj.capitalize()} est demandé pour quand ?"),
                l_("fournier", "happy", f"Pour {jour} matin. Huit heures. Considérez le week-end comme studieux."),
                l_("kevin", "worried", "Et si je ne le rends pas à temps ?"),
                l_("fournier", "smug", "On en reparlera lundi. Par un mail. Vendredi. Dix-sept heures cinquante-neuf.", punch=True),
            ],
        ))

    # --- G2 : la machine à café toujours en panne ---
    for (panne, coupable, excuse) in [
        ("en panne", "le service informatique", "il faut un badge"),
        ("en maintenance", "le directeur", "elle a besoin de repos"),
        ("en réparation", "les consultants", "ils ont vidé le réservoir"),
        ("hors service", "l'alternant", "il a mis du sel au lieu du sucre"),
    ]:
        tiger = panne.upper()
        if "PANNE" in tiger:
            tiger = "EN PANNE"
        elif "MAINTENANCE" in tiger:
            tiger = "EN MAINTENANCE"
        elif "RÉPARATION" in tiger or "REPARATION" in tiger:
            tiger = "EN RÉPARATION"
        else:
            tiger = "HORS SERVICE"
        add((
            OFFICE, "LA MACHINE|À CAFÉ|{0}".format(tiger),
            f"La machine à café est {panne} (enquête)", "travail / open space",
            ["travail", "opendspace", "cafe", "machine"],
            [
                l_("kevin", "neutral", "Quatre heures. La machine à café est {0}, c'est la quatrième fois.".format(panne)),
                l_("fournier", "happy", "J'ai ouvert une enquête. Le conseil a nommé un comité."),
                l_("kevin", "worried", "Le comité de la machine à café ?"),
                l_("fournier", "smug", "Il a ses dossiers. Dont celui du café décaféiné."),
                l_("kevin", "neutral", "Et le vrai café, il ne coule quand même jamais ?"),
                l_("fournier", "worried", f"Le comité a conclu : {excuse}."),
                l_("kevin", "neutral", "Donc on n'aura jamais de café.", punch=True),
            ],
        ))

    # --- G3 : le mute oublié ---
    for (lieu, phrase) in [
        ("le couloir", "Je préfère mon chien à mon équipe"),
        ("l'open space", "Cette réunion dure depuis trois heures"),
        ("le parking", "Mon chef dort pendant les présentations"),
        ("la cuisine", "Qui a encore fini le lait de la pause"),
    ]:
        add((
            OFFICE, "LE MUTE|OUBLIÉ",
            f"Le mute oublié ({lieu})", "travail / télétravail",
            ["teletravail", "visio", "reunion", "mute"],
            [
                l_("kevin", "worried", "{0} : micro ouvert. Et j'ai dit : {1}.".format(lieu.capitalize(), phrase)),
                l_("fournier", "angry", "Kevin. On vous entend pendant toute la réunion."),
                l_("kevin", "worried", "Toute ?"),
                l_("fournier", "smug", "Vous avez respiré fort pendant une heure quarante."),
                l_("kevin", "neutral", "Alors {0}...".format(phrase)),
                l_("fournier", "worried", "Le client l'a noté, oui. Il l'a copié dans le compte-rendu."),
                l_("kevin", "neutral", "J'enverrai une réponse en vous nommant dans le champ de mon mutage.", punch=True),
            ],
        ))

    # --- G4 : le poisson au micro-ondes ---
    for (plat, victime) in [
        ("du poisson", "le client"),
        ("du brocoli", "le stagiaire"),
        ("du chou", "la direction"),
        ("un plat mystérieux", "les pompiers"),
    ]:
        add((
            OFFICE, "LE MICRO-ONDES|DU MIDI",
            f"Le micro-ondes et {plat}", "travail / cantine",
            ["travail", "cantine", "midi", "bureau"],
            [
                l_("kevin", "neutral", "Midi. Quelqu'un réchauffe {0}.".format(plat)),
                l_("fournier", "worried", "Toute la cage d'escalier le sait déjà."),
                l_("kevin", "worried", "L'entreprise a été évacuée ?"),
                l_("fournier", "smug", "Non. {0} a écrit à la sécurité.".format(victime.capitalize())),
                l_("kevin", "neutral", "Il était marqué poisson sur le plat. C'était écrit."),
                l_("fournier", "angry", "Il a levé les yeux et a dit : je souffre."),
                l_("kevin", "neutral", "Au moins, le silence du déjeuner est resté intact.", punch=True),
            ],
        ))

    # --- G5 : le mot de passe oublié ---
    for (systeme, consequences) in [
        ("le portail des congés", "un congé perdu"),
        ("la bibliothèque", "un rendez-vous manqué"),
        ("le logiciel de paie", "un virement refait"),
        ("le serveur secret", "une alerte rouge"),
    ]:
        add((
            OFFICE, "LE MOT DE PASSE|OUBLIÉ",
            f"Le mot de passe oublié ({systeme})", "travail / administration",
            ["travail", "admin", "motdepasse", "bureaucratie"],
            [
                l_("kevin", "worried", "Trois essais. Le mot de passe de {0} est verrouillé.".format(systeme)),
                l_("fournier", "smug", "C'était votre date de naissance. Vendredi dernier. Comme toujours."),
                l_("kevin", "neutral", "Ma date de naissance, c'est le chiffre que j'ai eu à renouveler."),
                l_("fournier", "worried", "En attendant, {0}.".format(consequences)),
                l_("kevin", "worried", "On ne peut pas le réinitialiser ?"),
                l_("fournier", "smug", "Si. Avec une approbation à trois niveaux. Le niveau trois est en congé."),
                l_("kevin", "neutral", "Donc je redeviens comptable de moi-même chaque lundi.", punch=True),
            ],
        ))

    # --- G6 : la livraison « déposée » ---
    for (colis, lieu) in [
        ("une enceinte", "il n'y a rien"),
        ("une carte mère", "le paquet est chez le voisin"),
        ("un cadeau", "il est dans la poubelle du hall"),
        ("un pneu", "il a été signé par le chat"),
    ]:
        add((
            MARKET, "LIVRÉ.|DÉPOSÉ.|INTROUVABLE.",
            f"La livraison « déposée » ({colis})", "société / livraison",
            ["livraison", "colis", "ecommerce", "societe"],
            [
                l_("josette", "worried", "Le suivi dit : déposé. {0} commandé. {1}.".format(colis.capitalize(), lieu.capitalize())),
                l_("kevin", "smug", "Peut-être qu'il est sous la boîte aux lettres ?"),
                l_("josette", "angry", "J'ai regardé dix fois. Il y a juste un facteur qui dort."),
                l_("kevin", "neutral", "Essayez de relancer la livraison."),
                l_("josette", "worried", "C'est fait. Ils m'ont répondu : livré. Voilà."),
                l_("kevin", "neutral", "Qui a signé ?"),
                l_("josette", "angry", "Le fichier dit : l'employé. L'employé, c'est moi. Je n'ai rien vu.", punch=True),
            ],
        ))

    # --- G7 : la banque qui bloque pour « protéger » ---
    for (operation, message) in [
        ("un virement", "vérification de sécurité"),
        ("un paiement", "transaction inhabituelle"),
        ("une simple consultation", "activité suspecte"),
        ("le solde", "connexion depuis un lieu étranger"),
    ]:
        add((
            MARKET, "VOTRE BANQUE|VOUS PROTÈGE",
            f"La banque qui bloque ({operation})", "société / banque",
            ["banque", "argent", "virement", "administration"],
            [
                l_("josette", "worried", "Je fais {0}... et la banque bloque.".format(operation)),
                l_("kevin", "smug", "C'est pour vous protéger, madame."),
                l_("josette", "angry", "Elle m'a envoyé : {0}. Expliquez-moi.".format(message)),
                l_("kevin", "neutral", "Vous avez l'habitude de payer vos courses, non ?"),
                l_("josette", "happy", "Oui. Avec de l'argent. Qui est à moi."),
                l_("kevin", "worried", "Suivez simplement la procédure. Validez. Re-validez. Attendez."),
                l_("josette", "neutral", "Attendez... que je sois assez vieille pour qu'on me rende mon argent.", punch=True),
            ],
        ))

    # --- G8 : le dimanche soir ---
    for (pensee, creature) in [
        ("la réunion de lundi", "un lundi matin"),
        ("le mail en retard", "un mardi glacial"),
        ("le dossier non rendu", "un mercredi interminable"),
        ("la to-do de la semaine", "un jeudi lourd"),
    ]:
        add((
            OFFICE, "DIMANCHE|21 h 47",
            f"Dimanche soir : {pensee}", "société / vie quotidienne",
            ["dimanche", "angoisse", "lundi", "quotidien"],
            [
                l_("kevin", "worried", "Dimanche soir. Plus de week-end. Plus de cachet."),
                l_("fournier", "smug", "Une pensée : {0}.".format(pensee)),
                l_("kevin", "worried", "Ne le dites pas à voix haute, il va l'entendre."),
                l_("fournier", "happy", "Trop tard. Il l'a entendu. Il arrive {0}.".format(creature)),
                l_("kevin", "neutral", "Je peux au moins dormir ?"),
                l_("fournier", "worried", "Le cerveau a déjà lancé la semaine. Il est parti."),
                l_("kevin", "neutral", "Je vais me coucher du lundi en avance.", punch=True),
            ],
        ))

    # --- G9 : le groupe WhatsApp familial ---
    for (type_msg, auteur) in [
        ("une vidéo de chat", "Tonton"),
        ("une chaîne de prières", "Tatie"),
        ("une photo floue de flan", "Cousine"),
        ("un audio de quarante secondes", "Grand-père"),
    ]:
        add((
            MARKET, "LE GROUPE|DE LA FAMILLE",
            f"Le groupe WhatsApp familial ({auteur})", "société / famille",
            ["whatsapp", "famille", "groupe", "quotidien"],
            [
                l_("josette", "worried", "Sept heures du matin. {0} envoie {1}.".format(auteur, type_msg)),
                l_("kevin", "neutral", "Le groupe est déjà à soixante-trois messages. Personne n'a parlé."),
                l_("josette", "smug", "C'est {0} qui a répondu : bien reçu.".format("moi")),
                l_("kevin", "worried", "Il va maintenant y avoir vingt réponses à « bien reçu »."),
                l_("josette", "angry", "Qui ose quitter le groupe ? Les pressions familiales."),
                l_("kevin", "neutral", "Je reste. Sainte pacience, je regarde."),
                l_("josette", "smug", "On étudie, un jour, qui a les lois du groupe au meilleur silence.", punch=True),
            ],
        ))

    # --- G10 : l'appel « ça va ? » ---
    for (suite, niveau) in [
        ("tu dois m'aider à déménager", "niveau un"),
        ("j'ai perdu la carte bleue", "niveau deux"),
        ("c'est à propos du virement de mardi", "niveau trois"),
        ("la maison a un problème de toit", "niveau max"),
    ]:
        add((
            OFFICE, "L'APPEL|« ÇA VA ? »",
            f"L'appel qui commence par « ça va ? » ({niveau})", "société / quotidien",
            ["appel", "telephone", "stress", "quotidien"],
            [
                l_("kevin", "worried", "Le téléphone sonne. La personne dit : ça va."),
                l_("fournier", "smug", "Attendez. Il a dit « j'ai besoin de toi » en premier."),
                l_("kevin", "worried", "Il a dit : j'ai besoin. C'est {0}.".format(suite)),
                l_("fournier", "happy", "Et vous avez répondu quoi ?"),
                l_("kevin", "neutral", "J'ai dit : ça va. Et on a raccroché."),
                l_("fournier", "worried", "Donc {0} est en attente.".format(niveau)),
                l_("kevin", "worried", "C'est le principe de l'appel : on ne rappelle pas.", punch=True),
            ],
        ))

    # --- G11 : ChatGPT qui répond « en revanche » ---
    for (sujet, titre) in [
        ("un gâteau", "le gâteau qui se retourne"),
        ("une présentation", "la présentation qui se retourne"),
        ("un budget", "le budget qui se retourne"),
        ("un poème", "le poème qui se retourne"),
    ]:
        add((
            FACTORY, "L'IA RÉPOND|« EN REVANCHE »",
            f"ChatGPT répond en revanche ({sujet})", "tech / intelligence artificielle",
            ["ia", "chatgpt", "technologie", "bureau"],
            [
                l_("bob", "neutral", "J'ai demandé au grand modèle d'écrire un texte sur {0}.".format(sujet)),
                l_("kevin", "neutral", "Et alors ?"),
                l_("bob", "neutral", "Il a répondu : voici votre texte. En revanche, il est trop long."),
                l_("kevin", "worried", "C'est tout ?"),
                l_("bob", "neutral", "En revanche, j'ai fait un résumé. En revanche, le résumé est complet."),
                l_("kevin", "angry", "Je voulais juste {0} !".format(sujet)),
                l_("bob", "neutral", "En revanche, vous l'avez.", punch=True),
            ],
        ))

    # --- G12 : l'IA réorganise l'organigramme ---
    for (poste, remplacant) in [
        ("ton poste", "le modèle qui ne dort pas"),
        ("la réunion", "une vidéo résumée"),
        ("ta pause café", "un capteur qui surveille la fatigue"),
        ("ton bureau", "un espace flexible partagé"),
    ]:
        add((
            FACTORY, "L'IA REFONT|L'ORGANIGRAMME",
            f"L'IA refait l'organigramme ({poste})", "tech / travail",
            ["ia", "organigramme", "entreprise", "robot"],
            [
                l_("bob", "neutral", "L'IA a remplacé {0}.".format(poste)),
                l_("kevin", "worried", "Elle a remplacé qui par qui ?"),
                l_("bob", "neutral", "Par {0}.".format(remplacant)),
                l_("kevin", "angry", "Mais moi, je fais plus que ça ! Je fais du café, des photos, des rappels."),
                l_("bob", "neutral", "Le modèle fait tout ça. En dix-huit millièmes de seconde."),
                l_("kevin", "worried", "Et il prend des pauses, au moins ?"),
                l_("bob", "neutral", "Il a demandé une pause le premier jour. On a cru à une erreur.", punch=True),
            ],
        ))

    # --- G13 : les congés mais jamais de réponse ---
    for (periode, pretexte) in [
        ("août", "le responsable est en congé"),
        ("décembre", "c'est le rush de fin d'année"),
        ("les vacances de printemps", "on attend la confirmation"),
        ("l'été prochain", "la fusion des équipes"),
    ]:
        add((
            OFFICE, "MA DEMANDE|DE CONGÉS",
            f"La demande de congés sans réponse ({periode})", "travail / congés",
            ["conge", "vacances", "travail", "bureaucratie"],
            [
                l_("kevin", "neutral", "J'ai envoyé ma demande de congés pour {0} en janvier.".format(periode)),
                l_("fournier", "smug", "Le service l'a bien reçue. Elle est en attente."),
                l_("kevin", "worried", "En attente de quoi ?"),
                l_("fournier", "happy", "De la validation du comité. Qui valide les validations."),
                l_("kevin", "worried", "Le comité se réunit quand ?"),
                l_("fournier", "worried", "{0}.".format(pretexte.capitalize())),
                l_("kevin", "neutral", "Donc je réserve le voyage à l'aveugle.", punch=True),
            ],
        ))

    # --- G14 : la cuillère empruntée jamais rendue ---
    for (objet, coupable) in [
        ("une cuillère", "le service marketing"),
        ("une tasse", "les consultants de passage"),
        ("un stylo", "le client en visite"),
        ("le dernier café", "l'équipe du soir"),
    ]:
        add((
            MARKET, "L'OBJET|EMPRUNTÉ",
            f"L'objet emprunté et jamais rendu ({objet})", "travail / bureau",
            ["bureau", "objet", "vol", "economie"],
            [
                l_("josette", "angry", "On m'a pris {0} il y a trois jours.".format(objet)),
                l_("kevin", "smug", "Il y a une charte anti-emprunt, madame."),
                l_("josette", "worried", "Où est le panneau ?"),
                l_("kevin", "neutral", "Il est affiché. Juste à côté de {0}.".format(objet)),
                l_("josette", "angry", "Qui a pu le faire sans se faire repérer ?"),
                l_("kevin", "worried", "{0} est arrivé par l'ascenseur de service.".format(coupable.capitalize())),
                l_("josette", "neutral", "Donc on installe une caméra et une grosse chaîne à café.", punch=True),
            ],
        ))

    # --- G15 : le stagiaire pose LA question ---
    for (question, enjeu) in [
        ("pourquoi faire payer les clients", "la marge"),
        ("pourquoi signer les bons", "la hiérarchie"),
        ("pourquoi réunir autant", "le temps perdu"),
        ("qui lit le reporting", "l'ordre établi"),
    ]:
        add((
            OFFICE, "LA QUESTION|DU STAGIAIRE",
            f"Le stagiaire et {enjeu}", "travail / entreprise",
            ["stagiaire", "entreprise", "question", "humour"],
            [
                l_("kevin", "neutral", "Le stagiaire a levé la main. Le silence s'est installé."),
                l_("fournier", "worried", "Il a demandé : {0} ?".format(question)),
                l_("kevin", "worried", "C'est quoi le problème ? C'est une question normale."),
                l_("fournier", "smug", "Une question normale brise l'ordre des choses."),
                l_("kevin", "neutral", "Elle a quoi de menaçant ?"),
                l_("fournier", "worried", "Elle implique {0}. Personne ne veut en parler.".format(enjeu)),
                l_("kevin", "neutral", "Donc on engage un comité pour ne pas répondre.", punch=True),
            ],
        ))

    # --- G16 : le prix des pâtes change ---
    for (aliment, ancien, nouveau) in [
        ("les pâtes", "un euro", "quatre euros"),
        ("le beurre", "une pièce", "une fortune"),
        ("le café", "un café", "un salaire"),
        ("le pain", "une baguette", "une rareté"),
    ]:
        tag = "DES PÂTES" if aliment == "les pâtes" else "DU " + aliment.upper().lstrip("LE ").lstrip("LES ")
        add((
            MARKET, "LE PRIX|{0}".format(tag),
            f"Le prix de {aliment}", "société / inflation",
            ["inflation", "prix", "courses", "societe"],
            [
                l_("josette", "worried", "Quand j'étais jeune, {aliment} coûtaient {ancien}.".format(aliment=aliment, ancien=ancien)),
                l_("kevin", "neutral", "Maintenant, c'est {nouveau}. Pour le même paquet.".format(nouveau=nouveau)),
                l_("josette", "angry", "C'est le même emballage, c'est écrit pareil !"),
                l_("kevin", "smug", "Le prix, c'est le marché. Le goût, c'est la nostalgie."),
                l_("josette", "worried", "Et la marge ?"),
                l_("kevin", "neutral", "La marge, c'est nous, les clients."),
                l_("josette", "happy", "Alors je n'achète plus. Je cultive mon petit jardin.", punch=True),
            ],
        ))

    # ================= G17 à G26 : scénarios NEUFS ajoutés le 02/10/2026 =============
    # Règle (ORDRE J) : un groupe = un scénario = une seule vidéo publiable. Les
    # variantes d'un même groupe sont des doublons visuels, le garde les bloquera.
    # Ces scénarios sont des situations inédites, pas des variantes des G1..G16.

    # --- G17 : le badge qui n'ouvre plus rien ---
    for (porte, excuse) in [
        ("la porte du sous-sol", "elle a changé de numéro"),
        ("la porte des archives", "le lecteur est mort"),
        ("la porte de la salle de réunion", "le badge est périmé"),
        ("la porte des toilettes du 3e", "on a changé de serrure"),
    ]:
        add((
            OFFICE, "LE BADGE|N'OUVRE PLUS|RIEN",
            f"Le badge n'ouvre plus {porte}", "travail / accès",
            ["travail", "bureau", "badge", "securite"],
            [
                l_("fournier", "smug", "Approchez-vous de {0}, badgez, et pray.".format(porte)),
                l_("kevin", "neutral", "Ça ne sonne pas."),
                l_("fournier", "happy", "Ça ne sonnait déjà plus. C'est une porte, pas un orchestre."),
                l_("kevin", "worried", "On m'a dit que {0} était un problème résolu.".format(excuse)),
                l_("fournier", "smug", "Résolu par qui ?"),
                l_("kevin", "worried", "Par la personne qui l'a signalé."),
                l_("fournier", "happy", "Alors c'est réglé : plus personne ne rentre, et le problème est mort.", punch=True),
            ],
        ))

    # --- G18 : le ticket de caisse ---
    for (ticket, moment, accuse) in [
        ("le ticket", "à la caisse", "le client"),
        ("le code-barres", "sur le tapis", "le scanner"),
        ("le ticket", "dans le sac", "le antivirus du magasin"),
        ("la facture", "par mail", "le comptable"),
    ]:
        add((
            MARKET, "LE TICKET|EST PERDU|TOUJOURS",
            f"Le ticket disparaît {moment}", "quotidien / magasin",
            ["quotidien", "magasin", "ticket", "courses"],
            [
                l_("josette", "angry", "Je voudrais {0}, s'il vous plaît. Je l'ai payé.".format(ticket)),
                l_("kevin", "neutral", "Le ticket ? On l'a perdu {0}. Rien de personnel.".format(moment)),
                l_("josette", "worried", "Perdu comment ? Je l'ai eu en main, il y a deux minutes."),
                l_("kevin", "neutral", "Le système l'a oublié. C'est {0} qui décide.".format(accuse)),
                l_("josette", "angry", "Moi j'ai oublié le parmesan, lui il a oublié mon ticket. Je le plains."),
                l_("kevin", "worried", "Je peux vous mettre un bon de réduction."),
                l_("josette", "angry", "Gardez votre bon. À la fin du mois je viens au supermarché payer 47 euros.", punch=True),
            ],
        ))

    # --- G19 : la panne annoncée dans l'usine ---
    for (machine, cause, duree) in [
        ("l'emballeuse", "un capteur", "deux heures"),
        ("le convoyeur", "une vis", "quatre heures"),
        ("la presse", "le courant", "une journée"),
        ("le robot de palette", "un gravier", "trois semaines"),
    ]:
        add((
            FACTORY, "LA PANNE|EST PRÉVU",
            f"La panne de {machine} était prévue", "industrie / technique",
            ["industrie", "panne", "usine", "technique"],
            [
                l_("kevin", "neutral", "On nous a annoncé : {machine} en panne.".format(machine=machine)),
                l_("bob", "neutral", "Annoncé. Pas subi. C'est important."),
                l_("kevin", "worried", "On la répare depuis ce matin, non ?"),
                l_("bob", "neutral", "Depuis ce matin. Durée prévue : {duree}.".format(duree=duree)),
                l_("kevin", "worried", "Et la cause ?"),
                l_("bob", "neutral", "{cause}, mais::{cause}, donc personne ne peut rien dire.".format(cause=cause)),
                l_("kevin", "neutral", "Donc on attend que la panne se répare toute seule.", punch=True),
            ],
        ))

    # --- G20 : la conférence de presse ---
    for (question, reponse) in [
        ("Pourquoi ce retard ?", "Nous avons investi dans la qualité"),
        ("Combien ça coûte ?", "Le prix n'est pas le sujet"),
        ("Qui est responsable ?", "Je répondsra quand je serai au courant"),
        ("Et les salariés ?", "Les salariés sont notre première priorité"),
    ]:
        add((
            STAGE, "LA CONFÉRENCE|« JE RÉPONDSRA »",
            f"La conférence de presse qui ne répond pas", "communication / politique",
            ["politique", "communication", "presse", "humour"],
            [
                l_("ministre", "happy", "Je réponds volontiers à toutes vos questions."),
                l_("josette", "neutral", "Alors celle-ci : {0}".format(question)),
                l_("ministre", "smug", "{0}".format(reponse)),
                l_("josette", "worried", "Je n'ai pas compris la réponse, je n'ai pas eu la question."),
                l_("ministre", "happy", "C'est exactement pour ça qu'on fait des conferences de presse."),
                l_("josette", "neutral", "On fait des conferences de presse pour poser des questions ?"),
                l_("ministre", "smug", "Pour les faire poser par d'autres. Nous, on répond.", punch=True),
            ],
        ))

    # --- G21 : le salaire du 3 du mois ---
    for (jour, excuse, decouverte) in [
        ("le 3 du mois", "un décalage technique", "le 5"),
        ("le 1er", "un jour férié", "le 8"),
        ("le 15", "la clôture comptable", "le 22"),
        ("la fin du mois", "un décalage de virement", "le mois suivant"),
    ]:
        add((
            OFFICE, "LE SALAIRE|ATTENDU|TOUJOURS",
            f"Le salaire annoncé pour {jour}", "travail / argent",
            ["travail", "salaire", "argent", "patron"],
            [
                l_("fournier", "happy", "Les salaires sonteversés {0}, comme chaque mois.".format(jour)),
                l_("kevin", "neutral", "Et s'il n'y a rien {0} ?".format(jour)),
                l_("fournier", "smug", "Il y en a toujours. Parfois pas."),
                l_("kevin", "worried", "Vous avez dit « chaque mois ». J'ai retenu la date."),
                l_("fournier", "happy", "Rappel utile : les salaires seront virés {decouverte}, pour {excuse}.".format(decouverte=decouverte, excuse=excuse)),
                l_("kevin", "angry", "Et mon loyer, il est viré le 5, par la même banque."),
                l_("fournier", "smug", "Votre loyer, ce n'est pas mon budget. Et moi, je suis en_stage.", punch=True),
            ],
        ))

    # --- G22 : « à base de » ---
    for (produit, base) in [
        ("la compote", "des fruits"),
        ("le pain", "de la farine"),
        ("le fromage", "du lait"),
        ("les biscuits", "des tranches"),
    ]:
        add((
            MARKET, "« À BASE DE »|RIEN DU TOUT",
            f"« À base de » : l'étiquette qui ne dit rien", "consommation / marketing",
            ["consommation", "marketing", "etiquette", "quotidien"],
            [
                l_("josette", "neutral", "C'est marqué « à base de » ?"),
                l_("kevin", "happy", "Bien sûr. C'est même écrit en gros."),
                l_("josette", "worried", "Et la base ?"),
                l_("kevin", "neutral", "{base}. Deux pour cent.".format(base=base)),
                l_("josette", "angry", "Deux pour cent, c'est une adresse. Il y a une adresse dans cette bouteille."),
                l_("kevin", "happy", "L'adresse du fournisseur. On ne peut pas mettre « Kevin »."),
                l_("josette", "angry", "Si. Vous pouvez. « Fabriqué par Kevin, 98 % de eau. »", punch=True),
            ],
        ))

    # --- G23 : le nouveau qui parle robot ---
    for (phrase, precision) in [
        ("Bonjour à tous", "l'intonation"),
        ("Bonjour, je suis le nouveau", "le prénom"),
        ("Enchanté", "les mains"),
        ("J'ai une question", "la question"),
    ]:
        add((
            FACTORY, "LE NOUVEAU|PARLE|ROBOT",
            "Le nouveau collègue parle robot", "monde du travail / absurdité",
            ["travail", "collegue", "robot", "absurde"],
            [
                l_("kevin", "neutral", "Le nouveau dit : « {phrase} ». Mot pour mot.".format(phrase=phrase)),
                l_("bob", "neutral", "Ce n'est pas un défaut. C'est une édition limitée."),
                l_("kevin", "worried", "Il manque {0}.".format(precision)),
                l_("bob", "neutral", "Non. C'est ce qui fait le prix."),
                l_("kevin", "angry", "Il est en formation, il peut se tromper !"),
                l_("bob", "neutral", "Il ne s'est pas trompé. Il a répété. C'est pire."),
                l_("kevin", "neutral", "Bon. Bienvenue. Où sont les izquierda... où est la machine à café ?", punch=True),
            ],
        ))

    # --- G24 : le décret retiré ---
    for (decret, retrait) in [
        ("l'interdiction de café à 10 h", "de 15 h"),
        ("le port du casque obligatoire", "le casque au volant"),
        ("la réunion de 8 h pour tout le monde", "la réunion facultative"),
        ("l'obligation de>,</", "l.tag obligation"),
    ]:
        add((
            STAGE, "LE DÉCRET|EST ANNULÉ|TOUJOURS",
            "Le décret annoncé puis retiré", "administration / politique",
            ["politique", "decret", "administration", "humour"],
            [
                l_("ministre", "happy", "Dès demain : {0}.".format(decret)),
                l_("josette", "neutral", "C'est obligatoire pour qui ?"),
                l_("ministre", "smug", "Pour tout le monde. Puisque c'est juste."),
                l_("josette", "worried", "Et après l'annonce, on a le droit de faire autrement ?"),
                l_("ministre", "happy", "Bien sûr. C'est le principe de {0}.".format(retrait)),
                l_("josette", "angry", "Vous annulez la règle ET ce qui la rendait possible ?"),
                l_("ministre", "smug", "On garde l'ambiance. C'est plus rassurant.", punch=True),
            ],
        ))

    # --- G25 : le mot de passe « 123456 » ---
    for (system, consequence) in [
        ("la boîte mail", "onze mille mails"),
        ("le logiciel de paie", "tous les salaires"),
        ("le serveur de fichiers", "le disque dur"),
        ("la caméra du parking", "la porte d'entrée"),
    ]:
        add((
            OFFICE, "LE MOT DE PASSE|EST « 123456 »",
            "Le mot de passe trivial", "sécurité / informatique",
            ["securite", "motdepasse", "informatique", "travail"],
            [
                l_("kevin", "neutral", "Le mot de passe de {0}, c'est 123456.".format(system)),
                l_("fournier", "smug", "C'est le plus simple à retenir. Et le plus rapide à tester."),
                l_("kevin", "worried", "Personne ne l'a cracké ?"),
                l_("fournier", "happy", "Si. {0} s'est ouvert sans effort.".format(consequence)),
                l_("kevin", "angry", "Et on ne change pas le mot de passe ?"),
                l_("fournier", "smug", "On ne le changera jamais : personne ne l'lloubliera."),
                l_("kevin", "neutral", "C'est le pire argument de sécurité de ma carrière.", punch=True),
            ],
        ))

    # --- G26 : la file du drive ---
    for (file, musique, avis) in [
        ("celle du samedi", "une voz android", "il n'y a personne dans le magasin"),
        ("celle du soir", "du jazz", "le drive est plein"),
        ("celle du lundi", "un jingle", "c'est le drive du lundi"),
        ("celle des jours de semaine", "rien", "on est au drive, pas au concert"),
    ]:
        add((
            MARKET, "LA FILE|DU DRIVE|ATTEND",
            "La file d'attente au drive avec musique", "quotidien / magasin",
            ["quotidien", "magasin", "drive", "file"],
            [
                l_("josette", "neutral", "Il y a {file} derrière moi.".format(file=file)),
                l_("kevin", "happy", "C'est pour ça qu'on a mis {musique}.".format(musique=musique)),
                l_("josette", "worried", "On est {avis}.".format(avis=avis)),
                l_("kevin", "neutral", "Alors c'est de l'ambiance."),
                l_("josette", "angry", "Je n'ai pas payé pour l'ambiance, j'ai payé mes courses."),
                l_("kevin", "happy", "Elles sont dans le coffre. Vous voulez le ticket ou la musique ?"),
                l_("josette", "neutral", "Le ticket. La musique, je l'aurai gratuitement, toute la journée.", punch=True),
            ],
        ))

    # ================= G27 à G36 : scénarios neufs du 09/10/2026 =====================
    # Pourquoi : la banque ne tenait plus que 11 vidéos sans doublon, soit 2,2 jours à
    # 5 posts/jour. L'orchestrateur automatique aurait donc buté sur une file vide. On
    # ajoute 10 situations inédites (10 jours de contenu), toujours 4 variantes par
    # groupe — le champ `family` fait le reste.
    # Règle (ORDRE J) : un groupe = un scénario = UNE seule vidéo publiable.

    # --- G27 : l'ascenseur monte, il ne descend jamais ---
    for (depart, arrivee, excuse) in [
        ("le sous-sol", "le quatrième", "le capteur d'hydratation"),
        ("la cafétéria", "le premier", "la porte automatique"),
        ("les archives", "le hall", "le bouton d'évacuation"),
        ("le parking", "la rooftop", "le mode économie d'énergie"),
    ]:
        add((
            OFFICE, "L'ASCENSEUR|MONTE|JAMAIS|IL NE DESCEND PAS",
            f"L'ascenseur monte sans jamais descendre ({depart})", "quotidien / immeuble",
            ["quotidien", "ascenseur", "immeuble", "humour"],
            [
                l_("kevin", "worried", "J'appuie sur {arrivee}. L'ascenseur est parti : {depart}.".format(arrivee=arrivee, depart=depart)),
                l_("fournier", "smug", "Il monte. C'est tout ce qu'on lui a demandé."),
                l_("kevin", "angry", "Je ne lui ai pas demandé de monter. Je lui ai demandé de descendre."),
                l_("fournier", "happy", "Les trois premières fois, l'ascenseur obéit. Après, il fait ce qu'il veut."),
                l_("kevin", "worried", "Et l'escalier, alors ?"),
                l_("fournier", "smug", "L'escalier monte aussi. Mais lui, il ne vous fait pas payer."),
                l_("kevin", "neutral", "Il est bloqué au troisième depuis neuf heures.", punch=True),
            ],
        ))

    # --- G28 : la réunion de quatre heures pour une décision de quatre minutes ---
    for (objet, duree, decision) in [
        ("le budget de l'équipe", "quatre heures", "le même budget"),
        ("la nouvelle charte graphique", "trois heures", "l'ancienne charte"),
        ("le planning de septembre", "quatre heures", "le planning d'août"),
        ("l'organisation des équipes", "quatre heures", "personne ne sait"),
    ]:
        add((
            OFFICE, "LA RÉUNION|EST ARRIVÉE|À L'HEURE|POUT PAS",
            f"La réunion de {duree} ({objet})", "travail / réunion",
            ["travail", "reunion", "humour", "bureau"],
            [
                l_("kevin", "neutral", "{objet} : on a {duree} pour trancher.".format(objet=objet[0].upper() + objet[1:], duree=duree)),
                l_("fournier", "happy", "C'est parfait. Une décision de cette importance mérite {duree}.".format(duree=duree)),
                l_("kevin", "worried", "On a décidé quoi, du coup ?"),
                l_("fournier", "smug", "{decision}. On aurait pu le dire en quatre minutes.".format(decision=decision[0].upper() + decision[1:])),
                l_("kevin", "angry", "Alors pourquoi on a pointé pendant {duree} ?".format(duree=duree)),
                l_("fournier", "happy", "Parce que c'était la seule partie importante."),
                l_("kevin", "neutral", "La partie importante, c'est d'être là ?", punch=True),
            ],
        ))

    # --- G29 : l'appli de livraison change l'adresse ---
    for (commande, adresse) in [
        ("une Pizza", "la rue d'à côté"),
        ("des courses", "un autre quartier"),
        ("unQuem", "un village"),
        ("une fleur", "le parking du magasin"),
    ]:
        add((
            MARKET, "L'APPLI DE LIVRAISON|CHANGE D'ADRESSE|À MOITIÉ DU TRAJET",
            f"Le livreur livr elsewhere ({commande})", "société / livraison",
            ["livraison", "application", "quotidien", "humour"],
            [
                l_("josette", "neutral", "Le suivi dit : le livreur arrive."),
                l_("kevin", "happy", "Très bien. Il reste combien de temps ?"),
                l_("josette", "worried", "Il est à {adresse}. J'habite à deux kilomètres.".format(adresse=adresse)),
                l_("kevin", "neutral", "C'est le trajet le plus court pour lui."),
                l_("josette", "angry", "Et pour moi ?"),
                l_("kevin", "smug", "Pour vous, c'est deux kilomètres. Ça se marche."),
                l_("josette", "worried", "Le colis va arriver froide, et moi je vais arriver chaude.".format(commande=commande), punch=True),
            ],
        ))

    # --- G30 : le nouveau fait des bullet points à l'oral ---
    for (sujet, detail) in [
        ("le retard", "il y en a trois"),
        ("la qualité", "elle est en baisse"),
        ("le budget", "il est gelé"),
        ("la roadmap", "elle n'existe pas"),
    ]:
        add((
            OFFICE, "IL PARLE EN|PUCES|MAIS À L'ORAL",
            f"Le nouveau fait des puces à l'oral ({sujet})", "travail / communication",
            ["travail", "presentation", "humour", "bureau"],
            [
                l_("kevin", "neutral", "Le nouveau prend la parole. Premier point."),
                l_("fournier", "happy", "Deuxième point."),
                l_("kevin", "worried", "Il est en train de faire des puces à l'oral."),
                l_("fournier", "smug", "C'est plus lisible à l'oral, on le voit dans ses gestes."),
                l_("kevin", "neutral", "Troisième point : {detail}.".format(detail=detail)),
                l_("fournier", "happy", "Point suivant ?"),
                l_("kevin", "worried", "Il a terminé. Le dernier point c'était qu'il n'y en a pas.", punch=True),
            ],
        ))

    # --- G31 : l'IA répond à côté de la question ---
    for (question, reponse) in [
        ("combien de jours de congé", "voici une recette de tarte"),
        ("où est mon clavier", "les claviers sont une invention ancienne"),
        ("quelle heure est-il", "il est toujours l'heure de partir"),
        ("s'il pleut demain", "les pencils n'ont pas de parapluie"),
    ]:
        add((
            FACTORY, "L'IA A RÉPONDU|À CÔTÉ DE LA QUESTION",
            f"L'IA répond à côté de la question ({question})", "tech / IA",
            ["ia", "chatgpt", "technique", "humour"],
            [
                l_("kevin", "neutral", "Je demande : {question} ?".format(question=question)),
                l_("bob", "happy", "Excellente question. {reponse}.".format(reponse=reponse[0].upper() + reponse[1:])),
                l_("kevin", "angry", "Ce n'est pas ma réponse !"),
                l_("bob", "neutral", "C'est une réponse. Elle n'est pas à la question. C'est plus intéressant."),
                l_("kevin", "worried", "On peut au moins essayer de nouveau ?"),
                l_("bob", "smug", "On peut. Le modèle préfère parler de lui. C'est son seul sujet."),
                l_("kevin", "neutral", "Je vais lui demander quel jour on est. Il va me parler du poids de l'eau.", punch=True),
            ],
        ))

    # --- G32 : le rapport automatique faux (mais Accepted) ---
    for (indicateur, valeur, realite) in [
        ("le taux de présence", "98 %", "il y a deux jours de congés l'an dernier"),
        ("le coût des transports", "en baisse", "il a doublé"),
        ("la satisfaction équipe", "9/10", "personne n'a répondu"),
        ("le délai de livraison", "amélioré", "c'est pareil"),
    ]:
        add((
            FACTORY, "LE RAPPORT AUTOMATIQUE|EST FAUX|MAIS ACCEPTÉ",
            f"Le rapport automatique faux ({indicateur})", "tech / données",
            ["rapport", "donnees", "ia", "humour"],
            [
                l_("kevin", "neutral", "Le tableau de bord dit : {indicateur}, {valeur}.".format(indicateur=indicateur, valeur=valeur)),
                l_("bob", "happy", "Les chiffres sont calculés. Ils sont donc exacts."),
                l_("kevin", "worried", "Et en vrai ?"),
                l_("bob", "neutral", "En vrai, c'est faux : {realite}.".format(realite=realite[0].upper() + realite[1:])),
                l_("kevin", "angry", "Alors le tableau de bord est faux !"),
                l_("bob", "smug", "Le tableau de bord est vrai. C'est le monde qui est faux."),
                l_("kevin", "neutral", "Je vais mettre ça dans la présentation de demain.", punch=True),
            ],
        ))

    # --- G33 : l'attente pour un retrait en magasin ---
    for (commande, delai, excuse) in [
        ("une commande", "quarante-cinq minutes", "le véhicule attend sa tournée"),
        ("un retrait", "une heure", "le filtre a changé"),
        ("un retour", "deux heures", "le parking est plein"),
        ("un échange", "trois heures", "personne n'a l'article"),
    ]:
        add((
            MARKET, "ILS ONT DIT|QUARANTE MINUTES|ÇA FAIT {delai}".format(delai="UNE HEURE"),
            f"L'attente au comptoir ({commande})", "quotidien / magasin",
            ["quotidien", "magasin", "attente", "humour"],
            [
                l_("josette", "worried", "On m'a dit {delai} pour {commande}.".format(delai=delai, commande=commande)),
                l_("kevin", "happy", "{delai}. C'est noté sur le ticket.".format(delai=delai[0].upper() + delai[1:])),
                l_("josette", "angry", "Le ticket a été imprimé à 14 h 02. Il est 15 h 12."),
                l_("kevin", "smug", "Vous voyez, l'heure est respectée."),
                l_("josette", "worried", "L'heure de quoi, exactement ?"),
                l_("kevin", "neutral", "{excuse}. Le magasin ne répond plus de ces choses-là.".format(excuse=excuse[0].upper() + excuse[1:])),
                l_("josette", "angry", "La commande va repartir sans moi, et moi sans elle.".format(commande=commande), punch=True),
            ],
        ))

    # --- G34 : le décret sur le télétravail ---
    for (regle, precision) in [
        ("le télétravail obligatoire", "deux jours par semaine"),
        ("la présence obligatoire", "quatre jours par semaine"),
        ("le télétravail interdit", "cinq jours au bureau"),
        ("la réunion obligatoire", "en présentiel, debout"),
    ]:
        add((
            STAGE, "LE DÉCRET SUR LE|TÉLÉTRAVAIL|EST CLAIR",
            f"Le décret sur le télétravail ({regle})", "administration / travail",
            ["teletravail", "decret", "travail", "humour"],
            [
                l_("ministre", "happy", "Dès lundi : {regle}.".format(regle=regle)),
                l_("josette", "neutral", "C'est obligatoire pour tout le monde ?"),
                l_("ministre", "smug", "{precision}. Pour tout le monde.".format(precision=precision[0].upper() + precision[1:])),
                l_("josette", "worried", "Et si la connexion ne marche pas ce jour-là ?"),
                l_("ministre", "happy", "C'est précisément pour ça qu'il existe un décret."),
                l_("josette", "angry", "Le décret ne va pas redémarrer ma box."),
                l_("ministre", "smug", "On a prévu des offres. La connexion fait partie du foyer.", punch=True),
            ],
        ))

    # --- G35 : le collègue qui répond « c'est noté » ---
    for (sujet, relance) in [
        ("la demande de matériel", "elle n'a jamais été chiffrée"),
        ("le problème de bruit", "il n'a jamais été mesuré"),
        ("la formation obligatoire", "elle n'a jamais eu de contenu"),
        ("la clause sécurité", "elle n'a jamais été écrite"),
    ]:
        add((
            OFFICE, "IL RÉPOND|« C'EST NOTÉ »|À TOUT",
            f"Il répond « c'est noté » à tout ({sujet})", "travail / open space",
            ["travail", "open space", "humour", "bureau"],
            [
                l_("kevin", "neutral", "Je signale : {sujet}.".format(sujet=sujet)),
                l_("fournier", "smug", "C'est noté."),
                l_("kevin", "worried", "Noté où ?"),
                l_("fournier", "happy", "Dans ma tête. C'est très bien rangé."),
                l_("kevin", "angry", "Je peux avoir une trace ?"),
                l_("fournier", "smug", "{relance}.".format(relance=relance[0].upper() + relance[1:])),
                l_("kevin", "neutral", "J'ai demandé une trace. Pas un constat d'absence.", punch=True),
            ],
        ))

    # --- G36 : l'abonnement résilié mais facturé ---
    for (service, montant) in [
        ("le streaming", "onze euros"),
        ("le sport", "trente euros"),
        ("la musique", "dix euros"),
        ("le cloud", "quatre euros"),
    ]:
        add((
            MARKET, "J'AI RÉSILIÉ|{0} ET|ON M'A FACTURÉ".format(service.upper()),
            f"L'abonnement résilié mais facturé ({service})", "société / argent",
            ["abonnement", "argent", "quotidien", "humour"],
            [
                l_("josette", "angry", "J'ai résilié {service} en mars. J'ai encore été débitée de {montant}.".format(service=service, montant=montant)),
                l_("kevin", "smug", "Le résilié prend effet à la fin de l'abonnement en cours."),
                l_("josette", "worried", "On est en octobre."),
                l_("kevin", "happy", "Exactement. Il faut attendre la fin du prochain."),
                l_("josette", "angry", "Et si je me réabonne ?"),
                l_("kevin", "neutral", "Alors le résilié est annulé et vous payez les deux. C'est le principe du foyer."),
                l_("josette", "worried", "Je ne me réabonne pas. Je ne sais même pas comment on vérifie.", punch=True),
            ],
        ))

    # ============ G37 à G42 : scénarios NEUFS du 16/10/2026 =======================
    # Constat : la banque ne tenait plus que 1 scénario publiable sans doublon
    # (auto_144). Les 41 autres étaient des variantes de familles déjà publiées.
    # On ajoute 6 situations INÉDITES (2 jours à 3 posts/jour), sujets vérifiés
    # un par un contre les 36 familles existantes pour éviter tout doublon de
    # scénario. Mêmes personnages, décors, voix et structure (7 répliques + punch).

    # --- G37 : le thermostat réglé en guerre froide ---
    for (degres, coupable, excuse) in [
        ("dix-sept degrés", "le service technique", "c'est la température de la concentration"),
        ("quinze degrés", "la direction", "on chauffe la planète, pas le bureau"),
        ("dix-huit degrés", "le consultant en énergie", "c'est le seuil d'alerte nationale"),
        ("seize degrés", "les ressources humaines", "trop chaud, on dort ; trop froid, on travaille"),
    ]:
        add((
            OFFICE, "LE THERMOSTAT|EST EN|GUERRE FROIDE",
            f"Le thermostat réglé en guerre froide ({degres})", "travail / open space",
            ["travail", "bureau", "froid", "thermostat"],
            [
                l_("kevin", "worried", "Il fait {0} au bureau. Je tape en gants.".format(degres)),
                l_("fournier", "smug", "Le thermostat est réglé. C'est scientifique."),
                l_("kevin", "angry", "Scientifique ? J'ai du givre sur le clavier."),
                l_("fournier", "happy", "{0} a validé le réglage.".format(coupable.capitalize())),
                l_("kevin", "neutral", "Et la raison, officiellement ?"),
                l_("fournier", "smug", "{0}. C'est optimisé.".format(excuse)),
                l_("kevin", "worried", "Optimisé pour qui ? Le congélateur du rez-de-chaussée ?", punch=True),
            ],
        ))

    # --- G38 : le formulaire pour obtenir un formulaire ---
    for (document, niveau, delai) in [
        ("une attestation", "trois signatures", "deux semaines"),
        ("un duplicata", "un timbre fiscal", "un mois"),
        ("une autorisation", "une commission", "le trimestre"),
        ("une copie certifiée", "une validation croisée", "l'an prochain"),
    ]:
        add((
            OFFICE, "POUR AVOIR|UN FORMULAIRE|IL FAUT UN|FORMULAIRE",
            f"Le formulaire à remplir pour obtenir un formulaire ({document})", "travail / administration",
            ["travail", "bureaucratie", "formulaire", "admin"],
            [
                l_("kevin", "neutral", "Je viens chercher {0}, s'il vous plaît.".format(document)),
                l_("fournier", "happy", "Il faut d'abord remplir le formulaire de demande."),
                l_("kevin", "worried", "Le formulaire pour avoir le formulaire ?"),
                l_("fournier", "smug", "Exactement. C'est {0}. Et une pièce jointe.".format(niveau)),
                l_("kevin", "neutral", "Pièce jointe de quoi, à votre avis ?"),
                l_("fournier", "happy", "Du formulaire déjà rempli. Vous l'aurez dans {0}.".format(delai)),
                l_("kevin", "worried", "Donc je meurs de vieillesse en salle d'attente.", punch=True),
            ],
        ))

    # --- G39 : le ministre inaugure quelque chose qui n'existe pas ---
    for (lieu, promesse, realite) in [
        ("la médiathèque du quartier", "elle ouvrira en juin", "le terrain sert de parking"),
        ("la crèche de la gare", "cent places garanties", "il y a seulement un buisson"),
        ("le pont sur la rivière", "fin de chantier en 2027", "il n'y a pas de rivière"),
        ("la salle de sport municipale", "gratuite pour tous les habitants", "c'est un placard fermé à clé"),
    ]:
        add((
            STAGE, "L'INAUGURATION|DE QUELQUE CHOSE|QUI N'EXISTE PAS",
            f"Le ministre inaugure {lieu}", "politique / satire",
            ["politique", "satire", "inauguration", "humour"],
            [
                l_("ministre", "happy", "J'inaugure aujourd'hui {0} !".format(lieu)),
                l_("josette", "neutral", "Monsieur le ministre... il n'y a absolument rien ici."),
                l_("ministre", "smug", "{0}. C'est le plus beau projet du département.".format(promesse.capitalize())),
                l_("josette", "worried", "On coupe le ruban sur quoi, exactement ?"),
                l_("ministre", "happy", "Sur le terrain. Il représente l'espoir."),
                l_("josette", "angry", "En face, c'est le parking du centre commercial."),
                l_("ministre", "smug", "Alors on a inauguré la concurrence. C'est encore mieux.", punch=True),
            ],
        ))

    # --- G40 : le distributeur qui garde la monnaie ---
    for (article, somme, pretexte) in [
        ("un café", "cinquante centimes", "la machine ne rend pas les pièces"),
        ("un ticket de bus", "deux euros", "la monnaie est en réforme"),
        ("un sandwich", "trois euros cinquante", "le distributeur part en congé"),
        ("une carte de recharge", "dix euros", "la petite monnaie est devenue numérique"),
    ]:
        add((
            MARKET, "IL GARDE|LA MONNAIE|ET LE CAFÉ",
            f"Le distributeur qui garde la monnaie ({article})", "quotidien / argent",
            ["quotidien", "argent", "distributeur", "humour"],
            [
                l_("josette", "worried", "J'ai payé {0}. Il manque {1} de monnaie.".format(article, somme)),
                l_("kevin", "smug", "La machine ne rend pas. C'est son principe."),
                l_("josette", "angry", "Son principe, c'est donc de me voler {0} ?".format(somme)),
                l_("kevin", "neutral", "{0}.".format(pretexte.capitalize())),
                l_("josette", "worried", "Et je fais comment pour récupérer mon argent ?"),
                l_("kevin", "happy", "Vous patientez. Il rend tout à la fin du mois."),
                l_("josette", "angry", "Je reviens avec une pince. Elle rendra tout.", punch=True),
            ],
        ))

    # --- G41 : la carte de fidélité qui perd les points ---
    for (points, anciennete, excuse) in [
        ("mille points", "deux ans", "les points expirent en silence"),
        ("deux cents points", "un mois", "le système a été migré"),
        ("huit cents points", "six mois", "la carte a été remplacée"),
        ("cinq mille points", "trois ans", "le programme est parti en retraite"),
    ]:
        add((
            MARKET, "MA CARTE|DE FIDÉLITÉ|A DISPARU",
            f"La carte de fidélité qui perd les points ({anciennete})", "quotidien / magasin",
            ["quotidien", "magasin", "fidelite", "argent"],
            [
                l_("josette", "worried", "J'ai {0} sur ma carte. Depuis {1}.".format(points, anciennete)),
                l_("kevin", "smug", "Très bien. Vous voulez les utiliser ?"),
                l_("josette", "happy", "Oui, c'est pour mes courses du samedi."),
                l_("kevin", "neutral", "{0}.".format(excuse.capitalize())),
                l_("josette", "angry", "Comment ça prend sa retraite ? C'est une carte en plastique !"),
                l_("kevin", "smug", "Elle a servi trois ans sans congé. Elle l'a mérité."),
                l_("josette", "worried", "Donc mes points partent en vacances sans moi.", punch=True),
            ],
        ))

    # --- G42 : le répondeur « votre appel est important » ---
    for (service, duree, revelation) in [
        ("le service client", "quarante minutes", "le service client est une boucle audio"),
        ("le service technique", "une heure", "personne ne décroche le mardi"),
        ("la comptabilité", "deux heures", "tout le service est en réunion"),
        ("les ressources humaines", "trois heures", "le service a été délocalisé"),
    ]:
        add((
            FACTORY, "« VOTRE APPEL|EST IMPORTANT »|DEPUIS 40 MIN",
            f"Le répondeur qui ne passe jamais ({service})", "société / service client",
            ["quotidien", "telephone", "service", "humour"],
            [
                l_("bob", "neutral", "Vous êtes {0} en attente. Votre appel est important.".format(duree)),
                l_("kevin", "worried", "Il me dit ça depuis {0}.".format(duree)),
                l_("bob", "neutral", "Il le pense aussi. C'est pour ça qu'il le répète."),
                l_("kevin", "angry", "Je veux parler à un humain, moi."),
                l_("bob", "happy", "Un humain est en ligne. Il attend comme vous."),
                l_("kevin", "worried", "Et {0} ?".format(revelation)),
                l_("bob", "neutral", "Votre appel reste important. Bonne journée.", punch=True),
            ],
        ))

    # ============ G43 à G48 : scénarios NEUFS du 19/10/2026 =======================
    # Banque épuisée (0 post les 18-19/10) : 6 situations INÉDITES vérifiées un
    # par un contre les 82 sujets déjà produits (liste extraite des métadonnées).
    # Sujets écartés pour recouvrement : ascenseur, badge, mot de passe, prix,
    # répondeur, attente au comptoir, machine à café… Mêmes personnages, décors,
    # voix et structure (7 répliques + punch).

    # --- G43 : le parking « cinq minutes » depuis trois heures ---
    for (lieu, duree, excuse) in [
        ("devant la boulangerie", "trois heures", "c'est une dépose minute, ça se dépose et ça repart"),
        ("devant l'école", "deux heures", "le compteur est en grève"),
        ("devant la pharmacie", "une heure et demie", "la place est prioritaire pour tout le monde"),
        ("devant la mairie", "quatre heures", "l'agent est allé chercher la machine à lire les plaques"),
    ]:
        add((
            MARKET, "LE PARKING « CINQ MINUTES »|DEPUIS TROIS HEURES",
            f"Le parking « cinq minutes » depuis {duree} ({lieu})", "quotidien / rue",
            ["quotidien", "parking", "voiture", "humour"],
            [
                l_("josette", "worried", "Je suis garée {0} depuis {1}.".format(lieu, duree)),
                l_("kevin", "smug", "Oui. C'est une dépose minute."),
                l_("josette", "angry", "Je dépose quoi, exactement ?"),
                l_("kevin", "happy", "{0}.".format(excuse.capitalize())),
                l_("josette", "worried", "Et l'agent qui tourne autour de ma voiture depuis dix minutes ?"),
                l_("kevin", "neutral", "Il dépose aussi. Il repartira."),
                l_("josette", "angry", "Je suis pressée, moi. Je me dépose donc ici pour toujours.", punch=True),
            ],
        ))

    # --- G44 : la cantine et le plat du jour fantôme ---
    for (plat, excuse, alternative) in [
        ("le gratin dauphinois", "il était au menu hier", "il sera peut-être demain"),
        ("le poisson du vendredi", "c'est le poisson de mardi", "vous vous confondez de jour"),
        ("l'omelette aux fines herbes", "les herbes sont en congé", "la cuisine improvise à la place"),
        ("le dessert du chef", "le chef est parti", "il revient avec des idées"),
    ]:
        add((
            OFFICE, "LE PLAT DU JOUR|N'EXISTE PLUS|DEPUIS HIER",
            f"La cantine et le plat du jour fantôme ({plat})", "travail / cantine",
            ["travail", "cantine", "bureau", "humour"],
            [
                l_("kevin", "happy", "Bonjour, je voudrais {0}, s'il vous plaît.".format(plat)),
                l_("fournier", "smug", "Ah. Il n'est plus au menu."),
                l_("kevin", "angry", "Il était écrit en gros sur l'ardoise !"),
                l_("fournier", "neutral", "{0}. C'est très évolutif.".format(excuse.capitalize())),
                l_("kevin", "worried", "Et je mange quoi, du coup ?"),
                l_("fournier", "happy", "Vous avez de la chance : il reste {0}.".format(alternative)),
                l_("kevin", "angry", "Je suis tombé amoureux d'un plat fantôme. C'est ça ?", punch=True),
            ],
        ))

    # --- G45 : le logiciel de pointage en retard avant l'arrivée ---
    for (heure, responsable, excuse) in [
        ("huit heures trente", "le service informatique", "le logiciel a son propre fuseau horaire"),
        ("neuf heures pile", "les ressources humaines", "la pointeuse se synchronise avec la lune"),
        ("huit heures", "le prestataire", "la mise à jour a décalé la matinée"),
        ("neuf heures quinze", "la direction", "le logiciel pointe l'intention, pas l'arrivée"),
    ]:
        add((
            OFFICE, "LE LOGICIEL DE POINTAGE|ME MET EN RETARD|AVANT MON ARRIVÉE",
            f"Le pointage en retard à cause du logiciel ({heure})", "travail / horaires",
            ["travail", "bureau", "pointage", "humour"],
            [
                l_("kevin", "worried", "J'ai pointé à {0} et le logiciel me met en retard.".format(heure)),
                l_("fournier", "smug", "Le logiciel ne se trompe pas. C'est un algorithme."),
                l_("kevin", "angry", "L'algorithme dit que je suis arrivé après moi-même."),
                l_("fournier", "happy", "{0} a validé le fonctionnement.".format(responsable.capitalize())),
                l_("kevin", "neutral", "Et la raison, officiellement ?"),
                l_("fournier", "smug", "{0}. C'est optimisé.".format(excuse.capitalize())),
                l_("kevin", "worried", "Donc je travaille, mais en retard de façon scientifique.", punch=True),
            ],
        ))

    # --- G46 : « tu as deux secondes ? » ---
    for (sujet, duree, consequence) in [
        ("un truc rapide", "quarante-cinq minutes", "la réunion de dix heures est passée"),
        ("une petite modif", "une heure", "le café de dix heures est froid depuis longtemps"),
        ("un avis d'expert", "trente minutes", "on a fini par faire son idée"),
        ("deux secondes", "une heure vingt", "le déjeuner est devenu une réunion debout"),
    ]:
        add((
            OFFICE, "« TU AS|DEUX SECONDES ? »|NON.",
            f"Le collègue qui demande « deux secondes » ({duree})", "travail / bureau",
            ["travail", "bureau", "collègue", "humour"],
            [
                l_("fournier", "happy", "Kevin, tu as {0} ? C'est pour le boulot.".format(sujet)),
                l_("kevin", "neutral", "Oui, vas-y. Je t'écoute."),
                l_("fournier", "neutral", "(elle explique, puis explique encore, puis reformule)"),
                l_("kevin", "worried", "Il y a cinq minutes, tu avais deux secondes."),
                l_("fournier", "happy", "C'est justement le sujet : ça va vite."),
                l_("kevin", "angry", "{0} sont passées. {1}.".format(duree.capitalize(), consequence.capitalize())),
                l_("kevin", "worried", "On ne m'arrête plus. Je suis devenu une salle d'attente.", punch=True),
            ],
        ))

    # --- G47 : l'imprimante qui n'a jamais de toner ---
    for (doc, symptome, excuse) in [
        ("le contrat de trois pages", "le toner est détecté à sec", "l'imprimante a faim, ce n'est pas grave"),
        ("la note de frais", "il manque le cyan", "le cyan est en retraite"),
        ("la candidature du stagiaire", "elle imprime en miroir", "c'est une version originale"),
        ("le plan de la salle de réunion", "elle mange la dernière page", "elle vérifie la confidentialité"),
    ]:
        add((
            OFFICE, "L'IMPRIMANTE|N'A JAMAIS|DE TONER",
            f"L'imprimante qui n'a jamais de toner ({doc})", "travail / bureau",
            ["travail", "bureau", "imprimante", "humour"],
            [
                l_("kevin", "angry", "L'imprimante refuse. {0}.".format(symptome.capitalize())),
                l_("fournier", "smug", "Vous n'avez pas mis de papier."),
                l_("kevin", "worried", "Il y a du papier. Elle a avalé les trois feuilles d'avant."),
                l_("fournier", "happy", "{0}. Elle est plus maligne que vous.".format(excuse.capitalize())),
                l_("kevin", "neutral", "Je veux juste imprimer {0} !".format(doc)),
                l_("fournier", "neutral", "Alors demandez poliment. Et changez le toner. Et la lumière."),
                l_("kevin", "angry", "Je vais la négocier à la place. Elle comprend mieux les siens.", punch=True),
            ],
        ))

    # --- G48 : la dernière modification à dix-huit heures ---
    for (heure, chef, modif) in [
        ("dix-huit heures", "le directeur", "un dernier petit ajustement"),
        ("sept heures du soir", "la cheffe de projet", "une régression de deux pixels"),
        ("vingt heures", "le client", "on a repensé le concept"),
        ("minuit moins le quart", "le chef de projet", "une dernière chose avant demain"),
    ]:
        add((
            OFFICE, "LA DERNIÈRE MODIF|À DIX-HUIT|HEURES",
            f"La dernière modification à {heure} ({modif})", "travail / projets",
            ["travail", "bureau", "deadline", "humour"],
            [
                l_("fournier", "neutral", "Ce n'est pas livré ?"),
                l_("kevin", "worried", "Si. Il y a une heure. Vous aviez validé."),
                l_("fournier", "happy", "Oui, mais {0}. C'est tout petit.".format(modif)),
                l_("kevin", "angry", "À {0} ? Moi, je finis à dix-huit heures.".format(heure)),
                l_("fournier", "smug", "Les talents ne comptent pas les heures. {0} l'a demandé.".format(chef.capitalize())),
                l_("kevin", "neutral", "Et la modif, elle est dans le cahier des charges ?"),
                l_("fournier", "happy", "Non. Elle est dans ton cœur. Livre-la pour demain.", punch=True),
            ],
        ))

    return eps