#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_millionnaires.py — la carte du nombre de millionnaires par pays.

Ce que fait ce script, en une phrase :
il lit les chiffres recopiés des rapports du Credit Suisse et d'UBS
(scripts/millionnaires/sources.json), relie chaque nom de pays au code de la
carte, et écrit data/millionnaires.json au même format que les cartes du FMI.

À lancer :  python3 scripts/build_millionnaires.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).

D'OÙ VIENNENT LES CHIFFRES (choix d'Antonin du 21 novembre 2026)
  · 2011 → 2021 : les « Global Wealth Databook » du Credit Suisse, retrouvés
    dans les archives du web (le Credit Suisse a été racheté par UBS en 2023).
    Pour une cinquantaine de pays, le nombre EXACT (tableau « High net worth
    individuals by country »). Pour les ~130 autres, la part des adultes qui
    possèdent plus d'un million de dollars, arrondie à 0,1 %, multipliée par
    le nombre d'adultes : un ordre de grandeur. Une part affichée « 0,0 % »
    ne dit pas « zéro » mais « moins de 0,05 % » : le pays reste alors gris.
    Pas de 2013 (recueil introuvable) ni de 2010 (les millionnaires n'y sont
    pas comptés à part).
  · 2023 → 2025 : les « Global Wealth Report » d'UBS, qui ne publient plus que
    25 à 36 pays. Les autres sont gris (« donnée non disponible »).
  · 2022 : aucun rapport trouvé avec des chiffres par pays.

Un « millionnaire » est ici un ADULTE dont la fortune nette (immobilier et
placements, moins les dettes) dépasse un million de dollars américains.
"""

import json
import os
import unicodedata

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(RACINE, "scripts", "millionnaires", "sources.json")
PAYS = os.path.join(RACINE, "data", "pays.json")
SORTIE = os.path.join(RACINE, "data", "millionnaires.json")

# Les noms des rapports qui ne ressemblent pas à ceux de la carte.
ALIAS = {
    "united states of america": "USA", "korea": "KOR", "korea, rep.": "KOR",
    "south korea": "KOR", "mainland china": "CHN", "china, taiwan": "TWN",
    "taiwan (chinese taipei)": "TWN", "hong kong sar": "HKG",
    "hong kong sar, china": "HKG", "russian federation": "RUS",
    "czech republic": "CZE", "congo, dem. rep.": "COD", "congo, rep.": "COG",
    "kyrgyz republic": "KGZ", "lao pdr": "LAO", "macedonia": "MKD",
    "macedonia, fyr": "MKD", "syrian arab republic": "SYR",
    "swaziland": "SWZ", "yemen, rep.": "YEM", "west bank and gaza": "WBG",
    "türkiye": "TUR", "brunei darussalam": "BRN", "cape verde": "CPV",
    "antigua and barbuda": "ATG", "bosnia and herzegovina": "BIH",
    "central african republic": "CAF", "sao tome and principe": "STP",
    "solomon islands": "SLB", "st. kitts and nevis": "KNA",
    "st. lucia": "LCA", "st. vincent and the grenadines": "VCT",
    "trinidad and tobago": "TTO",
}
# Des régions, pas des pays : on les écarte.
REGIONS = {"africa", "asia - pacific", "asia-pacific", "europe", "world",
           "latin america", "latin america and caribbean", "north america",
           "northern america", "melanesia", "polynesia", "micronesia",
           "british caribbean", "dutch caribbean", "french caribbean"}


def cle(texte):
    """« Côte d'Ivoire », « Cote d'Ivoire », « Repu blic » -> une même clef."""
    return "".join(c for c in unicodedata.normalize("NFKD", texte.lower()) if c.isalnum())


def main():
    sources = json.load(open(SOURCES, encoding="utf-8"))
    pays = json.load(open(PAYS, encoding="utf-8"))["features"]
    codes = {}
    for f in pays:
        for langue in ("en", "fr"):
            codes[cle(f["properties"][langue])] = f["properties"]["iso"]
    for nom, iso in ALIAS.items():
        codes[cle(nom)] = iso

    valeurs, inconnus = {}, set()

    def poser(nom, annee, nombre):
        if nom.lower() in REGIONS:
            return
        iso = codes.get(cle(nom))
        if not iso:
            inconnus.add(nom)
            return
        if nombre:
            valeurs.setdefault(iso, {})[annee] = nombre

    for annee, lignes in sources["credit_suisse"]["annees"].items():
        for nom, (nombre, sorte) in lignes.items():
            # « 0,0 % » veut dire « moins de 0,05 % », pas « personne » : gris.
            poser(nom, annee, nombre if (sorte == "exact" or nombre > 0) else None)
    for annee, lignes in sources["ubs"]["annees"].items():
        for nom, nombre in lignes.items():
            poser(nom, annee, nombre)

    annees = sorted({int(a) for v in valeurs.values() for a in v})
    tous_fr = {"fr": "", "en": ""}
    contenu = {
        "indicateur": "millionnaires",
        "titre": {"fr": "Nombre de millionnaires", "en": "Number of millionaires"},
        "unite": tous_fr,
        "unite_longue": {
            "fr": "adultes dont la fortune dépasse 1 million de dollars",
            "en": "adults with net worth above USD 1 million",
        },
        "decimales": 0,
        "pic": True,
        "annees": annees,
        "derniere_annee_reelle": annees[-1],
        # La source propre à cette carte (les autres cartes citent le FMI).
        "source": {"fr": "Credit Suisse (2011-2021) et UBS (2023-2025), Global Wealth Report",
                   "en": "Credit Suisse (2011-2021) and UBS (2023-2025), Global Wealth Report"},
        "source_url": "https://www.ubs.com/global/en/wealthmanagement/insights/global-wealth-report.html",
        "valeurs": {iso: dict(sorted(v.items())) for iso, v in sorted(valeurs.items())},
    }
    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(contenu, f, ensure_ascii=False, separators=(",", ":"))

    print("Carte des millionnaires")
    print("  %d pays, années %s" % (len(valeurs), ", ".join(map(str, annees))))
    for a in annees:
        print("    %d : %d pays" % (a, sum(1 for v in valeurs.values() if str(a) in v)))
    if inconnus:
        print("  ATTENTION, noms non reconnus : %s" % ", ".join(sorted(inconnus)))
    print("  Écrit dans data/millionnaires.json (%d Ko)" % (os.path.getsize(SORTIE) // 1024))


if __name__ == "__main__":
    main()
