#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dirigeants.py — la carte de ceux qui dirigent chaque pays.

À lancer :  python3 scripts/build_dirigeants.py
(bibliothèque standard de Python uniquement ; un robot GitHub le lance chaque
jour, voir .github/workflows/maj-dirigeants.yml)

Les sources, choisies par Antonin le 25 novembre 2026 :

  Wikipédia « List of current heads of state and government »
      QUI dirige. La page colorie en vert celui qui a le pouvoir exécutif selon
      la constitution, en bleu celui qui l'exerce en réalité quand ce n'est pas
      le même. La règle : le bleu s'il y en a un, sinon le vert.
  Wikipédia « List of current state leaders by date of assumption of office »
      DEPUIS QUAND.
  Wikidata ....... femme ou homme, le nom en français, la photo.
  Wikimedia Commons ... les photos, leurs auteurs et leurs licences.

Les cas que la page ne permet pas de lire (un collège, un nom écrit autrement)
sont réglés à la main dans CORRECTIONS, plus bas.

Si le résultat paraît cassé (la page a changé de forme, trop de pays manquent),
rien n'est écrit : la carte garde ce qu'elle avait.
"""

import datetime
import html
import io
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

RACINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SORTIE = os.path.join(RACINE, "data", "dirigeants.json")
PHOTOS = os.path.join(RACINE, "data", "dirigeants")
CADRAGES = os.path.join(RACINE, "scripts", "dirigeants_cadrages.json")

PAGE_QUI = "List of current heads of state and government"
PAGE_QUAND = "List of current state leaders by date of assumption of office"
WIKIPEDIA = "https://en.wikipedia.org/w/api.php"
WIKIDATA = "https://www.wikidata.org/w/api.php"
COMMONS = "https://commons.wikimedia.org/w/api.php"
EN_TETES = {"User-Agent": "StatsMaps/1.0 (+https://statsmaps.com)"}

# Le nom d'un pays sur Wikipédia, quand ce n'est pas celui de data/pays.json.
PAYS_DE_WIKIPEDIA = {
    "Georgia (country)": "GEO", "Ivory Coast": "CIV", "Cape Verde": "CPV",
    "Democratic Republic of the Congo": "COD", "Republic of the Congo": "COG",
    "Czech Republic": "CZE", "East Timor": "TLS", "Timor-Leste": "TLS",
    "Federated States of Micronesia": "FSM", "Palestine": "WBG", "Holy See": "VAT",
    "Vatican City": "VAT", "The Gambia": "GMB", "Gambia": "GMB", "Bahamas": "BHS", "The Bahamas": "BHS", "Bahamas, The": "BHS",
    "Eswatini": "SWZ", "São Tomé and Príncipe": "STP", "Myanmar": "MMR",
    "North Macedonia": "MKD", "Turkey": "TUR", "Kosovo": "UVK", "Taiwan": "TWN",
    "South Korea": "KOR", "North Korea": "PRK", "Macau": "MAC", "Laos": "LAO",
    "Vietnam": "VNM", "Russia": "RUS", "Syria": "SYR", "Brunei": "BRN",
    "Antigua and Barbuda": "ATG", "Bosnia and Herzegovina": "BIH",
    "Central African Republic": "CAF", "Dominican Republic": "DOM",
    "Marshall Islands": "MHL", "Kingdom of the Netherlands": "NLD", "Netherlands": "NLD",
    "Saint Kitts and Nevis": "KNA", "Saint Vincent and the Grenadines": "VCT",
    "Solomon Islands": "SLB", "Trinidad and Tobago": "TTO",
}

# Ce que la page ne permet pas de lire. « article » : l'article de Wikipédia de
# la personne ; « titre » : sa fonction, en anglais, comme sur la page.
CORRECTIONS = {
    # Le vert désigne tout le Conseil fédéral : on prend son président, qui
    # change chaque 1er janvier (la page le marque « President »).
    "CHE": {"motif": r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\] \(\[\[President of the Swiss Confederation",
            "titre": "President"},
    # Le sultan est aussi Premier ministre : son nom est sur une autre ligne.
    "BRN": {"article": "Hassanal Bolkiah", "titre": "Sultan"},
    # Deux personnes écrites « Nom (fonction) » au lieu de « fonction – Nom ».
    "SDN": {"motif": r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\] \(President\)", "titre": "President"},
    "SMR": {"motif": r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\] \(\[\[San Marino Secretary",
            "titre": "Secretary for Foreign and Political Affairs"},
}

# Les dates choisies à la main. La clef est la PERSONNE, pas le pays : le jour
# où quelqu'un d'autre dirige, sa correction ne sert plus.
DATES_CHOISIES = {
    # Madagascar : Randrianirina prend le pouvoir le 14 octobre 2025, et prête
    # serment le 17 (la date de Wikipédia). Antonin a choisi le 14.
    "Q136500275": "2025-10-14",
    # Syrie : Ahmed al-Charaa dirige le pays depuis la chute d'Assad. Wikipédia
    # compte aussi ses années à la tête du « Gouvernement de salut », à Idleb.
    "Q7934206": "2024-12-08",
    # Arabie saoudite : Mohammed ben Salmane est prince héritier, la fonction
    # affichée, depuis le 21 juin 2017. La page des dates ne donne que son poste
    # de Premier ministre (27 septembre 2022).
    "Q6892571": "2017-06-21",
}

# Les photos d'origine russe acceptées par Antonin, une par une :
# Vladimir Poutine et Michael Randrianirina (Madagascar).
PHOTO_DE_WIKIPEDIA = {"Q7747", "Q136500275"}

# Une photo choisie à la main : identifiant Wikidata -> fichier de Commons.
CHOIX_DE_PHOTO = {
    "Q98497406": "Assimi Goita, August 2021 (cropped II).png",  # Voice of America
    "Q136500275": "Michael Randrianirina in February 2026.jpg",
    "Q2866": "Alexander Lukashenko 2020.jpg",   # département d'État américain
}

# Pas de photo libre et authentifiée : la calligraphie de son nom à la place, et
# un lien vers sa page Wikipédia (choix d'Antonin, 25 novembre 2026). La photo
# de Wikipédia n'est pas libre (« fair use ») : ne pas la copier.
CALLIGRAPHIES = {"Q24237654": "Hibatullah Akhundzada OCS wordmark.png"}

# Le titre en français. Une femme : la seconde forme.
TITRES = {
    "President": ("Président", "Présidente"),
    "Prime Minister": ("Premier ministre", "Première ministre"),
    "Acting President": ("Président par intérim", "Présidente par intérim"),
    "Interim President": ("Président par intérim", "Présidente par intérim"),
    "Transitional President": ("Président de la transition", "Présidente de la transition"),
    "Acting Prime Minister": ("Premier ministre par intérim", "Première ministre par intérim"),
    "Interim Prime Minister": ("Premier ministre par intérim", "Première ministre par intérim"),
    "Caretaker Prime Minister": ("Premier ministre chargé des affaires courantes",
                                 "Première ministre chargée des affaires courantes"),
    "Chancellor": ("Chancelier", "Chancelière"),
    "Federal Chancellor": ("Chancelier fédéral", "Chancelière fédérale"),
    "King": ("Roi", "Reine"), "Queen": ("Roi", "Reine"), "Emir": ("Émir", "Émir"),
    "Sultan": ("Sultan", "Sultane"), "Prince": ("Prince souverain", "Princesse souveraine"),
    "Regent": ("Régent", "Régente"), "Pope": ("Pape", "Pape"),
    "Sovereign Prince": ("Prince souverain", "Princesse souveraine"),
    "Co-Presidents": ("Coprésident (avec Rosario Murillo)", "Coprésidente"),
    "President of the Council of the Presidency for the Re-Foundation of the Republic":
        ("Président du Conseil de la présidence pour la refondation",) * 2,
    "President of the Presidential Leadership Council":
        ("Président du Conseil présidentiel", "Présidente du Conseil présidentiel"),
    "Sovereign": ("Souverain", "Souveraine"),
    "Supreme Leader": ("Guide suprême", "Guide suprême"),
    "Crown Prince": ("Prince héritier", "Princesse héritière"),
    "Taoiseach": ("Taoiseach (Premier ministre)", "Taoiseach (Première ministre)"),
    "Minister of State": ("Ministre d’État", "Ministre d’État"),
    "Premier": ("Premier ministre", "Première ministre"),
    "General Secretary of the Communist Party":
        ("Secrétaire général du Parti communiste", "Secrétaire générale du Parti communiste"),
    "First Secretary of the Communist Party":
        ("Premier secrétaire du Parti communiste", "Première secrétaire du Parti communiste"),
    "General Secretary of the Workers' Party":
        ("Secrétaire général du Parti du travail", "Secrétaire générale du Parti du travail"),
    "General Secretary of the People's Revolutionary Party":
        ("Secrétaire général du Parti révolutionnaire populaire",
         "Secrétaire générale du Parti révolutionnaire populaire"),
    "President of the People's Party":
        ("Président du Parti du peuple", "Présidente du Parti du peuple"),
    "Chairman of the People's Council":
        ("Président du Conseil du peuple", "Présidente du Conseil du peuple"),
    "Chairman of the All-Belarusian People's Assembly":
        ("Président de l’Assemblée populaire panbiélorusse",
         "Présidente de l’Assemblée populaire panbiélorusse"),
    "Honorary Chairman of Georgian Dream":
        ("Président honoraire du Rêve géorgien", "Présidente honoraire du Rêve géorgien"),
    "Acting High Representative":
        ("Haut représentant par intérim", "Haute représentante par intérim"),
    "High Representative": ("Haut représentant", "Haute représentante"),
    "Chief of the High Command": ("Chef du haut commandement", "Cheffe du haut commandement"),
    "President of the Patriotic Movement for Safeguard and Restoration":
        ("Président du Mouvement patriotique pour la sauvegarde et la restauration",) * 2,
    "President of the National Council for the Safeguard of the Homeland":
        ("Président du Conseil national pour la sauvegarde de la patrie",) * 2,
    "Secretary for Foreign and Political Affairs":
        ("Secrétaire d’État aux Affaires étrangères et politiques",) * 2,
}

MOIS = {m: i + 1 for i, m in enumerate(
    "January February March April May June July August September October "
    "November December".split())}


def dit(*a):
    print(*a, flush=True)


# --- 1. Lire Wikipédia, Wikidata, Commons ---------------------------------

def demander(adresse, **parametres):
    parametres.update(format="json", formatversion="2", maxlag="5")
    url = adresse + "?" + urllib.parse.urlencode(parametres)
    for essai in range(6):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=EN_TETES), timeout=90) as r:
                d = json.loads(r.read().decode("utf-8"))
            if "error" in d:
                raise RuntimeError(d["error"].get("code"))
            return d
        except Exception as ex:
            if essai == 5:
                raise
            dit("    …", type(ex).__name__, ex)
            time.sleep(8 * (essai + 1))


def page(titre):
    w = demander(WIKIPEDIA, action="parse", page=titre, prop="wikitext",
                 redirects=1)["parse"]["wikitext"]
    w = re.sub(r"<!--.*?-->", "", w, flags=re.S)
    w = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", w, flags=re.S)
    w = w.replace("{{snd}}", " – ").replace("&nbsp;", " ")
    # Les notes de bas de page sont pleines de noms et de dates : on les ôte.
    while True:
        g = gabarits(w, ("efn", "refn", "note"))
        if not g:
            return w
        debut, _, fin, _ = g[-1]
        w = w[:debut] + w[fin:]


def gabarits(texte, noms):
    """Les {{nom|…}} d'un texte : (début, nom, fin, contenu)."""
    sortie = []
    for m in re.finditer(r"\{\{\s*(%s)\s*(?=[|}])" % "|".join(noms), texte, re.I):
        prof, i = 0, m.start()
        while i < len(texte):
            if texte.startswith("{{", i):
                prof, i = prof + 1, i + 2
            elif texte.startswith("}}", i):
                prof, i = prof - 1, i + 2
                if prof == 0:
                    break
            else:
                i += 1
        sortie.append((m.start(), m.group(1).lower(), i, texte[m.end():i - 2]))
    return sortie


def sans_liens(t):
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\{\{\s*(?:small|nowrap|nobr|resize)\s*\|(?:[0-9.]+%?\|)?", "", t)
    return re.sub(r"\s+", " ", t.replace("}}", "").replace("'''", "").replace("''", "")).strip()


# --- 2. Qui dirige ? ------------------------------------------------------

def lire_qui():
    """{nom du pays sur Wikipédia : (couleur, titre en anglais, article)}"""
    w = page(PAGE_QUI)
    debut = w.index("==Member and observer")
    fin = w.index("==Alternative governments")
    blocs = re.split(r"\n!(?=[^\n]*\{\{flag\|)", w[debut:fin])[1:]
    nom_de = lambda b: re.match(r"[^\n]*?\{\{flag\|([^|}]+)", b).group(1).strip()

    resultat, i = {}, 0
    while i < len(blocs):
        nom, bloc = nom_de(blocs[i]), blocs[i]
        # Kosovo, Taïwan… : la case d'à côté dit qui les revendique, et c'est
        # après elle que viennent les dirigeants.
        if not gabarits(bloc, ("success", "operational")) and i + 1 < len(blocs):
            if "|" not in bloc.split("}}", 1)[1]:
                i += 1
                bloc = blocs[i]
        resultat.setdefault(nom, bloc)
        i += 1
    return resultat


def personne(bloc, correction):
    """(couleur, titre, article) de celui qui dirige, ou None."""
    if correction:
        article = correction.get("article")
        if not article:
            m = re.search(correction["motif"], bloc)
            if not m:
                return None
            article = m.group(1).strip()
        couleur = "bleu" if gabarits(bloc, ("operational",)) else "vert"
        return couleur, correction["titre"], article

    for gabarit, couleur in (("operational", "bleu"), ("success", "vert")):
        for _, _, _, contenu in gabarits(bloc, (gabarit,)):
            contenu = re.sub(r"^\|?\s*(?:align\s*=\s*\w+\s*\|)?\s*", "", contenu)
            morceaux = re.split(r"\s+–\s+", contenu, maxsplit=1)
            if len(morceaux) < 2 or "Vacant" in morceaux[1]:
                continue
            m = re.search(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", morceaux[1])
            if m:
                article = m.group(1).strip()
            else:
                # Déjà nommé plus haut dans la même case : sans lien cette fois.
                nom = sans_liens(morceaux[1])
                m = re.search(r"\[\[((?:[^\]|]*\|)?%s)\]\]" % re.escape(nom), bloc)
                article = m.group(1).split("|")[0] if m else nom
            return couleur, sans_liens(morceaux[0]), article
    return None


# --- 3. Depuis quand ? ----------------------------------------------------

def grille(tableau):
    """Les lignes d'un tableau de Wikipédia, cases fusionnées dépliées."""
    lignes, reports = [], {}
    for bloc in re.split(r"\n\|-[^\n]*", tableau)[1:]:
        cases = []
        for brute in re.split(r"\n\|(?!\})", "\n" + bloc.strip("\n"))[1:]:
            m = re.match(r"\s*((?:[a-z-]+\s*=\s*(?:\"[^\"]*\"|[^\s|]+)\s*)+)\|(?!\|)", brute, re.I)
            attributs, contenu = (m.group(1), brute[m.end():]) if m else ("", brute)
            n = re.search(r"rowspan\s*=\s*\"?(\d+)", attributs)
            cases.append((contenu.strip(), int(n.group(1)) if n else 1))
        ligne, colonne = [], 0
        while cases or colonne in reports:
            if colonne in reports:
                contenu, reste = reports.pop(colonne)
                if reste > 1:
                    reports[colonne] = (contenu, reste - 1)
                ligne.append(contenu)
                colonne += 1
                continue
            contenu, hauteur = cases.pop(0)
            if hauteur > 1:
                reports[colonne] = (contenu, hauteur - 1)
            ligne.append(contenu)
            colonne += 1
        if len(ligne) >= 3:
            lignes.append(ligne)
    return lignes


def article_de(case):
    """L'article de la personne nommée dans une case."""
    m = re.search(r"\{\{\s*sortname\s*\|([^}]*)\}\}", case, re.I)
    if m:
        brut = [x.strip() for x in m.group(1).split("|")]
        place = [x for x in brut if "=" not in x]
        nomme = dict(x.split("=", 1) for x in brut if "=" in x)
        if len(place) > 2 and place[2]:
            return place[2]
        nom = " ".join(place[:2]).strip()
        return nom + (" (%s)" % nomme["dab"].strip() if nomme.get("dab") else "")
    m = re.search(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", case)
    return m.group(1).strip() if m else None


def lire_quand():
    """[(article, pays sur Wikipédia, "AAAA-MM-JJ")]. Après 2021, l'année n'est
    plus dans la case mais dans le titre de la partie (« ===2024=== »)."""
    w = page(PAGE_QUAND)
    w = w[w.index("==List of state leaders"):w.index("==List of upcoming")]
    sortie = []
    for partie in re.split(r"\n(?====)", w)[1:]:
        annee = re.match(r"===\s*(\d{4})\s*===", partie)
        for ligne in grille(partie):
            m = re.search(r"(\d{1,2})\s+(%s)(?:\s+(\d{4}))?" % "|".join(MOIS), ligne[0])
            if not m:
                n = re.search(r"dts\|(?:[a-z]+=[^|]*\|)*(\d{4})\|(\d{1,2})\|(\d{1,2})", ligne[0])
                date = "%s-%02d-%02d" % (n.group(1), int(n.group(2)), int(n.group(3))) if n else None
            else:
                an = m.group(3) or (annee and annee.group(1))
                date = "%s-%02d-%02d" % (an, MOIS[m.group(2)], int(m.group(1))) if an else None
            pays = re.search(r"\{\{\s*flag(?:country)?\s*\|([^|}]+)", ligne[2], re.I)
            article = article_de(ligne[1])
            if date and pays and article:
                sortie.append((article, pays.group(1).strip(), date))
    return sortie


# --- 4. Wikidata et Commons -----------------------------------------------

def par_paquets(liste, n=40):
    liste = sorted(set(liste))
    for i in range(0, len(liste), n):
        yield liste[i:i + n]


def identifiants(articles):
    """Article de Wikipédia -> identifiant Wikidata (redirections suivies)."""
    sortie = {}
    for paquet in par_paquets(articles):
        d = demander(WIKIPEDIA, action="query", titles="|".join(paquet), redirects=1,
                     prop="pageprops", ppprop="wikibase_item|disambiguation")["query"]
        suite = {r["from"]: r["to"] for r in d.get("normalized", []) + d.get("redirects", [])}
        pages = {p["title"]: p.get("pageprops", {}) for p in d.get("pages", [])}
        for a in paquet:
            t = a
            for _ in range(3):
                t = suite.get(t, t)
            p = pages.get(t, {})
            if p.get("wikibase_item") and "disambiguation" not in p:
                sortie[a] = p["wikibase_item"]
        time.sleep(0.5)
    return sortie


def valeurs(entite, propriete):
    """Les valeurs d'une propriété, la préférée d'abord."""
    d = [x for x in entite.get("claims", {}).get(propriete, []) if x.get("rank") != "deprecated"]
    d.sort(key=lambda x: x.get("rank") != "preferred")
    v = [x.get("mainsnak", {}).get("datavalue", {}).get("value") for x in d]
    return [x for x in v if x is not None]


def valeur(entite, propriete):
    return next(iter(valeurs(entite, propriete)), None)


def fiches(qids):
    sortie = {}
    for paquet in par_paquets(qids):
        d = demander(WIKIDATA, action="wbgetentities", ids="|".join(paquet),
                     props="labels|claims|sitelinks", languages="fr|en|mul")
        for q, e in d["entities"].items():
            noms = {k: v["value"] for k, v in e.get("labels", {}).items()}
            sexe = valeur(e, "P21") or {}
            naissance = valeur(e, "P569") or {}
            sortie[q] = {
                "fr": noms.get("fr") or noms.get("mul") or noms.get("en"),
                "en": noms.get("en") or noms.get("mul") or noms.get("fr"),
                "g": {"Q6581097": "h", "Q6581072": "f", "Q1052281": "f",
                      "Q2449503": "h"}.get(sexe.get("id")),
                "ne": (naissance.get("time") or "")[1:11] or None,
                "photos": valeurs(e, "P18"),
                "wikis": {k: v["title"] for k, v in e.get("sitelinks", {}).items()
                          if k in WIKIS_POUR_PHOTO},
            }
        time.sleep(0.5)
    return sortie


# Aucune photo d'une institution, d'une agence ou d'un média russe (règle
# d'Antonin, 25 novembre 2026 : « JAMAIS rien de russe »).
RUSSE = re.compile(
    r"kremlin|кремл|state duma|госдума|государственная дума|russia|росси|путин|\btass\b|тасс|ria novosti|"
    r"риа новости|sputnik|roscongress|росконгресс|татарстан|tatarstan|\.ru\b|"
    r"presidential press and information office|presidential executive office|"
    r"krasilnikov|bobylev|бобылев|смирнов|бадышкин|пресс-служба|yandex|vk\.com", re.I)

# Où chercher une autre photo, dans cet ordre, quand la première ne convient pas.
WIKIS_POUR_PHOTO = ("enwiki", "frwiki", "dewiki", "eswiki", "ukwiki", "itwiki",
                    "plwiki", "ptwiki", "nlwiki", "svwiki", "jawiki", "arwiki")


def autres_photos(wikis):
    """Les photos choisies par les différentes Wikipédia pour une personne."""
    sortie = []
    for wiki in WIKIS_POUR_PHOTO:
        if wiki not in wikis:
            continue
        try:
            d = demander("https://%s.wikipedia.org/w/api.php" % wiki[:-4], action="query",
                         titles=wikis[wiki], redirects=1, prop="pageimages",
                         piprop="name", pilicense="free")["query"]
        except Exception:
            continue
        for p in d.get("pages", []):
            if p.get("pageimage") and p["pageimage"] not in sortie:
                sortie.append(p["pageimage"].replace("_", " "))
        time.sleep(0.3)
    return sortie


def photos(noms_de_fichiers):
    """Fichier de Commons -> adresse de la vignette, auteur, licence."""
    sortie = {}
    for paquet in par_paquets(["File:" + n for n in noms_de_fichiers], 25):
        d = demander(COMMONS, action="query", titles="|".join(paquet), prop="imageinfo",
                     iiprop="url|extmetadata|size", iiurlwidth="250",
                     iiextmetadatafilter="Artist|LicenseShortName|Credit")["query"]
        rendu = {r["to"]: r["from"] for r in d.get("normalized", [])}
        for p in d.get("pages", []):
            info = (p.get("imageinfo") or [None])[0]
            if not info:
                continue
            meta = {k: v.get("value", "") for k, v in info.get("extmetadata", {}).items()}
            net = lambda t: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()
            nom = rendu.get(p["title"], p["title"])[5:]
            sortie[nom.replace("_", " ")] = {
                "vignette": info.get("thumburl"), "page": info.get("descriptionurl"),
                "auteur": net(meta.get("Artist", ""))[:120],
                "licence": net(meta.get("LicenseShortName", "")),
                "russe": bool(RUSSE.search(" ".join(
                    [nom, net(meta.get("Artist", "")), meta.get("Artist", ""),
                     meta.get("Credit", "")]))),
            }
        time.sleep(0.5)
    return sortie


def telecharger_photo(adresse, chemin):
    for essai in range(5):
        try:
            with urllib.request.urlopen(
                    urllib.request.Request(adresse, headers=EN_TETES), timeout=60) as r:
                octets = r.read()
            if len(octets) < 800:
                raise RuntimeError("image vide")
            with open(chemin, "wb") as f:
                f.write(octets)
            time.sleep(0.6)
            return True
        except Exception as ex:
            dit("    … photo :", type(ex).__name__, str(ex)[:60])
            time.sleep(10 * (essai + 1))
    return False


# --- 5. Le déroulé --------------------------------------------------------

def titre_francais(titre, sexe):
    if titre in TITRES:
        return TITRES[titre][1 if sexe == "f" else 0]
    return None


def main():
    with io.open(os.path.join(RACINE, "data", "pays.json"), encoding="utf-8") as f:
        pays = {e["properties"]["iso"]: e["properties"] for e in json.load(f)["features"]}
    iso_par_nom = {p["en"]: iso for iso, p in pays.items()}
    iso_par_nom.update({k: v for k, v in PAYS_DE_WIKIPEDIA.items() if v in pays})

    dit("→ Wikipédia : qui dirige ?")
    retenus, illisibles = {}, []
    for nom, bloc in lire_qui().items():
        iso = iso_par_nom.get(nom)
        if not iso:
            illisibles.append("(hors carte) " + nom)
            continue
        p = personne(bloc, CORRECTIONS.get(iso))
        if p:
            retenus[iso] = p
        else:
            illisibles.append(nom)
    dit("  %d pays lus ; non lus : %s" % (len(retenus), ", ".join(illisibles) or "aucun"))

    dit("→ Wikipédia : depuis quand ?")
    quand = lire_quand()
    dit("  %d lignes" % len(quand))

    articles = [a for _, _, a in retenus.values()] + [l[0] for l in quand]
    qids = identifiants(articles)
    dates = {}
    for article, nom, date in quand:
        cle = (qids.get(article), iso_par_nom.get(nom))
        if all(cle) and date and (cle not in dates or date < dates[cle]):
            dates[cle] = date

    dit("→ Wikidata : femme ou homme, nom, photo")
    infos = fiches([qids[a] for _, _, a in retenus.values() if a in qids])
    images = photos([n for i in infos.values() for n in i["photos"]])
    propre = lambda n: (n or "").replace("_", " ")
    for q, i in infos.items():
        choix = CHOIX_DE_PHOTO.get(q)
        if choix and propre(choix) not in images:
            images.update(photos([choix]))
        candidates = ([choix] if choix else []) + i["photos"]
        bonne = lambda n: (images.get(propre(n)) and images[propre(n)]["vignette"]
                           and not images[propre(n)]["russe"])
        bonnes = [n for n in candidates if n and bonne(n)]
        # Sauf pour ceux-ci, dont la photo de Wikipédia convient (accord
        # d'Antonin, 25 novembre 2026).
        if not bonnes and q in PHOTO_DE_WIKIPEDIA:
            bonnes = [n for n in candidates if n and images.get(propre(n))]
        if not bonnes:
            autres = autres_photos(i["wikis"])
            images.update(photos([n for n in autres if propre(n) not in images]))
            bonnes = [n for n in autres if bonne(n)]
            dit("    %s : photo russe ou absente -> %s" % (i["fr"], bonnes[0] if bonnes else "RIEN"))
        if q in CALLIGRAPHIES:
            images.update(photos([CALLIGRAPHIES[q]]))
            bonnes = [CALLIGRAPHIES[q]]
        i["photo"] = bonnes[0] if bonnes else None

    ancien = {}
    if os.path.exists(SORTIE):
        with io.open(SORTIE, encoding="utf-8") as f:
            ancien = json.load(f).get("pays", {})
    cadrages = {}
    if os.path.exists(CADRAGES):
        with io.open(CADRAGES, encoding="utf-8") as f:
            cadrages = json.load(f)

    os.makedirs(PHOTOS, exist_ok=True)
    sortie, sans_date, sans_titre, sans_photo = {}, [], set(), []
    for iso, (couleur, titre, article) in sorted(retenus.items()):
        q = qids.get(article)
        i = infos.get(q, {})
        fiche = {
            "q": q, "fr": i.get("fr") or article, "en": i.get("en") or article,
            "g": i.get("g"), "ne": i.get("ne"),
            "titre": {"en": titre, "fr": titre_francais(titre, i.get("g")) or titre},
            "depuis": DATES_CHOISIES.get(q) or dates.get((q, iso)), "couleur": couleur,
        }
        if titre not in TITRES:
            sans_titre.add(titre)
        if not fiche["depuis"]:
            sans_date.append(pays[iso]["fr"])
        image = images.get(propre(i.get("photo")))
        if image and image["vignette"]:
            nom = "%s.jpg" % q
            chemin = os.path.join(PHOTOS, nom)
            meme = (ancien.get(iso, {}).get("photo") or {}).get("page") == image["page"]
            grande = os.path.join(PHOTOS, "g-" + nom)
            deja = meme and os.path.exists(chemin) and os.path.exists(grande)
            if deja or (telecharger_photo(image["vignette"], chemin) and
                        telecharger_photo(image["vignette"].replace("/250px-", "/500px-"), grande)):
                fiche["photo"] = {"page": image["page"], "auteur": image["auteur"],
                                  "licence": image["licence"]}
                if q in CALLIGRAPHIES:
                    fiche["photo"]["calligraphie"] = True
                    fiche["wiki"] = {
                        l: "https://%s.wikipedia.org/wiki/%s" % (
                            l, urllib.parse.quote(i["wikis"][l + "wiki"].replace(" ", "_")))
                        # En anglais seulement : la page française n'a pas la photo.
                        for l in ("en",) if l + "wiki" in i.get("wikis", {})}
                elif image["page"] in cadrages:
                    fiche["photo"]["visage"] = cadrages[image["page"]]
        if "photo" not in fiche:
            sans_photo.append(pays[iso]["fr"])
        sortie[iso] = fiche

    dit("  sans date :", ", ".join(sans_date) or "aucun")
    dit("  sans photo :", ", ".join(sans_photo) or "aucun")
    dit("  titres sans traduction :", "; ".join(sorted(sans_titre)) or "aucun")
    dit("  femme/homme inconnu :", ", ".join(k for k, v in sortie.items() if not v["g"]) or "aucun")

    # Le garde-fou : mieux vaut une carte d'hier qu'une carte cassée.
    attendus = max(180, int(len(ancien) * 0.95))
    if len(sortie) < attendus or len(sans_date) > 40:
        sys.exit("✗ Résultat suspect (%d pays, %d sans date) : rien n'est écrit."
                 % (len(sortie), len(sans_date)))

    # Du vandalisme, ou une page refaite : jamais autant de changements en un jour.
    changes = [k for k, v in sortie.items() if k in ancien and ancien[k]["q"] != v["q"]]
    if len(changes) > 12 and "--force" not in sys.argv:
        sys.exit("✗ %d dirigeants changent d'un coup (%s) : rien n'est écrit. "
                 "Si c'est normal : relancer avec --force." % (len(changes), ", ".join(changes)))

    utiles = {p + f["q"] + ".jpg" for f in sortie.values() if f.get("photo") for p in ("", "g-")}
    for nom in os.listdir(PHOTOS):
        if nom.endswith(".jpg") and nom not in utiles:
            os.remove(os.path.join(PHOTOS, nom))
    if sortie == ancien:
        dit("✓ Rien n'a changé.")
        return
    with io.open(SORTIE, "w", encoding="utf-8", newline="\n") as f:
        json.dump({"maj": datetime.date.today().isoformat(), "pays": sortie}, f,
                  ensure_ascii=False, indent=0, sort_keys=True)
    dit("✓ %d pays écrits dans data/dirigeants.json" % len(sortie))


if __name__ == "__main__":
    main()
