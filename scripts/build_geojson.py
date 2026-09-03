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
FUSIONS = [
    ("CYN", "CYP", "Chypre du Nord, reconnue par la seule Turquie, fondue dans Chypre"),
    ("SOL", "SOM", "le Somaliland, reconnu par aucun État, fondu dans la Somalie"),
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
# On leur donne ici le nom court d'usage.
NOMS_COURTS = {
    "CHN": ("Chine", "China"),
    "USA": ("États-Unis", "United States"),
    "COD": ("Rép. dém. du Congo", "DR Congo"),
    "CAF": ("Rép. centrafricaine", "Central African Rep."),
    "DOM": ("Rép. dominicaine", "Dominican Rep."),
    "PNG": ("Papouasie-N.-Guinée", "Papua New Guinea"),
    "SSD": ("Soudan du Sud", "South Sudan"),
    "BIH": ("Bosnie-Herzégovine", "Bosnia & Herzegovina"),
    "STP": ("Sao Tomé-et-Principe", "São Tomé & Príncipe"),
    "ARE": ("Émirats arabes unis", "United Arab Emirates"),
    "GBR": ("Royaume-Uni", "United Kingdom"),
    "PRK": ("Corée du Nord", "North Korea"),
    "KOR": ("Corée du Sud", "South Korea"),
    "LAO": ("Laos", "Laos"),
    "SYR": ("Syrie", "Syria"),
    "VAT": ("Vatican", "Vatican"),
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


def fusionner(pays, code_absorbe, code_hote, explication):
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
        if code in NOMS_COURTS:
            nom_fr, nom_en = NOMS_COURTS[code]

        pays_sortants.append({
            "type": "Feature",
            # La propriété "iso" sert d'identifiant à MapLibre (via promoteId)
            # pour colorier un pays au survol et lui attacher sa valeur.
            "properties": {
                "iso": code,
                "fr": nom_fr,
                "en": nom_en,
            },
            "geometry": geometrie,
        })

    if rattacher_crimee_a_ukraine(pays_sortants):
        print("  Crimée rattachée à l'Ukraine (résolution ONU 68/262).")

    for code_absorbe, code_hote, explication in FUSIONS:
        if not fusionner(pays_sortants, code_absorbe, code_hote, explication):
            print("  ATTENTION : fusion %s -> %s impossible." % (code_absorbe, code_hote))

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
