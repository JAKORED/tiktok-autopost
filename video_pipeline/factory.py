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


def _ep(no, pair, headline, title, topic, tags, lines):
    key = f"{pair[0]}_{pair[1]}"
    return dict(
        id=f"auto_{no:03d}", ep=no, set=SETS[key], left=pair[0], right=pair[1],
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
        eps.append(_ep(no, *e))

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

    return eps