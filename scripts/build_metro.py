#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_metro.py — prépare la carte des métros du monde.

Ce que fait ce script, en une phrase :
il demande à OpenStreetMap OÙ sont les métros du monde et à quoi ils
ressemblent, à Wikidata CE QU'ILS SONT et comment on les nomme dans les treize
langues du site, puis range le tout dans data/metro/.

À lancer :  python3 scripts/build_metro.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).

  ── Pourquoi ces deux sources, et pas Wikipédia ────────────────────────────

La version précédente lisait la page « List of metro systems » de Wikipédia en
grattant son HTML. Cela marchait, mais tenait à la mise en page d'une page que
personne ne nous a promis de laisser en l'état, et obligeait à recoller à la
main soixante-dix noms de pays sur leur code ISO.

Ici, chaque source ne dit que ce qu'elle sait le mieux :

  OpenStreetMap ... le terrain. Le tracé exact de chaque ligne, sa couleur
                    officielle, ses stations, les rails en travaux, et le nom
                    de la ville la plus proche. C'est aussi lui qui décide
                    ce qu'est un métro : une ligne « route=subway ».
  Wikidata ....... l'état civil. Le nom de la ville dans les treize langues,
                    le code ISO de son pays, l'année d'ouverture du réseau et
                    sa fréquentation annuelle. Tout arrive en quelques
                    requêtes, sous forme de tableau — rien à gratter.

Ce que l'on perd, et il faut le savoir : la fréquentation n'est connue que
pour la moitié des réseaux environ, et la frontière entre « métro » et
« tramway » est désormais celle du balisage d'OpenStreetMap, inégale selon
les pays. On la corrige d'un côté seulement : un « métro léger » n'entre que
si Wikidata le range explicitement parmi les métros (c'est ainsi que le DLR
de Londres entre, et que les tramways restent dehors).

Le script est long à tourner la première fois (il télécharge tous les métros
du monde, poliment). Tout est gardé dans scripts/.cache-metro/ : les fois
suivantes il repart de là. Pour tout retélécharger : --neuf
"""

import json
import math
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request

# --- Où l'on prend les données -------------------------------------------

OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

WIKIDATA = "https://query.wikidata.org/sparql"

# Les treize langues du site.
LANGUES = ["fr", "en", "uk", "de", "es", "it", "pt", "pl", "ja", "ko", "tr", "hi", "ar"]

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-metro")
SORTIE = os.path.join(DOSSIER, "data", "metro")

EN_TETES = {"User-Agent": "StatsMaps/1.0 (+https://statsmaps.com)"}


# --- Petits outils --------------------------------------------------------

def dit(*a):
    print(*a, flush=True)


def cache_lire(nom):
    chemin = os.path.join(CACHE, nom)
    if os.path.exists(chemin) and "--neuf" not in sys.argv:
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)
    return None


def cache_ecrire(nom, valeur):
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, nom), "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False)


def telecharger(url, donnees=None, essais=4, entetes=None):
    """Télécharge une page. Réessaie si le serveur est occupé."""
    for n in range(essais):
        try:
            corps = donnees.encode() if donnees else None
            req = urllib.request.Request(url, data=corps, headers=entetes or EN_TETES)
            with urllib.request.urlopen(req, timeout=900) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if n == essais - 1:
                raise
            attente = 20 * (n + 1)
            dit(f"    … {type(e).__name__} ; nouvel essai dans {attente} s")
            time.sleep(attente)


def slug(texte):
    """« Saint-Pétersbourg » -> « saint-petersbourg ». Sert aux noms de fichiers."""
    t = unicodedata.normalize("NFD", texte or "")
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().replace("'", "-").replace("’", "-")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "ville"


# --- Étape 1 : OpenStreetMap, tous les métros du monde --------------------

# On découpe le monde en six pavés plutôt que d'interroger ville par ville.
# Il n'y a que 2 582 lignes de métro sur la planète : six requêtes suffisent,
# et surtout on n'a plus besoin de savoir À L'AVANCE quelles villes ont un
# métro — c'est justement ce que la liste de Wikipédia servait à dire.
#              (sud,  ouest, nord,  est)
PAVES = [
    ("ameriques-nord", (5, -180, 85, -30)),
    ("ameriques-sud", (-60, -95, 5, -30)),
    ("europe-afrique", (-40, -30, 85, 45)),
    ("asie-ouest-sud", (-40, 45, 85, 100)),
    ("asie-est-nord", (28, 100, 85, 180)),
    ("asie-est-sud", (-50, 100, 28, 180)),
]

REQUETE = """[out:json][timeout:900];
(
  relation["route"="subway"]({boite});
  relation["route"="light_rail"]({boite});
);
out geom;
way["railway"="construction"]["construction"~"^(subway|light_rail)$"]({boite});
out geom;
"""


def moissonner():
    """Télécharge les six pavés du monde, ou les relit dans le cache."""
    for nom, (s, o, n, e) in PAVES:
        fichier = f"osm-{nom}.json"
        if cache_lire(fichier) is not None:
            dit(f"  {nom} : déjà dans le cache")
            continue
        dit(f"  {nom} … ")
        req = REQUETE.format(boite=f"{s},{o},{n},{e}")
        derniere = None
        for essai in range(3):
            for serveur in OVERPASS:
                try:
                    d = json.loads(telecharger(
                        serveur, "data=" + urllib.parse.quote(req), essais=1))
                    cache_ecrire(fichier, d)
                    dit(f"    {len(d.get('elements', []))} objets")
                    time.sleep(5)      # on ne bouscule pas un serveur bénévole
                    derniere = None
                    break
                except Exception as ex:
                    derniere = ex
                    dit(f"    … {serveur.split('/')[2]} : {type(ex).__name__}")
                    time.sleep(20)
            if derniere is None:
                break
        if derniere is not None:
            raise derniere


def lire_moisson():
    """Relit les six pavés, sans doublons : un métro à cheval sur deux pavés
    est renvoyé par les deux requêtes."""
    relations, voies = {}, {}
    for nom, _ in PAVES:
        d = cache_lire(f"osm-{nom}.json") or {"elements": []}
        for e in d.get("elements", []):
            (relations if e["type"] == "relation" else voies)[e["id"]] = e
    return list(relations.values()), list(voies.values())



# --- Étape 2 : de la géométrie -------------------------------------------


# Mots qui ne distinguent rien : ils reviennent dans presque tous les noms de
# réseau du monde et ne peuvent donc pas servir à reconnaître un réseau.
MOTS_VIDES = {
    "metro", "métro", "subway", "underground", "rail", "railway", "light",
    "transit", "rapid", "mass", "system", "line", "lines", "urban", "city",
    "the", "de", "du", "des", "la", "le", "of", "and", "et", "tunnelbana",
    "u", "bahn", "ubahn", "mrt", "lrt", "train", "tren", "metropolitana",
}

# La couleur d'une ligne qui n'en déclare aucune dans OpenStreetMap (4 % des
# lignes). Un gris bleuté, qui ne ressemble à aucune couleur officielle et se
# voit dans les deux thèmes.
COULEUR_INCONNUE = "#7A8A99"

# Au-delà de cette part de son tracé posée sur des rails « en construction »,
# une ligne n'est pas ouverte : c'est un chantier que quelqu'un a déjà décrit
# comme une ligne. La mesure ne laisse aucun doute — à Paris, la ligne 15 du
# Grand Paris Express est à 91 %, et les quatorze lignes en service à 0 %.
PART_EN_CHANTIER = 0.7

# 250 mètres de tolérance : à l'échelle d'un pays, un tracé au mètre près et
# un tracé au quart de kilomètre près sont le même trait à l'écran.
APERCU_TOLERANCE_M = 250.0

# 3 décimales = 110 mètres. Écrire plus, c'est écrire du bruit qu'aucun écran
# ne montrera jamais à cette échelle — et c'est un tiers du fichier en plus.
APERCU_DECIMALES = 3

def distance_km(a, b):
    """Distance à vol d'oiseau entre deux points (lon, lat), en kilomètres."""
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(d)))

def longueur_km(points):
    return sum(distance_km(points[i], points[i + 1]) for i in range(len(points) - 1))

def alleger(points, tolerance_m=12.0):
    """Retire les points inutiles d'un tracé (algorithme de Douglas-Peucker).

    Un tunnel de métro est dessiné dans OpenStreetMap avec un point tous les
    quelques mètres. À l'écran, un point tous les douze mètres suffit : le
    tracé est identique à l'œil, et le fichier trois à cinq fois plus léger.
    """
    if len(points) < 3:
        return points
    # On travaille en mètres approximatifs pour que la tolérance ait un sens
    # partout : un degré de longitude vaut 111 km à l'équateur, 55 km à Paris.
    lat0 = math.radians(points[len(points) // 2][1])
    kx = 111320.0 * math.cos(lat0)
    ky = 110540.0

    def recur(deb, fin, garder):
        pire, imax = 0.0, -1
        ax, ay = points[deb][0] * kx, points[deb][1] * ky
        bx, by = points[fin][0] * kx, points[fin][1] * ky
        dx, dy = bx - ax, by - ay
        norme = dx * dx + dy * dy
        for i in range(deb + 1, fin):
            px, py = points[i][0] * kx, points[i][1] * ky
            if norme == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / norme))
                d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
            if d > pire:
                pire, imax = d, i
        if pire > tolerance_m:
            garder.add(imax)
            recur(deb, imax, garder)
            recur(imax, fin, garder)

    garder = {0, len(points) - 1}
    sys.setrecursionlimit(10000)
    recur(0, len(points) - 1, garder)
    return [points[i] for i in sorted(garder)]

def arrondir(points, decimales=5):
    """5 décimales = un mètre. Au-delà, on stocke du bruit."""
    return [[round(p[0], decimales), round(p[1], decimales)] for p in points]

def centre(points):
    return [sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points)]

def geometrie(element):
    """Les tracés d'un élément OpenStreetMap, sous forme de listes de points.

    Une relation est faite de plusieurs bouts de voie ; on garde l'identifiant
    de chacun, parce que les deux sens d'une même ligne partagent souvent les
    mêmes bouts et qu'il ne faut les compter — et les dessiner — qu'une fois.
    """
    bouts = {}
    if element["type"] == "way":
        g = element.get("geometry") or []
        if len(g) > 1:
            bouts[element["id"]] = [[p["lon"], p["lat"]] for p in g]
        return bouts
    for m in element.get("members", []):
        g = m.get("geometry")
        if m.get("type") == "way" and g and len(g) > 1:
            bouts[m["ref"]] = [[p["lon"], p["lat"]] for p in g]
    return bouts

def nom_de_ligne(tags):
    """Le nom court d'une ligne, débarrassé de son itinéraire.

    OpenStreetMap écrit « 长沙地铁二号线: 龙虎岭 → 光达 » ou
    « Ligne 8 : Pointe du Lac → Balard » : le nom de la ligne, puis son
    terminus de départ et d'arrivée. Comme on réunit les deux sens en une
    seule ligne, tout ce qui suit les deux-points ou la flèche est faux la
    moitié du temps. On le retire.
    """
    for cle in ("name", "name:en"):
        n = tags.get(cle)
        if n:
            n = re.split(r"\s*[:：]\s|\s*[→⇄↔<>]\s*|\s+=>\s+", n)[0].strip()
            return n or None
    return None

def couleur_propre(valeur):
    """Ne garde qu'une couleur qu'un navigateur saura afficher.

    OpenStreetMap accepte « #E60012 » mais aussi « blue », « red/white » ou
    des fantaisies. On garde les codes hexadécimaux et les quelques noms de
    couleur de base ; le reste devient « pas de couleur », et la ligne prend
    alors la couleur neutre du site.
    """
    if not valeur:
        return None
    v = valeur.strip().split(";")[0].split("/")[0].strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", v):
        return v.upper()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", v):
        return ("#" + "".join(c * 2 for c in v[1:])).upper()
    NOMMEES = {
        "red": "#E4002B", "blue": "#0057B8", "green": "#00843D",
        "yellow": "#FFD100", "orange": "#FF8200", "purple": "#6A2C91",
        "brown": "#7B4B28", "pink": "#F58FB0", "grey": "#8A8D8F",
        "gray": "#8A8D8F", "black": "#2B2B2B", "white": "#D9D9D9",
        "cyan": "#00AEC7", "magenta": "#C6168D", "lime": "#8DC63F",
        "silver": "#B9BBB6", "gold": "#C5A253", "navy": "#003057",
        "teal": "#00857D", "olive": "#7A7C3C", "maroon": "#7C2529",
        "violet": "#8A2BE2", "turquoise": "#40E0D0", "beige": "#D9C9A3",
    }
    return NOMMEES.get(v.lower())

def mots_cles(texte):
    """Les mots d'un nom qui servent vraiment à le reconnaître.

    « Docklands Light Railway » -> {docklands} ; « Paris Metro » -> {paris}.
    """
    t = unicodedata.normalize("NFD", (texte or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {m for m in re.split(r"[^a-z0-9]+", t) if len(m) > 2 and m not in MOTS_VIDES}

def km_sans_voies_doubles(traces, pas_m=25.0, proche_m=25.0):
    """La longueur des VOIES réellement posées par un ensemble de tracés.

    Deux pièges se cumulent, et il faut les défaire tous les deux.

    Le premier : un métro est dessiné VOIE PAR VOIE dans OpenStreetMap, deux
    traits parallèles distants d'une dizaine de mètres, et une ligne y figure
    une fois par sens. Additionner ces tracés donne une ligne deux fois trop
    longue — la ligne 1 de Paris mesure 16,6 km et s'annonçait 39.

    Le second : à New York, vingt-huit services empruntent les mêmes tunnels.
    La somme de leurs longueurs fait 900 km, alors que le métro de New York
    en mesure 380 : c'est la longueur des VOIES qu'on publie partout, un
    tunnel parcouru par quatre lignes ne comptant qu'une fois.

    On mesure donc l'union : les tracés sont examinés du plus long au plus
    court, jalonnés tous les 25 mètres, et chaque jalon qui tombe à plus de
    25 mètres de tout jalon déjà retenu ajoute ses 25 mètres. Ce qui a déjà
    été parcouru n'est jamais recompté — et, contrairement à un tri qui
    écarterait les tracés entiers, la portion PROPRE d'une ligne qui partage
    un tronc commun avec une autre est bien comptée.

    Les tracés restent DESSINÉS en entier : à l'écran les voies parallèles se
    confondent, et les effacer ferait disparaître la moitié des aiguillages.
    Ce n'est que le compteur de kilomètres qui les ignore.
    """
    CASE = 50.0        # côté des cases du quadrillage de recherche, en mètres

    def cases_du_point(lon, lat, rayon=0):
        x = int(lon * 111320 * math.cos(math.radians(lat)) / CASE)
        y = int(lat * 110540 / CASE)
        if not rayon:
            return [(x, y)]
        return [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]

    def jalonner(points):
        """Un jalon tous les 25 m le long du tracé.

        Indispensable : un tunnel rectiligne allégé ne garde que ses deux
        extrémités, et comparer deux tunnels parallèles sur leurs seules
        extrémités ne prouverait rien.
        """
        sortie, reste = [points[0]], 0.0
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            d = distance_km(a, b) * 1000
            while reste + d >= pas_m:
                t = (pas_m - reste) / d if d else 1.0
                a = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
                sortie.append(a)
                d = distance_km(a, b) * 1000
                reste = 0.0
            reste += d
        sortie.append(points[-1])
        return sortie

    retenus = {}      # case -> liste de jalons déjà retenus
    neufs = 0
    for trace in sorted((t for t in traces if len(t) > 1), key=longueur_km, reverse=True):
        for p in jalonner(trace):
            voisins = [q for case in cases_du_point(p[0], p[1], 1)
                       for q in retenus.get(case, ())]
            if any(distance_km(p, q) * 1000 < proche_m for q in voisins):
                continue
            neufs += 1
            retenus.setdefault(cases_du_point(p[0], p[1])[0], []).append(p)
    return neufs * pas_m / 1000.0


# Au-delà de cette part de son tracé posée sur des rails « en construction »,
# une ligne n'est pas ouverte : c'est un chantier que quelqu'un a déjà décrit
# comme une ligne. La mesure ne laisse aucun doute — à Paris, la ligne 15 du
# Grand Paris Express est à 91 %, et les quatorze lignes en service à 0 %.
PART_EN_CHANTIER = 0.7

# 250 mètres de tolérance : à l'échelle d'un pays, un tracé au mètre près et
# un tracé au quart de kilomètre près sont le même trait à l'écran.
APERCU_TOLERANCE_M = 250.0

# 3 décimales = 110 mètres. Écrire plus, c'est écrire du bruit qu'aucun écran
# ne montrera jamais à cette échelle — et c'est un tiers du fichier en plus.
APERCU_DECIMALES = 3

def distance_km(a, b):
    """Distance à vol d'oiseau entre deux points (lon, lat), en kilomètres."""
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * math.asin(min(1.0, math.sqrt(d)))

def longueur_km(points):
    return sum(distance_km(points[i], points[i + 1]) for i in range(len(points) - 1))

def alleger(points, tolerance_m=12.0):
    """Retire les points inutiles d'un tracé (algorithme de Douglas-Peucker).

    Un tunnel de métro est dessiné dans OpenStreetMap avec un point tous les
    quelques mètres. À l'écran, un point tous les douze mètres suffit : le
    tracé est identique à l'œil, et le fichier trois à cinq fois plus léger.
    """
    if len(points) < 3:
        return points
    # On travaille en mètres approximatifs pour que la tolérance ait un sens
    # partout : un degré de longitude vaut 111 km à l'équateur, 55 km à Paris.
    lat0 = math.radians(points[len(points) // 2][1])
    kx = 111320.0 * math.cos(lat0)
    ky = 110540.0

    def recur(deb, fin, garder):
        pire, imax = 0.0, -1
        ax, ay = points[deb][0] * kx, points[deb][1] * ky
        bx, by = points[fin][0] * kx, points[fin][1] * ky
        dx, dy = bx - ax, by - ay
        norme = dx * dx + dy * dy
        for i in range(deb + 1, fin):
            px, py = points[i][0] * kx, points[i][1] * ky
            if norme == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / norme))
                d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
            if d > pire:
                pire, imax = d, i
        if pire > tolerance_m:
            garder.add(imax)
            recur(deb, imax, garder)
            recur(imax, fin, garder)

    garder = {0, len(points) - 1}
    sys.setrecursionlimit(10000)
    recur(0, len(points) - 1, garder)
    return [points[i] for i in sorted(garder)]

def arrondir(points, decimales=5):
    """5 décimales = un mètre. Au-delà, on stocke du bruit."""
    return [[round(p[0], decimales), round(p[1], decimales)] for p in points]

def centre(points):
    return [sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points)]

def geometrie(element):
    """Les tracés d'un élément OpenStreetMap, sous forme de listes de points.

    Une relation est faite de plusieurs bouts de voie ; on garde l'identifiant
    de chacun, parce que les deux sens d'une même ligne partagent souvent les
    mêmes bouts et qu'il ne faut les compter — et les dessiner — qu'une fois.
    """
    bouts = {}
    if element["type"] == "way":
        g = element.get("geometry") or []
        if len(g) > 1:
            bouts[element["id"]] = [[p["lon"], p["lat"]] for p in g]
        return bouts
    for m in element.get("members", []):
        g = m.get("geometry")
        if m.get("type") == "way" and g and len(g) > 1:
            bouts[m["ref"]] = [[p["lon"], p["lat"]] for p in g]
    return bouts

def nom_de_ligne(tags):
    """Le nom court d'une ligne, débarrassé de son itinéraire.

    OpenStreetMap écrit « 长沙地铁二号线: 龙虎岭 → 光达 » ou
    « Ligne 8 : Pointe du Lac → Balard » : le nom de la ligne, puis son
    terminus de départ et d'arrivée. Comme on réunit les deux sens en une
    seule ligne, tout ce qui suit les deux-points ou la flèche est faux la
    moitié du temps. On le retire.
    """
    for cle in ("name", "name:en"):
        n = tags.get(cle)
        if n:
            n = re.split(r"\s*[:：]\s|\s*[→⇄↔<>]\s*|\s+=>\s+", n)[0].strip()
            return n or None
    return None

def couleur_propre(valeur):
    """Ne garde qu'une couleur qu'un navigateur saura afficher.

    OpenStreetMap accepte « #E60012 » mais aussi « blue », « red/white » ou
    des fantaisies. On garde les codes hexadécimaux et les quelques noms de
    couleur de base ; le reste devient « pas de couleur », et la ligne prend
    alors la couleur neutre du site.
    """
    if not valeur:
        return None
    v = valeur.strip().split(";")[0].split("/")[0].strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", v):
        return v.upper()
    if re.fullmatch(r"#[0-9a-fA-F]{3}", v):
        return ("#" + "".join(c * 2 for c in v[1:])).upper()
    NOMMEES = {
        "red": "#E4002B", "blue": "#0057B8", "green": "#00843D",
        "yellow": "#FFD100", "orange": "#FF8200", "purple": "#6A2C91",
        "brown": "#7B4B28", "pink": "#F58FB0", "grey": "#8A8D8F",
        "gray": "#8A8D8F", "black": "#2B2B2B", "white": "#D9D9D9",
        "cyan": "#00AEC7", "magenta": "#C6168D", "lime": "#8DC63F",
        "silver": "#B9BBB6", "gold": "#C5A253", "navy": "#003057",
        "teal": "#00857D", "olive": "#7A7C3C", "maroon": "#7C2529",
        "violet": "#8A2BE2", "turquoise": "#40E0D0", "beige": "#D9C9A3",
    }
    return NOMMEES.get(v.lower())

def mots_cles(texte):
    """Les mots d'un nom qui servent vraiment à le reconnaître.

    « Docklands Light Railway » -> {docklands} ; « Paris Metro » -> {paris}.
    """
    t = unicodedata.normalize("NFD", (texte or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {m for m in re.split(r"[^a-z0-9]+", t) if len(m) > 2 and m not in MOTS_VIDES}

def km_sans_voies_doubles(traces):
    """Longueur d'un ensemble de tracés, sans compter deux fois les voies.

    Un métro est dessiné VOIE PAR VOIE dans OpenStreetMap : deux traits
    parallèles, distants d'une dizaine de mètres — et, pour une ligne, un
    tracé par SENS de circulation. Les additionner donne une ligne deux fois
    trop longue : la ligne 1 de Paris mesure 16,6 km et s'annonçait 39.

    On procède donc par élimination : les tracés sont examinés du plus long
    au plus court, et un tracé qui suit un tracé déjà compté — plus des
    trois quarts de ses points à moins de 25 m d'un tracé retenu — est la
    seconde voie du même tunnel, et n'est pas compté.

    Les deux traits restent DESSINÉS tous les deux : à l'écran ils se
    confondent, et les effacer ferait disparaître la moitié des aiguillages.
    Ce n'est que le compteur de kilomètres qui les ignore.

    Attention : à appeler LIGNE PAR LIGNE, jamais sur toute une ville. Deux
    lignes différentes partagent souvent un tronc commun sur plusieurs
    kilomètres, et ce tronc doit compter dans les deux.
    """
    PROCHE_M = 25.0
    CASE = 50.0        # côté des cases du quadrillage de recherche, en mètres

    def cases_du_point(lon, lat, rayon=0):
        x = int(lon * 111320 * math.cos(math.radians(lat)) / CASE)
        y = int(lat * 110540 / CASE)
        if not rayon:
            return [(x, y)]
        return [(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)]

    def echantillonner(points, pas_m=25.0):
        """Un point tous les 25 m le long du tracé.

        Indispensable : un tunnel rectiligne allégé ne garde que ses deux
        extrémités, et comparer deux tunnels parallèles sur leurs seules
        extrémités ne prouverait rien.
        """
        sortie, reste = [points[0]], 0.0
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            d = distance_km(a, b) * 1000
            while reste + d >= pas_m:
                t = (pas_m - reste) / d if d else 1.0
                a = [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]
                sortie.append(a)
                d = distance_km(a, b) * 1000
                reste = 0.0
            reste += d
        sortie.append(points[-1])
        return sortie

    retenus = {}      # case -> liste de points déjà retenus
    total = 0.0
    for trace in sorted((t for t in traces if len(t) > 1), key=longueur_km, reverse=True):
        points = echantillonner(trace)
        deja = 0
        for p in points:
            voisins = [q for case in cases_du_point(p[0], p[1], 1)
                       for q in retenus.get(case, ())]
            if any(distance_km(p, q) * 1000 < PROCHE_M for q in voisins):
                deja += 1
        if deja > 0.75 * len(points):
            continue
        total += longueur_km(trace)
        for p in points:
            retenus.setdefault(cases_du_point(p[0], p[1])[0], []).append(p)
    return total

def pas_encore_ouverte(traces, chantiers):
    """La ligne roule-t-elle sur des rails encore en travaux ?

    Rien dans OpenStreetMap ne dit qu'une ligne n'a pas encore ouvert : la
    ligne 15 de Paris y est décrite exactement comme la ligne 1, sans date ni
    mention de chantier. Mais SES RAILS, eux, sont balisés « en construction ».
    C'est donc le terrain qu'on interroge, et non l'étiquette.
    """
    if not chantiers or not traces:
        return False

    CASE = 60.0        # côté des cases du quadrillage, en mètres
    PROCHE_M = 40.0

    def case(p):
        return (int(p[0] * 111320 * math.cos(math.radians(p[1])) / CASE),
                int(p[1] * 110540 / CASE))

    grille = {}
    for t in chantiers:
        for p in t:
            grille.setdefault(case(p), []).append(p)

    points = [p for t in traces for p in t]
    dessus = 0
    for p in points:
        x, y = case(p)
        voisins = [q for i in (-1, 0, 1) for j in (-1, 0, 1)
                   for q in grille.get((x + i, y + j), ())]
        if any(distance_km(p, q) * 1000 < PROCHE_M for q in voisins):
            dessus += 1
    return dessus > PART_EN_CHANTIER * len(points)

def enchainer(segments):
    """Recolle bout à bout les morceaux d'une même ligne.

    OpenStreetMap découpe une ligne en dizaines de petits tronçons (un par
    portion entre deux aiguillages). Recollés, ils font deux ou trois longs
    tracés au lieu de quarante : le fichier est bien plus léger, et surtout
    la simplification qui suit peut alors couper franchement dans les points.
    """
    restants = [list(s) for s in segments if len(s) > 1]
    chemins = []
    while restants:
        chemin = restants.pop()
        colle = True
        while colle:
            colle = False
            for i, s in enumerate(restants):
                if s[0] == chemin[-1]:
                    chemin = chemin + s[1:]
                elif s[-1] == chemin[-1]:
                    chemin = chemin + s[-2::-1]
                elif s[-1] == chemin[0]:
                    chemin = s[:-1] + chemin
                elif s[0] == chemin[0]:
                    chemin = s[:0:-1] + chemin
                else:
                    continue
                restants.pop(i)
                colle = True
                break
        chemins.append(chemin)
    return chemins

def sans_doublons(points):
    """Après l'arrondi à 110 m, deux points voisins tombent souvent au même
    endroit : un tracé sur trois devient « A, A, B, B, B, C »."""
    propres = [points[0]]
    for p in points[1:]:
        if p != propres[-1]:
            propres.append(p)
    return propres

def ecrire(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(chemin)



# --- Étape 3 : ranger les lignes par réseau, puis par ville ---------------

# Deux lignes d'un même réseau distantes de plus de cela sont deux réseaux
# différents qui portent le même nom : « Metro » tout court sert d'étiquette
# dans une dizaine de pays. Soixante kilomètres, c'est plus que la plus longue
# agglomération à métro et bien moins que la distance entre deux villes.
MEME_RESEAU_KM = 60

# Au-delà de cette distance, aucune ville d'OpenStreetMap n'est assez proche
# pour qu'on puisse dire à qui appartient un réseau : on le laisse tomber.
VILLE_TROP_LOIN_KM = 45


def grappes(objets, position, seuil_km):
    """Regroupe des objets proches de proche en proche (« single-link »).

    Deux réseaux qui se touchent n'en font qu'un ; deux réseaux éloignés
    restent deux, même s'ils portent le même nom.
    """
    n = len(objets)
    parent = list(range(n))

    def racine(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    # Un quadrillage à la maille du seuil : deux objets assez proches pour
    # être liés tombent forcément dans la même case ou dans une case voisine.
    # Sans lui, cinq mille chantiers feraient vingt-cinq millions de mesures.
    #
    # La maille est comptée EN KILOMÈTRES et non en degrés : un degré de
    # longitude vaut 111 km à l'équateur mais 55 à Oslo, et une maille en
    # degrés y serait deux fois trop étroite — deux tronçons voisins
    # tomberaient dans des cases non adjacentes, et ne seraient jamais liés.
    def case(p):
        return (int(p[0] * 111.320 * math.cos(math.radians(p[1])) / seuil_km),
                int(p[1] * 110.540 / seuil_km))

    cases = {}
    for i, o in enumerate(objets):
        cases.setdefault(case(position(o)), []).append(i)

    for i, o in enumerate(objets):
        x, y = case(position(o))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in cases.get((x + dx, y + dy), ()):
                    if j <= i:
                        continue
                    if distance_km(position(o), position(objets[j])) <= seuil_km:
                        a, b = racine(i), racine(j)
                        if a != b:
                            parent[a] = b

    par_racine = {}
    for i, o in enumerate(objets):
        par_racine.setdefault(racine(i), []).append(o)
    return list(par_racine.values())


def arrets(relation):
    """Les stations desservies par une ligne, telles qu'OpenStreetMap les liste.

    Une relation de ligne énumère ses arrêts dans l'ordre, sous le rôle
    « stop ». C'est de là que vient le compte des stations : nulle part
    ailleurs on ne trouve, pour toutes les villes du monde, une liste des
    stations d'un métro.
    """
    return [(m["lon"], m["lat"]) for m in relation.get("members", [])
            if m.get("type") == "node" and "stop" in (m.get("role") or "")
            and m.get("lon") is not None]


def compter_stations(points, proche_m=150.0):
    """Combien de stations distinctes ? Les arrêts sont listés une fois par
    sens et une fois par ligne : République, à Paris, apparaît dix fois.
    Deux arrêts à moins de 150 m l'un de l'autre sont la même station —
    c'est la largeur d'un quai, pas la distance entre deux stations."""
    gardes = []
    case = {}
    C = 200.0
    for p in points:
        x = int(p[0] * 111320 * math.cos(math.radians(p[1])) / C)
        y = int(p[1] * 110540 / C)
        voisins = [q for i in (-1, 0, 1) for j in (-1, 0, 1)
                   for q in case.get((x + i, y + j), ())]
        if any(distance_km(p, q) * 1000 < proche_m for q in voisins):
            continue
        gardes.append(p)
        case.setdefault((x, y), []).append(p)
    return len(gardes)


def reseaux_du_monde(relations, metros_wikidata):
    """Range les 3 600 relations d'OpenStreetMap en réseaux.

    Trois tris successifs :
      1. on écarte les « métros légers » que Wikidata ne range pas parmi les
         métros — c'est ainsi que le DLR de Londres entre et que les tramways
         restent dehors ;
      2. on groupe par étiquette « network » , puis on recoupe chaque étiquette
         en morceaux géographiques : deux « Metro » à mille kilomètres l'un de
         l'autre sont deux réseaux ;
      3. dans chaque réseau, on réunit les relations qui portent le même
         numéro de ligne — les deux sens d'une même ligne, notamment.
    """
    par_etiquette, ecartees = {}, 0
    for r in relations:
        bouts = geometrie(r)
        if not bouts:
            continue
        tags = r.get("tags", {})
        if tags.get("route") == "light_rail":
            qid = tags.get("network:wikidata") or tags.get("operator:wikidata")
            if qid not in metros_wikidata:
                ecartees += 1
                continue
        r["_bouts"] = bouts
        r["_centre"] = centre([p for b in bouts.values() for p in b])
        etiquette = tags.get("network") or tags.get("operator") or "?"
        par_etiquette.setdefault(etiquette, []).append(r)

    dit(f"  {ecartees} métros légers écartés : Wikidata n'en fait pas des métros")

    reseaux = []
    for etiquette, rels in par_etiquette.items():
        for morceau in grappes(rels, lambda r: r["_centre"], MEME_RESEAU_KM):
            lignes = {}
            for r in morceau:
                tags = r.get("tags", {})
                cle = tags.get("ref") or nom_de_ligne(tags) or str(r["id"])
                l = lignes.setdefault(cle, {
                    "ref": tags.get("ref"), "noms": {}, "couleurs": {},
                    "bouts": {}, "arrets": [],
                })
                l["centre"] = r["_centre"]
                l["bouts"].update(r["_bouts"])
                l["arrets"] += arrets(r)
                n = nom_de_ligne(tags)
                if n:
                    l["noms"][n] = l["noms"].get(n, 0) + 1
                c = couleur_propre(tags.get("colour"))
                if c:
                    l["couleurs"][c] = l["couleurs"].get(c, 0) + 1
            qids = [r["tags"].get("network:wikidata") for r in morceau
                    if r["tags"].get("network:wikidata")]
            reseaux.append({
                "etiquette": etiquette if etiquette != "?" else None,
                "qid": max(set(qids), key=qids.count) if qids else None,
                "centre": centre([r["_centre"] for r in morceau]),
                "lignes": lignes,
            })
    return reseaux



# --- Étape 4 : à quelle ville appartient chaque réseau ? ------------------

LIEUX_PAR_REQUETE = 20


def population(tags):
    """Le nombre d'habitants tel qu'OpenStreetMap l'écrit : « 8908081 »,
    « 8,908,081 », « ~500000 ». On n'en garde que les chiffres."""
    chiffres = re.sub(r"[^0-9]", "", (tags.get("population") or "").split(".")[0])
    return int(chiffres) if chiffres else None


# Quand OpenStreetMap ne dit pas combien d'habitants, on suppose l'ordre de
# grandeur habituel du genre de lieu. Ces nombres ne servent qu'à comparer
# deux lieux entre eux, jamais à être affichés.
HABITANTS_PAR_DEFAUT = {"city": 120000, "borough": 60000, "municipality": 30000,
                        "suburb": 20000, "town": 12000}


def lieux_de(elements):
    """Ne garde d'un nœud d'OpenStreetMap que ce dont la carte a besoin."""
    lieux = []
    for e in elements:
        t = e.get("tags", {})
        if not t.get("name") or e.get("lon") is None:
            continue
        lieux.append({
            "lon": e["lon"], "lat": e["lat"],
            "nom": t["name"], "place": t.get("place"),
            "qid": t.get("wikidata"),
            "hab": population(t) or HABITANTS_PAR_DEFAUT.get(t.get("place"), 10000),
            "noms": {l: t[f"name:{l}"] for l in LANGUES if t.get(f"name:{l}")},
        })
    return lieux


def villes_proches(centres):
    """Demande à OpenStreetMap le nom de la ville la plus proche de chaque ligne.

    C'est OpenStreetMap qui nomme la ville, et non Wikidata : Wikidata range
    le métro de Copenhague dans la « commune de Copenhague » et celui de
    Londres dans le « Grand Londres », qui ne sont pas des noms de ville.
    Le nœud « place=city » d'OpenStreetMap, lui, s'appelle Copenhague — et il
    porte presque toujours (96 %) son identifiant Wikidata, par lequel on ira
    chercher ses treize traductions.

    On demande TOUTES les villes du monde d'un coup — elles ne sont que douze
    mille, dix méga-octets — plutôt qu'un rayon autour de chaque ligne. Une
    recherche par rayon oblige Overpass à balayer la planète une fois par
    ligne : la même moisson passait d'une demi-heure à deux minutes et demie.

    On garde la réponse BRUTE dans le cache : régler la façon de choisir la
    ville ne doit pas obliger à retélécharger dix méga-octets.
    """
    brut = cache_lire("lieux-villes-brut.json")
    if brut is None:
        dit("  toutes les villes du monde, en une requête")
        req = '[out:json][timeout:900];\nnode["place"="city"];\nout tags center;'
        brut = json.loads(telecharger(OVERPASS[0], "data=" + urllib.parse.quote(req)))
        cache_ecrire("lieux-villes-brut.json", brut)
    lieux = lieux_de(brut.get("elements", []))
    dit(f"  {len(lieux)} villes")

    # Quelques lignes n'ont aucune ville à moins de 45 km : elles desservent un
    # bourg ou une banlieue qu'OpenStreetMap ne classe pas « city ». On ne va
    # chercher les bourgs QUE pour celles-là — il y a dix fois plus de bourgs
    # que de villes, et les charger tous coûterait cher pour trois réponses.
    index = index_des_lieux(lieux)
    seuls = [c for c in centres if not ville_du_reseau(c, index)]
    if not seuls:
        return lieux
    brut = cache_lire("lieux-bourgs-brut.json")
    if brut is None:
        dit(f"  {len(seuls)} lignes sans ville : on cherche autour d'elles")
        rayon = int(VILLE_TROP_LOIN_KM * 1000)
        elements = []
        for i in range(0, len(seuls), LIEUX_PAR_REQUETE):
            lot = seuls[i:i + LIEUX_PAR_REQUETE]
            # Une valeur ÉCRITE EN TOUTES LETTRES et non une expression
            # régulière : Overpass tient un index par étiquette exacte, mais
            # doit tout balayer dès qu'on lui donne un motif à reconnaître.
            autour = "".join(
                f'  node["place"="{genre}"](around:{rayon},{lat},{lon});\n'
                for lon, lat in lot
                for genre in ("town", "municipality", "borough", "suburb"))
            req = f"[out:json][timeout:600];\n(\n{autour});\nout tags center;"
            d = json.loads(telecharger(OVERPASS[0], "data=" + urllib.parse.quote(req)))
            elements += d.get("elements", [])
            time.sleep(3)
        brut = {"elements": list({e["id"]: e for e in elements}.values())}
        cache_ecrire("lieux-bourgs-brut.json", brut)
    bourgs = lieux_de(brut.get("elements", []))
    dit(f"  {len(bourgs)} bourgs de secours")
    return lieux + bourgs


def index_des_lieux(lieux):
    """Range les douze mille villes du monde dans un quadrillage.

    Sans lui, chercher la ville la plus proche de chacune des mille cinq cents
    lignes reviendrait à mesurer dix-huit millions de distances. Avec, on ne
    compare qu'aux villes des neuf cases voisines — une dizaine.
    """
    index = {}
    for l in lieux:
        index.setdefault(case_de(l["lon"], l["lat"], VILLE_TROP_LOIN_KM), []).append(l)
    return index


def case_de(lon, lat, cote_km):
    """La case du quadrillage où tombe un point, en cases de `cote_km` de côté."""
    return (int(lon * 111.320 * math.cos(math.radians(lat)) / cote_km),
            int(lat * 110.540 / cote_km))


def ville_de_la_ligne(points, index):
    """La ville d'une ligne, pesée sur TOUS ses arrêts et non sur son centre.

    Une ligne de banlieue traverse la campagne : son centre géométrique tombe
    entre deux villes. La ligne Yellow du BART va de San Francisco à Antioch,
    et son milieu est dans un lotissement — elle était donnée à Antioch.
    En additionnant la masse ville par ville sur chacun de ses arrêts, c'est
    le centre-ville, où les stations se serrent, qui l'emporte.
    """
    if not points:
        return None
    total = {}
    lieux = {}
    for p in points:
        x, y = case_de(p[0], p[1], VILLE_TROP_LOIN_KM)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for l in index.get((x + dx, y + dy), ()):
                    d = distance_km(p, (l["lon"], l["lat"]))
                    if d > VILLE_TROP_LOIN_KM:
                        continue
                    cle = id(l)
                    lieux[cle] = l
                    total[cle] = total.get(cle, 0.0) + l["hab"] / (d + 10.0) ** 2
    if not total:
        return None
    return lieux[max(total, key=total.get)]


def ville_du_reseau(centre_ligne, index):
    """À quelle ville appartient une ligne ?

    « La plus proche » ne suffit pas, et c'est le piège de cette carte :
    OpenStreetMap classe « place=city » les arrondissements de Pékin et de
    Tokyo, et la City de Londres — mille habitants au cœur d'une ville de
    neuf millions. La ligne Central du métro de Londres passe littéralement
    au-dessus de la City : « la plus proche » la lui donnerait, et le métro
    de Londres se retrouverait coupé en morceaux.

    On pèse donc chaque candidate comme une masse : son nombre d'habitants
    divisé par le carré de sa distance. Londres l'emporte alors sur la City
    (9,9 contre 0,014), Pékin sur Chaoyang, Tokyo sur Meguro — mais Yokohama
    garde son métro face à Tokyo, et Foshan face à Canton, parce que la
    distance, élevée au carré, pèse plus lourd que la taille.

    Les dix kilomètres ajoutés à la distance évitent qu'un hameau posé
    exactement sur une ligne ne l'emporte par une division par zéro.
    """
    x, y = case_de(centre_ligne[0], centre_ligne[1], VILLE_TROP_LOIN_KM)
    meilleur, meilleure_masse = None, 0.0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for l in index.get((x + dx, y + dy), ()):
                d = distance_km(centre_ligne, (l["lon"], l["lat"]))
                if d > VILLE_TROP_LOIN_KM:
                    continue
                masse = l["hab"] / (d + 10.0) ** 2
                if masse > meilleure_masse:
                    meilleur, meilleure_masse = l, masse
    return meilleur


# --- Étape 5 : Wikidata, l'état civil ------------------------------------

def sparql(requete, nom_cache):
    """Interroge Wikidata. Une requête, un tableau — rien à gratter."""
    d = cache_lire(nom_cache)
    if d is not None:
        return d
    url = WIKIDATA + "?format=json&query=" + urllib.parse.quote(requete)
    entetes = dict(EN_TETES)
    entetes["Accept"] = "application/sparql-results+json"
    d = json.loads(telecharger(url, entetes=entetes))["results"]["bindings"]
    cache_ecrire(nom_cache, d)
    time.sleep(1)
    return d


def val(ligne, clef, defaut=None):
    return ligne[clef]["value"] if clef in ligne else defaut


def qid_de(uri):
    return uri.rsplit("/", 1)[1] if uri else None


def metros_selon_wikidata():
    """Les identifiants de tout ce que Wikidata range parmi les métros.

    Sert d'arbitre pour une seule question, mais elle est décisive : un
    « métro léger » d'OpenStreetMap est-il un métro ? Le DLR de Londres et
    le Skytrain de Vancouver le sont ; le tramway de Lille ne l'est pas.
    """
    lignes = sparql("""
SELECT ?sys WHERE { ?sys wdt:P31/wdt:P279* wd:Q5503 . }
""", "wd-metros.json")
    return {qid_de(val(l, "sys")) for l in lignes}


def etat_civil_des_reseaux(qids):
    """Année d'ouverture, fréquentation, et nom du réseau en treize langues."""
    par_qid = {}
    liste = sorted(qids)
    lignes = []
    # Par paquets : la requête voyage dans l'adresse, qu'un serveur refuse
    # au-delà de quelques milliers de caractères.
    for i in range(0, len(liste), 120):
        valeurs = " ".join("wd:" + q for q in liste[i:i + 120])
        lignes += sparql("""
SELECT ?sys ?nom ?langue ?ouverture ?voyageurs WHERE {
  VALUES ?sys { %s }
  OPTIONAL { ?sys rdfs:label ?nom . BIND(LANG(?nom) AS ?langue)
             FILTER(?langue IN (%s)) }
  OPTIONAL { ?sys wdt:P1619 ?ouverture . }
  OPTIONAL { ?sys wdt:P3872 ?voyageurs . }
}
""" % (valeurs, ", ".join('"%s"' % l for l in LANGUES)), f"wd-reseaux-{i // 120}.json")
    for l in lignes:
        q = qid_de(val(l, "sys"))
        f = par_qid.setdefault(q, {"noms": {}, "ouvertures": set(), "voyageurs": set()})
        if val(l, "langue"):
            f["noms"][val(l, "langue")] = val(l, "nom")
        if val(l, "ouverture"):
            f["ouvertures"].add(val(l, "ouverture")[:4])
        if val(l, "voyageurs"):
            f["voyageurs"].add(float(val(l, "voyageurs")))
    for f in par_qid.values():
        annees = sorted(int(a) for a in f["ouvertures"] if a.isdigit())
        f["depuis"] = annees[0] if annees else None
        # Wikidata garde toutes les années de fréquentation les unes à côté
        # des autres, sans dire laquelle est la plus récente : on prend la
        # plus grande, qui est presque toujours la dernière connue.
        f["vy"] = round(max(f["voyageurs"]) / 1e6, 1) if f["voyageurs"] else None
    return par_qid


def etat_civil_des_villes(qids):
    """Le nom de la ville dans les treize langues du site.

    C'est tout ce qu'on demande à Wikidata sur une ville : le pays, lui, vient
    du fond de carte (voir pays_du_point). Wikidata ne donne pas de code ISO à
    trois lettres aux Pays-Bas, et Amsterdam disparaissait sans un mot.
    """
    par_qid = {}
    liste = sorted(qids)
    for i in range(0, len(liste), 150):
        valeurs = " ".join("wd:" + q for q in liste[i:i + 150])
        lignes = sparql("""
SELECT ?ville ?nom ?langue WHERE {
  VALUES ?ville { %s }
  ?ville rdfs:label ?nom . BIND(LANG(?nom) AS ?langue)
  FILTER(?langue IN (%s))
}
""" % (valeurs, ", ".join('"%s"' % l for l in LANGUES)), f"wd-villes-{i // 150}.json")
        for l in lignes:
            q = qid_de(val(l, "ville"))
            f = par_qid.setdefault(q, {"noms": {}})
            if val(l, "langue"):
                f["noms"][val(l, "langue")] = val(l, "nom")
    return par_qid



# --- Le pays : par le fond de carte du site lui-même ----------------------

# Wikidata ne donne pas de code ISO à trois lettres à tous les pays : celui
# des Pays-Bas manque, et Amsterdam, Rotterdam et Delft disparaissaient sans
# un mot. Plutôt que de rustiner, on demande au fond de carte du site : une
# ville est dans le pays où la carte la dessine, et pas dans un autre. Aucune
# table à tenir à jour, et le classement ne peut plus contredire le dessin.

# Hong Kong et Macao ont leur propre contour sur le fond de carte, et leur
# propre code ISO. Le classement par pays de StatsMaps les compte pourtant
# avec la Chine — c'était déjà le choix de la version précédente. La ville,
# elle, garde son nom : la carte écrit « Hong Kong » et non « Chine ».
RATTACHES = {"HKG": "CHN", "MAC": "CHN"}


def charger_pays():
    """Lit data/pays.json — les 202 pays que la carte dessine déjà."""
    with open(os.path.join(DOSSIER, "data", "pays.json"), encoding="utf-8") as f:
        d = json.load(f)
    pays = []
    for f2 in d["features"]:
        g = f2["geometry"]
        anneaux = ([g["coordinates"][0]] if g["type"] == "Polygon"
                   else [p[0] for p in g["coordinates"]])
        # Le cadre de pays.json sert à cadrer la carte, pas à situer un
        # point : celui des États-Unis s'arrête au 24e parallèle et laissait
        # Honolulu, au 21e, hors de son propre pays. On le recalcule.
        xs = [x for a in anneaux for x, _ in a]
        ys = [y for a in anneaux for _, y in a]
        pays.append({"iso": f2["properties"]["iso"],
                     "cadre": [min(xs), min(ys), max(xs), max(ys)],
                     "anneaux": anneaux})
    return pays


def dans_l_anneau(lon, lat, anneau):
    """Le point est-il dans ce contour ? (lancer de rayon)

    On compte combien de fois un rayon parti du point vers l'est traverse le
    contour : un nombre impair veut dire qu'on était dedans.
    """
    dedans = False
    j = len(anneau) - 1
    for i in range(len(anneau)):
        xi, yi = anneau[i]
        xj, yj = anneau[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            dedans = not dedans
        j = i
    return dedans


def pays_du_point(lon, lat, pays):
    """Le code ISO du pays qui contient ce point, ou le plus proche.

    Le repli par le plus proche sert aux villes portuaires : le contour des
    pays est simplifié pour tenir dans un fichier léger, et Copenhague ou
    Stockholm tombent parfois de quelques centaines de mètres dans la mer.
    """
    candidats = [p for p in pays
                 if p["cadre"][0] - 0.5 <= lon <= p["cadre"][2] + 0.5
                 and p["cadre"][1] - 0.5 <= lat <= p["cadre"][3] + 0.5]
    for p in candidats:
        if any(dans_l_anneau(lon, lat, a) for a in p["anneaux"]):
            return RATTACHES.get(p["iso"], p["iso"])
    meilleur, plus_court = None, 1e9
    for p in candidats:
        for a in p["anneaux"]:
            for x, y in a:
                d = (x - lon) ** 2 + ((y - lat) * 1.6) ** 2
                if d < plus_court:
                    meilleur, plus_court = p["iso"], d
    # 0,5 degré au carré ≈ 55 km : au-delà, le point est en pleine mer et
    # n'appartient à personne.
    return RATTACHES.get(meilleur, meilleur) if plus_court < 0.25 else None


# --- Étape 6 : assembler les villes --------------------------------------

# Les tronçons en construction se regroupent plus serré que les réseaux : un
# chantier isolé à 25 km d'un autre est un autre chantier.
MEME_CHANTIER_KM = 25


def lire_chantiers(voies):
    """Les tronçons en travaux, regroupés en chantiers."""
    morceaux = []
    for v in voies:
        bouts = geometrie(v)
        if not bouts:
            continue
        points = list(bouts.values())[0]
        tags = v.get("tags", {})
        morceaux.append({
            "points": points, "centre": centre(points),
            "couleur": couleur_propre(tags.get("colour")),
            "nom": nom_de_ligne(tags),
        })
    return grappes(morceaux, lambda m: m["centre"], MEME_CHANTIER_KM)


def fondre(cible, source):
    """Verse les lignes de `source` dans `cible`.

    Deux lignes de même numéro n'en font qu'une : à Montréal, un sens de la
    ligne orange porte l'étiquette « Métro de Montréal » et l'autre n'en porte
    aucune. Sans cette fusion, la ligne orange compterait deux fois.
    """
    for cle, l in source.items():
        deja = cible.get(cle)
        if deja is None:
            cible[cle] = l
            continue
        deja["bouts"].update(l["bouts"])
        deja["arrets"] += l["arrets"]
        for n, c in l["noms"].items():
            deja["noms"][n] = deja["noms"].get(n, 0) + c
        for n, c in l["couleurs"].items():
            deja["couleurs"][n] = deja["couleurs"].get(n, 0) + c


def cle_de_ville(lieu):
    """Deux réseaux tombent sur la même ville : ils doivent la partager.
    L'identifiant Wikidata sert de clef quand il existe, sinon le nom et la
    position arrondie — deux villes homonymes restent alors distinctes."""
    if lieu.get("qid"):
        return lieu["qid"]
    return f'{slug(lieu["nom"])}@{round(lieu["lon"], 1)},{round(lieu["lat"], 1)}'


def assembler(reseaux, chantiers, lieux):
    """Chaque réseau et chaque chantier rejoint sa ville."""
    villes = {}
    index = index_des_lieux(lieux)

    def ville_de(lieu):
        cle = cle_de_ville(lieu)
        return villes.setdefault(cle, {
            "cle": cle, "lieu": lieu, "reseaux": {}, "chantiers": [],
        })

    orphelins = {"lignes": 0, "chantiers": 0}
    for r in reseaux:
        for cle, ligne in r["lignes"].items():
            # C'est la LIGNE qu'on rattache, et non le réseau. En Allemagne et
            # en Scandinavie, l'étiquette « network » est celle de l'autorité
            # de transport régionale : le VRR couvre Düsseldorf, Duisbourg,
            # Essen et Dortmund. Rattacher son réseau entier donnerait vingt-
            # neuf lignes à une seule de ces villes.
            # Les arrêts d'abord ; à défaut le centre du tracé, pour les
            # quelques lignes qui n'en listent aucun.
            lieu = (ville_de_la_ligne(ligne["arrets"], index)
                    or ville_du_reseau(ligne["centre"], index))
            if not lieu:
                orphelins["lignes"] += 1
                continue
            ville = ville_de(lieu)
            reseau = ville["reseaux"].setdefault((r["etiquette"], r["qid"]), {
                "etiquette": r["etiquette"], "qid": r["qid"], "lignes": {},
            })
            # Une même clef peut revenir depuis deux réseaux homonymes de la
            # même ville : on ne perd rien, on la renomme.
            k, n = cle, 2
            while k in reseau["lignes"]:
                k, n = f"{cle}#{n}", n + 1
            reseau["lignes"][k] = ligne

    for groupe in chantiers:
        c = centre([m["centre"] for m in groupe])
        lieu = ville_du_reseau(c, index)
        if not lieu:
            orphelins["chantiers"] += 1
            continue
        ville_de(lieu)["chantiers"] += groupe

    dit(f"  {len(villes)} villes · {orphelins['lignes']} lignes et "
        f"{orphelins['chantiers']} chantiers trop loin de toute ville, écartés")
    return villes


# --- Étape 7 : écrire les fichiers du site -------------------------------

def fabriquer(villes, etat_villes, etat_reseaux, metros_wikidata):
    """Écrit data/metro/monde.json et un fichier par ville."""
    pays_dessines = charger_pays()
    fiches, poids_total, sans_pays = [], 0, []
    # Il y a une Valencia en Espagne et une au Venezuela : sans cela, la
    # seconde écraserait le fichier de la première.
    slugs_pris = {}

    for ville in villes.values():
        lieu = ville["lieu"]
        civil = etat_villes.get(lieu.get("qid"), {})
        iso = pays_du_point(lieu["lon"], lieu["lat"], pays_dessines)
        if not iso:
            sans_pays.append(lieu["nom"])
            continue

        # --- les chantiers d'abord : ils servent à reconnaître, juste après,
        #     les « lignes » qui ne sont en fait que des chantiers.
        chantiers = []
        for m in ville["chantiers"]:
            t = arrondir(alleger(m["points"]))
            if len(t) > 1:
                chantiers.append({"couleur": m["couleur"], "nom": m["nom"], "t": t})
        rails_en_travaux = [c["t"] for c in chantiers]
        km_chantier = km_sans_voies_doubles(rails_en_travaux)

        # LE TRI DÉCISIF, ville par ville. À Tokyo, OpenStreetMap décrit
        # comme « route=subway » non seulement le métro, mais les vingt
        # services d'interconnexion des chemins de fer privés qui le
        # prolongent — Tokyu, Odakyu, Seibu, Tobu. Additionnés, ils donnaient
        # 1 194 km et 35 lignes pour un métro qui en compte 304 et 13.
        #
        # La règle : SI Wikidata reconnaît au moins un réseau de cette ville
        # comme un métro, alors seuls ceux-là comptent. Sinon on garde tout,
        # et c'est ce qui sauve Munich, Chicago, Vienne, Berlin, Milan et
        # Rome, dont l'étiquette « network » est celle d'une autorité de
        # transport que Wikidata ne range pas parmi les métros. Là où la
        # seconde source sait trancher on l'écoute ; là où elle ne sait pas,
        # on s'en remet au terrain.
        reseaux_de_la_ville = list(ville["reseaux"].values())
        reconnus = [r for r in reseaux_de_la_ville if r["qid"] in metros_wikidata]
        if reconnus:
            # Les lignes SANS étiquette de réseau ne doivent pas tomber avec
            # les autres : à Montréal, les lignes verte et jaune n'en portent
            # aucune, et la ville perdait la moitié de son métro. Quand la
            # ville n'a qu'un seul réseau reconnu, on les lui verse ; sinon on
            # les garde à part, faute de savoir à qui les donner.
            anonymes = [r for r in reseaux_de_la_ville
                        if not r["etiquette"] and r not in reconnus]
            if anonymes and len(reconnus) == 1:
                for r in anonymes:
                    fondre(reconnus[0]["lignes"], r["lignes"])
                anonymes = []
            reseaux_de_la_ville = reconnus + anonymes

        lignes, systemes = [], []
        for r in reseaux_de_la_ville:
            lignes_du_reseau, arrets_du_reseau = [], []
            for cle, l in r["lignes"].items():
                traces = [arrondir(alleger(b)) for b in l["bouts"].values()]
                traces = [t for t in traces if len(t) > 1]
                if not traces or pas_encore_ouverte(traces, rails_en_travaux):
                    continue
                # Un métro qui roule liste ses arrêts : 96 % des lignes en ont.
                # Les 4 % qui n'en ont pas portent des noms sans équivoque —
                # « Extensión Proyectada », « U2-Verlängerung (2028) »,
                # « Extensie M4 » : ce sont des projets dessinés d'avance.
                # Sans cette règle, Bogotá, Bagdad et Koweït apparaissaient
                # sur la carte avec un métro qu'ils n'ont pas.
                if not l["arrets"]:
                    continue
                couleur = max(l["couleurs"], key=l["couleurs"].get) if l["couleurs"] else None
                nom = max(l["noms"], key=l["noms"].get) if l["noms"] else None
                arrets_du_reseau += l["arrets"]
                lignes_du_reseau.append({
                    "ref": l["ref"], "nom": nom, "reseau": r["etiquette"],
                    "couleur": couleur or COULEUR_INCONNUE,
                    "sansCouleur": 1 if not couleur else 0,
                    "km": round(km_sans_voies_doubles(traces), 1), "t": traces,
                })
            if not lignes_du_reseau:
                continue
            lignes += lignes_du_reseau
            civil_r = etat_reseaux.get(r["qid"], {})
            systemes.append({
                "n": civil_r.get("noms") or {"en": r["etiquette"] or lieu["nom"]},
                "depuis": civil_r.get("depuis"),
                "km": round(km_sans_voies_doubles(
                    [t for l in lignes_du_reseau for t in l["t"]]), 1),
                "st": compter_stations(arrets_du_reseau) or None,
                "vy": civil_r.get("vy"),
            })

        if not lignes and not chantiers:
            continue
        lignes.sort(key=lambda x: (-x["km"], x["ref"] or ""))

        # La longueur d'une ville n'est PAS la somme de ses lignes : à New
        # York, vingt-huit services partagent les mêmes tunnels, et cette
        # somme donnait 900 km pour un métro qui en mesure 380. On remesure
        # l'union des voies, ce que publient les exploitants.
        km_ville = round(km_sans_voies_doubles([t for l in lignes for t in l["t"]]), 1)
        stations = compter_stations(
            [a for r in reseaux_de_la_ville
             for l in r["lignes"].values() for a in l["arrets"]])
        depuis = [s["depuis"] for s in systemes if s["depuis"]]
        voyageurs = [s["vy"] for s in systemes if s["vy"]]

        noms = dict(lieu.get("noms") or {})
        noms.update(civil.get("noms") or {})
        noms.setdefault("en", lieu["nom"])

        s = slug(noms.get("en") or lieu["nom"])
        if s in slugs_pris:
            s = f"{s}-{iso.lower()}"
            while s in slugs_pris:
                s += "-2"
        slugs_pris[s] = True
        poids_total += ecrire(os.path.join(SORTIE, "villes", s + ".json"),
                              {"s": s, "lignes": lignes, "chantiers": chantiers})

        # Les chantiers d'une ville qui n'a pas encore de métro : c'est son
        # premier, et la carte l'annonce en orange.
        futur = []
        if not lignes:
            vus = set()
            for c in chantiers:
                if c["nom"] and c["nom"] not in vus:
                    vus.add(c["nom"])
                    futur.append({"n": {"en": c["nom"]}, "debut": None, "prevu": None})

        fiches.append({
            "s": s, "iso": iso,
            "lon": round(lieu["lon"], 4), "lat": round(lieu["lat"], 4),
            "n": noms,
            "km": km_ville or None,
            "st": stations or None,
            "vy": round(sum(voyageurs), 1) if voyageurs else None,
            "depuis": min(depuis) if depuis else None,
            "lg": len(lignes) or None,
            "kmc": round(km_chantier, 1) or None,
            "enService": 1 if lignes else 0,
            "sys": [{k: s2[k] for k in ("n", "depuis", "km", "st")} for s2 in systemes],
            "futur": futur,
        })

    if sans_pays:
        dit(f"  {len(sans_pays)} villes hors de tout pays du fond de carte, "
            f"écartées : {', '.join(sorted(sans_pays)[:8])}")

    # --- le classement par pays, additionné depuis les villes.
    #     Plus de tableau recopié : ce qui est écrit ici est la somme de ce
    #     qui est dessiné sur la carte, et ne peut donc pas le contredire.
    pays = {}
    for f in fiches:
        p = pays.setdefault(f["iso"], {"iso": f["iso"], "sys": 0, "km": 0.0, "lg": 0,
                                       "st": 0, "depuis": None, "kmc": 0.0, "villes": []})
        p["sys"] += len(f["sys"])
        p["km"] += f["km"] or 0
        p["lg"] += f["lg"] or 0
        p["st"] += f["st"] or 0
        p["kmc"] += f["kmc"] or 0
        if f["depuis"]:
            p["depuis"] = min(p["depuis"] or 9999, f["depuis"])
        if f["enService"]:
            p["villes"].append(f["s"])
    for p in pays.values():
        p["km"] = round(p["km"], 1) or None
        p["kmc"] = round(p["kmc"], 1) or None
    classement = sorted(pays.values(), key=lambda p: (-p["sys"], -(p["km"] or 0)))

    monde = {
        "maj": time.strftime("%Y-%m-%d"),
        "pays": classement,
        "villes": sorted(fiches, key=lambda f: -(f["km"] or 0)),
    }
    poids_index = ecrire(os.path.join(SORTIE, "monde.json"), monde)

    # Les villes d'une fabrication précédente qui n'apparaissent plus doivent
    # partir : un nom de fichier change dès qu'une ville est renommée, et la
    # carte irait chercher un tracé que le classement ne mentionne plus.
    ecrits = {f["s"] + ".json" for f in fiches}
    dossier = os.path.join(SORTIE, "villes")
    orphelins = [n for n in os.listdir(dossier)
                 if n.endswith(".json") and n not in ecrits]
    for n in orphelins:
        os.remove(os.path.join(dossier, n))
    if orphelins:
        dit(f"  {len(orphelins)} fichiers de villes d'une fabrication "
            f"précédente, effacés")

    dit(f"  {len(fiches)} villes · {sum(len(f['sys']) for f in fiches)} réseaux · "
        f"{sum(f['lg'] or 0 for f in fiches)} lignes · "
        f"{sum(f['st'] or 0 for f in fiches)} stations")
    dit(f"  data/metro/monde.json : {poids_index // 1024} Ko ; "
        f"les {len(fiches)} fichiers de ville : {poids_total // 1024} Ko en tout")
    return monde



def fabriquer_apercu():
    """Écrit data/metro/apercu.json à partir des fichiers de ville déjà écrits."""
    dossier = os.path.join(SORTIE, "villes")
    lignes = []
    for nom in sorted(os.listdir(dossier)):
        if not nom.endswith(".json"):
            continue
        with open(os.path.join(dossier, nom), encoding="utf-8") as f:
            ville = json.load(f)
        for l in ville.get("lignes", []):
            for chemin in enchainer(l.get("t") or []):
                p = arrondir(alleger(chemin, APERCU_TOLERANCE_M), APERCU_DECIMALES)
                p = sans_doublons(p)
                if len(p) > 1:
                    # Le nom de fichier de la ville voyage avec le tracé : c'est
                    # ce qui permet d'ouvrir la bonne fiche quand on clique sur
                    # une ligne de loin, avant que le tracé détaillé soit là.
                    lignes.append([l["couleur"], p, ville["s"]])
    poids = ecrire(os.path.join(SORTIE, "apercu.json"), {"l": lignes})
    dit(f"  data/metro/apercu.json : {len(lignes)} tracés, {poids // 1024} Ko")
    return poids



# --- Le déroulé ------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)

    # Raccourci : refaire seulement l'aperçu du monde, sans rien retélécharger.
    if "--apercu" in sys.argv:
        dit("→ Aperçu du monde, à partir des fichiers de ville déjà écrits")
        fabriquer_apercu()
        sys.exit(0)

    dit("→ OpenStreetMap : tous les métros du monde, en six pavés")
    moissonner()
    relations, voies = lire_moisson()
    dit(f"  {len(relations)} lignes et {len(voies)} tronçons en construction")

    dit("→ Wikidata : qu'est-ce qui est un métro ?")
    metros = metros_selon_wikidata()
    dit(f"  {len(metros)} métros reconnus")

    dit("→ Rangement : les relations en réseaux, puis en lignes")
    reseaux = reseaux_du_monde(relations, metros)
    chantiers = lire_chantiers(voies)
    dit(f"  {len(reseaux)} réseaux · {len(chantiers)} chantiers")

    dit("→ OpenStreetMap : le nom de la ville la plus proche de chaque réseau")
    lieux = villes_proches([r["centre"] for r in reseaux]
                           + [centre([m["centre"] for m in g]) for g in chantiers])
    dit(f"  {len(lieux)} villes candidates")

    villes = assembler(reseaux, chantiers, lieux)

    dit("→ Wikidata : les noms en treize langues, le pays, l'ouverture")
    etat_villes = etat_civil_des_villes(
        {v["lieu"]["qid"] for v in villes.values() if v["lieu"].get("qid")})
    etat_reseaux = etat_civil_des_reseaux(
        {r["qid"] for v in villes.values()
         for r in v["reseaux"].values() if r["qid"]})
    dit(f"  {len(etat_villes)} villes et {len(etat_reseaux)} réseaux renseignés")

    dit("→ Écriture de data/metro/")
    fabriquer(villes, etat_villes, etat_reseaux, metros)

    dit("→ Aperçu du monde entier, pour l'arrivée sur la carte")
    fabriquer_apercu()
    dit("✓ Terminé.")
