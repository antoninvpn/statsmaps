#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_geojson.py — prépare le fond de carte de StatsMaps.

Ce que fait ce script, en une phrase :
il télécharge les frontières des pays du monde, les allège, et les range
dans data/pays.geojson pour que la carte s'affiche très vite.

À lancer :  python3 scripts/build_geojson.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).
"""

import json
import os
import sys
import urllib.request

# --- Réglages -------------------------------------------------------------

# Frontières du monde, résolution 1:110m (la plus légère). Domaine public.
SOURCE_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
    "/master/geojson/ne_110m_admin_0_countries.geojson"
)

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

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER_SORTIE = os.path.join(RACINE, "data", "pays.geojson")


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

        if not code or code == "-99":
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
    print("  Écrit dans data/pays.geojson  (%d Ko)" % round(poids_ko))
    print("Terminé.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erreur:
        print("ERREUR : %s" % erreur, file=sys.stderr)
        sys.exit(1)
