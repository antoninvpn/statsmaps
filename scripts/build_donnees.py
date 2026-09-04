#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_donnees.py — va chercher les chiffres chez le FMI et les range dans data/.

Ce que fait ce script, en une phrase :
il appelle l'API publique du FMI (IMF DataMapper), garde uniquement les vrais pays
(pas les groupes comme « Monde » ou « Zone euro »), et écrit un fichier par carte.

À lancer :  python3 scripts/build_donnees.py
Aucune installation nécessaire (bibliothèque standard de Python uniquement).

Le vocabulaire des titres et des unités est RECOPIÉ du FMI
(https://www.imf.org/external/datamapper/profile/AUT), pour que le site dise
exactement la même chose que sa source. C'est pourquoi le PIB nominal et le PIB
en parité de pouvoir d'achat portent le MÊME titre — « PIB, prix courants » —
et ne se distinguent que par leur unité. C'est la façon de faire du FMI.

Les cartes « année record » ne sont plus fabriquées ici : le navigateur les
calcule tout seul à partir des chiffres de la carte affichée (voir la fonction
donneesRecord() dans assets/js/carte.js). Cela évite de télécharger deux fois
les mêmes données.
"""

import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

# --- Réglages -------------------------------------------------------------

API = "https://www.imf.org/external/datamapper/api/v1"

# Les treize langues du site, écrites une fois pour toutes : cela évite de les
# recopier dans chaque indicateur qui n'a qu'une seule unité (« % »).
LANGUES = ("fr", "en", "uk", "de", "es", "it", "pt",
           "pl", "ja", "ko", "tr", "hi", "ar")

# « Variation annuelle en pourcentage », l'unité du FMI pour la croissance et
# l'inflation. Elle sert deux fois, on l'écrit donc une seule.
POURCENT_ANNUEL = {
    "fr": "variation annuelle en pourcentage",
    "en": "annual percent change",
    "uk": "річна зміна у відсотках",
    "de": "jährliche prozentuale Veränderung",
    "es": "variación porcentual anual",
    "it": "variazione percentuale annua",
    "pt": "variação percentual anual",
    "pl": "roczna zmiana procentowa",
    "ja": "年間変化率",
    "ko": "연간 변화율",
    "tr": "yıllık yüzde değişim",
    "hi": "वार्षिक प्रतिशत परिवर्तन",
    "ar": "التغير السنوي بالنسبة المئوية",
}

# Les cartes du site.
#
#   fichier ....... le nom du fichier data/<fichier>.json, et l'identifiant de
#                   la carte dans assets/js/carte.js et scripts/build_pages.py
#   code_fmi ...... l'indicateur chez le FMI
#   categorie ..... la rubrique de l'accueil (« economie », « demographie »)
#   famille ....... les cartes d'une même famille sont deux VERSIONS d'une même
#                   grandeur (le PIB en dollars courants et en parité de pouvoir
#                   d'achat). Le site propose alors de passer de l'une à l'autre.
#   variante ...... le nom de la version, pour le bouton de bascule
#   pic ........... cette carte a-t-elle un onglet « Pic » ? Il répond à la
#                   question « en quelle année ce pays a-t-il été à son
#                   maximum ? », et elle a un sens pour les sept cartes : le
#                   pic du PIB, mais aussi le pic d'inflation (le Venezuela en
#                   2018) ou le pic de population (le Japon en 2011). Une
#                   future carte pourrait s'en passer — un indice sans unité,
#                   par exemple — d'où le réglage.
#   decimales ..... le nombre maximum de décimales affichées. Trois, c'est tout
#                   ce que contiennent les fichiers : le site montre donc toute
#                   la précision disponible. Les zéros inutiles ne sont pas
#                   écrits (« 2,3 % » et non « 2,300 % »).
#   titre ......... le titre du FMI, traduit
#   unite ......... l'unité COURTE, pour la colonne étroite du classement
#   unite_longue .. l'unité du FMI en toutes lettres, sous le titre de la légende
INDICATEURS = [
    {
        "fichier": "pib-nominal",
        "code_fmi": "NGDPD",
        "categorie": "economie",
        "famille": "pib",
        "variante": "nominal",
        "pic": True,
        "decimales": 3,
        "titre": {
            "fr": "PIB, prix courants",
            "en": "GDP, current prices",
            "uk": "ВВП, поточні ціни",
            "de": "BIP, jeweilige Preise",
            "es": "PIB, precios corrientes",
            "it": "PIL, prezzi correnti",
            "pt": "PIB, preços correntes",
            "pl": "PKB, ceny bieżące",
            "ja": "GDP、現行価格",
            "ko": "GDP, 경상가격",
            "tr": "GSYİH, cari fiyatlar",
            "hi": "जीडीपी, वर्तमान मूल्य",
            "ar": "الناتج المحلي الإجمالي، الأسعار الجارية",
        },
        "unite": {
            "fr": "Md$", "en": "bn$", "uk": "млрд $", "de": "Mrd. $",
            "es": "mm$", "it": "mld $", "pt": "mM$", "pl": "mld $",
            "ja": "十億ドル", "ko": "십억 $", "tr": "milyar $",
            "hi": "अरब $", "ar": "مليار $",
        },
        "unite_longue": {
            "fr": "milliards de dollars US",
            "en": "billions of U.S. dollars",
            "uk": "мільярди доларів США",
            "de": "Milliarden US-Dollar",
            "es": "miles de millones de dólares de EE. UU.",
            "it": "miliardi di dollari USA",
            "pt": "mil milhões de dólares dos EUA",
            "pl": "miliardy dolarów amerykańskich",
            "ja": "十億米ドル",
            "ko": "십억 미국 달러",
            "tr": "milyar ABD doları",
            "hi": "अरब अमेरिकी डॉलर",
            "ar": "مليارات الدولارات الأمريكية",
        },
    },
    {
        "fichier": "pib-ppa",
        "code_fmi": "PPPGDP",
        "categorie": "economie",
        "famille": "pib",
        "variante": "ppa",
        "pic": True,
        "decimales": 3,
        # Même titre que le PIB nominal : c'est ainsi que le FMI les présente.
        # Seule l'unité les distingue.
        "titre": {
            "fr": "PIB, prix courants",
            "en": "GDP, current prices",
            "uk": "ВВП, поточні ціни",
            "de": "BIP, jeweilige Preise",
            "es": "PIB, precios corrientes",
            "it": "PIL, prezzi correnti",
            "pt": "PIB, preços correntes",
            "pl": "PKB, ceny bieżące",
            "ja": "GDP、現行価格",
            "ko": "GDP, 경상가격",
            "tr": "GSYİH, cari fiyatlar",
            "hi": "जीडीपी, वर्तमान मूल्य",
            "ar": "الناتج المحلي الإجمالي، الأسعار الجارية",
        },
        "unite": {
            "fr": "Md $ int.", "en": "bn int$", "uk": "млрд міжн. $",
            "de": "Mrd. int. $", "es": "mm $ int.", "it": "mld $ int.",
            "pt": "mM $ int.", "pl": "mld $ międz.", "ja": "十億国際ドル",
            "ko": "십억 국제 $", "tr": "milyar ulus. $", "hi": "अरब अंत. $",
            "ar": "مليار $ دولي",
        },
        "unite_longue": {
            "fr": "parité de pouvoir d’achat ; milliards de dollars internationaux",
            "en": "purchasing power parity; billions of international dollars",
            "uk": "паритет купівельної спроможності; мільярди міжнародних доларів",
            "de": "Kaufkraftparität; Milliarden internationale Dollar",
            "es": "paridad de poder adquisitivo; miles de millones de dólares internacionales",
            "it": "parità di potere d’acquisto; miliardi di dollari internazionali",
            "pt": "paridade de poder de compra; mil milhões de dólares internacionais",
            "pl": "parytet siły nabywczej; miliardy dolarów międzynarodowych",
            "ja": "購買力平価、十億国際ドル",
            "ko": "구매력 평가; 십억 국제 달러",
            "tr": "satın alma gücü paritesi; milyar uluslararası dolar",
            "hi": "क्रय शक्ति समता; अरब अंतर्राष्ट्रीय डॉलर",
            "ar": "تعادل القوة الشرائية؛ مليارات الدولارات الدولية",
        },
    },
    {
        "fichier": "pib-par-habitant",
        "code_fmi": "NGDPDPC",
        "categorie": "economie",
        "famille": "pib-par-habitant",
        "variante": "nominal",
        "pic": True,
        "decimales": 3,
        "titre": {
            "fr": "PIB par habitant, prix courants",
            "en": "GDP per capita, current prices",
            "uk": "ВВП на душу населення, поточні ціни",
            "de": "BIP pro Kopf, jeweilige Preise",
            "es": "PIB per cápita, precios corrientes",
            "it": "PIL pro capite, prezzi correnti",
            "pt": "PIB per capita, preços correntes",
            "pl": "PKB na mieszkańca, ceny bieżące",
            "ja": "一人当たりGDP、現行価格",
            "ko": "1인당 GDP, 경상가격",
            "tr": "Kişi başına GSYİH, cari fiyatlar",
            "hi": "प्रति व्यक्ति जीडीपी, वर्तमान मूल्य",
            "ar": "نصيب الفرد من الناتج المحلي الإجمالي، الأسعار الجارية",
        },
        "unite": {
            "fr": "$/hab.", "en": "$/capita", "uk": "$/особу", "de": "$/Kopf",
            "es": "$/hab.", "it": "$/ab.", "pt": "$/hab.", "pl": "$/mieszk.",
            "ja": "ドル／人", "ko": "$/인", "tr": "$/kişi",
            "hi": "$/व्यक्ति", "ar": "$/فرد",
        },
        "unite_longue": {
            "fr": "dollars US par habitant",
            "en": "U.S. dollars per capita",
            "uk": "доларів США на душу населення",
            "de": "US-Dollar pro Kopf",
            "es": "dólares de EE. UU. per cápita",
            "it": "dollari USA pro capite",
            "pt": "dólares dos EUA per capita",
            "pl": "dolary amerykańskie na mieszkańca",
            "ja": "一人当たり米ドル",
            "ko": "1인당 미국 달러",
            "tr": "kişi başına ABD doları",
            "hi": "प्रति व्यक्ति अमेरिकी डॉलर",
            "ar": "دولار أمريكي للفرد",
        },
    },
    {
        "fichier": "pib-par-habitant-ppa",
        "code_fmi": "PPPPC",
        "categorie": "economie",
        "famille": "pib-par-habitant",
        "variante": "ppa",
        "pic": True,
        "decimales": 3,
        "titre": {
            "fr": "PIB par habitant, prix courants",
            "en": "GDP per capita, current prices",
            "uk": "ВВП на душу населення, поточні ціни",
            "de": "BIP pro Kopf, jeweilige Preise",
            "es": "PIB per cápita, precios corrientes",
            "it": "PIL pro capite, prezzi correnti",
            "pt": "PIB per capita, preços correntes",
            "pl": "PKB na mieszkańca, ceny bieżące",
            "ja": "一人当たりGDP、現行価格",
            "ko": "1인당 GDP, 경상가격",
            "tr": "Kişi başına GSYİH, cari fiyatlar",
            "hi": "प्रति व्यक्ति जीडीपी, वर्तमान मूल्य",
            "ar": "نصيب الفرد من الناتج المحلي الإجمالي، الأسعار الجارية",
        },
        "unite": {
            "fr": "$ int./hab.", "en": "int$/capita", "uk": "міжн. $/особу",
            "de": "int. $/Kopf", "es": "$ int./hab.", "it": "$ int./ab.",
            "pt": "$ int./hab.", "pl": "$ międz./mieszk.", "ja": "国際ドル／人",
            "ko": "국제 $/인", "tr": "ulus. $/kişi", "hi": "अंत. $/व्यक्ति",
            "ar": "$ دولي/فرد",
        },
        "unite_longue": {
            "fr": "parité de pouvoir d’achat ; dollars internationaux par habitant",
            "en": "purchasing power parity; international dollars per capita",
            "uk": "паритет купівельної спроможності; міжнародних доларів на душу населення",
            "de": "Kaufkraftparität; internationale Dollar pro Kopf",
            "es": "paridad de poder adquisitivo; dólares internacionales per cápita",
            "it": "parità di potere d’acquisto; dollari internazionali pro capite",
            "pt": "paridade de poder de compra; dólares internacionais per capita",
            "pl": "parytet siły nabywczej; dolary międzynarodowe na mieszkańca",
            "ja": "購買力平価、一人当たり国際ドル",
            "ko": "구매력 평가; 1인당 국제 달러",
            "tr": "satın alma gücü paritesi; kişi başına uluslararası dolar",
            "hi": "क्रय शक्ति समता; प्रति व्यक्ति अंतर्राष्ट्रीय डॉलर",
            "ar": "تعادل القوة الشرائية؛ دولار دولي للفرد",
        },
    },
    {
        "fichier": "croissance",
        "code_fmi": "NGDP_RPCH",
        "categorie": "economie",
        "famille": None,
        "variante": None,
        "pic": True,
        "decimales": 3,
        "titre": {
            "fr": "Croissance du PIB réel",
            "en": "Real GDP growth",
            "uk": "Зростання реального ВВП",
            "de": "Reales BIP-Wachstum",
            "es": "Crecimiento del PIB real",
            "it": "Crescita del PIL reale",
            "pt": "Crescimento do PIB real",
            "pl": "Wzrost realnego PKB",
            "ja": "実質GDP成長率",
            "ko": "실질 GDP 성장률",
            "tr": "Reel GSYİH büyümesi",
            "hi": "वास्तविक जीडीपी वृद्धि",
            "ar": "نمو الناتج المحلي الإجمالي الحقيقي",
        },
        "unite": {langue: "%" for langue in LANGUES},
        "unite_longue": POURCENT_ANNUEL,
    },
    {
        "fichier": "inflation",
        "code_fmi": "PCPIPCH",
        "categorie": "economie",
        "famille": None,
        "variante": None,
        "pic": True,
        "decimales": 3,
        "titre": {
            "fr": "Taux d’inflation, prix à la consommation",
            "en": "Inflation rate, average consumer prices",
            "uk": "Рівень інфляції, споживчі ціни",
            "de": "Inflationsrate, Verbraucherpreise",
            "es": "Tasa de inflación, precios al consumidor",
            "it": "Tasso d’inflazione, prezzi al consumo",
            "pt": "Taxa de inflação, preços no consumidor",
            "pl": "Stopa inflacji, ceny konsumpcyjne",
            "ja": "インフレ率、消費者物価",
            "ko": "물가상승률, 소비자물가",
            "tr": "Enflasyon oranı, tüketici fiyatları",
            "hi": "मुद्रास्फीति दर, उपभोक्ता मूल्य",
            "ar": "معدل التضخم، أسعار المستهلك",
        },
        "unite": {langue: "%" for langue in LANGUES},
        "unite_longue": POURCENT_ANNUEL,
    },
    {
        "fichier": "population",
        "code_fmi": "LP",
        "categorie": "demographie",
        "famille": None,
        "variante": None,
        "pic": True,
        "decimales": 3,
        "titre": {
            "fr": "Population",
            "en": "Population",
            "uk": "Населення",
            "de": "Bevölkerung",
            "es": "Población",
            "it": "Popolazione",
            "pt": "População",
            "pl": "Ludność",
            "ja": "人口",
            "ko": "인구",
            "tr": "Nüfus",
            "hi": "जनसंख्या",
            "ar": "عدد السكان",
        },
        "unite": {
            "fr": "M hab.", "en": "M people", "uk": "млн осіб", "de": "Mio.",
            "es": "M hab.", "it": "mln ab.", "pt": "M hab.", "pl": "mln osób",
            "ja": "百万人", "ko": "백만 명", "tr": "milyon kişi",
            "hi": "मिलियन", "ar": "مليون نسمة",
        },
        "unite_longue": {
            "fr": "millions d’habitants",
            "en": "millions of people",
            "uk": "мільйони осіб",
            "de": "Millionen Menschen",
            "es": "millones de personas",
            "it": "milioni di persone",
            "pt": "milhões de pessoas",
            "pl": "miliony osób",
            "ja": "百万人",
            "ko": "백만 명",
            "tr": "milyon kişi",
            "hi": "मिलियन लोग",
            "ar": "ملايين النسمة",
        },
    },
]

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER_DATA = os.path.join(RACINE, "data")

# Les fichiers d'une version précédente du site, que ce script ne fabrique plus.
# On les efface pour ne pas laisser traîner des chiffres que plus personne
# n'affiche : les cartes « année record » sont maintenant calculées par le
# navigateur à partir de la carte affichée.
FICHIERS_ABANDONNES = [
    "annee-record-pib.json",
    "annee-record-pib-par-habitant.json",
]


# --- Outils ---------------------------------------------------------------

# Depuis 2025, le FMI filtre les requêtes qui ne viennent pas d'un vrai
# navigateur : on reçoit « 403 Access Denied ». Deux filtres se cumulent.
#
#   1. Les en-têtes. Une simple ligne « User-Agent: StatsMaps » ne passe plus ;
#      il faut se présenter comme un navigateur, avec le même jeu d'en-têtes.
#      C'est le rôle de EN_TETES ci-dessous.
#   2. La poignée de main TLS elle-même. Le serveur reconnaît le logiciel qui
#      se connecte à la FORME de sa négociation chiffrée, avant même de lire
#      la moindre en-tête. Python a une signature reconnaissable, et se fait
#      refouler quels que soient ses en-têtes. curl, lui, passe.
#
# D'où la façon de faire : on appelle curl, présent partout (macOS, Linux,
# les serveurs de GitHub), et on ne se rabat sur Python que s'il manque.
EN_TETES = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.imf.org/external/datamapper/profile/AUT",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Dest": "empty",
}

CURL = shutil.which("curl")


def _telecharger(url):
    """Rapporte le texte de la page, par curl si possible, sinon par Python."""
    if CURL:
        commande = [CURL, "--silent", "--show-error", "--fail", "--compressed",
                    "--max-time", "90", "--location"]
        for nom, valeur in EN_TETES.items():
            commande += ["-H", "%s: %s" % (nom, valeur)]
        commande.append(url)
        fini = subprocess.run(commande, capture_output=True)
        if fini.returncode != 0:
            raise RuntimeError(
                "curl a échoué (code %d) : %s"
                % (fini.returncode, fini.stderr.decode("utf-8", "replace").strip())
            )
        return fini.stdout.decode("utf-8")

    requete = urllib.request.Request(url, headers=EN_TETES)
    with urllib.request.urlopen(requete, timeout=90) as reponse:
        return reponse.read().decode("utf-8")


def appeler_api(chemin, essais=3):
    """Appelle l'API du FMI et renvoie le JSON. Réessaie si le serveur bafouille."""
    url = "%s/%s" % (API, chemin)
    derniere_erreur = None
    for numero in range(1, essais + 1):
        try:
            return json.loads(_telecharger(url))
        except (urllib.error.URLError, RuntimeError, ValueError) as erreur:
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
            "de": "IWF, World Economic Outlook",
            "es": "FMI, World Economic Outlook",
            "it": "FMI, World Economic Outlook",
            "pt": "FMI, World Economic Outlook",
            "pl": "MFW, World Economic Outlook",
            "ja": "IMF, World Economic Outlook",
            "ko": "IMF, World Economic Outlook",
            "tr": "IMF, World Economic Outlook",
            "hi": "IMF, World Economic Outlook",
            "ar": "صندوق النقد الدولي، World Economic Outlook",
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
            "unite_longue": indicateur["unite_longue"],
            "decimales": indicateur["decimales"],
            "pic": indicateur["pic"],
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
            "categorie": indicateur["categorie"],
            "famille": indicateur["famille"],
            "variante": indicateur["variante"],
            "pic": indicateur["pic"],
            "titre": indicateur["titre"],
            "unite": indicateur["unite"],
            "unite_longue": indicateur["unite_longue"],
            "annees": [annees[0], annees[-1]],
            "nb_pays": len(valeurs),
        }

    total_ko += ecrire_json("meta.json", meta)

    # 3. Le ménage : les fichiers d'une version précédente du site.
    for nom in FICHIERS_ABANDONNES:
        chemin = os.path.join(DOSSIER_DATA, nom)
        if os.path.exists(chemin):
            os.remove(chemin)
            print("  Supprimé (calculé par le navigateur maintenant) : %s" % nom)

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
