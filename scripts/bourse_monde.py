#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bourse_monde.py — la liste de TOUTES les entreprises cotées du monde.

Ce que fait ce module, en une phrase :
il demande à OpenFIGI (le service gratuit de Bloomberg) la liste de toutes les
actions cotées, une par entreprise et par pays, et la range dans
scripts/.cache-bourse/monde/.

Il complète build_bourse.py, qui part de Wikidata : Wikidata ne connaît qu'une
partie des entreprises cotées (Bonduelle, par exemple, n'y a pas sa bourse
renseignée), alors qu'OpenFIGI les connaît toutes.

  ── Ce qu'il faut savoir sur OpenFIGI ──────────────────────────────────────

  · Une même action y figure PLUSIEURS fois : une fois par place où elle
    s'échange (Tokyo « JT », Osaka…) et une fois pour le pays entier (« JP »).
    Ce dernier enregistrement est dit « composite » : c'est le seul qu'on
    garde. On le reconnaît à ce que son identifiant (figi) est égal à son
    identifiant composite (compositeFIGI).

  · Les entreprises disparues en sont retirées (Enron, Lehman Brothers et
    Twitter n'y sont plus) — c'est ce qui permet la mise à jour quotidienne.

  · Aux États-Unis, il compte aussi les titres échangés « de gré à gré »
    (OTC), hors de toute bourse. On ne les garde pas : voir actions_us().

  · La clé : scripts/.cle-openfigi sur le Mac, le secret OPENFIGI_KEY sur
    GitHub. Avec elle, 20 questions par minute ; sans elle, 5.

À lancer seul, pour tester :  python3 scripts/bourse_monde.py
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ICI = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ICI, ".cache-bourse", "monde")
OPENFIGI = "https://api.openfigi.com/v3"
EN_TETES = {"User-Agent": "StatsMaps/1.0 (+https://statsmaps.com)",
            "Content-Type": "application/json"}

# Les sortes d'actions qu'on garde. Les « Depositary Receipt » (les ADR) sont
# écartés : ce sont des copies, cotées à New York, d'actions d'entreprises
# étrangères déjà comptées dans leur propre pays.
SORTES = ["Common Stock", "REIT"]


def dit(*a):
    print(*a, flush=True)


def cle():
    if os.environ.get("OPENFIGI_KEY"):
        return os.environ["OPENFIGI_KEY"].strip()
    chemin = os.path.join(ICI, ".cle-openfigi")
    if os.path.exists(chemin):
        return open(chemin, encoding="utf-8").read().strip()
    return None


# --- Parler à OpenFIGI, sans dépasser la limite ---------------------------

_derniers_appels = []


def attendre_mon_tour():
    """Pas plus de N questions par minute (20 avec la clé, 5 sans) : on note
    l'heure de chaque question, et on attend si la minute est déjà pleine."""
    limite = 19 if cle() else 4
    while True:
        maintenant = time.time()
        while _derniers_appels and maintenant - _derniers_appels[0] > 61:
            _derniers_appels.pop(0)
        if len(_derniers_appels) < limite:
            _derniers_appels.append(maintenant)
            return
        time.sleep(61 - (maintenant - _derniers_appels[0]) + 0.1)


def demander(chemin, corps, essais=6):
    entetes = dict(EN_TETES)
    if cle():
        entetes["X-OPENFIGI-APIKEY"] = cle()
    for n in range(essais):
        attendre_mon_tour()
        try:
            req = urllib.request.Request(OPENFIGI + chemin, data=json.dumps(corps).encode(),
                                         headers=entetes, method="POST")
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:            # trop de questions : on patiente
                time.sleep(60)
            elif e.code >= 500 and n < essais - 1:
                time.sleep(20 * (n + 1))
            else:
                raise
        except Exception:
            if n == essais - 1:
                raise
            time.sleep(20 * (n + 1))
    raise RuntimeError("OpenFIGI ne répond pas")


def lire(nom, secours=False):
    """La mémoire. Pour le robot (--monde), ce qui a plus de 20 heures est
    redemandé — sauf en secours, quand le serveur est en panne."""
    chemin = os.path.join(CACHE, nom)
    if not os.path.exists(chemin) or ("--neuf" in sys.argv and not secours):
        return None
    if ("--monde" in sys.argv and not secours
            and time.time() - os.path.getmtime(chemin) > 20 * 3600):
        return None
    return json.load(open(chemin, encoding="utf-8"))


def garder(nom, valeur):
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(CACHE, nom), "w", encoding="utf-8") as f:
        json.dump(valeur, f, ensure_ascii=False)


# --- Étape 1 : la bourse principale de chaque pays ------------------------
#
# Chaque code est celui qu'emploie Bloomberg pour la place principale d'un
# pays (Londres « LN », Paris « FP », Tokyo « JP »…). Pour les États-Unis, c'est
# le code « US », qui regroupe toutes les bourses américaines.
#
# Certaines places listent AUSSI des entreprises étrangères (l'Allemagne en
# compte 14 000, le Mexique et le Pérou cotent Amazon). Ces doublons sont
# fondus à l'étape 3, grâce au numéro de « classe » d'une action, le même
# partout où elle s'échange.
#
# On n'y met PAS certains codes trompeurs d'OpenFIGI : « X2 » et « EO » sont
# des plateformes qui recotent en euros des actions du monde entier.

# L'ORDRE compte : une action cotée à plusieurs endroits prend pour place
# principale la première de la liste où elle apparaît. Les places qui recotent
# beaucoup d'entreprises étrangères (Allemagne, Suisse, Vienne, Luxembourg,
# Mexique, Pérou) sont donc mises À LA FIN : sinon Samsung ou Volvo auraient
# Francfort pour bourse principale.
PLACES = """
US LN FP NA BB PL ID IM SM SS DC FH NO IR ET LR LH PW CP HB RO CR SV BU GA CY
TI RM JP CH HK TT KS IN SP MK TB IJ PM VN PA SL BD AU NZ CN BZ CI AR CB SJ EY
NL KN MC TU GN BG MS ZH IT AB UH DH QD KK BI OM JR UK
GR SW AV LX MM PE
""".split()
# « UK » n'est PAS le Royaume-Uni (c'est « LN », Londres) : c'est l'UKRAINE
# (bourse de Kyiv, PFTS), ajoutée le 22 novembre 2026 : elle manquait, et
# avec elle plus de deux cents entreprises ukrainiennes.


# --- Étape 2 : toutes les actions, pays par pays ---------------------------

def actions_du_pays(code):
    """Toutes les actions d'un pays (code composite), page par page — cent par
    page. Gardées dans le cache, une fois par pays : si le programme est
    interrompu, il reprend au pays suivant."""
    nom_cache = "actions_%s.json" % code
    connu = lire(nom_cache)
    if connu is not None:
        return connu
    try:
        actions = _actions_du_pays(code)
    except Exception as e:
        # OpenFIGI en panne pour ce pays : la liste de la veille, s'il y en a une.
        hier = lire(nom_cache, secours=True)
        if hier is None:
            raise
        dit(f"    … OpenFIGI ne répond pas pour {code} ({type(e).__name__}) : liste précédente gardée")
        return hier
    garder(nom_cache, actions)
    return actions


def _actions_du_pays(code):
    actions = []
    for sorte in SORTES:
        suite = None
        while True:
            corps = {"exchCode": code, "securityType2": sorte, "marketSecDes": "Equity"}
            if suite:
                corps["start"] = suite
            d = demander("/filter", corps)
            for x in d.get("data", []):
                if x.get("figi"):
                    actions.append({
                        "figi": x["figi"], "classe": x.get("shareClassFIGI"),
                        "nom": x.get("name") or "", "symbole": x.get("ticker") or "",
                        "place": code, "sorte": sorte,
                    })
            suite = d.get("next")
            if not suite:
                break
    return actions


# --- Étape 3 : aux États-Unis, seulement les vraies bourses ---------------

NASDAQ = "https://www.nasdaqtrader.com/dynamic/SymDir/"


def symboles_us():
    """Les symboles des actions cotées sur une vraie bourse américaine (New
    York, Nasdaq, NYSE American, Cboe…), d'après la liste que le Nasdaq publie
    chaque jour. Les fonds indiciels (ETF) et les titres d'essai sont exclus.
    Renvoie, pour chaque symbole, la lettre de sa bourse : Q pour le Nasdaq,
    N pour New York, A pour NYSE American, P pour NYSE Arca, Z pour Cboe."""
    connu = lire("symboles_us.json")
    if connu is not None:
        return connu
    try:
        symboles = _symboles_us()
    except Exception as e:
        hier = lire("symboles_us.json", secours=True)
        if hier is None:
            raise
        dit(f"    … liste du Nasdaq injoignable ({type(e).__name__}) : liste précédente gardée")
        return hier
    garder("symboles_us.json", symboles)
    return symboles


def _symboles_us():
    symboles = {}
    for fichier, colonne in (("nasdaqlisted.txt", "Symbol"), ("otherlisted.txt", "ACT Symbol")):
        texte = None
        for n in range(5):
            try:
                req = urllib.request.Request(NASDAQ + fichier, headers={"User-Agent": EN_TETES["User-Agent"]})
                texte = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", "replace")
                break
            except Exception:
                if n == 4:
                    raise
                time.sleep(20 * (n + 1))
        for ligne in csv.DictReader(io.StringIO(texte), delimiter="|"):
            if not ligne.get("Test Issue") or ligne["Test Issue"] == "Y" or ligne.get("ETF") == "Y":
                continue
            # « BRK.B » au Nasdaq s'écrit « BRK/B » chez OpenFIGI.
            symboles[ligne[colonne].replace(".", "/").upper()] = ligne.get("Exchange") or "Q"
    return symboles


def sous_place(action, us):
    """La bourse précise d'une action, quand un pays en a plusieurs :
    New York ou le Nasdaq pour les États-Unis (d'après la liste du Nasdaq),
    Shanghai, Shenzhen ou Pékin pour la Chine (d'après le numéro de l'action :
    600… à Shanghai, 000… et 300… à Shenzhen, 8… et 4… à Pékin)."""
    p = action["places"][0]
    if p == "US":
        return "US/" + us.get(action["symbole"].upper(), "N")
    if p == "CH":
        s = action["symbole"]
        if s[:1] in ("6", "9"):
            return "CH/SH"
        if s[:1] in ("0", "2", "3"):
            return "CH/SZ"
        return "CH/BJ"
    return p


def toutes_les_actions():
    """Toutes les actions des bourses principales, une seule fois chacune.

    Une action cotée dans plusieurs pays (Amazon à New York, à Mexico et à
    Lima) garde le même numéro de « classe » partout : on la garde une fois,
    avec la liste de ses places. La première de la liste PLACES où elle
    apparaît est retenue comme sa place principale."""
    us = symboles_us()
    dit(f"  {len(us)} titres cotés sur une vraie bourse américaine")
    par_classe = {}
    for n, code in enumerate(PLACES, 1):
        actions = actions_du_pays(code)
        if code == "US":
            actions = [a for a in actions if a["symbole"].upper() in us]
        for a in actions:
            clef = a.get("classe") or a["figi"]
            if clef in par_classe:
                if code not in par_classe[clef]["places"]:
                    par_classe[clef]["places"].append(code)
            else:
                a = dict(a, places=[code])
                par_classe[clef] = a
        if n % 5 == 0:
            dit(f"    {n} / {len(PLACES)} places · {len(par_classe)} actions différentes")
    return list(par_classe.values())


# --- Étape 4 : retrouver chaque entreprise dans GLEIF ----------------------
#
# GLEIF est le registre mondial des « LEI », le numéro d'identité que doit
# avoir toute entreprise dont les titres s'échangent sur un marché. Il donne
# l'adresse exacte du siège, et il est mis à jour chaque jour.
#
# OpenFIGI ne donne pas ce numéro : il faut retrouver l'entreprise par son NOM.
# Or les deux ne l'écrivent pas pareil :
#     OpenFIGI (Bloomberg) ... « SOUTH CHINA FIN HOLDINGS LTD »
#     GLEIF .................. « South China Financial Holdings Limited »
# On ramène donc les deux à une même « clef » : majuscules, sans accents ni
# ponctuation, chaque mot sous une forme unique (FINANCIAL et FIN -> FIN),
# sans les formes juridiques (LIMITED, SA, INC…), qui ne distinguent rien.

import csv
import io
import unicodedata
import zipfile

GLEIF_ZIP = os.path.join(ICI, ".cache-bourse", "gleif", "lei2.csv.zip")


def telecharger_gleif():
    """Le registre complet de GLEIF (500 Mo) et sa liste de titres (35 Mo),
    retéléchargés quand ils ont plus d'un jour : GLEIF les republie chaque
    matin."""
    def vieux(chemin):
        return not os.path.exists(chemin) or time.time() - os.path.getmtime(chemin) > 20 * 3600
    os.makedirs(os.path.dirname(GLEIF_ZIP), exist_ok=True)
    taches = [
        (GLEIF_ZIP, "https://goldencopy.gleif.org/api/v2/golden-copies/publishes/lei2/latest",
         lambda d: d["data"]["full_file"]["csv"]["url"]),
        (os.path.join(os.path.dirname(GLEIF_ZIP), "isin-lei.zip"),
         "https://mapping.gleif.org/api/v2/isin-lei/latest",
         lambda d: d["data"]["attributes"]["downloadLink"]),
    ]
    for chemin, api, adresse in taches:
        if not vieux(chemin):
            continue
        try:
            _telecharger_un_fichier_gleif(chemin, api, adresse)
        except Exception as e:
            if not os.path.exists(chemin):
                raise
            dit(f"    … GLEIF injoignable ({type(e).__name__}) : fichier précédent gardé")


def _telecharger_un_fichier_gleif(chemin, api, adresse):
    for n in range(4):
        try:
            return _telecharger_un_fichier_gleif_une_fois(chemin, api, adresse)
        except Exception:
            if n == 3:
                raise
            time.sleep(60 * (n + 1))


def _telecharger_un_fichier_gleif_une_fois(chemin, api, adresse):
    req = urllib.request.Request(api, headers={"User-Agent": EN_TETES["User-Agent"]})
    url = adresse(json.loads(urllib.request.urlopen(req, timeout=120).read().decode()))
    dit(f"  téléchargement de {os.path.basename(chemin)}…")
    req = urllib.request.Request(url, headers={"User-Agent": EN_TETES["User-Agent"]})
    with urllib.request.urlopen(req, timeout=1800) as r, open(chemin + ".tmp", "wb") as f:
        while True:
            bloc = r.read(1 << 20)
            if not bloc:
                break
            f.write(bloc)
    os.replace(chemin + ".tmp", chemin)

# Un mot -> sa forme unique. Les abréviations de Bloomberg à gauche de la
# flèche, ce qu'elles veulent dire à droite, sont ramenées au même mot.
FORMES_UNIQUES = {}
for _forme, _variantes in {
    "INTL": "INTERNATIONAL INTERNATL INTERNAT INTL INT'L",
    "HLDG": "HOLDINGS HOLDING HLDGS HLDG HOLD HLD",
    "GRP": "GROUP GRP GRUPO GROUPE GRUPPE",
    "FIN": "FINANCIAL FINANCE FINANCIERE FINL FIN",
    "TECH": "TECHNOLOGY TECHNOLOGIES TECHNOLOGIE TECHNOLOGIES TECHNOLOGIES TECH TECHS",
    "IND": "INDUSTRIES INDUSTRY INDUSTRIAL INDUSTRIAS INDUSTRIE INDS IND",
    "BK": "BANK BANCO BANQUE BK",
    "MFG": "MANUFACTURING MFG",
    "PHARM": "PHARMACEUTICAL PHARMACEUTICALS PHARMACEUTICA PHARMA PHARM PHARMS",
    "DEV": "DEVELOPMENT DEVELOPMENTS DEV",
    "SVC": "SERVICES SERVICE SVCS SVC SERV",
    "ENT": "ENTERPRISES ENTERPRISE ENT",
    "PROP": "PROPERTIES PROPERTY PPTY PPTYS PROP PROPS",
    "RES": "RESOURCES RESOURCE RES RESRC",
    "AMER": "AMERICA AMERICAN AMER",
    "NATL": "NATIONAL NATL",
    "SYS": "SYSTEMS SYSTEM SYS",
    "COMM": "COMMUNICATIONS COMMUNICATION COMMS COMM",
    "ELEC": "ELECTRIC ELECTRICAL ELECTRONICS ELECTRONIC ELEC",
    "INV": "INVESTMENTS INVESTMENT INVT INVS INV",
    "MGMT": "MANAGEMENT MGMT",
    "INS": "INSURANCE INS",
    "CHEM": "CHEMICALS CHEMICAL CHEM",
    "ENGR": "ENGINEERING ENGR",
    "CONST": "CONSTRUCTION CONSTR CONST",
    "LAB": "LABORATORIES LABORATORY LABS LAB",
    "MED": "MEDICAL MED",
    "SEC": "SECURITIES SECURITY SEC",
    "TRANS": "TRANSPORTATION TRANSPORT TRANS",
    "ASSOC": "ASSOCIATES ASSOCIATED ASSOC",
    "PRODS": "PRODUCTS PRODUCT PRODS PROD",
    "INFO": "INFORMATION INFO",
    "SOLN": "SOLUTIONS SOLUTION SOLN SOLNS",
    "TEL": "TELECOMMUNICATIONS TELECOMMUNICATION TELECOM TEL",
    "MATL": "MATERIALS MATERIAL MATL MATLS",
    "EQUIP": "EQUIPMENT EQUIP",
    "BANCORP": "BANCORPORATION BANCORP",
    "CTR": "CENTER CENTRE CTR",
    "MKT": "MARKETS MARKET MKT MKTS",
    "AND": "AND &",
}.items():
    for _v in _variantes.split():
        FORMES_UNIQUES[_v] = _forme

# Les formes juridiques : elles ne distinguent rien (« Accor SA » = « Accor »).
FORMES_JURIDIQUES = set("""
CORP CORPORATION INC INCORPORATED CO COMPANY LTD LIMITED PLC LLC LP LLP SA SAS
SCA SE SPA AG NV BV AB ASA AS OYJ OY KK GMBH KGAA BHD TBK PT JSC PJSC OJSC PCL
SAB CV DE THE PUBLIC KABUSHIKI KAISHA SAOG SAQ QSC QPSC PSC SAL SRL SAA SACI
ADR REG ORD SHS CL CLASS A B C H N
""".split())


def sans_accents(texte):
    return "".join(c for c in unicodedata.normalize("NFKD", texte)
                   if not unicodedata.combining(c))


def clef_de_nom(nom, tronque=False):
    """« South China Financial Holdings Limited » -> « SOUTH CHINA FIN HLDG ».
    Si le nom vient d'OpenFIGI et fait 28 caractères, il a sans doute été coupé
    par Bloomberg : son dernier mot est peut-être incomplet, on l'enlève."""
    texte = sans_accents(nom).upper().replace("&", " AND ")
    texte = re.sub(r"[^A-Z0-9 ]+", " ", texte)
    mots = texte.split()
    if tronque and len(nom) >= 27 and len(mots) > 1:
        mots = mots[:-1]
    mots = [FORMES_UNIQUES.get(m, m) for m in mots]
    mots = [m for m in mots if m not in FORMES_JURIDIQUES]
    return " ".join(mots)


def debut_de_clef(clef):
    """Les deux premiers mots : de quoi trier vite 3,5 millions de noms."""
    return " ".join(clef.split()[:2])


COLONNES_ADRESSE = ["FirstAddressLine", "AddressNumber", "AdditionalAddressLine.1",
                    "AdditionalAddressLine.2", "City", "Region", "PostalCode", "Country"]


def chercher_dans_gleif(actions):
    """Pour chaque action, les entreprises de GLEIF dont la clef de nom
    correspond. On lit les 3,5 millions de lignes UNE fois, en ne gardant que
    celles dont les deux premiers mots intéressent l'une de nos actions."""
    voulus = {}
    for a in actions:
        c = clef_de_nom(a["nom"], tronque=True)
        if c:
            voulus.setdefault(debut_de_clef(c), []).append(a)
    candidats = {}
    with zipfile.ZipFile(GLEIF_ZIP) as z:
        with z.open(z.namelist()[0]) as brut:
            lecteur = csv.reader(io.TextIOWrapper(brut, encoding="utf-8"))
            entete = next(lecteur)
            col = {nom: i for i, nom in enumerate(entete)}
            noms_cols = [col["Entity.LegalName"]] + [
                i for nom, i in col.items()
                if re.fullmatch(r"Entity\.(Transliterated)?OtherEntityNames\."
                                r"(Transliterated)?OtherEntityName\.\d+", nom)]
            for n, ligne in enumerate(lecteur, 1):
                if n % 500000 == 0:
                    dit(f"    {n} lignes de GLEIF lues · {len(candidats)} entreprises retenues")
                if ligne[col["Entity.EntityStatus"]] != "ACTIVE":
                    continue
                for i in noms_cols:
                    nom = ligne[i]
                    if not nom:
                        continue
                    c = clef_de_nom(nom)
                    if debut_de_clef(c) in voulus:
                        lei = ligne[col["LEI"]]
                        fiche = candidats.setdefault(lei, {
                            "lei": lei,
                            "nom": ligne[col["Entity.LegalName"]],
                            "clefs": [],
                            "pays": ligne[col["Entity.HeadquartersAddress.Country"]]
                                    or ligne[col["Entity.LegalAddress.Country"]],
                            "adresse": {k: ligne[col["Entity.HeadquartersAddress." + k]]
                                        for k in COLONNES_ADRESSE},
                            "categorie": ligne[col["Entity.EntityCategory"]],
                            "statut": ligne[col["Registration.RegistrationStatus"]],
                        })
                        if c not in fiche["clefs"]:
                            fiche["clefs"].append(c)
    return candidats


# Le pays de chaque place (code ISO à deux lettres, celui de GLEIF). Il sert à
# départager deux homonymes : « Alpha Bank » à Athènes est la grecque.
PAYS_DES_PLACES = {
    "US": "US", "LN": "GB", "FP": "FR", "NA": "NL", "BB": "BE", "PL": "PT", "ID": "IE",
    "IM": "IT", "SM": "ES", "SS": "SE", "DC": "DK", "FH": "FI", "NO": "NO", "IR": "IS",
    "ET": "EE", "LR": "LV", "LH": "LT", "PW": "PL", "CP": "CZ", "HB": "HU", "RO": "RO",
    "CR": "HR", "SV": "SI", "BU": "BG", "GA": "GR", "CY": "CY", "TI": "TR", "RM": "RU",
    "JP": "JP", "CH": "CN", "HK": "HK", "TT": "TW", "KS": "KR", "IN": "IN", "SP": "SG",
    "MK": "MY", "TB": "TH", "IJ": "ID", "PM": "PH", "VN": "VN", "PA": "PK", "SL": "LK",
    "BD": "BD", "AU": "AU", "NZ": "NZ", "CN": "CA", "BZ": "BR", "CI": "CL", "AR": "AR",
    "CB": "CO", "SJ": "ZA", "EY": "EG", "NL": "NG", "KN": "KE", "MC": "MA", "TU": "TN",
    "GN": "GH", "BG": "BW", "MS": "MU", "ZH": "ZW", "IT": "IL", "AB": "SA", "UH": "AE",
    "DH": "AE", "QD": "QA", "KK": "KW", "BI": "BH", "OM": "OM", "JR": "JO", "UK": "UA",
    "GR": "DE", "SW": "CH", "AV": "AT", "LX": "LU", "MM": "MX", "PE": "PE",
}


# Les places où se cotent beaucoup d'entreprises ÉTRANGÈRES (une société
# chinoise à Hong Kong ou à New York, israélienne au Nasdaq, minière
# australienne à Toronto…). Ailleurs, une entreprise cotée doit être trouvée
# dans le pays de sa bourse : « OPTIM » à Tokyo n'est pas l'OPTIM espagnole.
PLACES_INTERNATIONALES = {"US", "LN", "HK", "SP", "CN", "AU", "NA", "ID", "GR", "SW",
                          "AV", "LX", "MM", "PE", "IM", "FP", "SS", "NO"}


def nom_complet(nom):
    """Le nom avec ses formes juridiques (« BONDUELLE SCA ») : sert à
    départager les homonymes d'un même pays (la maison mère « Bonduelle SCA »
    et sa filiale « Bonduelle SAS »)."""
    texte = sans_accents(nom).upper().replace("&", " AND ")
    texte = re.sub(r"[^A-Z0-9 ]+", " ", texte)
    return " ".join(FORMES_UNIQUES.get(m, m) for m in texte.split())


GLEIF_ISIN = os.path.join(ICI, ".cache-bourse", "gleif", "isin-lei.zip")


def titres_par_lei(leis):
    """Combien de titres (actions, obligations…) chaque entreprise a émis,
    d'après la liste que GLEIF publie chaque jour. Entre deux homonymes,
    l'entreprise cotée est celle qui en a émis : la maison mère « Bonduelle »
    en a, la holding intermédiaire du même nom n'en a aucun."""
    compte = {}
    if not os.path.exists(GLEIF_ISIN):
        return compte
    with zipfile.ZipFile(GLEIF_ISIN) as z:
        with z.open(z.namelist()[0]) as brut:
            for ligne in io.TextIOWrapper(brut, encoding="utf-8"):
                lei = ligne[:20]
                if lei in leis:
                    compte[lei] = compte.get(lei, 0) + 1
    return compte


FILIALE = re.compile(r"\bL\.?\s?L\.?\s?C\b|\bL\.?\s?L\.?\s?P\b|,?\s\bL\.?P\.?$", re.I)


def choisir_dans_gleif(actions, candidats, leis_connus=()):
    """Pour chaque action, LA bonne entreprise de GLEIF, ou aucune.

    Un candidat convient si sa clef de nom est la même que celle de l'action.
    Quand Bloomberg a coupé le nom à 28 caractères, la clef du candidat doit
    COMMENCER par celle de l'action, lettre à lettre (« …LOUIS VUI » trouve
    « …LOUIS VUITTON », mais « GRUPO MEXICANO DE DESARROLLO » ne trouve plus
    « GRUPO MEXICANO DE PROYECTOS »).
    Entre plusieurs :
      0. celui dont Wikidata donne le numéro LEI (c'est ainsi que Bonduelle
         est trouvée : GLEIF a deux entreprises de ce nom, Wikidata sait
         laquelle est cotée) ;
      1. celui qui est du pays d'une des places de cotation (OBLIGATOIRE hors
         des places internationales) ;
      2. celui dont le nom complet, forme juridique comprise, est le même ;
      3. une entreprise « ordinaire » plutôt qu'un fonds ou une succursale ;
      4. un numéro LEI à jour (« ISSUED ») plutôt qu'expiré ;
      5. une entreprise qui a émis des titres plutôt qu'une qui n'en a aucun.
    S'il en reste plusieurs à égalité, on n'en choisit AUCUN : mieux vaut un
    point gris qu'une entreprise posée chez son homonyme."""
    par_premier_mot = {}
    for fiche in candidats.values():
        for c in fiche["clefs"]:
            if c:
                par_premier_mot.setdefault(c.split()[0], []).append((c, fiche))
    titres = titres_par_lei(set(candidats))
    trouves = {}
    for a in actions:
        coupe = len(a["nom"]) >= 27
        clef = clef_de_nom(a["nom"])
        if not clef:
            continue
        bons = {}
        for c, fiche in par_premier_mot.get(clef.split()[0], []):
            if c == clef or (coupe and c.startswith(clef)):
                bons[fiche["lei"]] = fiche
        # Une « LLC » ou une « LP » américaine n'émet pas d'actions cotées :
        # c'est une filiale (« GLOBANT, LLC » n'est pas « GLOBANT SA »).
        if not FILIALE.search(a["nom"]):
            bons = {k: f for k, f in bons.items() if not FILIALE.search(f["nom"])}
        if not bons:
            continue
        pays = {PAYS_DES_PLACES.get(p) for p in a["places"]}
        if not set(a["places"]) & PLACES_INTERNATIONALES:
            bons = {k: f for k, f in bons.items() if f["pays"] in pays}
            if not bons:
                continue
        complet = nom_complet(a["nom"])
        def note(f):
            return (f["lei"] in leis_connus,
                    f["pays"] in pays, nom_complet(f["nom"]) == complet,
                    f["categorie"] in ("GENERAL", ""), f["statut"] == "ISSUED",
                    titres.get(f["lei"], 0) > 0)
        tries = sorted(bons.values(), key=note, reverse=True)
        if len(tries) > 1 and note(tries[0]) == note(tries[1]):
            continue  # homonymes indiscernables
        trouves[a["figi"]] = tries[0]
    return trouves


# --- Étape 5 : placer une adresse sur la carte -----------------------------
#
# Deux services gratuits, tous deux tirés de données publiques :
#   · Nominatim, le moteur de recherche d'adresses d'OpenStreetMap, pour le
#     monde entier. Sa règle : une question par seconde au plus, et garder les
#     réponses pour ne jamais redemander. On la respecte à la lettre.
#   · celui de l'Institut géographique du Japon (GSI), pour les adresses
#     japonaises, écrites en japonais, que Nominatim lit mal.
#
# Toutes les réponses sont gardées dans scripts/adresses.json. Ce fichier-là
# EST publié avec le site : c'est ce qui évite au robot de GitHub, qui repart
# chaque matin de zéro, de rechercher 40 000 adresses tous les jours.

ADRESSES = os.path.join(ICI, "adresses.json")

# Les adresses qui ne sont pas un siège mais celle d'un agent juridique : des
# milliers d'entreprises américaines déclarent l'adresse de leur avocat dans
# le Delaware, et beaucoup d'autres une boîte aux lettres aux Bermudes.
AGENTS = re.compile(r"1209 ORANGE|251 LITTLE FALLS|CORPORATION TRUST|CORPORATION SERVICE COMPANY|"
                    r"\bC/O\b|CARE OF|CANON'S COURT|CLARENDON HOUSE|UGLAND HOUSE|"
                    r"P\.?\s?O\.? BOX|POSTFACH|BOITE POSTALE", re.I)

# Ce qui, dans une ligne d'adresse, gêne la recherche sans aider à placer le
# point : l'étage, le bureau, la « suite »…
BRUIT = re.compile(r"\b(suite|ste|unit|room|rm|floor|fl|level|lvl|apt|bldg|office|"
                   r"etage|étage|piso|stock|ofic|oficina|bureau)\b\.?\s*[\w-]*|"
                   r"\b\d+(st|nd|rd|th|e|er|ème)\s+(floor|étage|etage)\b|\b\d+/F\b", re.I)

_memoire = None
_dernier_nominatim = [0.0]


def memoire():
    global _memoire
    if _memoire is None:
        _memoire = json.load(open(ADRESSES, encoding="utf-8")) if os.path.exists(ADRESSES) else {}
    return _memoire


def enregistrer_memoire():
    with open(ADRESSES, "w", encoding="utf-8") as f:
        json.dump(memoire(), f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def question_nominatim(parametres):
    attente = 1.05 - (time.time() - _dernier_nominatim[0])
    if attente > 0:
        time.sleep(attente)
    _dernier_nominatim[0] = time.time()
    url = "https://nominatim.openstreetmap.org/search?" + \
        urllib.parse.urlencode(dict(parametres, format="json", limit=1))
    req = urllib.request.Request(url, headers={"User-Agent": EN_TETES["User-Agent"]})
    for n in range(4):
        try:
            return json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
        except Exception:
            time.sleep(10 * (n + 1))
    return []


def question_japon(texte):
    url = "https://msearch.gsi.go.jp/address-search/AddressSearch?q=" + urllib.parse.quote(texte)
    req = urllib.request.Request(url, headers={"User-Agent": EN_TETES["User-Agent"]})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    except Exception:
        return None
    time.sleep(0.3)
    return r[0]["geometry"]["coordinates"] if r else None


# Les sortes de résultats de Nominatim qui ne sont PAS un bâtiment ou une rue.
TROP_VAGUE = {"city", "town", "village", "municipality", "county", "state", "region",
              "suburb", "postcode", "country", "hamlet", "district", "borough",
              "city_district", "province", "island", "quarter", "neighbourhood"}


def placer(adresse, hors_ligne=False):
    """Une adresse de GLEIF -> [lon, lat, précision] ou None.
    précision : 1 = au bâtiment ou à la rue (bleu), 0 = à la ville (jaune).
    hors_ligne : ne rien demander à personne, seulement regarder ce qui est
    déjà dans scripts/adresses.json."""
    lignes = [adresse.get(k) or "" for k in ("FirstAddressLine", "AdditionalAddressLine.1",
                                              "AdditionalAddressLine.2")]
    ville, pays = adresse.get("City") or "", adresse.get("Country") or ""
    cp = adresse.get("PostalCode") or ""
    clef = "|".join([*lignes, adresse.get("AddressNumber") or "", cp, ville, pays])
    m = memoire()
    if clef in m or hors_ligne:
        return m.get(clef)

    resultat = None
    tout = " ".join(lignes)
    # Wilmington, dans le Delaware : la ville où des milliers d'entreprises
    # américaines déclarent l'adresse de leur agent juridique, sans y avoir le
    # moindre bureau. On n'y pose personne ; Wikidata donnera la vraie ville.
    if pays == "US" and (adresse.get("Region") or "") == "US-DE" and "WILMINGTON" in ville.upper():
        m[clef] = None
        return None
    if not AGENTS.search(tout):
        if pays == "JP" and re.search(r"[぀-鿿]", tout + ville):
            p = question_japon((adresse.get("Region") or "") + ville + tout)
            if p:
                resultat = [round(p[0], 5), round(p[1], 5), 1]
        else:
            morceaux = []
            for l in lignes:
                for b in l.split(","):
                    b = BRUIT.sub("", b).strip(" ,")
                    if b:
                        morceaux.append(b)
            numero = adresse.get("AddressNumber") or ""
            rues = [b for b in morceaux if re.search(r"\d", b) and re.search(r"[^\W\d_]{3}", b)]
            rue = rues[0] if rues else (morceaux[0] if morceaux else "")
            if numero and numero not in rue:
                rue = numero + " " + rue
            if rue:
                essais = [{"street": rue, "city": ville, "postalcode": cp, "country": pays},
                          {"street": rue, "city": ville, "country": pays}]
                for e in essais:
                    r = question_nominatim({k: v for k, v in e.items() if v})
                    if r and r[0].get("addresstype") not in TROP_VAGUE:
                        resultat = [round(float(r[0]["lon"]), 5), round(float(r[0]["lat"]), 5), 1]
                        break
    if resultat is None and ville:
        resultat = placer_ville(ville, pays)
    m[clef] = resultat
    if len(m) % 50 == 0:
        enregistrer_memoire()
    return resultat


def placer_ville(ville, pays):
    """Le centre d'une ville : le repli quand la rue est introuvable."""
    m = memoire()
    clef = "ville|%s|%s" % (ville.upper(), pays)
    if clef not in m:
        r = question_nominatim({"city": ville, "country": pays})
        m[clef] = [round(float(r[0]["lon"]), 5), round(float(r[0]["lat"]), 5), 0] if r else None
    return m[clef]


if __name__ == "__main__":
    a = lire("toutes.json")
    if a is None:
        dit("→ OpenFIGI : toutes les actions des bourses principales")
        a = toutes_les_actions()
        garder("toutes.json", a)
    dit(f"  {len(a)} actions différentes")
    if "--gleif" in sys.argv:
        dit("→ GLEIF : chercher chaque entreprise dans le registre")
        candidats = lire("gleif_candidats.json")
        if candidats is None:
            candidats = chercher_dans_gleif(a)
            garder("gleif_candidats.json", candidats)
        trouves = choisir_dans_gleif(a, candidats)
        garder("gleif_trouves.json", trouves)
        leis = {f["lei"] for f in trouves.values()}
        dit(f"  {len(trouves)} actions reliées à GLEIF, soit {len(leis)} entreprises")
    if "--placer" in sys.argv:
        # Placer sur la carte l'adresse de chaque entreprise reliée à GLEIF.
        # Une adresse par seconde : c'est long (plusieurs heures la première
        # fois), mais tout est gardé dans scripts/adresses.json au fur et à
        # mesure, et le programme reprend là où il s'était arrêté.
        trouves = lire("gleif_trouves.json") or {}
        fiches = {f["lei"]: f for f in trouves.values()}
        dit(f"→ Placer {len(fiches)} sièges sur la carte")
        bilan = {"bleu": 0, "jaune": 0, "rien": 0}
        debut = time.time()
        for n, f in enumerate(fiches.values(), 1):
            r = placer(f["adresse"])
            bilan["rien" if not r else ("bleu" if r[2] == 1 else "jaune")] += 1
            if n % 200 == 0:
                enregistrer_memoire()
                reste = (time.time() - debut) / n * (len(fiches) - n) / 3600
                dit(f"    {n} / {len(fiches)} · {bilan} · encore ~{reste:.1f} h")
        enregistrer_memoire()
        dit(f"  terminé : {bilan}")
