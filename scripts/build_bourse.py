#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_bourse.py — prépare la carte des entreprises cotées en bourse.

Ce que fait ce script, en une phrase :
il demande à Wikidata la liste de toutes les entreprises cotées en bourse,
l'endroit de leur siège, leur secteur, leurs chiffres et leur logo, puis range
le tout dans data/bourse/.

À lancer :  python3 scripts/build_bourse.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).

  ── Une seule source : Wikidata ─────────────────────────────────────────────

Wikidata est la grande base de données libre qui sert aussi à Wikipédia. Pour
chaque entreprise, elle sait (quand quelqu'un l'a renseigné) :

  · sur quelle(s) bourse(s) elle est cotée, et sous quel symbole ;
  · où est son siège ;
  · son secteur d'activité ;
  · son chiffre d'affaires, ses effectifs, sa valeur en bourse ;
  · son logo (sur Wikimedia Commons) et son site officiel.

  ── Bleu ou jaune : à quel point le siège est-il bien placé ? ─────────────

Le siège d'une entreprise est le plus souvent noté « Paris » ou « Tokyo »,
c'est-à-dire une VILLE, et non une adresse. Seule une minorité a la position
exacte de son immeuble. On distingue donc les deux, à la demande d'Antonin :

  bleu .... l'adresse exacte est connue (coordonnées de l'immeuble) ;
  jaune ... on ne connaît que la ville : le point est posé au centre-ville.

Le script est long la première fois (il télécharge aussi quelques milliers de
logos, poliment). Tout est gardé dans scripts/.cache-bourse/ : les fois
suivantes il repart de là. Pour tout retélécharger : --neuf
Pour ne pas toucher aux logos : --sans-logos
"""

import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# On réemploie la façon dont la carte des métros trouve le pays d'un point :
# le fond de carte du site (data/pays.json), et non Wikidata — ainsi la
# Crimée, Chypre ou le Sahara occidental suivent les mêmes choix partout.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_metro import charger_pays, pays_du_point  # noqa: E402

WIKIDATA = "https://query.wikidata.org/sparql"
EN_TETES = {"User-Agent": "StatsMaps/1.0 (+https://statsmaps.com)"}

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".cache-bourse")
SORTIE = os.path.join(DOSSIER, "data", "bourse")
LOGOS = os.path.join(SORTIE, "logos")

# La largeur des logos téléchargés, en pixels. Wikimedia ne fabrique vite que
# certaines tailles « standard » ; 120 en est une. Sur la carte, le logo est
# affiché dans un rond de 30 pixels : 120 reste net même sur un écran Retina.
LARGEUR_LOGO = 120


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


def telecharger(url, essais=4, entetes=None, binaire=False):
    """Télécharge une page. Réessaie si le serveur est occupé."""
    for n in range(essais):
        try:
            req = urllib.request.Request(url, headers=entetes or EN_TETES)
            with urllib.request.urlopen(req, timeout=300) as r:
                corps = r.read()
                return corps if binaire else corps.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            # 404 : le fichier n'existe pas, inutile d'insister.
            if e.code == 404 or n == essais - 1:
                raise
            attente = 15 * (n + 1)
            dit(f"    … erreur {e.code} ; nouvel essai dans {attente} s")
            time.sleep(attente)
        except Exception as e:
            if n == essais - 1:
                raise
            attente = 15 * (n + 1)
            dit(f"    … {type(e).__name__} ; nouvel essai dans {attente} s")
            time.sleep(attente)


def sparql(requete, nom_cache):
    """Interroge Wikidata. Une requête, un tableau — rien à gratter."""
    d = cache_lire(nom_cache)
    if d is not None:
        return d
    url = WIKIDATA + "?format=json&query=" + urllib.parse.quote(requete)
    entetes = dict(EN_TETES)
    entetes["Accept"] = "application/sparql-results+json"
    # Quand une question prend trop de temps, Wikidata coupe sa réponse en
    # plein milieu : le texte reçu n'est alors pas lisible. On réessaie.
    for essai in range(3):
        try:
            d = json.loads(telecharger(url, entetes=entetes))["results"]["bindings"]
            break
        except ValueError:
            if essai == 2:
                raise
            dit("    … réponse coupée ; nouvel essai dans 30 s")
            time.sleep(30)
    cache_ecrire(nom_cache, d)
    time.sleep(1)
    return d


def val(ligne, clef, defaut=None):
    return ligne[clef]["value"] if clef in ligne else defaut


def qid(uri):
    """« http://www.wikidata.org/entity/Q312 » -> « Q312 ». None si ce n'est
    pas une vraie fiche (Wikidata note parfois « valeur inconnue »)."""
    if not uri or "/entity/Q" not in uri:
        return None
    return uri.rsplit("/", 1)[1]


def point(wkt):
    """« Point(2.35 48.85) » -> (2.35, 48.85). None si illisible, ou si le
    point est sur la Lune : Wikidata accepte des coordonnées d'autres astres."""
    if not wkt or "<" in wkt:
        return None
    m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", wkt)
    if not m:
        return None
    lon, lat = float(m.group(1)), float(m.group(2))
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        return None
    return lon, lat


def distance_km(a, b):
    x = math.radians(b[0] - a[0]) * math.cos(math.radians((a[1] + b[1]) / 2))
    y = math.radians(b[1] - a[1])
    return 6371 * math.hypot(x, y)


def ecrire(chemin, valeur):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False, separators=(",", ":"))
    return os.path.getsize(chemin)


# --- Les secteurs ---------------------------------------------------------
#
# Wikidata connaît plus de 1 300 « secteurs d'activité » différents pour les
# entreprises cotées : « service financier », « système bancaire », « secteur
# financier », « banking »… On les regroupe en une vingtaine de grandes
# familles, celles qu'on coche et décoche dans le panneau de la carte.
#
# Comment on range un secteur, dans l'ordre :
#   1. il est dans la liste ci-dessous (les ~250 plus fréquents, rangés à la
#      main) ;
#   2. sinon, Wikidata dit qu'il est une SORTE de l'un d'eux (« banque
#      d'investissement » est une sorte de « banque ») ;
#   3. sinon, un mot de son nom anglais le trahit (« … insurance … ») ;
#   4. sinon, il n'est pas rangé, et l'entreprise tombe dans « Autre » si elle
#      n'a pas d'autre secteur.
#
# Les noms affichés sont dans assets/js/i18n.js (« bourse_sec_banque »…).

SECTEURS = {
    "banque": """Q837171 Q806718 Q57774188 Q22687 Q43015 Q29584334 Q16319025
                 Q4290 Q14864997 Q873442 Q96107414 Q3435731""",
    "assurance": "Q43183 Q2518196 Q334911 Q626608",
    "immobilier": "Q1660132 Q697852 Q695829 Q684740 Q401404",
    "logiciel": """Q880371 Q11661 Q638608 Q1481411 Q1540863 Q56611700 Q75 Q483639
                   Q1254596 Q21157865 Q11016 Q3510521 Q189900 Q1318054 Q97466003
                   Q5892272 Q110702998 Q11492876 Q1068473 Q1301371""",
    "ia": "Q11660 Q2539 Q197536 Q107307291",
    "electronique": """Q11650 Q5358497 Q2986369 Q11456 Q132898730 Q1067601
                       Q73768396 Q66221 Q1546066 Q56604188 Q3749263""",
    "telecom": "Q2401742 Q418 Q56598901 Q1780509 Q11024",
    "medias": """Q11033 Q56611639 Q173799 Q19595701 Q1415395 Q746359 Q932586
                 Q3972943 Q16023725 Q15078788 Q289 Q273623 Q1193236 Q37038
                 Q133080 Q638 Q10302058 Q59308842 Q4438117""",
    "jeux": "Q941594 Q11416 Q61054412 Q1368944 Q3550859",
    "sante": """Q507443 Q7108 Q12303494 Q31207 Q15067276 Q1519843 Q63383285
               Q327092 Q6554101""",
    "energie": """Q862571 Q2151621 Q2316331 Q383973 Q1326885 Q1326624 Q1951366
                 Q21328659 Q1778629 Q12880211 Q1349660 Q22656 Q40858 Q12089268
                 Q192127 Q48767813 Q12705 Q1304795 Q1341477 Q474883 Q99529212""",
    "mines": "Q44497 Q1945600 Q2285982 Q1924906 Q4063722 Q1071389 Q11467 Q22704511 Q1384538",
    "chimie": "Q207652 Q96472399 Q2283886 Q117156504 Q12144907 Q206615 Q1933500 Q11469",
    "industrie": """Q187939 Q101333 Q1957908 Q1803786 Q43035 Q10861389 Q770899
                   Q8148 Q474200 Q170978 Q184199 Q11023 Q11990434""",
    "automobile": "Q190117 Q3477381 Q786803",
    "aeronautique": "Q3477363 Q392933 Q1875606 Q2729047 Q3798668 Q16955053",
    "transport": """Q7590 Q177777 Q155930 Q651658 Q178512 Q3565868 Q1757562
                   Q2516512 Q1807108 Q765633""",
    "commerce": "Q126793 Q484847 Q220695 Q601401 Q7361709 Q867147 Q216107 Q10932402",
    "alimentation": """Q540912 Q4899370 Q627371 Q11451 Q396622 Q907703 Q13554450
                      Q11644505 Q107601756 Q18646422 Q637776 Q38112 Q30693206""",
    "consommation": "Q607081 Q11828862 Q12684 Q12752882 Q3246832 Q161439 Q56573357 Q1187656",
    "tourisme": """Q1495452 Q11707 Q49389 Q41958 Q9323634 Q81799 Q1285245 Q171141
                  Q27686 Q104714944 Q1751445""",
    "construction": "Q385378 Q13405640 Q77590 Q1799415 Q96472425",
    "services": "Q2029911 Q130286 Q63348704 Q1056396 Q39809 Q180388 Q55638 Q7406919",
    "conglomerat": "Q778575 Q219577 Q112165992 Q112166038 Q716785",
}

# Le secteur de ceux qui n'en ont aucun de reconnu.
AUTRE = "autre"

# Les « secteurs » qui n'en sont pas : Wikidata range parfois là le NOM d'une
# nomenclature (« Classification internationale type des industries »).
IGNORES = {"Q1666934"}

# Étape 3 : les mots qui trahissent un secteur dans son nom anglais.
# L'ordre compte : « investment bank » doit tomber dans la banque avant que
# « investment » ne soit lu ailleurs.
MOTS_DES_SECTEURS = [
    ("ia", r"artificial intelligence|machine learning"),
    ("assurance", r"insur|reinsur"),
    ("banque", r"bank|financ|invest|asset management|credit|payment|brokerage|stock exchange"),
    ("immobilier", r"real estate|property|reit"),
    ("jeux", r"video game|gambling|casino|betting|lotter"),
    ("medias", r"media|broadcast|film|music|publish|television|radio|newspaper|advertis|entertainment"),
    ("telecom", r"telecom|mobile phone|wireless"),
    ("electronique", r"semiconductor|electronic|computer hardware|chip"),
    ("logiciel", r"software|internet|information technology|computing|cloud|data|cyber|digital"),
    ("sante", r"pharma|biotech|health|medic|hospital|drug|diagnost"),
    ("energie", r"oil|petrol|gas|energy|electric power|electricity|solar|wind power|nuclear|utilit|coal|water"),
    ("mines", r"mining|steel|metal|iron|copper|gold|alumin|zinc|nickel"),
    ("chimie", r"chemi|paper|packag|cement|glass|plastic|fertili"),
    ("automobile", r"automo|motor vehicle|car manufactur|tire|tyre"),
    ("aeronautique", r"aero|aircraft|defen|arms|space"),
    ("transport", r"transport|shipping|airline|railway|logistic|freight|port"),
    ("commerce", r"retail|wholesale|e-commerce|store|supermarket|trade"),
    ("alimentation", r"food|beverage|brew|tobacco|agricult|dairy|drink|wine|meat|fish"),
    ("consommation", r"textile|apparel|clothing|fashion|cosmetic|luxury|jewel|footwear|consumer"),
    ("tourisme", r"hotel|restaurant|touris|travel|hospitality|leisure"),
    ("construction", r"construction|building|civil engineering|infrastructure"),
    ("industrie", r"manufactur|machine|engineering|industr|equipment|robot"),
    ("services", r"consult|service|staffing|outsourc|marketing|waste"),
]

SECTEUR_DU_QID = {}
for _s, _liste in SECTEURS.items():
    for _q in _liste.split():
        SECTEUR_DU_QID[_q] = _s


# --- Étape 1 : les entreprises et leurs bourses ---------------------------

def cotations():
    """Toutes les cotations EN COURS : une entreprise qui a quitté la bourse
    (une date de fin sur sa cotation) ou qui n'existe plus (une date de
    dissolution) n'est pas une entreprise cotée."""
    lignes = sparql("""
        SELECT ?e ?x ?symbole WHERE {
          ?e p:P414 ?s . ?s ps:P414 ?x .
          FILTER NOT EXISTS { ?s pq:P582 ?fin }
          FILTER NOT EXISTS { ?e wdt:P576 ?dissolution }
          OPTIONAL { ?s pq:P249 ?symbole }
        }""", "cotations.json")
    resultat = {}
    for l in lignes:
        e, x = qid(val(l, "e")), qid(val(l, "x"))
        if not e or not x:
            continue
        cotes = resultat.setdefault(e, {})
        symboles = cotes.setdefault(x, [])
        s = val(l, "symbole")
        if s and s not in symboles:
            symboles.append(s)
    return resultat


# --- Étape 2 : le siège ---------------------------------------------------

def sieges():
    """Pour chaque entreprise, ses sièges possibles, avec ce qu'on en sait :
    la ville (ou l'immeuble), les coordonnées précises et l'adresse quand
    elles sont notées sur le siège lui-même."""
    lignes = sparql("""
        SELECT ?e ?h ?rang ?cq ?adr ?ch ?fin WHERE {
          ?e wdt:P414 ?x .
          ?e p:P159 ?s . ?s ps:P159 ?h ; wikibase:rank ?rang .
          OPTIONAL { ?s pq:P625 ?cq }
          OPTIONAL { ?s pq:P6375 ?adr }
          OPTIONAL { ?s pq:P582 ?fin }
          OPTIONAL { ?h wdt:P625 ?ch }
        }""", "sieges.json")
    resultat = {}
    for l in lignes:
        e, h = qid(val(l, "e")), qid(val(l, "h"))
        if not e or not h:
            continue
        resultat.setdefault(e, []).append({
            "lieu": h,
            "prefere": val(l, "rang", "").endswith("PreferredRank"),
            "ancien": "fin" in l or val(l, "rang", "").endswith("DeprecatedRank"),
            "precis": point(val(l, "cq")),
            "adresse": val(l, "adr"),
            "centre": point(val(l, "ch")),
        })
    return resultat


def immeubles():
    """Les sièges qui sont des IMMEUBLES et non des villes (« Tour Total »,
    « Apple Park »). Leurs coordonnées sont celles du bâtiment : bleu."""
    # Demander tout d'un coup (« quels sièges sont une sorte de bâtiment ? »)
    # dépasse la minute que Wikidata accorde à une question. On procède en
    # deux temps : d'abord la NATURE de chaque siège (« ville », « gratte-
    # ciel », « commune du Japon »…), puis, parmi ces quelques milliers de
    # natures, lesquelles sont des bâtiments.
    lignes = sparql("""
        SELECT DISTINCT ?h ?t WHERE {
          ?e wdt:P414 ?x ; wdt:P159 ?h .
          ?h wdt:P31 ?t .
        }""", "natures_sieges.json")
    natures = {}
    for l in lignes:
        h, t = qid(val(l, "h")), qid(val(l, "t"))
        if h and t:
            natures.setdefault(h, set()).add(t)

    toutes = sorted(set().union(*natures.values())) if natures else []
    batiments = set()
    for n in range(0, len(toutes), 200):
        paquet = toutes[n:n + 200]
        lignes = sparql("""
            SELECT ?t WHERE {
              VALUES ?t { %s }
              ?t wdt:P279* wd:Q811979 .
            }""" % " ".join("wd:" + q for q in paquet), "batiments_%d.json" % n)
        batiments |= {qid(val(l, "t")) for l in lignes}

    # Un lieu qui est À LA FOIS une ville et un bâtiment (cela arrive : une
    # cité-État est parfois rangée parmi les « structures ») reste une ville.
    villes = {"Q515", "Q1549591", "Q486972", "Q1093829", "Q5119", "Q200250",
              "Q174844", "Q15284", "Q3957", "Q532"}
    return {h for h, ts in natures.items() if ts & batiments and not ts & villes}


def coordonnees_propres():
    """Certaines entreprises portent elles-mêmes des coordonnées : celles de
    leur siège. Et parfois une adresse."""
    lignes = sparql("""
        SELECT ?e ?c ?adr WHERE {
          ?e wdt:P414 ?x .
          { ?e wdt:P625 ?c } UNION { ?e wdt:P6375 ?adr }
        }""", "coordonnees.json")
    coords, adresses = {}, {}
    for l in lignes:
        e = qid(val(l, "e"))
        if point(val(l, "c")):
            coords.setdefault(e, point(val(l, "c")))
        if val(l, "adr"):
            adresses.setdefault(e, val(l, "adr"))
    return coords, adresses


def choisir_siege(candidats, immeubles_connus):
    """Parmi les sièges notés, le bon : un siège actuel plutôt qu'un ancien,
    celui que Wikidata marque « préféré », et à égalité celui qui est le
    mieux placé."""
    def note(c):
        return (not c["ancien"], c["prefere"],
                bool(c["precis"]) or c["lieu"] in immeubles_connus,
                bool(c["centre"]))
    candidats = [c for c in candidats if c["centre"] or c["precis"]]
    return max(candidats, key=note) if candidats else None


# --- Étape 3 : les noms ---------------------------------------------------

# Chaque nom est gardé DEUX fois, pour les deux langues du site :
#   pour la page française ... le nom français s'il existe, sinon l'anglais,
#                              sinon le nom « multilingue » de Wikidata, sinon
#                              la première langue trouvée ;
#   pour la page anglaise .... le même ordre, mais l'anglais d'abord.
# Le nom anglais n'est écrit dans le fichier (clef « ne », « ve ») que s'il
# diffère du français : « Apple » n'a pas besoin d'être écrit deux fois.
ORDRE_DES_LANGUES = ["fr", "en", "mul", "de", "es", "it", "pt", "nl", "sv",
                     "pl", "ru", "ja", "zh", "ko", "tr", "ar", "id", "he"]


def noms(requete, nom_cache):
    """Renvoie deux tableaux : les noms pour la page française, et ceux pour
    la page anglaise."""
    lignes = sparql(requete, nom_cache)
    ordre_en = ["en"] + [lg for lg in ORDRE_DES_LANGUES if lg != "en"]
    resultats = []
    for ordre in (ORDRE_DES_LANGUES, ordre_en):
        meilleurs = {}
        for l in lignes:
            q = qid(val(l, "e"))
            lg = val(l, "lg")
            if not q or lg not in ordre:
                continue
            rang = ordre.index(lg)
            if q not in meilleurs or rang < meilleurs[q][0]:
                meilleurs[q] = (rang, val(l, "l"))
        resultats.append({q: v[1] for q, v in meilleurs.items()})
    return resultats


LANGUES_SPARQL = ", ".join('"%s"' % lg for lg in ORDRE_DES_LANGUES)


def noms_des_entreprises():
    return noms("""
        SELECT ?e ?l (LANG(?l) AS ?lg) WHERE {
          ?e wdt:P414 ?x ; rdfs:label ?l .
          FILTER(LANG(?l) IN (%s))
        }""" % LANGUES_SPARQL, "noms_entreprises.json")


def noms_des_lieux():
    return noms("""
        SELECT DISTINCT ?e ?l (LANG(?l) AS ?lg) WHERE {
          ?x wdt:P414 ?b ; wdt:P159 ?e .
          ?e rdfs:label ?l .
          FILTER(LANG(?l) IN (%s))
        }""" % LANGUES_SPARQL, "noms_lieux.json")


def noms_des_bourses(qids):
    valeurs = " ".join("wd:" + q for q in qids)
    return noms("""
        SELECT ?e ?l (LANG(?l) AS ?lg) WHERE {
          VALUES ?e { %s }
          ?e rdfs:label ?l .
          FILTER(LANG(?l) IN (%s))
        }""" % (valeurs, LANGUES_SPARQL), "noms_bourses.json")


# --- Étape 4 : logo, site, notoriété --------------------------------------

def logos_et_sites():
    lignes = sparql("""
        SELECT ?e ?logo ?site ?rang WHERE {
          ?e wdt:P414 ?x .
          { ?e wdt:P154 ?logo }
          UNION
          { ?e p:P856 ?s . ?s ps:P856 ?site ; wikibase:rank ?rang .
            FILTER(?rang != wikibase:DeprecatedRank) }
        }""", "logos_sites_2.json")
    logos, candidats = {}, {}
    for l in lignes:
        e = qid(val(l, "e"))
        if val(l, "logo"):
            logos.setdefault(e, val(l, "logo"))
        if val(l, "site"):
            candidats.setdefault(e, []).append(
                (val(l, "rang", "").endswith("PreferredRank"), val(l, "site")))
    # Une entreprise a souvent plusieurs sites (un par pays). On prend celui
    # que Wikidata marque « préféré », et sinon le plus court : c'est presque
    # toujours le site mondial (apple.com plutôt que apple.com.cn).
    sites = {e: sorted(c, key=lambda c: (not c[0], len(c[1]), c[1]))[0][1]
             for e, c in candidats.items()}
    return logos, sites


def notoriete():
    """Le nombre d'articles Wikipédia consacrés à l'entreprise, toutes langues
    confondues. C'est notre mesure de « taille » : elle existe pour toutes,
    alors que le chiffre d'affaires manque à la plupart. Sur la carte, c'est
    elle qui décide quel logo passe devant quand deux se chevauchent."""
    lignes = sparql("""
        SELECT ?e ?n WHERE { ?e wdt:P414 ?x ; wikibase:sitelinks ?n . }""",
        "notoriete.json")
    return {qid(val(l, "e")): int(val(l, "n", 0)) for l in lignes}


# --- Étape 5 : les secteurs -----------------------------------------------

def secteurs_bruts():
    lignes = sparql("""
        SELECT ?e ?i ?en WHERE {
          ?e wdt:P414 ?x ; wdt:P452 ?i .
          OPTIONAL { ?i rdfs:label ?en FILTER(LANG(?en) = "en") }
        }""", "secteurs.json")
    par_entreprise, noms_anglais = {}, {}
    for l in lignes:
        e, i = qid(val(l, "e")), qid(val(l, "i"))
        if not e or not i or i in IGNORES:
            continue
        par_entreprise.setdefault(e, set()).add(i)
        if val(l, "en"):
            noms_anglais[i] = val(l, "en")
    return par_entreprise, noms_anglais


def ranger_les_secteurs(tous, noms_anglais):
    """Chaque secteur de Wikidata -> une de nos grandes familles (étapes 1 à
    3 décrites en haut de la section « Les secteurs »)."""
    rangement = {i: SECTEUR_DU_QID[i] for i in tous if i in SECTEUR_DU_QID}

    # Étape 2 : « est une sorte de ». On demande à Wikidata, par paquets, à
    # quelle famille connue appartient chaque secteur pas encore rangé.
    restants = sorted(i for i in tous if i not in rangement)
    racines = " ".join("wd:" + q for q in SECTEUR_DU_QID)
    for n in range(0, len(restants), 60):
        paquet = restants[n:n + 60]
        lignes = sparql("""
            SELECT ?i ?a WHERE {
              VALUES ?i { %s }
              VALUES ?a { %s }
              ?i wdt:P279+ ?a .
            }""" % (" ".join("wd:" + q for q in paquet), racines),
            "ancetres_%d.json" % n)
        for l in lignes:
            i, a = qid(val(l, "i")), qid(val(l, "a"))
            rangement.setdefault(i, SECTEUR_DU_QID[a])

    # Étape 3 : un mot du nom anglais.
    for i in tous:
        if i in rangement:
            continue
        nom = noms_anglais.get(i, "").lower()
        for s, motif in MOTS_DES_SECTEURS:
            if re.search(motif, nom):
                rangement[i] = s
                break
    return rangement


# --- Étape 6 : les chiffres -----------------------------------------------

def dernier_chiffre(propriete, nom_cache):
    """La valeur la plus RÉCENTE d'un chiffre (chiffre d'affaires, effectifs,
    capitalisation), avec son unité et son année."""
    lignes = sparql("""
        SELECT ?e ?v ?unite ?date WHERE {
          ?e wdt:P414 ?x .
          ?e p:%s ?s . ?s psv:%s ?n ; wikibase:rank ?rang .
          FILTER(?rang != wikibase:DeprecatedRank)
          ?n wikibase:quantityAmount ?v .
          OPTIONAL { ?n wikibase:quantityUnit ?unite }
          OPTIONAL { ?s pq:P585 ?date }
        }""" % (propriete, propriete), nom_cache)
    meilleurs = {}
    for l in lignes:
        e = qid(val(l, "e"))
        try:
            v = float(val(l, "v"))
        except (TypeError, ValueError):
            continue
        if not e or v <= 0:
            continue
        date = val(l, "date", "")
        annee = int(date[:4]) if re.match(r"^\d{4}", date or "") else 0
        if e not in meilleurs or annee > meilleurs[e][2]:
            meilleurs[e] = (v, qid(val(l, "unite")), annee)
    return meilleurs


def codes_des_monnaies(qids):
    """Q4916 -> « EUR ». Le code ISO à trois lettres, lisible partout."""
    if not qids:
        return {}
    valeurs = " ".join("wd:" + q for q in qids)
    lignes = sparql("""
        SELECT ?u ?code WHERE { VALUES ?u { %s } ?u wdt:P498 ?code . }""" % valeurs,
        "monnaies.json")
    return {qid(val(l, "u")): val(l, "code") for l in lignes}


# --- Étape 7 : les logos --------------------------------------------------

def nom_du_logo(q):
    return os.path.join(LOGOS, q + ".png")


def un_logo(travail):
    """Télécharge un logo, déjà réduit par Wikimedia à 120 pixels de large.
    Wikimedia fabrique la version réduite en PNG même quand l'original est un
    dessin SVG : on obtient toujours une image que le navigateur sait lire."""
    q, adresse = travail
    chemin = nom_du_logo(q)
    if os.path.exists(chemin):
        return "deja"
    nom_fichier = urllib.parse.unquote(adresse.rsplit("/", 1)[1])
    url = ("https://commons.wikimedia.org/wiki/Special:FilePath/"
           + urllib.parse.quote(nom_fichier) + "?width=%d" % LARGEUR_LOGO)
    try:
        corps = telecharger(url, essais=3, binaire=True)
    except Exception:
        return "echec"
    # On ne garde que ce qui est vraiment une image PNG, JPEG ou GIF, et pas
    # trop lourde : le reste (une page d'erreur, un PDF…) est écarté.
    if not (corps[:8] == b"\x89PNG\r\n\x1a\n" or corps[:3] == b"\xff\xd8\xff"
            or corps[:4] == b"GIF8") or len(corps) > 150000:
        return "echec"
    with open(chemin, "wb") as f:
        f.write(corps)
    time.sleep(0.2)
    return "neuf"


def telecharger_les_logos(logos):
    os.makedirs(LOGOS, exist_ok=True)
    travaux = sorted(logos.items())
    bilan = {"deja": 0, "neuf": 0, "echec": 0}
    # Quatre téléchargements à la fois : assez pour ne pas y passer la nuit,
    # assez peu pour rester poli avec les serveurs de Wikimedia.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for n, r in enumerate(pool.map(un_logo, travaux), 1):
            bilan[r] += 1
            if n % 250 == 0:
                dit(f"    {n} / {len(travaux)} logos…")
    dit(f"  {bilan['neuf']} logos téléchargés, {bilan['deja']} déjà là, "
        f"{bilan['echec']} introuvables")


# --- Étape 8 : tout assembler ---------------------------------------------

# En dessous de cette distance, des coordonnées « précises » ne sont en fait
# que celles de la ville recopiées : on les compte comme jaunes.
MEME_POINT_KM = 0.3


def arrondi(v):
    """Cinq décimales : un mètre près, bien assez pour un immeuble."""
    return round(v, 5)


def chiffre_ou_rien(chiffres, e, monnaies=None):
    if e not in chiffres:
        return None
    v, unite, annee = chiffres[e]
    v = round(v) if v >= 100 else round(v, 2)
    if monnaies is None:
        return [v, annee or None]
    code = monnaies.get(unite)
    if not code:
        # Un montant sans monnaie connue ne veut rien dire : on l'écarte.
        return None
    return [v, code, annee or None]


def main():
    dit("→ Wikidata : les entreprises cotées et leurs bourses")
    cotes = cotations()
    dit(f"  {len(cotes)} entreprises cotées")

    dit("→ Wikidata : leurs sièges")
    candidats = sieges()
    batis = immeubles()
    coords_propres, adresses_propres = coordonnees_propres()
    dit(f"  {len(candidats)} avec un siège · {len(batis)} sièges qui sont des immeubles")

    dit("→ Wikidata : les noms")
    noms_e, noms_e_en = noms_des_entreprises()
    noms_l, noms_l_en = noms_des_lieux()

    dit("→ Wikidata : logos, sites, notoriété")
    logos, sites = logos_et_sites()
    renom = notoriete()

    dit("→ Wikidata : les secteurs")
    bruts, noms_anglais = secteurs_bruts()
    tous = set().union(*bruts.values()) if bruts else set()
    rangement = ranger_les_secteurs(tous, noms_anglais)
    dit(f"  {len(tous)} secteurs Wikidata, {len(rangement)} rangés dans nos familles")

    dit("→ Wikidata : chiffre d'affaires, effectifs, capitalisation")
    ca = dernier_chiffre("P2139", "chiffre_affaires.json")
    effectifs = dernier_chiffre("P1128", "effectifs.json")
    capi = dernier_chiffre("P2226", "capitalisation.json")
    monnaies = codes_des_monnaies(sorted({c[1] for c in list(ca.values()) + list(capi.values())
                                          if c[1]}))

    dit("→ Assemblage")
    pays = charger_pays()
    entreprises = []
    for e, bourses in cotes.items():
        siege = choisir_siege(candidats.get(e, []), batis)
        propre = coords_propres.get(e)
        if not siege and not propre:
            continue  # aucun moyen de la placer

        # Où poser le point, et en quelle couleur.
        centre = siege["centre"] if siege else None
        if siege and siege["precis"]:
            position, exact = siege["precis"], True
        elif propre:
            position, exact = propre, True
        elif siege["lieu"] in batis:
            position, exact = centre, True
        else:
            position, exact = centre, False
        # Des coordonnées « précises » qui tombent pile sur le centre de la
        # ville ne sont pas précises.
        if exact and centre and siege["lieu"] not in batis \
                and distance_km(position, centre) < MEME_POINT_KM:
            exact = False

        familles = sorted({rangement[i] for i in bruts.get(e, ()) if i in rangement})
        ligne = {
            "q": e,
            "n": noms_e.get(e, e),
            "x": arrondi(position[0]),
            "y": arrondi(position[1]),
            "p": 1 if exact else 0,
            "b": sorted(bourses),
            "s": familles or [AUTRE],
            "v": noms_l.get(siege["lieu"]) if siege else None,
            "i": pays_du_point(position[0], position[1], pays),
            "r": renom.get(e, 0),
        }
        # Les noms anglais, seulement quand ils diffèrent du français.
        if noms_e_en.get(e) and noms_e_en[e] != ligne["n"]:
            ligne["ne"] = noms_e_en[e]
        ville_en = noms_l_en.get(siege["lieu"]) if siege else None
        if ville_en and ville_en != ligne["v"]:
            ligne["ve"] = ville_en
        symboles = sorted({s for liste in bourses.values() for s in liste})
        if symboles:
            ligne["t"] = symboles[:4]
        adresse = (siege["adresse"] if siege else None) or adresses_propres.get(e)
        if adresse:
            ligne["a"] = adresse
        if e in logos:
            ligne["l"] = 1
        if e in sites:
            ligne["w"] = sites[e]
        for clef, valeur in (("ca", chiffre_ou_rien(ca, e, monnaies)),
                             ("ef", chiffre_ou_rien(effectifs, e)),
                             ("cb", chiffre_ou_rien(capi, e, monnaies))):
            if valeur:
                ligne[clef] = valeur
        entreprises.append(ligne)

    # Les plus connues d'abord : c'est l'ordre dans lequel la carte les pose,
    # et celui de la liste quand on cherche un nom.
    entreprises.sort(key=lambda x: (-x["r"], x["n"]))

    # Les bourses, rangées de la plus fournie à la moins fournie. Chaque
    # entreprise ne garde que le NUMÉRO de sa bourse dans cette liste : c'est
    # dix fois plus court que de répéter « New York Stock Exchange » 1 900 fois.
    compte = {}
    for x in entreprises:
        for b in x["b"]:
            compte[b] = compte.get(b, 0) + 1
    ordre = sorted(compte, key=lambda b: -compte[b])
    noms_b, noms_b_en = noms_des_bourses(ordre)
    numero = {b: n for n, b in enumerate(ordre)}
    for x in entreprises:
        x["b"] = sorted(numero[b] for b in x["b"])
    bourses = []
    for b in ordre:
        bourse = {"q": b, "n": noms_b.get(b, b), "c": compte[b]}
        if noms_b_en.get(b) and noms_b_en[b] != bourse["n"]:
            bourse["ne"] = noms_b_en[b]
        bourses.append(bourse)

    familles = {}
    for x in entreprises:
        for s in x["s"]:
            familles[s] = familles.get(s, 0) + 1
    secteurs = [{"id": s, "c": familles[s]}
                for s in sorted(familles, key=lambda s: (s == AUTRE, -familles[s]))]

    taille = ecrire(os.path.join(SORTIE, "entreprises.json"), {
        "maj": time.strftime("%Y-%m-%d"),
        "secteurs": secteurs,
        "bourses": bourses,
        "entreprises": entreprises,
    })
    exactes = sum(x["p"] for x in entreprises)
    dit(f"  {len(entreprises)} entreprises placées : {exactes} à l'adresse exacte (bleu), "
        f"{len(entreprises) - exactes} au centre-ville (jaune)")
    dit(f"  {len(bourses)} bourses · {len(secteurs)} secteurs · "
        f"data/bourse/entreprises.json : {taille // 1024} Ko")

    if "--sans-logos" not in sys.argv:
        dit("→ Wikimedia Commons : les logos")
        telecharger_les_logos({x["q"]: logos[x["q"]] for x in entreprises if x["q"] in logos})
        # Une entreprise dont le logo n'a pas pu être téléchargé perd sa marque
        # « a un logo » : la carte affichera ses initiales.
        for x in entreprises:
            if x.get("l") and not os.path.exists(nom_du_logo(x["q"])):
                del x["l"]
        ecrire(os.path.join(SORTIE, "entreprises.json"), {
            "maj": time.strftime("%Y-%m-%d"),
            "secteurs": secteurs,
            "bourses": bourses,
            "entreprises": entreprises,
        })
    dit("✓ Terminé.")


if __name__ == "__main__":
    main()
