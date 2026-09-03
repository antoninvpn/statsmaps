#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_geojson.py — prépare le fond de carte de StatsMaps.

Ce que fait ce script, en une phrase :
il télécharge les frontières des pays du monde, les allège, et les range
dans data/pays.json pour que la carte s'affiche très vite.

À lancer :  python3 scripts/build_geojson.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).
"""

import json
import os
import sys
import urllib.request

# --- Réglages -------------------------------------------------------------

# Frontières du monde, résolution 1:50 millions. Domaine public.
#
# Pourquoi le 1:50m et pas le 1:110m (plus léger) ? Parce que le 110m ne
# contient que 177 pays : il oublie tous les petits, dont Singapour, Hong Kong,
# Malte et le Liechtenstein — qui est pourtant le premier pays du monde pour le
# PIB par habitant. Avec le 50m, les 197 pays suivis par le FMI sont présents.
SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
    "/master/geojson/ne_50m_admin_0_countries.geojson"
)

# Natural Earth publie à part le contour des territoires disputés. On y prend
# le plateau du Golan, que le fichier principal dessine à l'intérieur d'Israël.
SOURCE_DISPUTES = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
    "/master/geojson/ne_50m_admin_0_breakaway_disputed_areas.geojson"
)

# L'Antarctique n'est pas un pays, n'a aucune donnée économique, et occupe une
# grande tache grise en bas de la carte. On ne le garde pas.
PAYS_EXCLUS = {"ATA"}

# --- Territoires fusionnés -----------------------------------------------
# Natural Earth dessine certains territoires comme des pays à part entière,
# parce qu'ils sont administrés séparément « dans les faits ». StatsMaps suit
# la reconnaissance internationale : ces territoires sont fondus dans le pays
# dont ils font officiellement partie, sans laisser de trait entre les deux.
#
# Format : (code du territoire absorbé, code du pays qui l'absorbe, explication)
#
# Cas à part : le Sahara occidental. L'ONU le classe « territoire non autonome »
# et ne reconnaît pas la souveraineté marocaine ; contrairement aux deux autres
# lignes ci-dessous, cette fusion-là est donc un choix éditorial de StatsMaps et
# non l'application du droit international. Il est assumé et volontaire.
FUSIONS = [
    ("CYN", "CYP", "Chypre du Nord, reconnue par la seule Turquie, fondue dans Chypre"),
    ("SOL", "SOM", "le Somaliland, reconnu par aucun État, fondu dans la Somalie"),
    ("SAH", "MAR", "le Sahara occidental fondu dans le Maroc"),
]

# --- Qui figure dans le classement ? -------------------------------------
# Le classement du site compte 197 pays : les 193 États membres de l'ONU, plus
# le Vatican, la Palestine, Taïwan et le Kosovo.
#
# Le FMI, lui, ne publie pas exactement cette liste. Deux corrections :

# 1. Quatre pays souverains que le FMI ne suit pas. Ils doivent quand même
#    apparaître dans le classement, à la ligne « donnée non disponible ».
#    (Cuba et la Corée du Nord ne transmettent pas leurs chiffres au FMI ;
#    Monaco et le Vatican n'en sont pas membres.)
PAYS_HORS_FMI = {"CUB", "PRK", "MCO", "VAT"}

# 2. Quatre entités suivies par le FMI qui ne sont PAS des États souverains.
#    Elles restent sur la carte avec leur chiffre et leur couleur, mais ne sont
#    ni numérotées ni comptées dans le classement. Elles portent deux drapeaux :
#    d'abord celui de l'État dont elles dépendent, puis le leur.
#    Format : code du territoire -> code à deux lettres de l'État.
TERRITOIRES = {
    "PRI": "US",  # Puerto Rico, territoire non incorporé des États-Unis
    "HKG": "CN",  # Hong Kong, région administrative spéciale de la Chine
    "MAC": "CN",  # Macao, région administrative spéciale de la Chine
    "ABW": "NL",  # Aruba, pays constitutif du royaume des Pays-Bas
}

# --- Les territoires rattachés à leur État -------------------------------
# Natural Earth dessine séparément les territoires dépendants : le Groenland,
# la Nouvelle-Calédonie, les Bermudes... Faute de chiffres du FMI, ils
# apparaissaient tous en gris « donnée non disponible », ce qui donnait une
# carte trouée sans que ce gris veuille dire quoi que ce soit d'utile.
#
# StatsMaps les rattache donc à l'État dont ils dépendent : ils en prennent la
# couleur et la valeur. Le Groenland devient danois, Tahiti française,
# les Malouines britanniques.
#
# EXCEPTION IMPORTANTE : les quatre territoires que le FMI suit séparément —
# Hong Kong, Macao, Puerto Rico et Aruba — ne sont PAS rattachés. Ils ont leurs
# propres chiffres, et les fondre dans la Chine, les États-Unis ou les Pays-Bas
# reviendrait à jeter ces chiffres à la poubelle. Ils gardent donc leur forme,
# leur couleur, et leur double drapeau dans le classement (voir TERRITOIRES).
TERRITOIRES_RATTACHES = {
    "GBR": ["AIA", "BMU", "CYM", "FLK", "GGY", "IMN", "IOT", "JEY",
            "MSR", "PCN", "SGS", "SHN", "TCA", "VGB"],
    "FRA": ["ATF", "BLM", "MAF", "NCL", "PYF", "SPM", "WLF"],
    "USA": ["ASM", "GUM", "MNP", "VIR"],
    "AUS": ["ATC", "HMD", "IOA", "NFK"],
    "DNK": ["FRO", "GRL"],
    "NLD": ["CUW", "SXM"],
    # Niue et les îles Cook ne sont pas des dépendances au sens strict : ce sont
    # des États librement associés à la Nouvelle-Zélande. Natural Earth les
    # classe toutefois en « Dependency », et ils n'ont aucun chiffre du FMI.
    # Pour retirer ce rattachement, il suffit d'effacer la ligne ci-dessous.
    "NZL": ["COK", "NIU"],
    "FIN": ["ALD"],
}

# --- Trois enclaves trop petites pour le fond de carte -------------------
# Gibraltar (6,8 km²), Ceuta (18,5 km²) et Melilla (12,3 km²) n'existent pas
# dans le fichier 1:50 millions : Natural Earth ne les dessine pas à cette
# échelle. Leurs contours sont donc recopiés ici depuis le fichier 1:10
# millions du même Natural Earth, plutôt que de télécharger 12 Mo pour trois
# formes qui ne changeront jamais.
#
# Ils gardent 4 décimales (environ 11 mètres) au lieu de 2 : à 1 km près,
# Gibraltar, qui fait 1,7 km sur 3,3 km, disparaîtrait purement et simplement.
#
# Format : (nom, code du pays auquel on l'ajoute, contours)
ENCLAVES = [
    ("Gibraltar", "GBR", [[[-5.3584, 36.1411], [-5.3388, 36.1411], [-5.3399, 36.1298], [-5.3391, 36.1238], [-5.342, 36.1105], [-5.3502, 36.1193], [-5.3584, 36.1411]]]),
    ("Ceuta", "ESP", [[[-5.3407, 35.8474], [-5.3629, 35.8638], [-5.3784, 35.8817], [-5.3897, 35.902], [-5.3989, 35.9245], [-5.3852, 35.9262], [-5.3662, 35.9248], [-5.3441, 35.9147], [-5.3274, 35.9042], [-5.3093, 35.9008], [-5.2831, 35.9117], [-5.2919, 35.8905], [-5.3356, 35.8624], [-5.3407, 35.8474]], [[-5.4188, 35.9156], [-5.416, 35.9135], [-5.4179, 35.9109], [-5.4203, 35.9116], [-5.4208, 35.9143], [-5.4188, 35.9156]]]),
    ("Melilla", "ESP", [[[-2.9478, 35.3298], [-2.922, 35.288], [-2.9132, 35.2772], [-2.9129, 35.2769], [-2.943, 35.2679], [-2.9638, 35.2862], [-2.9669, 35.3139], [-2.9478, 35.3298]]]),
]

# Précision des coordonnées, en nombre de décimales.
# 2 décimales ≈ 1 km de précision : largement suffisant pour une carte du monde,
# et ça divise le poids du fichier par 5.
DECIMALES = 2

# Le fond de carte et le FMI n'utilisent pas toujours le même code pour un pays.
# Voici les rares cas à corriger pour que les données se collent bien.
CORRECTIONS_CODES = {
    "KOS": "UVK",  # Kosovo
    "SDS": "SSD",  # Soudan du Sud
    "PSX": "WBG",  # Palestine -> "West Bank and Gaza" chez le FMI
}

# Quelques pays ont un nom officiel trop long pour tenir dans le classement.
# On leur donne ici le nom court d'usage, dans les trois langues du site :
#                     (français, anglais, ukrainien)
NOMS_COURTS = {
    "CHN": ("Chine", "China", "Китай"),
    "USA": ("États-Unis", "United States", "США"),
    "COD": ("Rép. dém. du Congo", "DR Congo", "ДР Конго"),
    "CAF": ("Rép. centrafricaine", "Central African Rep.", "ЦАР"),
    "DOM": ("Rép. dominicaine", "Dominican Rep.", "Домініканська Респ."),
    "PNG": ("Papouasie-N.-Guinée", "Papua New Guinea", "Папуа-Нова Гвінея"),
    "SSD": ("Soudan du Sud", "South Sudan", "Південний Судан"),
    "BIH": ("Bosnie-Herzégovine", "Bosnia & Herzegovina", "Боснія і Герцеговина"),
    "STP": ("Sao Tomé-et-Principe", "São Tomé & Príncipe", "Сан-Томе і Принсіпі"),
    "ARE": ("Émirats arabes unis", "United Arab Emirates", "ОАЕ"),
    "GBR": ("Royaume-Uni", "United Kingdom", "Велика Британія"),
    "PRK": ("Corée du Nord", "North Korea", "Північна Корея"),
    "KOR": ("Corée du Sud", "South Korea", "Південна Корея"),
    "LAO": ("Laos", "Laos", "Лаос"),
    "SYR": ("Syrie", "Syria", "Сирія"),
    "VAT": ("Vatican", "Vatican", "Ватикан"),
    "ZAF": ("Afrique du Sud", "South Africa", "ПАР"),
    "VCT": ("Saint-Vincent-et-les-Gr.", "St. Vincent & Gren.", "Сент-Вінсент і Гренадини"),
    "KNA": ("Saint-Kitts-et-Nevis", "St. Kitts & Nevis", "Сент-Кітс і Невіс"),
    "ATG": ("Antigua-et-Barbuda", "Antigua & Barbuda", "Антигуа і Барбуда"),
    "TTO": ("Trinité-et-Tobago", "Trinidad & Tobago", "Тринідад і Тобаго"),
    "MKD": ("Macédoine du Nord", "North Macedonia", "Північна Македонія"),
    "GNQ": ("Guinée équatoriale", "Equatorial Guinea", "Екваторіальна Гвінея"),
    "IRN": ("Iran", "Iran", "Іран"),
    "VEN": ("Venezuela", "Venezuela", "Венесуела"),
    "TZA": ("Tanzanie", "Tanzania", "Танзанія"),
    "BOL": ("Bolivie", "Bolivia", "Болівія"),
    "MDA": ("Moldavie", "Moldova", "Молдова"),
    # L'usage français écrit « Porto Rico ». C'est une déformation : le nom du
    # territoire est espagnol et s'écrit Puerto Rico. On garde la forme exacte.
    "PRI": ("Puerto Rico", "Puerto Rico", "Пуерто-Рико"),
    # Natural Earth donne « Аоминь » (transcription du chinois) ; en ukrainien
    # l'usage courant est « Макао ».
    "MAC": ("Macao", "Macao", "Макао"),
}

# --- La Crimée -----------------------------------------------------------
# Natural Earth rattache la Crimée à la Russie : c'est leur vue « de fait »,
# celle du contrôle militaire sur le terrain.
# StatsMaps suit le droit international : la résolution 68/262 de l'Assemblée
# générale de l'ONU (mars 2014) reconnaît la Crimée comme territoire ukrainien.
# On la déplace donc du côté ukrainien.
#
# Dans le fichier source, la Crimée est un morceau séparé de la géométrie
# russe. On le reconnaît à sa position : cette « boîte » l'entoure et ne
# contient aucun autre morceau de la Russie.
CRIMEE_BOITE = (32.0, 44.0, 37.0, 46.5)  # lon min, lat min, lon max, lat max

# --- Les Kouriles du Sud -------------------------------------------------
# Natural Earth rattache à la Russie les quatre groupes d'îles qu'elle occupe
# depuis 1945 : Etorofu (Itouroup), Kounachiri (Kounachir), Chikotan et les
# Habomai. Le Japon les revendique sous le nom de « Territoires du Nord » ;
# aucun traité de paix n'a jamais réglé la question depuis 1945.
# StatsMaps les rattache au Japon.
#
# Ce sont des îles : il n'y a rien à souder, il suffit de les déplacer.
# On les reconnaît à leur position. Cette boîte ne contient aucun autre morceau
# de la Russie : l'île d'Ouroup, la suivante vers le nord et incontestablement
# russe, ne commence qu'à 45,8° de latitude et 149,2° de longitude.
KOURILES_BOITE = (145.0, 43.0, 149.0, 45.6)

# --- Le plateau du Golan -------------------------------------------------
# Natural Earth dessine le Golan à l'intérieur d'Israël, qui l'occupe depuis
# 1967 et l'a annexé en 1981. La résolution 497 du Conseil de sécurité de l'ONU
# a déclaré cette annexion « nulle et non avenue » ; le Golan reste syrien pour
# le droit international. StatsMaps le rattache donc à la Syrie.
#
# Contrairement aux Kouriles, ce n'est pas une île : il faut découper le
# contour israélien, puis souder le morceau obtenu à la Syrie.
NOM_GOLAN = "Golan Heights"

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Le fichier porte l'extension .json et non .geojson : c'est le même contenu,
# mais GitHub ne compresse de façon garantie que les types qu'il reconnaît.
# Ici, ça fait passer le téléchargement de 1 371 Ko à environ 400 Ko.
FICHIER_SORTIE = os.path.join(RACINE, "data", "pays.json")


# --- Outils ---------------------------------------------------------------

def telecharger(url):
    """Télécharge une URL et renvoie le JSON décodé."""
    print("  Téléchargement de %s ..." % url.split("/")[-1])
    requete = urllib.request.Request(url, headers={"User-Agent": "StatsMaps/1.0"})
    with urllib.request.urlopen(requete, timeout=120) as reponse:
        return json.loads(reponse.read().decode("utf-8"))


def contour_dispute(fichier_disputes, nom):
    """Va chercher un territoire disputé dans le fichier de Natural Earth et
    renvoie son contour, arrondi comme le reste de la carte."""
    for element in fichier_disputes["features"]:
        if element["properties"].get("NAME") == nom:
            geometrie = element["geometry"]
            coords = (geometrie["coordinates"] if geometrie["type"] == "Polygon"
                      else geometrie["coordinates"][0])
            return arrondir(coords)[0]
    return None


def drapeau(code_deux_lettres):
    """Transforme un code de pays à deux lettres (FR) en drapeau emoji (🇫🇷).

    Un drapeau emoji n'est pas une image : c'est simplement les deux lettres du
    pays écrites dans un alphabet spécial (dit « indicateurs régionaux »). Le
    téléphone ou l'ordinateur du visiteur les remplace tout seul par le dessin.
    Sur Windows, qui n'a pas ces dessins, les deux lettres restent visibles."""
    code = (code_deux_lettres or "").upper()
    if len(code) != 2 or not code.isalpha():
        return ""  # pas de code utilisable : pas de drapeau, et c'est tout
    return "".join(chr(0x1F1E6 + ord(lettre) - ord("A")) for lettre in code)


def arrondir(coordonnees):
    """Arrondit récursivement toutes les coordonnées d'une géométrie."""
    if isinstance(coordonnees[0], (int, float)):
        return [round(coordonnees[0], DECIMALES), round(coordonnees[1], DECIMALES)]
    return [arrondir(element) for element in coordonnees]


def anneaux_valides(geometrie):
    """
    Après arrondi, un tout petit pays peut se réduire à un point.
    On enlève les morceaux devenus trop petits pour être dessinés.
    """
    type_geom = geometrie["type"]
    coords = geometrie["coordinates"]

    def anneau_ok(anneau):
        # Un polygone a besoin d'au moins 4 points distincts pour être dessinable.
        return len(set(map(tuple, anneau))) >= 3

    if type_geom == "Polygon":
        anneaux = [a for a in coords if anneau_ok(a)]
        return {"type": "Polygon", "coordinates": anneaux} if anneaux else None

    if type_geom == "MultiPolygon":
        polygones = []
        for polygone in coords:
            anneaux = [a for a in polygone if anneau_ok(a)]
            if anneaux:
                polygones.append(anneaux)
        return {"type": "MultiPolygon", "coordinates": polygones} if polygones else None

    return geometrie


def liste_des_polygones(geometrie):
    """Renvoie toujours une liste de polygones, que la géométrie soit un
    Polygon (un seul morceau) ou un MultiPolygon (plusieurs morceaux)."""
    if geometrie["type"] == "Polygon":
        return [geometrie["coordinates"]]
    return list(geometrie["coordinates"])


def aire(contour):
    """Surface d'un contour (formule dite « du lacet »). Sert de contrôle."""
    total = 0.0
    for i in range(len(contour) - 1):
        x1, y1 = contour[i]
        x2, y2 = contour[i + 1]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def suite_partagee(contour, points_communs):
    """Repère, dans un contour, la suite ININTERROMPUE de points communs.
    Renvoie leurs positions, ou None si la situation est ambiguë."""
    n = len(contour)
    positions = [i for i, pt in enumerate(contour) if tuple(pt) in points_communs]
    if not positions:
        return None
    ensemble = set(positions)
    # Le début de la suite : un point commun dont le précédent ne l'est pas.
    debuts = [i for i in positions if (i - 1) % n not in ensemble]
    if len(debuts) != 1:
        return None  # plusieurs suites séparées : trop risqué, on renonce
    suite, i = [], debuts[0]
    while i in ensemble and len(suite) <= n:
        suite.append(i)
        i = (i + 1) % n
    return suite if len(suite) == len(positions) else None


def cote_exclusive(contour, suite):
    """Le trajet propre à ce morceau : tout son contour SAUF la partie
    partagée, mais en gardant les deux points de jonction."""
    n = len(contour)
    trajet, i = [], suite[-1]
    while True:
        trajet.append(contour[i])
        if i == suite[0]:
            return trajet
        i = (i + 1) % n
        if len(trajet) > n + 1:
            return None


def souder(contour_a, contour_b):
    """Fusionne deux contours qui se touchent le long d'une frontière commune,
    de façon à n'en former qu'un seul, sans trait au milieu.
    Renvoie None si la fusion n'est pas sûre — on préfère ne rien faire."""
    a, b = contour_a[:-1], contour_b[:-1]  # on retire le point de fermeture
    communs = set(map(tuple, a)) & set(map(tuple, b))
    if len(communs) < 2:
        return None

    suite_a = suite_partagee(a, communs)
    suite_b = suite_partagee(b, communs)
    if suite_a is None or suite_b is None:
        return None

    # La frontière commune doit être la même des deux côtés, à l'envers.
    if [a[i] for i in suite_a] != [b[i] for i in reversed(suite_b)]:
        return None

    trajet_a = cote_exclusive(a, suite_a)
    trajet_b = cote_exclusive(b, suite_b)
    if trajet_a is None or trajet_b is None:
        return None

    fusion = trajet_b[:-1] + trajet_a[:-1]
    fusion.append(fusion[0])  # on referme le contour

    # Contrôle : la surface obtenue doit être la somme des deux surfaces.
    attendu = aire(contour_a) + aire(contour_b)
    if attendu == 0 or abs(aire(fusion) - attendu) / attendu > 0.01:
        return None
    return fusion


def detacher(contour_entier, contour_partie):
    """L'opération inverse de souder() : retire d'un pays un territoire dessiné
    à l'intérieur de son contour, et renvoie le contour du pays sans lui.
    Renvoie None si le découpage n'est pas sûr — on préfère ne rien faire."""
    entier, partie = contour_entier[:-1], contour_partie[:-1]
    communs = set(map(tuple, entier)) & set(map(tuple, partie))
    if len(communs) < 2:
        return None

    suite_entier = suite_partagee(entier, communs)
    suite_partie = suite_partagee(partie, communs)
    if suite_entier is None or suite_partie is None:
        return None

    # Ce qui reste du contour du pays une fois enlevé le bord extérieur du
    # territoire, et la ligne de séparation entre les deux.
    reste = cote_exclusive(entier, suite_entier)
    coupe = cote_exclusive(partie, suite_partie)
    if reste is None or coupe is None:
        return None

    attendu = aire(contour_entier) - aire(contour_partie)
    if attendu <= 0:
        return None

    # Le territoire est À L'INTÉRIEUR du pays : son bord extérieur suit donc le
    # contour du pays dans le même sens. Pour refermer le pays sans lui, on
    # parcourt ce qui reste de son contour, puis la ligne de séparation À
    # L'ENVERS. (Le second essai couvre le cas où la source changerait de sens.)
    for anneau in (reste[:-1] + coupe[::-1][:-1], reste[:-1] + coupe[:-1]):
        ferme = anneau + [anneau[0]]
        if abs(aire(ferme) - attendu) / attendu < 0.005:
            return ferme
    return None


def rattacher_golan_a_la_syrie(pays, contour_golan):
    """Retire le plateau du Golan du contour israélien, puis le soude à la
    Syrie de façon qu'aucun trait ne subsiste à l'intérieur de celle-ci."""
    israel = syrie = None
    for element in pays:
        code = element["properties"]["iso"]
        if code == "ISR":
            israel = element
        elif code == "SYR":
            syrie = element
    if israel is None or syrie is None or contour_golan is None:
        return False

    morceaux_israel = liste_des_polygones(israel["geometry"])
    for indice, morceau in enumerate(morceaux_israel):
        sans_golan = detacher(morceau[0], contour_golan)
        if sans_golan is not None:
            morceaux_israel[indice] = [sans_golan] + morceau[1:]
            break
    else:
        print("  ATTENTION : découpage du Golan impossible, rien n'a été fait.")
        return False

    if len(morceaux_israel) == 1:
        israel["geometry"] = {"type": "Polygon", "coordinates": morceaux_israel[0]}
    else:
        israel["geometry"] = {"type": "MultiPolygon", "coordinates": morceaux_israel}

    # Le Golan touche la Syrie : on les soude pour qu'aucune frontière interne
    # ne reste visible.
    morceaux_syrie = liste_des_polygones(syrie["geometry"])
    for indice, morceau in enumerate(morceaux_syrie):
        fusion = souder(morceau[0], contour_golan)
        if fusion is not None:
            morceaux_syrie[indice] = [fusion] + morceau[1:]
            break
    else:
        morceaux_syrie.append([contour_golan])
        print("  ATTENTION : soudure du Golan impossible, il reste un morceau"
              " séparé (un trait de contour restera visible).")

    if len(morceaux_syrie) == 1:
        syrie["geometry"] = {"type": "Polygon", "coordinates": morceaux_syrie[0]}
    else:
        syrie["geometry"] = {"type": "MultiPolygon", "coordinates": morceaux_syrie}
    return True


def cadrage_du_pays(geometrie):
    """La zone que la carte doit afficher quand on clique sur ce pays.

    On ne peut pas simplement englober tous ses morceaux : la France possède
    des îles dans le Pacifique et l'Espagne les Canaries. On cadre donc sur le
    plus gros morceau, en y ajoutant seulement ceux qui sont juste à côté —
    moins de 20 degrés, soit environ 2 000 km. Le Japon garde ainsi ses quatre
    îles et l'Indonésie son archipel, mais Tahiti ne tire plus la France à
    l'autre bout du monde.

    Ce calcul est fait ICI, et pas dans le navigateur, parce qu'il doit avoir
    lieu AVANT que les territoires dépendants soient rattachés : sinon le
    Groenland, plus grand que le Danemark, deviendrait « le plus gros morceau
    du Danemark » et cliquer sur Copenhague cadrerait sur l'Arctique."""
    boites = []
    for morceau in liste_des_polygones(geometrie):
        lons = [point[0] for point in morceau[0]]
        lats = [point[1] for point in morceau[0]]
        boites.append((min(lons), min(lats), max(lons), max(lats)))

    principale = max(boites, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
    proches = [
        b for b in boites
        if max(0, principale[0] - b[2], b[0] - principale[2]) <= 20
        and max(0, principale[1] - b[3], b[1] - principale[3]) <= 20
    ]
    return [round(min(b[0] for b in proches), 2), round(min(b[1] for b in proches), 2),
            round(max(b[2] for b in proches), 2), round(max(b[3] for b in proches), 2)]


def ajouter_enclaves(pays):
    """Ajoute au fond de carte les trois enclaves absentes du fichier source."""
    ajoutees = []
    for nom, code_hote, contours in ENCLAVES:
        hote = None
        for element in pays:
            if element["properties"]["iso"] == code_hote:
                hote = element
                break
        if hote is None:
            continue
        morceaux = liste_des_polygones(hote["geometry"]) + [[c] for c in contours]
        hote["geometry"] = {"type": "MultiPolygon", "coordinates": morceaux}
        ajoutees.append(nom)
    if ajoutees:
        print("  Enclaves ajoutées : %s." % ", ".join(ajoutees))
    return ajoutees


def deplacer_iles(pays, code_source, code_destination, boite, explication):
    """Déplace d'un pays à l'autre tous les morceaux entièrement contenus dans
    une boîte. Réservé aux ÎLES : rien n'est soudé, les morceaux changent
    simplement de propriétaire."""
    source = destination = None
    for element in pays:
        code = element["properties"]["iso"]
        if code == code_source:
            source = element
        elif code == code_destination:
            destination = element
    if source is None or destination is None:
        return False

    lon_min, lat_min, lon_max, lat_max = boite

    def dans_la_boite(polygone):
        contour = polygone[0]
        lons = [point[0] for point in contour]
        lats = [point[1] for point in contour]
        return (lon_min <= min(lons) and max(lons) <= lon_max
                and lat_min <= min(lats) and max(lats) <= lat_max)

    morceaux_source = liste_des_polygones(source["geometry"])
    deplaces = [m for m in morceaux_source if dans_la_boite(m)]
    if not deplaces:
        print("  ATTENTION : aucune île trouvée pour %s." % explication)
        return False

    source["geometry"] = {
        "type": "MultiPolygon",
        "coordinates": [m for m in morceaux_source if not dans_la_boite(m)],
    }
    destination["geometry"] = {
        "type": "MultiPolygon",
        "coordinates": liste_des_polygones(destination["geometry"]) + deplaces,
    }
    print("  %s (%d île(s) déplacée(s))." % (explication, len(deplaces)))
    return True


def fusionner(pays, code_absorbe, code_hote, explication=None):
    """Fond un territoire dans un autre pays : les contours qui se touchent
    sont soudés, les îles détachées sont simplement rattachées.
    Le territoire absorbé disparaît de la liste."""
    absorbe = hote = None
    for element in pays:
        code = element["properties"]["iso"]
        if code == code_absorbe:
            absorbe = element
        elif code == code_hote:
            hote = element
    if absorbe is None or hote is None:
        return False

    morceaux = liste_des_polygones(hote["geometry"])
    soudures = 0

    for morceau in liste_des_polygones(absorbe["geometry"]):
        for indice, cible in enumerate(morceaux):
            fusion = souder(cible[0], morceau[0])
            if fusion is not None:
                # [contour extérieur soudé] + les éventuels trous des deux côtés
                morceaux[indice] = [fusion] + cible[1:] + morceau[1:]
                soudures += 1
                break
        else:
            morceaux.append(morceau)  # île séparée : rien à souder

    if len(morceaux) == 1:
        hote["geometry"] = {"type": "Polygon", "coordinates": morceaux[0]}
    else:
        hote["geometry"] = {"type": "MultiPolygon", "coordinates": morceaux}

    pays.remove(absorbe)
    if explication:
        print("  Fusion : %s (%d soudure(s))." % (explication, soudures))
    return True


def rattacher_crimee_a_ukraine(pays):
    """Déplace le morceau « Crimée » de la Russie vers l'Ukraine,
    puis le soude au continent pour qu'aucun trait ne les sépare.
    Renvoie True si le déplacement a bien eu lieu."""
    russie = ukraine = None
    for element in pays:
        code = element["properties"]["iso"]
        if code == "RUS":
            russie = element
        elif code == "UKR":
            ukraine = element
    if russie is None or ukraine is None:
        return False

    lon_min, lat_min, lon_max, lat_max = CRIMEE_BOITE

    def est_la_crimee(polygone):
        contour = polygone[0]
        lons = [point[0] for point in contour]
        lats = [point[1] for point in contour]
        return (lon_min <= min(lons) and max(lons) <= lon_max
                and lat_min <= min(lats) and max(lats) <= lat_max)

    morceaux_russie = liste_des_polygones(russie["geometry"])
    crimee = [m for m in morceaux_russie if est_la_crimee(m)]
    if len(crimee) != 1:
        # Le fichier source a changé : on préfère ne rien faire plutôt que
        # de déplacer le mauvais morceau, et on le signale.
        print("  ATTENTION : %d morceau(x) trouvé(s) dans la zone de la Crimée,"
              " déplacement annulé." % len(crimee))
        return False

    restants = [m for m in morceaux_russie if not est_la_crimee(m)]
    russie["geometry"] = {"type": "MultiPolygon", "coordinates": restants}

    morceaux_ukraine = liste_des_polygones(ukraine["geometry"]) + crimee

    # La Crimée est reliée au continent par l'isthme de Perekop : les deux
    # morceaux se touchent déjà. On les soude pour qu'aucun trait de contour
    # ne vienne dessiner une frontière à l'intérieur de l'Ukraine.
    contour_crimee = crimee[0][0]
    for indice, morceau in enumerate(morceaux_ukraine):
        if morceau is crimee[0]:
            continue
        fusion = souder(morceau[0], contour_crimee)
        if fusion is not None:
            # Le morceau soudé remplace le continent, et la Crimée disparaît
            # en tant que morceau distinct.
            morceaux_ukraine[indice] = [fusion] + morceau[1:]
            morceaux_ukraine.remove(crimee[0])
            print("  Crimée soudée au continent : plus aucune frontière interne.")
            break
    else:
        print("  ATTENTION : soudure impossible, la Crimée reste un morceau"
              " séparé (un trait de contour restera visible).")

    if len(morceaux_ukraine) == 1:
        ukraine["geometry"] = {"type": "Polygon", "coordinates": morceaux_ukraine[0]}
    else:
        ukraine["geometry"] = {"type": "MultiPolygon", "coordinates": morceaux_ukraine}
    return True


# --- Programme principal --------------------------------------------------

def main():
    print("Préparation du fond de carte StatsMaps")
    print("-" * 55)

    brut = telecharger(SOURCE_URL)
    disputes = telecharger(SOURCE_DISPUTES)
    pays_entrants = brut["features"]
    print("  %d pays trouvés dans le fichier source." % len(pays_entrants))

    pays_sortants = []
    ignores = []

    for element in pays_entrants:
        props = element["properties"]
        code = props.get("ADM0_A3")

        if not code or code == "-99" or code in PAYS_EXCLUS:
            ignores.append(props.get("NAME", "?"))
            continue

        # On applique la correction de code si nécessaire.
        code = CORRECTIONS_CODES.get(code, code)

        geometrie = {
            "type": element["geometry"]["type"],
            "coordinates": arrondir(element["geometry"]["coordinates"]),
        }
        geometrie = anneaux_valides(geometrie)

        if geometrie is None:
            ignores.append(props.get("NAME", "?"))
            continue

        nom_fr = props.get("NAME_FR") or props.get("NAME")
        nom_en = props.get("NAME")
        nom_uk = props.get("NAME_UK") or nom_en
        if code in NOMS_COURTS:
            nom_fr, nom_en, nom_uk = NOMS_COURTS[code]

        # Le code à deux lettres sert uniquement à fabriquer le drapeau.
        # "_EH" est la version corrigée par Natural Earth : elle rattrape les
        # pays laissés à "-99" dans la colonne d'origine (dont la France !).
        code_deux_lettres = props.get("ISO_A2_EH") or props.get("ISO_A2") or ""
        emoji = drapeau(code_deux_lettres)
        if code in TERRITOIRES:
            # Deux drapeaux collés : l'État d'abord, le territoire ensuite.
            emoji = drapeau(TERRITOIRES[code]) + emoji

        pays_sortants.append({
            "type": "Feature",
            # La propriété "iso" sert d'identifiant à MapLibre (via promoteId)
            # pour colorier un pays au survol et lui attacher sa valeur.
            "properties": {
                "iso": code,
                "fr": nom_fr,
                "en": nom_en,
                "uk": nom_uk,
                "d": emoji,  # "d" comme drapeau
            },
            "geometry": geometrie,
        })

        # "p" comme pays : à faire figurer dans le classement bien que le FMI
        # ne publie rien. "t" comme territoire : à montrer mais pas à compter.
        if code in PAYS_HORS_FMI:
            pays_sortants[-1]["properties"]["p"] = 1
        if code in TERRITOIRES:
            pays_sortants[-1]["properties"]["t"] = 1

    if rattacher_crimee_a_ukraine(pays_sortants):
        print("  Crimée rattachée à l'Ukraine (résolution ONU 68/262).")

    deplacer_iles(pays_sortants, "RUS", "JPN", KOURILES_BOITE,
                  "Kouriles du Sud rattachées au Japon")

    if rattacher_golan_a_la_syrie(pays_sortants, contour_dispute(disputes, NOM_GOLAN)):
        print("  Golan rattaché à la Syrie (résolution ONU 497).")

    for code_absorbe, code_hote, explication in FUSIONS:
        if not fusionner(pays_sortants, code_absorbe, code_hote, explication):
            print("  ATTENTION : fusion %s -> %s impossible." % (code_absorbe, code_hote))

    # Le cadrage est mémorisé MAINTENANT, avant l'ajout des enclaves et le
    # rattachement des territoires : c'est le pays lui-même qu'on veut cadrer.
    for element in pays_sortants:
        element["properties"]["c"] = cadrage_du_pays(element["geometry"])

    ajouter_enclaves(pays_sortants)

    # Les territoires dépendants prennent la couleur de leur État.
    for code_hote in sorted(TERRITOIRES_RATTACHES):
        rattaches = [code for code in TERRITOIRES_RATTACHES[code_hote]
                     if fusionner(pays_sortants, code, code_hote)]
        manquants = set(TERRITOIRES_RATTACHES[code_hote]) - set(rattaches)
        print("  %s ← %d territoire(s) rattaché(s)%s"
              % (code_hote, len(rattaches),
                 " ; INTROUVABLES : %s" % ", ".join(sorted(manquants)) if manquants else ""))

    resultat = {"type": "FeatureCollection", "features": pays_sortants}

    os.makedirs(os.path.dirname(FICHIER_SORTIE), exist_ok=True)
    with open(FICHIER_SORTIE, "w", encoding="utf-8") as fichier:
        json.dump(resultat, fichier, separators=(",", ":"), ensure_ascii=False)

    poids_ko = os.path.getsize(FICHIER_SORTIE) / 1024
    print("-" * 55)
    print("  %d pays conservés." % len(pays_sortants))
    if ignores:
        print("  %d ignorés (trop petits ou sans code) : %s"
              % (len(ignores), ", ".join(ignores)))
    print("  Écrit dans data/pays.json  (%d Ko)" % round(poids_ko))
    print("Terminé.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erreur:
        print("ERREUR : %s" % erreur, file=sys.stderr)
        sys.exit(1)
