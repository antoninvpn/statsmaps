#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_donnees.py — va chercher les chiffres chez le FMI et les range dans data/.

Ce que fait ce script, en une phrase :
il appelle l'API publique du FMI (IMF DataMapper), garde uniquement les vrais pays
(pas les groupes comme « Monde » ou « Zone euro »), et écrit un fichier par carte.

À lancer :  python3 scripts/build_donnees.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).
"""

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

# --- Réglages -------------------------------------------------------------

API = "https://www.imf.org/external/datamapper/api/v1"

# Les cartes du site. Pour en ajouter une, il suffit d'ajouter une ligne ici
# (puis de créer la page HTML correspondante).
INDICATEURS = [
    {
        "fichier": "pib-nominal",
        "code_fmi": "NGDPD",
        "unite": {"fr": "Md$", "en": "bn$"},
        "titre": {"fr": "PIB nominal", "en": "Nominal GDP"},
        "decimales": 0,
    },
    {
        "fichier": "pib-par-habitant",
        "code_fmi": "NGDPDPC",
        "unite": {"fr": "$/hab.", "en": "$/capita"},
        "titre": {"fr": "PIB par habitant", "en": "GDP per capita"},
        "decimales": 0,
    },
    {
        "fichier": "croissance",
        "code_fmi": "NGDP_RPCH",
        "unite": {"fr": "%", "en": "%"},
        "titre": {"fr": "Croissance du PIB réel", "en": "Real GDP growth"},
        "decimales": 1,
    },
]

# Certaines entrées de la liste « pays » du FMI ne sont pas des pays souverains
# ou n'apparaissent pas sur la carte ; on ne les exclut pas ici, la carte
# les ignorera simplement si elle n'a pas leur frontière.

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(RACINE, "data")


# --- Outils ---------------------------------------------------------------

def appeler_api(chemin, essais=3):
    """Appelle l'API du FMI et renvoie le JSON. Réessaie si le serveur bafouille."""
    url = "%s/%s" % (API, chemin)
    derniere_erreur = None
    for numero in range(1, essais + 1):
        try:
            requete = urllib.request.Request(
                url, headers={"User-Agent": "StatsMaps/1.0 (+https://statsmaps.com)"}
            )
            with urllib.request.urlopen(requete, timeout=90) as reponse:
                return json.loads(reponse.read().decode("utf-8"))
        except (urllib.error.URLError, ValueError) as erreur:
            derniere_erreur = erreur
            print("    tentative %d/%d échouée (%s)" % (numero, essais, erreur))
            if numero < essais:
                time.sleep(3 * numero)
    raise RuntimeError("Impossible de joindre le FMI pour %s : %s" % (chemin, derniere_erreur))


def ecrire_json(nom_fichier, contenu):
    chemin = os.path.join(DOSSIER_DATA, nom_fichier)
    with open(chemin, "w", encoding="utf-8") as fichier:
        json.dump(contenu, fichier, separators=(",", ":"), ensure_ascii=False)
    return os.path.getsize(chemin) / 1024


# --- Programme principal --------------------------------------------------

def main():
    print("Mise à jour des données FMI pour StatsMaps")
    print("-" * 55)
    os.makedirs(DOSSIER_DATA, exist_ok=True)

    # 1. La liste officielle des pays du FMI. Elle sert de filtre : tout ce qui
    #    n'est pas dedans est un groupe (Monde, Zone euro, G7...) et on l'écarte.
    print("  Récupération de la liste des pays ...")
    liste_pays = appeler_api("countries")["countries"]
    codes_pays = set(liste_pays.keys())
    print("  %d pays reconnus par le FMI." % len(codes_pays))

    annee_courante = datetime.date.today().year
    # Le FMI publie des estimations pour l'année en cours et des projections
    # pour les suivantes. On considère « réelle » la dernière année révolue.
    derniere_annee_reelle = annee_courante - 1

    meta = {
        "mis_a_jour_le": datetime.date.today().isoformat(),
        "source": {
            "fr": "FMI, World Economic Outlook",
            "en": "IMF, World Economic Outlook",
        },
        "source_url": "https://www.imf.org/external/datamapper/datasets/WEO",
        "derniere_annee_reelle": derniere_annee_reelle,
        "indicateurs": {},
    }

    total_ko = 0

    # 2. Un appel par indicateur.
    for indicateur in INDICATEURS:
        code = indicateur["code_fmi"]
        print("  Récupération de %s (%s) ..." % (indicateur["titre"]["fr"], code))

        brut = appeler_api(code)["values"][code]

        valeurs = {}
        annees_vues = set()

        for code_pays, par_annee in brut.items():
            if code_pays not in codes_pays:
                continue  # c'est un groupe ou une région : on écarte
            propres = {}
            for annee, valeur in par_annee.items():
                if isinstance(valeur, (int, float)):
                    propres[annee] = round(float(valeur), 3)
                    annees_vues.add(int(annee))
            if propres:
                valeurs[code_pays] = propres

        annees = sorted(annees_vues)

        contenu = {
            "indicateur": indicateur["fichier"],
            "code_fmi": code,
            "titre": indicateur["titre"],
            "unite": indicateur["unite"],
            "decimales": indicateur["decimales"],
            "annees": annees,
            "derniere_annee_reelle": derniere_annee_reelle,
            "valeurs": valeurs,
        }

        poids = ecrire_json("%s.json" % indicateur["fichier"], contenu)
        total_ko += poids
        print("    %d pays, années %d-%d, %d Ko"
              % (len(valeurs), annees[0], annees[-1], round(poids)))

        meta["indicateurs"][indicateur["fichier"]] = {
            "code_fmi": code,
            "titre": indicateur["titre"],
            "unite": indicateur["unite"],
            "annees": [annees[0], annees[-1]],
            "nb_pays": len(valeurs),
        }

    total_ko += ecrire_json("meta.json", meta)

    print("-" * 55)
    print("  Total écrit : %d Ko dans data/" % round(total_ko))
    print("  Dernière année réelle : %d (au-delà = projections FMI)" % derniere_annee_reelle)
    print("Terminé.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erreur:
        print("ERREUR : %s" % erreur, file=sys.stderr)
        sys.exit(1)
