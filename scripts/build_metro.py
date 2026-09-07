#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_metro.py — prépare la carte des métros du monde.

Ce que fait ce script, en une phrase :
il récupère la liste officielle des métros du monde chez Wikipédia, va chercher
le tracé réel de chaque ligne et sa couleur officielle dans OpenStreetMap, et
range le tout dans data/metro/ pour que la carte s'affiche très vite.

À lancer :  python3 scripts/build_metro.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).

Le script est long à tourner la première fois (il interroge OpenStreetMap ville
par ville, poliment). Tout ce qu'il télécharge est gardé dans
scripts/.cache-metro/ : les fois suivantes, il repart de là en quelques
secondes. Pour tout retélécharger : effacer ce dossier, ou lancer

    python3 scripts/build_metro.py --neuf
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
from html.parser import HTMLParser

# --- Où l'on prend les données -------------------------------------------

# 1. LA LISTE DE RÉFÉRENCE. « Qu'est-ce qu'un vrai métro ? » est une question
#    piégeuse : le tramway souterrain de Cologne y ressemble, le RER de Séoul
#    aussi, et pourtant ni l'un ni l'autre n'en est un. Plutôt que d'inventer
#    notre propre définition, on reprend celle de Wikipédia, qui applique les
#    critères de l'UITP (voie entièrement séparée du reste de la circulation,
#    haute fréquence, service urbain) et dont la liste est surveillée depuis
#    des années. Elle donne aussi les chiffres du panneau : longueur, stations,
#    fréquentation.
WIKI = "https://en.wikipedia.org/w/api.php"
PAGE_LISTE = "List_of_metro_systems"

# 2. LES TRACÉS ET LES COULEURS. OpenStreetMap est la seule source au monde qui
#    donne le dessin exact de chaque ligne ET sa couleur officielle. 96 % des
#    lignes portent leur couleur (le rose #FF7F32 de la ligne 5 à Paris).
OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Les treize langues du site. Wikipédia connaît le nom de chaque ville dans
# chacune : « Londres », « ロンドン », « لندن ». Il n'y a donc rien à traduire
# à la main — c'est le même principe que les noms de pays de Natural Earth.
LANGUES = ["fr", "en", "uk", "de", "es", "it", "pt", "pl", "ja", "ko", "tr", "hi", "ar"]

# Les noms de pays de Wikipédia ne sont pas ceux de nos fichiers. On les relie
# par leur code ISO à trois lettres, celui de data/pays.json.
PAYS_ISO = {
    "Algeria": "DZA", "Argentina": "ARG", "Armenia": "ARM", "Australia": "AUS",
    "Austria": "AUT", "Azerbaijan": "AZE", "Bangladesh": "BGD", "Belarus": "BLR",
    "Belgium": "BEL", "Brazil": "BRA", "Bulgaria": "BGR", "Canada": "CAN",
    "Chile": "CHL", "China": "CHN", "Colombia": "COL", "Czech Republic": "CZE",
    "Czechia": "CZE", "Denmark": "DNK", "Dominican Republic": "DOM",
    "Ecuador": "ECU", "Egypt": "EGY", "Finland": "FIN", "France": "FRA", "Georgia (country)": "GEO",
    "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN", "India": "IND",
    "Indonesia": "IDN", "Iran": "IRN", "Ireland": "IRL", "Israel": "ISR",
    "Italy": "ITA", "Ivory Coast": "CIV", "Japan": "JPN", "Kazakhstan": "KAZ",
    "Malaysia": "MYS", "Mexico": "MEX", "Netherlands": "NLD", "Nigeria": "NGA",
    "North Korea": "PRK", "Norway": "NOR", "Pakistan": "PAK", "Panama": "PAN",
    "Peru": "PER", "Philippines": "PHL", "Poland": "POL", "Portugal": "PRT",
    "Qatar": "QAT", "Romania": "ROU", "Russia": "RUS", "Saudi Arabia": "SAU",
    "Serbia": "SRB", "Singapore": "SGP", "South Korea": "KOR", "Spain": "ESP",
    "Sweden": "SWE", "Switzerland": "CHE", "Taiwan": "TWN", "Thailand": "THA",
    "Turkey": "TUR", "Türkiye": "TUR", "Ukraine": "UKR",
    "United Arab Emirates": "ARE", "United Kingdom": "GBR",
    "United States": "USA", "Uzbekistan": "UZB", "Venezuela": "VEN",
    "Vietnam": "VNM",
}

# Hong Kong et Macao : Wikipédia les range sous « China », et c'est aussi le
# choix de StatsMaps pour le classement par pays. Mais la carte doit pouvoir
# écrire « Hong Kong » plutôt que « Chine » sous la pastille : la ville porte
# donc son propre nom, et son pays reste la Chine.

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


def telecharger(url, donnees=None, essais=4):
    """Télécharge une page. Réessaie si le serveur est occupé."""
    for n in range(essais):
        try:
            corps = donnees.encode() if donnees else None
            req = urllib.request.Request(url, data=corps, headers=EN_TETES)
            with urllib.request.urlopen(req, timeout=600) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if n == essais - 1:
                raise
            attente = 20 * (n + 1)
            dit(f"    … {type(e).__name__} ; nouvel essai dans {attente} s")
            time.sleep(attente)


def slug(texte):
    """« Saint-Pétersbourg » -> « saint-petersbourg ». Sert aux noms de fichiers."""
    t = unicodedata.normalize("NFD", texte)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower().replace("'", "-").replace("’", "-")
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "ville"


def nombre(texte):
    """« 56.7 km (35.2 mi) » -> 56.7 ; « 1,234 » -> 1234."""
    if not texte:
        return None
    t = texte.replace(",", "").replace(" ", " ")
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    return float(m.group(1)) if m else None


def annee(texte):
    m = re.search(r"(1[89]\d\d|20\d\d)", texte or "")
    return int(m.group(1)) if m else None


# --- Étape 1 : la liste de référence de Wikipédia -------------------------

class Tableaux(HTMLParser):
    """Découpe les tableaux d'une page Wikipédia en lignes de cellules.

    On lit la page **déjà mise en page** plutôt que sa source, parce que les
    cellules fusionnées (une seule case « Inde » en face de quinze villes) y
    sont explicites. Sur la source, elles obligent à deviner, et on perd des
    pays entiers.

    Chaque cellule est rendue sous la forme (texte, liens), où les liens sont
    les titres des articles pointés — c'est ainsi qu'on récupère le nom exact
    du pays et de la ville, sans dépendre du texte affiché.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.pile, self.table = [], [], None
        self.ligne, self.cellule, self.liens = None, None, None
        self.report, self.colonne, self.ignorer = {}, 0, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table":
            self.pile.append(self.table)
            self.table, self.report = [], {}
        elif tag == "tr" and self.table is not None:
            self.ligne, self.colonne = [], 0
        elif tag in ("td", "th") and self.ligne is not None:
            self.cellule, self.liens = [], []
            self.span = (int(a.get("rowspan") or 1), int(a.get("colspan") or 1))
        elif tag == "a" and self.liens is not None:
            href = a.get("href", "")
            if href.startswith("/wiki/"):
                titre = urllib.parse.unquote(href[6:].split("#")[0]).replace("_", " ")
                if ":" not in titre:
                    self.liens.append(titre)
        elif tag in ("sup", "style", "script"):
            self.ignorer += 1

    def handle_endtag(self, tag):
        if tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = self.pile.pop() if self.pile else None
        elif tag == "tr" and self.ligne is not None:
            self._reports_restants()
            if self.ligne:
                self.table.append(self.ligne)
            self.ligne = None
        elif tag in ("td", "th") and self.cellule is not None:
            texte = re.sub(r"\s+", " ", "".join(self.cellule)).strip()
            for _ in range(self.span[1]):
                self._poser(texte, self.liens, self.span[0])
            self.cellule, self.liens = None, None
        elif tag in ("sup", "style", "script"):
            self.ignorer = max(0, self.ignorer - 1)

    def _reports_restants(self):
        while self.report.get(self.colonne, [0, 0, 0])[2] > 0:
            r = self.report[self.colonne]
            self.ligne.append((r[0], r[1]))
            r[2] -= 1
            self.colonne += 1

    def _poser(self, texte, liens, rowspan):
        self._reports_restants()
        self.ligne.append((texte, liens))
        if rowspan > 1:
            self.report[self.colonne] = [texte, liens, rowspan - 1]
        self.colonne += 1

    def handle_data(self, d):
        if self.cellule is not None and not self.ignorer:
            self.cellule.append(d)


def liste_wikipedia():
    """Les trois tableaux de « List of metro systems »."""
    html = cache_lire("wikipedia.json")
    if html is None:
        dit("→ Wikipédia : la liste de référence des métros du monde")
        url = (f"{WIKI}?action=parse&page={PAGE_LISTE}&prop=text"
               "&format=json&formatversion=2")
        html = json.loads(telecharger(url))["parse"]["text"]
        cache_ecrire("wikipedia.json", html)

    p = Tableaux()
    p.feed(html)

    def entete(t):
        return " ".join(c[0] for c in t[0]).lower() if t else ""

    t_systemes = t_pays = t_chantiers = None
    for t in p.tables:
        e = entete(t)
        if "annual ridership" in e and "city" in e and t_systemes is None:
            t_systemes = t
        elif e.startswith("country") and "inauguration" in e:
            t_pays = t
        elif "construction started" in e:
            t_chantiers = t
    if not (t_systemes and t_pays and t_chantiers):
        sys.exit("✗ Wikipédia a changé la forme de ses tableaux : script à revoir.")

    systemes = []
    for l in t_systemes[1:]:
        if len(l) < 8:
            continue
        ville = l[0][1][0] if l[0][1] else l[0][0]
        pays = l[1][1][0] if l[1][1] else l[1][0]
        nom = l[2][1][0] if l[2][1] else l[2][0]
        systemes.append({
            "ville_wiki": ville,
            "ville_affichee": l[0][0] or ville,
            "pays_wiki": pays,
            "nom_wiki": nom,
            "nom": l[2][0] or nom,
            "ouverture": annee(l[3][0]),
            "agrandi": annee(l[4][0]),
            "stations": nombre(l[5][0]),
            "km": nombre(l[6][0]),
            "voyageurs": nombre(l[7][0]),
        })

    pays = []
    for l in t_pays[1:]:
        if len(l) < 7:
            continue
        nom = l[0][1][0] if l[0][1] else l[0][0]
        pays.append({
            "pays_wiki": nom,
            "systemes": nombre(l[1][0]),
            "km": nombre(l[2][0]),
            "lignes": nombre(l[3][0]),
            "stations": nombre(l[4][0]),
            "ouverture": annee(l[6][0]),
        })

    chantiers = []
    for l in t_chantiers[1:]:
        if len(l) < 5:
            continue
        ville = l[0][1][0] if l[0][1] else l[0][0]
        chantiers.append({
            "ville_wiki": ville,
            "ville_affichee": l[0][0] or ville,
            "pays_wiki": l[1][1][0] if l[1][1] else l[1][0],
            "nom": l[2][0],
            "nom_wiki": l[2][1][0] if l[2][1] else l[2][0],
            "debut": annee(l[3][0]),
            "prevu": annee(l[4][0]),
        })

    dit(f"  {len(systemes)} systèmes en service · {len(pays)} pays · "
        f"{len(chantiers)} premiers métros en construction")
    return systemes, pays, chantiers


# --- Étape 2 : où sont ces villes, et comment les appelle-t-on ? ----------

def _api_wiki(params):
    url = WIKI + "?" + urllib.parse.urlencode(params)
    return json.loads(telecharger(url))


def _lots(liste, taille=50):
    for i in range(0, len(liste), taille):
        yield liste[i:i + taille]


def _pages(d):
    """Renvoie {titre demandé -> page}, en suivant les redirections.

    Wikipédia redirige « Bombay » vers « Mumbai » : sans cela on ne
    retrouverait pas la ville qu'on avait demandée.
    """
    q = d.get("query", {})
    redir = {r["from"]: r["to"] for r in q.get("redirects", [])}
    norm = {n["from"]: n["to"] for n in q.get("normalized", [])}
    par_titre = {p["title"]: p for p in q.get("pages", [])}

    def trouver(t):
        t = norm.get(t, t)
        return par_titre.get(redir.get(t, t))
    return trouver


def villes_coordonnees_et_noms(titres, fichier="villes.json"):
    """Pour chaque article de Wikipédia : ses coordonnées et son nom en 13 langues.

    Sert deux fois : pour les villes (« Londres », « ロンドン ») et pour les
    réseaux (« Métro de Londres »). Dans le second cas les coordonnées sont
    vides, ce qui est sans importance.

    Deux demandes séparées, et c'est important : réclamer les coordonnées et
    les traductions dans le même appel fait tronquer la réponse (un article de
    ville a 250 traductions, la limite est de 500 pour tout l'appel) et une
    centaine de villes revenaient alors sans position.

    Les noms traduits viennent des « liens de langue » de l'article : c'est
    Wikipédia qui écrit « Londres » en français et « ロンドン » en japonais,
    pas nous. Même principe que les noms de pays de Natural Earth.
    """
    connu = cache_lire(fichier) or {}
    manquants = [t for t in titres if t not in connu]
    if not manquants:
        return connu

    dit(f"→ Wikipédia : nom en 13 langues de {len(manquants)} articles")
    for lot in _lots(manquants):
        d = _api_wiki({"action": "query", "format": "json", "formatversion": "2",
                       "prop": "coordinates", "colimit": "max",
                       "titles": "|".join(lot), "redirects": "1"})
        trouver = _pages(d)
        for t in lot:
            p = trouver(t)
            co = ((p or {}).get("coordinates") or [{}])[0]
            connu[t] = {"lat": co.get("lat"), "lon": co.get("lon"),
                        "noms": {"en": (p or {}).get("title", t)}}
        time.sleep(0.2)

    for langue in LANGUES:
        if langue == "en":
            continue
        for lot in _lots(manquants):
            d = _api_wiki({"action": "query", "format": "json", "formatversion": "2",
                           "prop": "langlinks", "lllang": langue, "lllimit": "500",
                           "titles": "|".join(lot), "redirects": "1"})
            trouver = _pages(d)
            for t in lot:
                p = trouver(t) or {}
                for ll in p.get("langlinks", []):
                    connu[t]["noms"][langue] = ll["title"]
            time.sleep(0.2)
        dit(f"    noms en {langue} ✓")

    cache_ecrire(fichier, connu)
    return connu


# Trois villes dont l'article de Wikipédia ne déclare aucune coordonnée
# (leur encadré n'utilise pas le modèle habituel). Position du centre-ville.
COORDONNEES_A_LA_MAIN = {
    "Delhi": (28.6139, 77.2090),
    "Nagpur": (21.1458, 79.0882),
    "Navi Mumbai": (19.0330, 73.0297),
}


# --- Étape 3 : les tracés, dans OpenStreetMap -----------------------------

# Rayon interrogé autour du centre-ville, en kilomètres. Assez large pour aller
# chercher les bouts de ligne en grande banlieue, assez serré pour ne pas
# attraper le métro de la ville voisine. Les agglomérations qui se touchent —
# Canton et Foshan, Tokyo et Yokohama — sont départagées après coup : chaque
# ligne est rattachée à la ville dont son centre est le plus proche.
RAYON_KM = 45

# On interroge OpenStreetMap par paquets de villes plutôt qu'une par une :
# une requête coûte surtout du temps d'attente, et 24 requêtes valent mieux
# que 232 pour le serveur comme pour nous (une heure au lieu de quatre).
VILLES_PAR_REQUETE = 10

REQUETE = """[out:json][timeout:600];
(
{autour_relations}
);
out geom;
(
{autour_chantiers}
);
out geom;
"""


def osm_paquet(lot, cle):
    """Interroge OpenStreetMap autour d'un paquet de villes.

    On demande trois choses :
      · les lignes de métro en service          (relation route=subway)
      · les lignes de « métro léger »           (relation route=light_rail)
        — le tri entre vrais métros automatiques (le DLR de Londres) et
          tramways déguisés se fait plus tard, à la lumière de la liste de
          Wikipédia ;
      · les tronçons en construction            (way railway=construction)
        — ceux-là sont dessinés en pointillés.
    """
    d = cache_lire(f"osm-{cle}.json")
    if d is not None:
        return d
    # « out geom » et non « out tags geom » : dans le langage d'Overpass,
    # « tags » n'ajoute pas les étiquettes à la géométrie, il DEMANDE les
    # étiquettes SEULES — et les relations reviennent alors sans aucun tracé.
    r = int(RAYON_KM * 1000)
    rel, chantiers = [], []
    for lat, lon in lot:
        rel.append(f'  relation["route"="subway"](around:{r},{lat},{lon});')
        rel.append(f'  relation["route"="light_rail"](around:{r},{lat},{lon});')
        chantiers.append(
            '  way["railway"="construction"]'
            f'["construction"~"^(subway|light_rail)$"](around:{r},{lat},{lon});')
    req = REQUETE.format(autour_relations="\n".join(rel),
                         autour_chantiers="\n".join(chantiers))
    derniere = None
    for essai in range(3):
        for serveur in OVERPASS:
            try:
                d = json.loads(telecharger(serveur, "data=" + urllib.parse.quote(req),
                                           essais=1))
                cache_ecrire(f"osm-{cle}.json", d)
                time.sleep(3)      # on ne bouscule pas un serveur bénévole
                return d
            except Exception as e:
                derniere = e
                dit(f"    … {serveur.split('/')[2]} : {type(e).__name__}")
                time.sleep(15)
    raise derniere


def moissonner(villes_utiles):
    """Interroge OpenStreetMap pour toutes les villes, par paquets."""
    titres = sorted(villes_utiles)
    paquets = [titres[i:i + VILLES_PAR_REQUETE]
               for i in range(0, len(titres), VILLES_PAR_REQUETE)]
    for n, paquet in enumerate(paquets, 1):
        cle = f"{n:02d}-" + slug(paquet[0])
        if cache_lire(f"osm-{cle}.json") is not None:
            continue
        dit(f"  [{n}/{len(paquets)}] {paquet[0]} … {paquet[-1]}")
        osm_paquet([(villes_utiles[t]["lat"], villes_utiles[t]["lon"]) for t in paquet],
                   cle)
    return [f"osm-{n:02d}-{slug(p[0])}.json" for n, p in enumerate(paquets, 1)]


# --- Étape 4 : de la géométrie -------------------------------------------

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


# --- Étape 5 : rattacher chaque ligne à sa ville --------------------------

# Au-delà de cette distance du centre-ville, une ligne trouvée par la requête
# n'appartient à aucune des villes de la liste : c'est un tramway de banlieue
# ou le réseau d'une ville voisine qui n'a pas de métro. On la laisse tomber.
RATTACHEMENT_KM = 60

# Mots qui ne distinguent rien : ils reviennent dans presque tous les noms de
# réseau du monde et ne peuvent donc pas servir à reconnaître un réseau.
MOTS_VIDES = {
    "metro", "métro", "subway", "underground", "rail", "railway", "light",
    "transit", "rapid", "mass", "system", "line", "lines", "urban", "city",
    "the", "de", "du", "des", "la", "le", "of", "and", "et", "tunnelbana",
    "u", "bahn", "ubahn", "mrt", "lrt", "train", "tren", "metropolitana",
}


def mots_cles(texte):
    """Les mots d'un nom qui servent vraiment à le reconnaître.

    « Docklands Light Railway » -> {docklands} ; « Paris Metro » -> {paris}.
    """
    t = unicodedata.normalize("NFD", (texte or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return {m for m in re.split(r"[^a-z0-9]+", t) if len(m) > 2 and m not in MOTS_VIDES}


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


def lire_moisson():
    """Relit tous les paquets téléchargés, sans doublons."""
    relations, chantiers = {}, {}
    for nom in sorted(os.listdir(CACHE)):
        if not nom.startswith("osm-"):
            continue
        with open(os.path.join(CACHE, nom), encoding="utf-8") as f:
            for e in json.load(f).get("elements", []):
                (relations if e["type"] == "relation" else chantiers)[e["id"]] = e
    return list(relations.values()), list(chantiers.values())


def ville_la_plus_proche(point, index):
    """La ville dont le centre est le plus près, et à quelle distance."""
    meilleure, courte = None, 1e9
    for titre, (lon, lat) in index.items():
        d = distance_km(point, (lon, lat))
        if d < courte:
            meilleure, courte = titre, d
    return meilleure, courte


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


def rassembler(systemes, pays_wiki, chantiers_wiki, villes):
    """Range les tracés d'OpenStreetMap ville par ville, ligne par ligne."""
    index = {t: (v["lon"], v["lat"]) for t, v in villes.items()}
    par_ville = {}
    for t in villes:
        par_ville[t] = {"lignes": {}, "chantiers": []}

    # Les réseaux que Wikipédia reconnaît dans chaque ville, en mots-clés :
    # ils servent à trancher le cas des lignes taguées « métro léger ».
    attendus = {}
    for s in systemes:
        v = s["ville_wiki"]
        attendus.setdefault(v, set()).update(mots_cles(s["nom"]) | mots_cles(s["nom_wiki"]))
    for v in attendus:
        attendus[v] -= mots_cles(v)     # le nom de la ville ne distingue rien

    relations, voies = lire_moisson()
    dit(f"  {len(relations)} lignes et {len(voies)} tronçons en construction à trier")

    ecartees = {"loin": 0, "leger": 0, "vide": 0}
    for r in relations:
        bouts = geometrie(r)
        if not bouts:
            ecartees["vide"] += 1
            continue
        tags = r.get("tags", {})
        tous = [p for b in bouts.values() for p in b]
        ville, d = ville_la_plus_proche(centre(tous), index)
        if d > RATTACHEMENT_KM:
            ecartees["loin"] += 1
            continue
        if tags.get("route") == "light_rail":
            # Un « light_rail » n'entre que s'il porte le nom d'un réseau que
            # Wikipédia range parmi les métros : c'est ainsi que le DLR de
            # Londres entre et que le tramway de Lille reste dehors.
            mots = (mots_cles(tags.get("network")) | mots_cles(tags.get("operator"))
                    | mots_cles(tags.get("name")))
            if not (mots & attendus.get(ville, set())):
                ecartees["leger"] += 1
                continue
        # Les deux sens d'une même ligne portent le même réseau et le même
        # numéro : c'est ce couple qui fait l'identité d'une ligne.
        cle = (tags.get("network") or tags.get("operator") or "",
               tags.get("ref") or nom_de_ligne(tags) or str(r["id"]))
        ligne = par_ville[ville]["lignes"].setdefault(cle, {
            "ref": tags.get("ref"), "noms": {}, "couleurs": {}, "bouts": {},
        })
        ligne["bouts"].update(bouts)
        n = nom_de_ligne(tags)
        if n:
            ligne["noms"][n] = ligne["noms"].get(n, 0) + 1
        c = couleur_propre(tags.get("colour"))
        if c:
            ligne["couleurs"][c] = ligne["couleurs"].get(c, 0) + 1

    for v in voies:
        bouts = geometrie(v)
        if not bouts:
            continue
        tous = [p for b in bouts.values() for p in b]
        ville, d = ville_la_plus_proche(centre(tous), index)
        if d > RATTACHEMENT_KM:
            continue
        tags = v.get("tags", {})
        par_ville[ville]["chantiers"].append({
            "points": list(bouts.values())[0],
            "couleur": couleur_propre(tags.get("colour")),
            "nom": nom_de_ligne(tags),
        })

    dit(f"  écartées : {ecartees['loin']} trop loin d'une ville de la liste, "
        f"{ecartees['leger']} métros légers non reconnus, {ecartees['vide']} sans tracé")
    return par_ville


# --- Étape 6 : écrire les fichiers du site --------------------------------

# La couleur d'une ligne qui n'en déclare aucune dans OpenStreetMap (4 % des
# lignes). Un gris bleuté, qui ne ressemble à aucune couleur officielle et se
# voit dans les deux thèmes.
COULEUR_INCONNUE = "#7A8A99"


def ecrire(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(chemin)


def fabriquer(systemes, pays_wiki, chantiers_wiki, villes, recolte):
    """Écrit data/metro/monde.json et un fichier par ville."""
    par_ville_systemes = {}
    for s in systemes:
        par_ville_systemes.setdefault(s["ville_wiki"], []).append(s)
    en_chantier = {}
    for c in chantiers_wiki:
        en_chantier.setdefault(c["ville_wiki"], []).append(c)

    fiches, poids_total = [], 0
    for titre in sorted(set(par_ville_systemes) | set(en_chantier)):
        v = villes.get(titre)
        if not v or not v.get("lat"):
            continue
        r = recolte.get(titre, {"lignes": {}, "chantiers": []})
        s_ville = par_ville_systemes.get(titre, [])
        c_ville = en_chantier.get(titre, [])
        pays_nom = (s_ville or c_ville)[0]["pays_wiki"]
        iso = PAYS_ISO.get(pays_nom)
        if not iso:
            dit(f"  ⚠ pays inconnu : {pays_nom} ({titre}) — à ajouter dans PAYS_ISO")
            continue

        # --- les lignes, allégées
        lignes, km_lignes = [], 0.0
        for (reseau, _), l in r["lignes"].items():
            traces = [arrondir(alleger(b)) for b in l["bouts"].values()]
            traces = [t for t in traces if len(t) > 1]
            if not traces:
                continue
            km = sum(longueur_km(t) for t in traces)
            km_lignes += km
            couleur = max(l["couleurs"], key=l["couleurs"].get) if l["couleurs"] else None
            nom = max(l["noms"], key=l["noms"].get) if l["noms"] else None
            lignes.append({
                "ref": l["ref"], "nom": nom, "reseau": reseau or None,
                "couleur": couleur or COULEUR_INCONNUE,
                "sansCouleur": 1 if not couleur else 0,
                "km": round(km, 1), "t": traces,
            })
        lignes.sort(key=lambda x: (-x["km"], x["ref"] or ""))

        # --- les chantiers
        chantiers = []
        for c in r["chantiers"]:
            t = arrondir(alleger(c["points"]))
            if len(t) > 1:
                chantiers.append({"couleur": c["couleur"], "nom": c["nom"], "t": t})
        km_chantier = km_des_chantiers(chantiers)

        s = slug(titre)
        poids_total += ecrire(os.path.join(SORTIE, "villes", s + ".json"),
                              {"s": s, "lignes": lignes, "chantiers": chantiers})

        fiches.append({
            "s": s, "iso": iso, "lon": round(v["lon"], 4), "lat": round(v["lat"], 4),
            "n": v["noms"],
            "km": round(sum(x["km"] or 0 for x in s_ville), 1) or None,
            "st": int(sum(x["stations"] or 0 for x in s_ville)) or None,
            "vy": round(sum(x["voyageurs"] or 0 for x in s_ville), 1) or None,
            "depuis": min([x["ouverture"] for x in s_ville if x["ouverture"]] or [0]) or None,
            "lg": len(lignes) or None,
            "kmc": round(km_chantier, 1) or None,
            "enService": 1 if s_ville else 0,
            "sys": [{"n": x["noms"], "depuis": x["ouverture"], "km": x["km"],
                     "st": int(x["stations"]) if x["stations"] else None}
                    for x in s_ville],
            "futur": [{"n": x["noms"], "debut": x["debut"], "prevu": x["prevu"]}
                      for x in c_ville],
        })

    # --- le classement par pays
    km_chantier_pays = {}
    for f in fiches:
        km_chantier_pays[f["iso"]] = km_chantier_pays.get(f["iso"], 0) + (f["kmc"] or 0)
    pays = []
    for p in pays_wiki:
        iso = PAYS_ISO.get(p["pays_wiki"])
        if not iso:
            dit(f"  ⚠ pays inconnu au classement : {p['pays_wiki']}")
            continue
        pays.append({
            "iso": iso, "sys": int(p["systemes"] or 0), "km": p["km"],
            "lg": int(p["lignes"] or 0), "st": int(p["stations"] or 0),
            "depuis": p["ouverture"],
            "kmc": round(km_chantier_pays.get(iso, 0), 1) or None,
            "villes": [f["s"] for f in fiches if f["iso"] == iso and f["enService"]],
        })
    # Les pays qui n'ont qu'un chantier ne figurent pas au tableau de Wikipédia
    # (ils n'ont pas encore de métro) : on les ajoute, à zéro.
    connus = {p["iso"] for p in pays}
    for f in fiches:
        if f["iso"] not in connus and not f["enService"]:
            connus.add(f["iso"])
            pays.append({"iso": f["iso"], "sys": 0, "km": None, "lg": 0, "st": 0,
                         "depuis": None, "kmc": km_chantier_pays.get(f["iso"]),
                         "villes": []})
    pays.sort(key=lambda p: (-p["sys"], -(p["km"] or 0)))

    monde = {
        "maj": time.strftime("%Y-%m-%d"),
        "pays": pays,
        "villes": sorted(fiches, key=lambda f: -(f["km"] or 0)),
    }
    poids_index = ecrire(os.path.join(SORTIE, "monde.json"), monde)

    dit(f"  {len(fiches)} villes · {sum(len(f['sys']) for f in fiches)} réseaux · "
        f"{sum(f['lg'] or 0 for f in fiches)} lignes dessinées")
    dit(f"  data/metro/monde.json : {poids_index // 1024} Ko ; "
        f"les {len(fiches)} fichiers de ville : {poids_total // 1024} Ko en tout")
    return monde


def km_des_chantiers(chantiers):
    """Longueur des tronçons en construction, sans compter deux fois les voies.

    Un tunnel de métro est dessiné VOIE PAR VOIE dans OpenStreetMap : deux
    traits parallèles, distants d'une dizaine de mètres. Les additionner
    donnerait un chantier deux fois trop long.

    On procède donc par élimination : les tronçons sont examinés du plus long
    au plus court, et un tronçon qui suit un tronçon déjà compté — plus des
    trois quarts de ses points à moins de 25 m d'un tracé retenu — est la
    seconde voie du même tunnel, et n'est pas compté.

    Les deux traits restent DESSINÉS tous les deux : à l'écran ils se
    confondent, et les effacer ferait disparaître la moitié des aiguillages.
    Ce n'est que le compteur de kilomètres qui les ignore.
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
    for c in sorted(chantiers, key=lambda c: -longueur_km(c["t"])):
        points = echantillonner(c["t"])
        deja = 0
        for p in points:
            voisins = [q for case in cases_du_point(p[0], p[1], 1)
                       for q in retenus.get(case, ())]
            if any(distance_km(p, q) * 1000 < PROCHE_M for q in voisins):
                deja += 1
        if deja > 0.75 * len(points):
            continue
        total += longueur_km(c["t"])
        for p in points:
            retenus.setdefault(cases_du_point(p[0], p[1])[0], []).append(p)
    return total


if __name__ == "__main__":
    os.makedirs(CACHE, exist_ok=True)
    systemes, pays, chantiers = liste_wikipedia()
    titres = sorted({s["ville_wiki"] for s in systemes} |
                    {c["ville_wiki"] for c in chantiers})
    villes = villes_coordonnees_et_noms(titres)
    for t, (lat, lon) in COORDONNEES_A_LA_MAIN.items():
        if t in villes and not villes[t].get("lat"):
            villes[t]["lat"], villes[t]["lon"] = lat, lon
    utiles = {t: v for t, v in villes.items() if v.get("lat")}
    sans = [t for t in titres if t not in utiles]
    dit(f"  {len(utiles)} villes situées" + (f" ; sans position : {sans}" if sans else ""))

    # Le nom des réseaux, lui aussi dans les treize langues : « Métro de
    # Londres », « ロンドン地下鉄 ». Même source, même méthode que les villes.
    reseaux = villes_coordonnees_et_noms(
        sorted({s["nom_wiki"] for s in systemes} | {c["nom_wiki"] for c in chantiers}),
        fichier="reseaux.json")
    for s in systemes + chantiers:
        s["noms"] = reseaux.get(s["nom_wiki"], {}).get("noms") or {"en": s["nom"]}

    dit("→ OpenStreetMap : les tracés et les couleurs, ville par ville")
    moissonner(utiles)

    dit("→ Rangement : chaque ligne à sa ville")
    recolte = rassembler(systemes, pays, chantiers, utiles)

    dit("→ Écriture de data/metro/")
    fabriquer(systemes, pays, chantiers, utiles, recolte)
    dit("✓ Terminé.")
