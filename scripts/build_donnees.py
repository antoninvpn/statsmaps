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
        "unite": {"fr": "Md$", "en": "bn$", "uk": "млрд $"},
        "titre": {"fr": "PIB nominal", "en": "Nominal GDP", "uk": "Номінальний ВВП"},
        "decimales": 0,
    },
    {
        "fichier": "pib-par-habitant",
        "code_fmi": "NGDPDPC",
        "unite": {"fr": "$/hab.", "en": "$/capita", "uk": "$/особу"},
        "titre": {"fr": "PIB par habitant", "en": "GDP per capita",
                  "uk": "ВВП на душу населення"},
        "decimales": 0,
    },
    {
        "fichier": "croissance",
        "code_fmi": "NGDP_RPCH",
        "unite": {"fr": "%", "en": "%", "uk": "%"},
        "titre": {"fr": "Croissance du PIB réel", "en": "Real GDP growth",
                  "uk": "Зростання реального ВВП"},
        "decimales": 1,
    },
]

# --- Les cartes « année record » -----------------------------------------
# Celles-ci ne sont PAS téléchargées : elles se calculent à partir des chiffres
# déjà récupérés juste au-dessus. La question qu'elles posent est : « en quelle
# année ce pays a-t-il été à son maximum ? »
#
# Le curseur des années garde son rôle : posé sur 2008, il montre le record
# atteint « à cette date ». On voit donc la crise de 2008, puis le Covid,
# arriver en faisant glisser le curseur — et, au-delà de la dernière année
# constatée, les projections du FMI jusqu'en 2031.
INDICATEURS_RECORD = [
    {
        "fichier": "annee-record-pib",
        "depuis": "pib-nominal",
        "titre": {"fr": "Année record du PIB",
                  "en": "When GDP peaked",
                  "uk": "Рекордний рік ВВП"},
        "legende_unite": {"fr": "années écoulées depuis le record",
                          "en": "years since the peak",
                          "uk": "років від рекорду"},
    },
    {
        "fichier": "annee-record-pib-par-habitant",
        "depuis": "pib-par-habitant",
        "titre": {"fr": "Année record du PIB par habitant",
                  "en": "When GDP per capita peaked",
                  "uk": "Рекордний рік ВВП на душу населення"},
        "legende_unite": {"fr": "années écoulées depuis le record",
                          "en": "years since the peak",
                          "uk": "років від рекорду"},
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


def edition_weo(aujourd_hui):
    """De quelle édition du rapport ces chiffres viennent-ils ?

    Le FMI publie le World Economic Outlook deux fois par an, à la mi-avril et
    à la mi-octobre. On en déduit l'édition à partir de la date du jour : c'est
    forcément la dernière parue. Renvoie par exemple (2026, 4) pour avril 2026.

    Le site affichera donc « World Economic Outlook (avril 2026) », et passera
    tout seul à « octobre 2026 » après la parution suivante, sans rien changer
    dans le code."""
    if (aujourd_hui.month, aujourd_hui.day) >= (10, 15):
        return aujourd_hui.year, 10
    if (aujourd_hui.month, aujourd_hui.day) >= (4, 15):
        return aujourd_hui.year, 4
    return aujourd_hui.year - 1, 10


def annees_record(valeurs):
    """Calcule, pour chaque pays et chaque année, l'année de son record.

    On avance année par année en gardant en mémoire le plus haut chiffre vu
    jusque-là. Exemple pour la Grèce : en 2007 le record est 2007, en 2008 il
    devient 2008, et il reste 2008 pour toutes les années suivantes, parce que
    la Grèce n'a jamais retrouvé son niveau d'avant-crise.

    Les projections du FMI comptent comme les autres années : au-delà de la
    dernière année constatée, le curseur montre donc quels pays sont *prévus*
    pour battre leur record, et lesquels ne le retrouveront toujours pas.

    On n'écrit une valeur que pour les années où le pays a vraiment un chiffre :
    ainsi la carte « record » affiche exactement les mêmes pays que la carte
    d'origine, ni plus ni moins."""
    resultat = {}
    for code_pays, par_annee in valeurs.items():
        record_annee = None
        record_valeur = None
        par_annee_record = {}
        for annee in sorted(int(a) for a in par_annee):
            valeur = par_annee[str(annee)]
            if record_valeur is None or valeur > record_valeur:
                record_valeur = valeur
                record_annee = annee
            par_annee_record[str(annee)] = record_annee
        if par_annee_record:
            resultat[code_pays] = par_annee_record
    return resultat


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

    annee_weo, mois_weo = edition_weo(datetime.date.today())

    meta = {
        "mis_a_jour_le": datetime.date.today().isoformat(),
        # L'édition du rapport, affichée à côté de la source.
        "edition": {"annee": annee_weo, "mois": mois_weo},
        "source": {
            "fr": "FMI, World Economic Outlook",
            "en": "IMF, World Economic Outlook",
            "uk": "МВФ, World Economic Outlook",
        },
        "source_url": "https://www.imf.org/external/datamapper/datasets/WEO",
        "derniere_annee_reelle": derniere_annee_reelle,
        "indicateurs": {},
    }

    total_ko = 0
    valeurs_par_fichier = {}  # sert ensuite à calculer les cartes « record »

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

        valeurs_par_fichier[indicateur["fichier"]] = valeurs

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

    # 3. Les deux cartes « année record », calculées et non téléchargées.
    for indicateur in INDICATEURS_RECORD:
        print("  Calcul de %s ..." % indicateur["titre"]["fr"])

        valeurs = annees_record(valeurs_par_fichier[indicateur["depuis"]])
        annees = sorted({int(a) for par_annee in valeurs.values() for a in par_annee})

        contenu = {
            "indicateur": indicateur["fichier"],
            "code_fmi": meta["indicateurs"][indicateur["depuis"]]["code_fmi"],
            "titre": indicateur["titre"],
            # La valeur affichée est une année : elle n'a pas d'unité, et le site
            # doit l'écrire « 2008 » et non « 2 008 ». C'est ce que dit "format".
            "unite": {"fr": "", "en": "", "uk": ""},
            "legende_unite": indicateur["legende_unite"],
            "format": "annee",
            "decimales": 0,
            "annees": annees,
            "derniere_annee_reelle": derniere_annee_reelle,
            "valeurs": valeurs,
        }

        poids = ecrire_json("%s.json" % indicateur["fichier"], contenu)
        total_ko += poids
        print("    %d pays, années %d-%d, %d Ko"
              % (len(valeurs), annees[0], annees[-1], round(poids)))

        meta["indicateurs"][indicateur["fichier"]] = {
            "code_fmi": contenu["code_fmi"],
            "titre": indicateur["titre"],
            "unite": contenu["unite"],
            "annees": [annees[0], annees[-1]],
            "nb_pays": len(valeurs),
        }

    total_ko += ecrire_json("meta.json", meta)

    print("-" * 55)
    print("  Total écrit : %d Ko dans data/" % round(total_ko))
    print("  Dernière année réelle : %d (au-delà = projections FMI)" % derniere_annee_reelle)
    print("  Édition du rapport : World Economic Outlook %s %d"
          % ("avril" if mois_weo == 4 else "octobre", annee_weo))
    print("Terminé.")


if __name__ == "__main__":
    try:
        main()
    except Exception as erreur:
        print("ERREUR : %s" % erreur, file=sys.stderr)
        sys.exit(1)
