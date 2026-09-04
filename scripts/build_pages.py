#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pages.py — fabrique TOUTES les pages du site, dans les treize langues.

    python3 scripts/build_pages.py

Pourquoi ce script existe
-------------------------
Le site a 10 pages par langue — l'accueil, 2 pages de catégorie et 7 cartes —
et 13 langues, soit 130 fichiers HTML. Ces fichiers sont rigoureusement
identiques à quelques mots près : le titre, l'adresse, et la langue. Les écrire
à la main voudrait dire, à chaque petit changement — un lien dans le menu, une
balise pour Google — répéter la même retouche 130 fois sans en oublier une.

Ici, tout est écrit UNE fois : les modèles HTML en bas du fichier, et les
textes de chaque langue dans la grande liste LANGUES.

Comment le site est organisé
----------------------------
    l'accueil ........... les CATÉGORIES (Économie, Démographie)
      une catégorie ..... les CARTES qu'elle contient (PIB, croissance…)
        une carte ....... la carte elle-même, avec ses éventuelles VARIANTES

Une variante est une autre façon de mesurer la MÊME chose : le PIB en dollars
courants, ou le PIB en parité de pouvoir d'achat. Les deux ont leur propre
adresse — c'est ce que Google indexe — et un bouton passe de l'une à l'autre
dans le panneau de gauche.

Ce que ce script fabrique
-------------------------
    index.html + 9 dossiers ..................... le français, à la racine
    en/, ua/, de/, es/, it/, pt/, pl/,
    ja/, ko/, tr/, hi/, ar/ ..................... les douze autres langues
    sitemap.xml ................................. la carte du site pour Google

Il retouche aussi 404.html, mais seulement sa rangée de boutons « accueil » :
tout le reste de cette page (son texte, son style) s'écrit à la main.

Ce qu'il ne fabrique PAS du tout : robots.txt, CNAME et le dossier assets/,
qui ne dépendent d'aucune langue.

Pour ajouter une langue
-----------------------
    1. Ajouter son bloc dans LANGUES ci-dessous (le plus long : il faut
       traduire les noms et les phrases des cartes).
    2. Ajouter son bloc dans assets/js/i18n.js (les textes des boutons).
    3. Ajouter son code dans le tableau LANGUES de build_geojson.py, puis
       relancer ce script-là : les noms des 197 pays viennent de Natural Earth
       et n'ont pas à être traduits à la main.
    4. Ajouter sa langue dans les titres et unités de build_donnees.py.
    5. Relancer ce script.

Pour ajouter une carte
----------------------
    1. Une ligne dans INDICATEURS de build_donnees.py (titre et unité).
    2. Les tranches de couleur dans CARTES de assets/js/carte.js.
    3. Une ligne dans CARTES ci-dessous, sa catégorie dans CATEGORIES, et son
       entrée "cartes" dans CHACUN des treize blocs de LANGUES.
    4. Relancer ce script : les 13 pages, les menus et le sitemap suivent.
"""

import io
import os

SITE = "https://statsmaps.com"
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- LES CARTES
#
#   identifiant ... celui du fichier data/<identifiant>.json et de carte.js
#   pastille ...... l'emoji de la vignette ; il ne dépend pas de la langue
#   famille ....... les cartes d'une même famille sont deux VERSIONS d'une même
#                   grandeur, et un bouton passe de l'une à l'autre. None quand
#                   la carte est seule de son espèce.
#   variante ...... le nom de la version, dont le libellé est traduit dans
#                   chaque langue (voir "variantes" dans LANGUES)
#   principale .... la version montrée par défaut, celle qui apparaît dans le
#                   menu du haut et sur la page de sa catégorie
CARTES = [
    # identifiant,              pastille, famille,            variante,  principale
    ("pib-nominal",             "💰", "pib",              "nominal", True),
    ("pib-ppa",                 "💰", "pib",              "ppa",     False),
    ("pib-par-habitant",        "👤", "pib-par-habitant", "nominal", True),
    ("pib-par-habitant-ppa",    "👤", "pib-par-habitant", "ppa",     False),
    ("croissance",              "📈", None,               None,      True),
    ("inflation",               "🔥", None,               None,      True),
    ("population",              "👥", None,               None,      True),
]

# ----------------------------------------------------------- LES CATÉGORIES
#
# L'accueil montre ces rubriques ; chacune a sa page, qui montre ses cartes.
# Seules les cartes PRINCIPALES y figurent : on n'affiche pas deux vignettes
# pour le PIB, on entre dans la carte et on choisit son unité sur place.
CATEGORIES = [
    ("economie", "💶", ["pib-nominal", "pib-par-habitant", "croissance", "inflation"]),
    ("demographie", "👥", ["population"]),
]

# Le menu du haut ne montre JAMAIS tout le site à la fois : il montre le niveau
# où l'on se trouve.
#
#   sur l'accueil ................. les catégories (Économie · Démographie)
#   sur une page de catégorie ..... les catégories aussi : on est encore à cet
#                                   étage, et on peut passer à la rubrique voisine
#   sur une carte ................. les cartes de SA catégorie, et elles seules
#
# Sans cela, la carte de la population affichait le PIB et l'inflation dans son
# menu, alors qu'elles appartiennent à une autre rubrique.
#
# Seules les cartes PRINCIPALES y figurent : la version en parité de pouvoir
# d'achat se choisit dans le panneau de gauche, une fois la carte ouverte.
# Mettre les deux ferait un menu où « PIB » apparaîtrait deux fois.

# Pour chaque famille, la liste de ses variantes, dans l'ordre d'affichage.
FAMILLES = {}
for _identifiant, _pastille, _famille, _variante, _principale in CARTES:
    if _famille:
        FAMILLES.setdefault(_famille, []).append((_identifiant, _variante))

# La pastille de chaque carte, retrouvée par son identifiant.
PASTILLES = {c[0]: c[1] for c in CARTES}

# La famille de chaque carte (None quand elle est seule de son espèce).
FAMILLE_DE = {c[0]: c[2] for c in CARTES}

# Les cartes de chaque catégorie, retrouvées par l'identifiant de celle-ci.
CARTES_DE = {identifiant: cartes for identifiant, _, cartes in CATEGORIES}

# Et l'inverse : la catégorie de chaque carte. Les variantes ne sont pas listées
# dans CATEGORIES — on n'affiche pas deux vignettes pour le PIB — elles suivent
# donc la catégorie de leur carte principale.
CATEGORIE_DE = {}
for _identifiant, _, _cartes in CATEGORIES:
    for _carte in _cartes:
        CATEGORIE_DE[_carte] = _identifiant
for _identifiant, _, _famille, _, _principale in CARTES:
    if not _principale and _famille:
        _principales = [i for i, _, f, _, p in CARTES if f == _famille and p]
        CATEGORIE_DE[_identifiant] = CATEGORIE_DE[_principales[0]]

# La version de MapLibre, écrite une seule fois pour les 91 pages de carte.
MAPLIBRE = "5.6.1"


# ==========================================================================
#  LES TREIZE LANGUES
#
#  Un bloc par langue, avec TOUT ce qui la concerne. C'est volontairement
#  répétitif : pour corriger une faute en allemand, on ouvre le bloc "de" et
#  tout y est, sans avoir à sauter d'un fichier à l'autre.
#
#  - code ............. celui de i18n.js et de build_geojson.py
#  - dossier .......... le dossier du site ("" pour le français, à la racine)
#  - hreflang ......... le code que lit Google (celui de l'ukrainien est "uk",
#                       alors que son dossier s'appelle "ua" — c'est voulu)
#  - sens ............. "rtl" pour les langues qui s'écrivent de droite à gauche
#  - modele_titre ..... le titre que voit Google, fabriqué à partir du nom de
#                       la carte. Écrit une fois par langue plutôt que 7 fois.
#  - modele_titre_categorie  idem pour les pages de rubrique, qui ne sont pas
#                       des cartes mais des sommaires
#  - modele_description  idem pour la phrase de résumé
#  - variantes ........ les libellés du bouton « dollars / parité de pouvoir
#                       d'achat », les mêmes pour toutes les familles
#  - slug ............. l'adresse de la page. Traduite quand la langue s'écrit
#                       en alphabet latin ; en anglais pour le japonais, le
#                       coréen, l'hindi et l'arabe, où une adresse en écriture
#                       native deviendrait illisible une fois encodée par le
#                       navigateur (%E4%B8%80%E4%BA%BA...), et où « GDP » est
#                       de toute façon la forme employée couramment.
#  - nom .............. le nom de la carte, pour le titre et la vignette
#  - nav / nav_court .. les deux libellés du menu du haut (large / téléphone)
#  - texte ............ la phrase de la vignette, reprise en tête de la
#                       description que lit Google
# ==========================================================================

LANGUES = []
# -------------------------------------------------------------- Français ---
LANGUES.append({
    "code": "fr", "dossier": "", "hreflang": "fr", "sens": "ltr",
    "drapeau": "🇫🇷", "nom": "Français", "nav_aria": "Cartes",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Langue", "theme_label": "Changer de thème",
    "theme_clair": "Passer en thème clair", "theme_sombre": "Passer en thème sombre",
    "variantes_label": "Unité",
    "modele_titre": "{nom}, par pays — carte mondiale interactive | StatsMaps",
    "modele_titre_categorie": "{nom} — toutes les cartes | StatsMaps",
    "modele_description": (
        "{texte} Carte interactive de 197 pays, de 1980 à 2031, à partir des données officielles du FMI (World Economic Outlook) : classement mondial et évolution année par année."),
    "accueil": {
        "titre": "StatsMaps — cartes et statistiques mondiales",
        "description": "Cartes interactives des statistiques mondiales : PIB, PIB par habitant, croissance, inflation et population de 197 pays, de 1980 à 2031, à partir des données officielles du FMI.",
        "h1": "Les statistiques du monde, en cartes.",
        "intro": "StatsMaps met en carte les grands indicateurs mondiaux à partir de sources officielles. Choisis une catégorie pour voir les cartes qu’elle contient : aujourd’hui l’économie et la démographie, à partir des données du Fonds monétaire international — 197 pays, de 1980 à 2031.",
        "bientot": "Bientôt : infrastructures, énergie, éducation et santé.",
        "pied": "Données : FMI (World Economic Outlook) · Fond de carte : Natural Earth · Site sans publicité ni traceur.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Parité de pouvoir d’achat"},
    "categories": {
        "economie": {
            "slug": "economie",
            "nom": "Économie",
            "texte": "Le PIB, la richesse par habitant, la croissance et l’inflation.",
            "h1": "L’économie mondiale, en cartes.",
            "intro": "Quatre cartes tirées du World Economic Outlook du Fonds monétaire international : 197 pays, de 1980 à 2031, projections comprises.",
        },
        "demographie": {
            "slug": "demographie",
            "nom": "Démographie",
            "texte": "Le nombre d’habitants de chaque pays, année par année.",
            "h1": "La démographie mondiale, en cartes.",
            "intro": "Le FMI publie aussi la population de chaque pays : 197 pays, de 1980 à 2031, projections comprises.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pib-nominal",
            "nom": "PIB",
            "nav": "PIB", "nav_court": "PIB",
            "texte": "La taille de chaque économie, en milliards de dollars courants.",
        },
        "pib-ppa": {
            "slug": "pib-ppa",
            "nom": "PIB en parité de pouvoir d’achat",
            "nav": "PIB (PPA)", "nav_court": "PIB PPA",
            "texte": "La taille de chaque économie une fois le coût de la vie corrigé, en dollars internationaux.",
        },
        "pib-par-habitant": {
            "slug": "pib-par-habitant",
            "nom": "PIB par habitant",
            "nav": "PIB par habitant", "nav_court": "PIB/hab.",
            "texte": "La richesse produite par personne, en dollars courants.",
        },
        "pib-par-habitant-ppa": {
            "slug": "pib-par-habitant-ppa",
            "nom": "PIB par habitant en parité de pouvoir d’achat",
            "nav": "PIB par habitant (PPA)", "nav_court": "PIB/hab. PPA",
            "texte": "La richesse produite par personne une fois le coût de la vie corrigé, en dollars internationaux.",
        },
        "croissance": {
            "slug": "croissance",
            "nom": "Croissance du PIB",
            "nav": "Croissance", "nav_court": "Croissance",
            "texte": "L’évolution du PIB réel d’une année sur l’autre, en pourcentage.",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "Inflation",
            "nav": "Inflation", "nav_court": "Inflation",
            "texte": "La hausse des prix à la consommation d’une année sur l’autre, en pourcentage.",
        },
        "population": {
            "slug": "population",
            "nom": "Population",
            "nav": "Population", "nav_court": "Population",
            "texte": "Le nombre d’habitants de chaque pays, en millions.",
        },
    },
})

# --------------------------------------------------------------- English ---
LANGUES.append({
    "code": "en", "dossier": "en", "hreflang": "en", "sens": "ltr",
    "drapeau": "🇬🇧", "nom": "English", "nav_aria": "Maps",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Language", "theme_label": "Switch theme",
    "theme_clair": "Switch to light theme", "theme_sombre": "Switch to dark theme",
    "variantes_label": "Unit",
    "modele_titre": "{nom} by country — interactive world map | StatsMaps",
    "modele_titre_categorie": "{nom} — all the maps | StatsMaps",
    "modele_description": (
        "{texte} An interactive map of 197 countries, from 1980 to 2031, built on official IMF data (World Economic Outlook): world ranking and year-by-year change."),
    "accueil": {
        "titre": "StatsMaps — world maps and statistics",
        "description": "Interactive maps of world statistics: GDP, GDP per capita, growth, inflation and population for 197 countries, from 1980 to 2031, from official IMF data.",
        "h1": "The world’s statistics, mapped.",
        "intro": "StatsMaps turns major global indicators into interactive maps, using official sources. Pick a category to see the maps inside it: for now the economy and demographics, based on International Monetary Fund data — 197 countries, from 1980 to 2031.",
        "bientot": "Coming soon: infrastructure, energy, education and health.",
        "pied": "Data: IMF (World Economic Outlook) · Basemap: Natural Earth · No ads, no trackers.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Purchasing power parity"},
    "categories": {
        "economie": {
            "slug": "economy",
            "nom": "Economy",
            "texte": "GDP, wealth per person, growth and inflation.",
            "h1": "The world economy, mapped.",
            "intro": "Four maps drawn from the International Monetary Fund’s World Economic Outlook: 197 countries, from 1980 to 2031, projections included.",
        },
        "demographie": {
            "slug": "demographics",
            "nom": "Demographics",
            "texte": "How many people live in each country, year by year.",
            "h1": "World demographics, mapped.",
            "intro": "The IMF also publishes each country’s population: 197 countries, from 1980 to 2031, projections included.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "gdp",
            "nom": "GDP",
            "nav": "GDP", "nav_court": "GDP",
            "texte": "The size of each economy, in billions of current US dollars.",
        },
        "pib-ppa": {
            "slug": "gdp-ppp",
            "nom": "GDP at purchasing power parity",
            "nav": "GDP (PPP)", "nav_court": "GDP PPP",
            "texte": "The size of each economy once the cost of living is taken into account, in international dollars.",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "nom": "GDP per capita",
            "nav": "GDP per capita", "nav_court": "GDP/cap.",
            "texte": "Wealth produced per person, in current US dollars.",
        },
        "pib-par-habitant-ppa": {
            "slug": "gdp-per-capita-ppp",
            "nom": "GDP per capita at purchasing power parity",
            "nav": "GDP per capita (PPP)", "nav_court": "GDP/cap. PPP",
            "texte": "Wealth produced per person once the cost of living is taken into account, in international dollars.",
        },
        "croissance": {
            "slug": "growth",
            "nom": "GDP growth",
            "nav": "Growth", "nav_court": "Growth",
            "texte": "Year-on-year change in real GDP, as a percentage.",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "Inflation",
            "nav": "Inflation", "nav_court": "Inflation",
            "texte": "Year-on-year rise in consumer prices, as a percentage.",
        },
        "population": {
            "slug": "population",
            "nom": "Population",
            "nav": "Population", "nav_court": "Population",
            "texte": "How many people live in each country, in millions.",
        },
    },
})

# ------------------------------------------------------------ Українська ---
LANGUES.append({
    "code": "uk", "dossier": "ua", "hreflang": "uk", "sens": "ltr",
    "drapeau": "🇺🇦", "nom": "Українська", "nav_aria": "Карти",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Мова", "theme_label": "Змінити тему",
    "theme_clair": "Перейти на світлу тему", "theme_sombre": "Перейти на темну тему",
    "variantes_label": "Одиниця",
    "modele_titre": "{nom} за країнами — інтерактивна карта світу | StatsMaps",
    "modele_titre_categorie": "{nom} — усі карти | StatsMaps",
    "modele_description": (
        "{texte} Інтерактивна карта 197 країн, від 1980 до 2031 року, за офіційними даними МВФ (World Economic Outlook): світовий рейтинг і зміни рік за роком."),
    "accueil": {
        "titre": "StatsMaps — карти та світова статистика",
        "description": "Інтерактивні карти світової статистики: ВВП, ВВП на душу населення, зростання, інфляція та населення 197 країн, від 1980 до 2031 року, за офіційними даними МВФ.",
        "h1": "Статистика світу — на картах.",
        "intro": "StatsMaps перетворює головні світові показники на інтерактивні карти, спираючись на офіційні джерела. Оберіть категорію, щоб побачити її карти: сьогодні це економіка та демографія, за даними Міжнародного валютного фонду — 197 країн, від 1980 до 2031 року.",
        "bientot": "Незабаром: інфраструктура, енергетика, освіта та охорона здоров’я.",
        "pied": "Дані: МВФ (World Economic Outlook) · Основа карти: Natural Earth · Без реклами та стеження.",
    },
    "variantes": {"nominal": "Номінальний", "ppa": "Паритет купівельної спроможності"},
    "categories": {
        "economie": {
            "slug": "ekonomika",
            "nom": "Економіка",
            "texte": "ВВП, багатство на особу, зростання та інфляція.",
            "h1": "Світова економіка на картах.",
            "intro": "Чотири карти зі звіту World Economic Outlook Міжнародного валютного фонду: 197 країн, від 1980 до 2031 року, разом із прогнозами.",
        },
        "demographie": {
            "slug": "demohrafiia",
            "nom": "Демографія",
            "texte": "Скільки людей живе в кожній країні, рік за роком.",
            "h1": "Світова демографія на картах.",
            "intro": "МВФ публікує також населення кожної країни: 197 країн, від 1980 до 2031 року, разом із прогнозами.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "vvp",
            "nom": "ВВП",
            "nav": "ВВП", "nav_court": "ВВП",
            "texte": "Розмір кожної економіки, у мільярдах доларів у поточних цінах.",
        },
        "pib-ppa": {
            "slug": "vvp-pks",
            "nom": "ВВП за паритетом купівельної спроможності",
            "nav": "ВВП (ПКС)", "nav_court": "ВВП ПКС",
            "texte": "Розмір кожної економіки з урахуванням вартості життя, у міжнародних доларах.",
        },
        "pib-par-habitant": {
            "slug": "vvp-na-osobu",
            "nom": "ВВП на душу населення",
            "nav": "ВВП на душу населення", "nav_court": "ВВП/особу",
            "texte": "Багатство, вироблене на одну особу, у доларах у поточних цінах.",
        },
        "pib-par-habitant-ppa": {
            "slug": "vvp-na-osobu-pks",
            "nom": "ВВП на душу населення за ПКС",
            "nav": "ВВП на душу населення (ПКС)", "nav_court": "ВВП/особу ПКС",
            "texte": "Багатство, вироблене на одну особу з урахуванням вартості життя, у міжнародних доларах.",
        },
        "croissance": {
            "slug": "zrostannia",
            "nom": "Зростання ВВП",
            "nav": "Зростання", "nav_court": "Зростання",
            "texte": "Зміна реального ВВП рік до року, у відсотках.",
        },
        "inflation": {
            "slug": "infliatsiia",
            "nom": "Інфляція",
            "nav": "Інфляція", "nav_court": "Інфляція",
            "texte": "Зростання споживчих цін рік до року, у відсотках.",
        },
        "population": {
            "slug": "naselennia",
            "nom": "Населення",
            "nav": "Населення", "nav_court": "Населення",
            "texte": "Кількість жителів кожної країни, у мільйонах.",
        },
    },
})

# --------------------------------------------------------------- Deutsch ---
LANGUES.append({
    "code": "de", "dossier": "de", "hreflang": "de", "sens": "ltr",
    "drapeau": "🇩🇪", "nom": "Deutsch", "nav_aria": "Karten",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Sprache", "theme_label": "Thema wechseln",
    "theme_clair": "Zum hellen Thema wechseln", "theme_sombre": "Zum dunklen Thema wechseln",
    "variantes_label": "Einheit",
    "modele_titre": "{nom} nach Ländern — interaktive Weltkarte | StatsMaps",
    "modele_titre_categorie": "{nom} — alle Karten | StatsMaps",
    "modele_description": (
        "{texte} Eine interaktive Karte mit 197 Ländern, von 1980 bis 2031, auf Grundlage offizieller IWF-Daten (World Economic Outlook): Weltrangliste und Entwicklung Jahr für Jahr."),
    "accueil": {
        "titre": "StatsMaps — Weltkarten und Statistiken",
        "description": "Interaktive Karten der Weltstatistik: BIP, BIP pro Kopf, Wachstum, Inflation und Bevölkerung von 197 Ländern, von 1980 bis 2031, nach offiziellen IWF-Daten.",
        "h1": "Die Statistiken der Welt, als Karte.",
        "intro": "StatsMaps bringt die großen weltweiten Kennzahlen auf interaktive Karten, aus offiziellen Quellen. Wähle eine Rubrik, um ihre Karten zu sehen: heute die Wirtschaft und die Bevölkerung, nach Daten des Internationalen Währungsfonds — 197 Länder, von 1980 bis 2031.",
        "bientot": "Demnächst: Infrastruktur, Energie, Bildung und Gesundheit.",
        "pied": "Daten: IWF (World Economic Outlook) · Kartengrundlage: Natural Earth · Ohne Werbung, ohne Tracker.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Kaufkraftparität"},
    "categories": {
        "economie": {
            "slug": "wirtschaft",
            "nom": "Wirtschaft",
            "texte": "BIP, Wohlstand pro Kopf, Wachstum und Inflation.",
            "h1": "Die Weltwirtschaft, als Karte.",
            "intro": "Vier Karten aus dem World Economic Outlook des Internationalen Währungsfonds: 197 Länder, von 1980 bis 2031, Prognosen inbegriffen.",
        },
        "demographie": {
            "slug": "demografie",
            "nom": "Demografie",
            "texte": "Wie viele Menschen in jedem Land leben, Jahr für Jahr.",
            "h1": "Die Bevölkerung der Welt, als Karte.",
            "intro": "Der IWF veröffentlicht auch die Bevölkerung jedes Landes: 197 Länder, von 1980 bis 2031, Prognosen inbegriffen.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominales-bip",
            "nom": "BIP",
            "nav": "BIP", "nav_court": "BIP",
            "texte": "Die Größe jeder Volkswirtschaft, in Milliarden US-Dollar zu jeweiligen Preisen.",
        },
        "pib-ppa": {
            "slug": "bip-kkp",
            "nom": "BIP zu Kaufkraftparität",
            "nav": "BIP (KKP)", "nav_court": "BIP KKP",
            "texte": "Die Größe jeder Volkswirtschaft, um die Lebenshaltungskosten bereinigt, in internationalen Dollar.",
        },
        "pib-par-habitant": {
            "slug": "bip-pro-kopf",
            "nom": "BIP pro Kopf",
            "nav": "BIP pro Kopf", "nav_court": "BIP/Kopf",
            "texte": "Die je Person erwirtschaftete Leistung, in US-Dollar zu jeweiligen Preisen.",
        },
        "pib-par-habitant-ppa": {
            "slug": "bip-pro-kopf-kkp",
            "nom": "BIP pro Kopf zu Kaufkraftparität",
            "nav": "BIP pro Kopf (KKP)", "nav_court": "BIP/Kopf KKP",
            "texte": "Die je Person erwirtschaftete Leistung, um die Lebenshaltungskosten bereinigt, in internationalen Dollar.",
        },
        "croissance": {
            "slug": "bip-wachstum",
            "nom": "BIP-Wachstum",
            "nav": "Wachstum", "nav_court": "Wachstum",
            "texte": "Die Veränderung des realen BIP von Jahr zu Jahr, in Prozent.",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "Inflation",
            "nav": "Inflation", "nav_court": "Inflation",
            "texte": "Der Anstieg der Verbraucherpreise von Jahr zu Jahr, in Prozent.",
        },
        "population": {
            "slug": "bevoelkerung",
            "nom": "Bevölkerung",
            "nav": "Bevölkerung", "nav_court": "Bevölkerung",
            "texte": "Wie viele Menschen in jedem Land leben, in Millionen.",
        },
    },
})

# --------------------------------------------------------------- Español ---
LANGUES.append({
    "code": "es", "dossier": "es", "hreflang": "es", "sens": "ltr",
    "drapeau": "🇪🇸", "nom": "Español", "nav_aria": "Mapas",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Idioma", "theme_label": "Cambiar de tema",
    "theme_clair": "Cambiar al tema claro", "theme_sombre": "Cambiar al tema oscuro",
    "variantes_label": "Unidad",
    "modele_titre": "{nom} por país — mapa mundial interactivo | StatsMaps",
    "modele_titre_categorie": "{nom} — todos los mapas | StatsMaps",
    "modele_description": (
        "{texte} Mapa interactivo de 197 países, de 1980 a 2031, con datos oficiales del FMI (World Economic Outlook): clasificación mundial y evolución año a año."),
    "accueil": {
        "titre": "StatsMaps — mapas y estadísticas mundiales",
        "description": "Mapas interactivos de las estadísticas mundiales: PIB, PIB per cápita, crecimiento, inflación y población de 197 países, de 1980 a 2031, con datos oficiales del FMI.",
        "h1": "Las estadísticas del mundo, en mapas.",
        "intro": "StatsMaps lleva los grandes indicadores mundiales a mapas interactivos, a partir de fuentes oficiales. Elige una categoría para ver sus mapas: hoy la economía y la demografía, con datos del Fondo Monetario Internacional — 197 países, de 1980 a 2031.",
        "bientot": "Próximamente: infraestructuras, energía, educación y salud.",
        "pied": "Datos: FMI (World Economic Outlook) · Mapa base: Natural Earth · Sin publicidad ni rastreadores.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Paridad de poder adquisitivo"},
    "categories": {
        "economie": {
            "slug": "economia",
            "nom": "Economía",
            "texte": "El PIB, la riqueza por habitante, el crecimiento y la inflación.",
            "h1": "La economía mundial, en mapas.",
            "intro": "Cuatro mapas extraídos del World Economic Outlook del Fondo Monetario Internacional: 197 países, de 1980 a 2031, proyecciones incluidas.",
        },
        "demographie": {
            "slug": "demografia",
            "nom": "Demografía",
            "texte": "Cuántas personas viven en cada país, año a año.",
            "h1": "La demografía mundial, en mapas.",
            "intro": "El FMI también publica la población de cada país: 197 países, de 1980 a 2031, proyecciones incluidas.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pib-nominal",
            "nom": "PIB",
            "nav": "PIB", "nav_court": "PIB",
            "texte": "El tamaño de cada economía, en miles de millones de dólares corrientes.",
        },
        "pib-ppa": {
            "slug": "pib-ppa",
            "nom": "PIB en paridad de poder adquisitivo",
            "nav": "PIB (PPA)", "nav_court": "PIB PPA",
            "texte": "El tamaño de cada economía una vez corregido el coste de la vida, en dólares internacionales.",
        },
        "pib-par-habitant": {
            "slug": "pib-per-capita",
            "nom": "PIB per cápita",
            "nav": "PIB per cápita", "nav_court": "PIB/hab.",
            "texte": "La riqueza producida por persona, en dólares corrientes.",
        },
        "pib-par-habitant-ppa": {
            "slug": "pib-per-capita-ppa",
            "nom": "PIB per cápita en paridad de poder adquisitivo",
            "nav": "PIB per cápita (PPA)", "nav_court": "PIB/hab. PPA",
            "texte": "La riqueza producida por persona una vez corregido el coste de la vida, en dólares internacionales.",
        },
        "croissance": {
            "slug": "crecimiento-pib",
            "nom": "Crecimiento del PIB",
            "nav": "Crecimiento", "nav_court": "Crecimiento",
            "texte": "La variación del PIB real de un año a otro, en porcentaje.",
        },
        "inflation": {
            "slug": "inflacion",
            "nom": "Inflación",
            "nav": "Inflación", "nav_court": "Inflación",
            "texte": "La subida de los precios al consumo de un año a otro, en porcentaje.",
        },
        "population": {
            "slug": "poblacion",
            "nom": "Población",
            "nav": "Población", "nav_court": "Población",
            "texte": "Cuántas personas viven en cada país, en millones.",
        },
    },
})

# -------------------------------------------------------------- Italiano ---
LANGUES.append({
    "code": "it", "dossier": "it", "hreflang": "it", "sens": "ltr",
    "drapeau": "🇮🇹", "nom": "Italiano", "nav_aria": "Mappe",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Lingua", "theme_label": "Cambia tema",
    "theme_clair": "Passa al tema chiaro", "theme_sombre": "Passa al tema scuro",
    "variantes_label": "Unità",
    "modele_titre": "{nom} per paese — mappa mondiale interattiva | StatsMaps",
    "modele_titre_categorie": "{nom} — tutte le mappe | StatsMaps",
    "modele_description": (
        "{texte} Mappa interattiva di 197 paesi, dal 1980 al 2031, con i dati ufficiali del FMI (World Economic Outlook): classifica mondiale ed evoluzione anno per anno."),
    "accueil": {
        "titre": "StatsMaps — mappe e statistiche mondiali",
        "description": "Mappe interattive delle statistiche mondiali: PIL, PIL pro capite, crescita, inflazione e popolazione di 197 paesi, dal 1980 al 2031, con i dati ufficiali del FMI.",
        "h1": "Le statistiche del mondo, in mappa.",
        "intro": "StatsMaps trasforma i grandi indicatori mondiali in mappe interattive, a partire da fonti ufficiali. Scegli una categoria per vedere le sue mappe: oggi l’economia e la demografia, con i dati del Fondo monetario internazionale — 197 paesi, dal 1980 al 2031.",
        "bientot": "Prossimamente: infrastrutture, energia, istruzione e sanità.",
        "pied": "Dati: FMI (World Economic Outlook) · Mappa di base: Natural Earth · Senza pubblicità né tracciamento.",
    },
    "variantes": {"nominal": "Nominale", "ppa": "Parità di potere d’acquisto"},
    "categories": {
        "economie": {
            "slug": "economia",
            "nom": "Economia",
            "texte": "Il PIL, la ricchezza per abitante, la crescita e l’inflazione.",
            "h1": "L’economia mondiale, in mappa.",
            "intro": "Quattro mappe tratte dal World Economic Outlook del Fondo monetario internazionale: 197 paesi, dal 1980 al 2031, proiezioni comprese.",
        },
        "demographie": {
            "slug": "demografia",
            "nom": "Demografia",
            "texte": "Quante persone vivono in ogni paese, anno per anno.",
            "h1": "La demografia mondiale, in mappa.",
            "intro": "Il FMI pubblica anche la popolazione di ogni paese: 197 paesi, dal 1980 al 2031, proiezioni comprese.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pil-nominale",
            "nom": "PIL",
            "nav": "PIL", "nav_court": "PIL",
            "texte": "La dimensione di ogni economia, in miliardi di dollari correnti.",
        },
        "pib-ppa": {
            "slug": "pil-ppa",
            "nom": "PIL a parità di potere d’acquisto",
            "nav": "PIL (PPA)", "nav_court": "PIL PPA",
            "texte": "La dimensione di ogni economia una volta corretto il costo della vita, in dollari internazionali.",
        },
        "pib-par-habitant": {
            "slug": "pil-pro-capite",
            "nom": "PIL pro capite",
            "nav": "PIL pro capite", "nav_court": "PIL/ab.",
            "texte": "La ricchezza prodotta per persona, in dollari correnti.",
        },
        "pib-par-habitant-ppa": {
            "slug": "pil-pro-capite-ppa",
            "nom": "PIL pro capite a parità di potere d’acquisto",
            "nav": "PIL pro capite (PPA)", "nav_court": "PIL/ab. PPA",
            "texte": "La ricchezza prodotta per persona una volta corretto il costo della vita, in dollari internazionali.",
        },
        "croissance": {
            "slug": "crescita-pil",
            "nom": "Crescita del PIL",
            "nav": "Crescita", "nav_court": "Crescita",
            "texte": "La variazione del PIL reale da un anno all’altro, in percentuale.",
        },
        "inflation": {
            "slug": "inflazione",
            "nom": "Inflazione",
            "nav": "Inflazione", "nav_court": "Inflazione",
            "texte": "L’aumento dei prezzi al consumo da un anno all’altro, in percentuale.",
        },
        "population": {
            "slug": "popolazione",
            "nom": "Popolazione",
            "nav": "Popolazione", "nav_court": "Popolazione",
            "texte": "Quante persone vivono in ogni paese, in milioni.",
        },
    },
})

# ------------------------------------------------------------- Português ---
LANGUES.append({
    "code": "pt", "dossier": "pt", "hreflang": "pt", "sens": "ltr",
    "drapeau": "🇵🇹", "nom": "Português", "nav_aria": "Mapas",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Idioma", "theme_label": "Mudar de tema",
    "theme_clair": "Mudar para o tema claro", "theme_sombre": "Mudar para o tema escuro",
    "variantes_label": "Unidade",
    "modele_titre": "{nom} por país — mapa mundial interativo | StatsMaps",
    "modele_titre_categorie": "{nom} — todos os mapas | StatsMaps",
    "modele_description": (
        "{texte} Mapa interativo de 197 países, de 1980 a 2031, com dados oficiais do FMI (World Economic Outlook): classificação mundial e evolução ano a ano."),
    "accueil": {
        "titre": "StatsMaps — mapas e estatísticas mundiais",
        "description": "Mapas interativos das estatísticas mundiais: PIB, PIB per capita, crescimento, inflação e população de 197 países, de 1980 a 2031, com dados oficiais do FMI.",
        "h1": "As estatísticas do mundo, em mapas.",
        "intro": "O StatsMaps transforma os grandes indicadores mundiais em mapas interativos, a partir de fontes oficiais. Escolhe uma categoria para ver os seus mapas: hoje a economia e a demografia, com dados do Fundo Monetário Internacional — 197 países, de 1980 a 2031.",
        "bientot": "Em breve: infraestruturas, energia, educação e saúde.",
        "pied": "Dados: FMI (World Economic Outlook) · Mapa base: Natural Earth · Sem publicidade nem rastreadores.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Paridade de poder de compra"},
    "categories": {
        "economie": {
            "slug": "economia",
            "nom": "Economia",
            "texte": "O PIB, a riqueza por habitante, o crescimento e a inflação.",
            "h1": "A economia mundial, em mapas.",
            "intro": "Quatro mapas retirados do World Economic Outlook do Fundo Monetário Internacional: 197 países, de 1980 a 2031, projeções incluídas.",
        },
        "demographie": {
            "slug": "demografia",
            "nom": "Demografia",
            "texte": "Quantas pessoas vivem em cada país, ano a ano.",
            "h1": "A demografia mundial, em mapas.",
            "intro": "O FMI publica também a população de cada país: 197 países, de 1980 a 2031, projeções incluídas.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pib-nominal",
            "nom": "PIB",
            "nav": "PIB", "nav_court": "PIB",
            "texte": "O tamanho de cada economia, em mil milhões de dólares correntes.",
        },
        "pib-ppa": {
            "slug": "pib-ppc",
            "nom": "PIB em paridade de poder de compra",
            "nav": "PIB (PPC)", "nav_court": "PIB PPC",
            "texte": "O tamanho de cada economia depois de corrigido o custo de vida, em dólares internacionais.",
        },
        "pib-par-habitant": {
            "slug": "pib-per-capita",
            "nom": "PIB per capita",
            "nav": "PIB per capita", "nav_court": "PIB/hab.",
            "texte": "A riqueza produzida por pessoa, em dólares correntes.",
        },
        "pib-par-habitant-ppa": {
            "slug": "pib-per-capita-ppc",
            "nom": "PIB per capita em paridade de poder de compra",
            "nav": "PIB per capita (PPC)", "nav_court": "PIB/hab. PPC",
            "texte": "A riqueza produzida por pessoa depois de corrigido o custo de vida, em dólares internacionais.",
        },
        "croissance": {
            "slug": "crescimento-pib",
            "nom": "Crescimento do PIB",
            "nav": "Crescimento", "nav_court": "Crescimento",
            "texte": "A variação do PIB real de um ano para o outro, em percentagem.",
        },
        "inflation": {
            "slug": "inflacao",
            "nom": "Inflação",
            "nav": "Inflação", "nav_court": "Inflação",
            "texte": "A subida dos preços no consumidor de um ano para o outro, em percentagem.",
        },
        "population": {
            "slug": "populacao",
            "nom": "População",
            "nav": "População", "nav_court": "População",
            "texte": "Quantas pessoas vivem em cada país, em milhões.",
        },
    },
})

# ---------------------------------------------------------------- Polski ---
LANGUES.append({
    "code": "pl", "dossier": "pl", "hreflang": "pl", "sens": "ltr",
    "drapeau": "🇵🇱", "nom": "Polski", "nav_aria": "Mapy",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Język", "theme_label": "Zmień motyw",
    "theme_clair": "Przełącz na jasny motyw", "theme_sombre": "Przełącz na ciemny motyw",
    "variantes_label": "Jednostka",
    "modele_titre": "{nom} według krajów — interaktywna mapa świata | StatsMaps",
    "modele_titre_categorie": "{nom} — wszystkie mapy | StatsMaps",
    "modele_description": (
        "{texte} Interaktywna mapa 197 krajów, od 1980 do 2031 roku, na oficjalnych danych MFW (World Economic Outlook): ranking światowy i zmiany rok po roku."),
    "accueil": {
        "titre": "StatsMaps — mapy i statystyki świata",
        "description": "Interaktywne mapy statystyk świata: PKB, PKB na mieszkańca, wzrost, inflacja i ludność 197 krajów, od 1980 do 2031 roku, na oficjalnych danych MFW.",
        "h1": "Statystyki świata na mapach.",
        "intro": "StatsMaps przedstawia najważniejsze światowe wskaźniki na interaktywnych mapach, w oparciu o oficjalne źródła. Wybierz kategorię, aby zobaczyć jej mapy: dziś gospodarka i demografia, na danych Międzynarodowego Funduszu Walutowego — 197 krajów, od 1980 do 2031 roku.",
        "bientot": "Wkrótce: infrastruktura, energetyka, edukacja i zdrowie.",
        "pied": "Dane: MFW (World Economic Outlook) · Podkład mapowy: Natural Earth · Bez reklam i śledzenia.",
    },
    "variantes": {"nominal": "Nominalne", "ppa": "Parytet siły nabywczej"},
    "categories": {
        "economie": {
            "slug": "gospodarka",
            "nom": "Gospodarka",
            "texte": "PKB, bogactwo na mieszkańca, wzrost i inflacja.",
            "h1": "Gospodarka świata na mapach.",
            "intro": "Cztery mapy z raportu World Economic Outlook Międzynarodowego Funduszu Walutowego: 197 krajów, od 1980 do 2031 roku, wraz z prognozami.",
        },
        "demographie": {
            "slug": "demografia",
            "nom": "Demografia",
            "texte": "Ilu ludzi mieszka w każdym kraju, rok po roku.",
            "h1": "Demografia świata na mapach.",
            "intro": "MFW publikuje także liczbę ludności każdego kraju: 197 krajów, od 1980 do 2031 roku, wraz z prognozami.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pkb-nominalne",
            "nom": "PKB",
            "nav": "PKB", "nav_court": "PKB",
            "texte": "Wielkość każdej gospodarki, w miliardach dolarów bieżących.",
        },
        "pib-ppa": {
            "slug": "pkb-psn",
            "nom": "PKB według parytetu siły nabywczej",
            "nav": "PKB (PSN)", "nav_court": "PKB PSN",
            "texte": "Wielkość każdej gospodarki po uwzględnieniu kosztów życia, w dolarach międzynarodowych.",
        },
        "pib-par-habitant": {
            "slug": "pkb-na-mieszkanca",
            "nom": "PKB na mieszkańca",
            "nav": "PKB na mieszkańca", "nav_court": "PKB/mieszk.",
            "texte": "Bogactwo wytworzone na osobę, w dolarach bieżących.",
        },
        "pib-par-habitant-ppa": {
            "slug": "pkb-na-mieszkanca-psn",
            "nom": "PKB na mieszkańca według parytetu siły nabywczej",
            "nav": "PKB na mieszkańca (PSN)", "nav_court": "PKB/mieszk. PSN",
            "texte": "Bogactwo wytworzone na osobę po uwzględnieniu kosztów życia, w dolarach międzynarodowych.",
        },
        "croissance": {
            "slug": "wzrost-pkb",
            "nom": "Wzrost PKB",
            "nav": "Wzrost", "nav_court": "Wzrost",
            "texte": "Zmiana realnego PKB z roku na rok, w procentach.",
        },
        "inflation": {
            "slug": "inflacja",
            "nom": "Inflacja",
            "nav": "Inflacja", "nav_court": "Inflacja",
            "texte": "Wzrost cen konsumpcyjnych z roku na rok, w procentach.",
        },
        "population": {
            "slug": "ludnosc",
            "nom": "Ludność",
            "nav": "Ludność", "nav_court": "Ludność",
            "texte": "Ilu ludzi mieszka w każdym kraju, w milionach.",
        },
    },
})

# ------------------------------------------------------------------- 日本語 ---
LANGUES.append({
    "code": "ja", "dossier": "ja", "hreflang": "ja", "sens": "ltr",
    "drapeau": "🇯🇵", "nom": "日本語", "nav_aria": "地図",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "言語", "theme_label": "テーマを切り替える",
    "theme_clair": "ライトテーマにする", "theme_sombre": "ダークテーマにする",
    "variantes_label": "単位",
    "modele_titre": "国別の{nom} — インタラクティブ世界地図 | StatsMaps",
    "modele_titre_categorie": "{nom} — 地図の一覧 | StatsMaps",
    "modele_description": (
        "{texte} 1980年から2031年まで、197か国のインタラクティブ地図。IMFの公式データ（World Economic Outlook）による世界ランキングと年ごとの推移。"),
    "accueil": {
        "titre": "StatsMaps — 世界の地図と統計",
        "description": "世界の統計をインタラクティブ地図で。197か国のGDP、一人当たりGDP、成長率、インフレ率、人口を、1980年から2031年まで。IMFの公式データによる。",
        "h1": "世界の統計を、地図で。",
        "intro": "StatsMapsは、公式統計をもとに世界の主要な指標を地図にします。カテゴリーを選ぶと、その地図が並びます。今日は経済と人口統計。国際通貨基金（IMF）のデータで、197か国、1980年から2031年まで。",
        "bientot": "近日公開：インフラ、エネルギー、教育、保健。",
        "pied": "データ：IMF（World Economic Outlook）· 地図：Natural Earth · 広告なし、追跡なし。",
    },
    "variantes": {"nominal": "名目", "ppa": "購買力平価"},
    "categories": {
        "economie": {
            "slug": "economy",
            "nom": "経済",
            "texte": "GDP、一人当たりの豊かさ、成長率、インフレ率。",
            "h1": "世界の経済を、地図で。",
            "intro": "国際通貨基金（IMF）のWorld Economic Outlookによる4つの地図。197か国、1980年から2031年まで、予測を含みます。",
        },
        "demographie": {
            "slug": "demographics",
            "nom": "人口統計",
            "texte": "各国に暮らす人の数を、年ごとに。",
            "h1": "世界の人口を、地図で。",
            "intro": "IMFは各国の人口も公表しています。197か国、1980年から2031年まで、予測を含みます。",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "nom": "GDP",
            "nav": "GDP", "nav_court": "GDP",
            "texte": "各国経済の規模を、名目の十億ドルで。",
        },
        "pib-ppa": {
            "slug": "gdp-ppp",
            "nom": "購買力平価GDP",
            "nav": "GDP（PPP）", "nav_court": "GDP PPP",
            "texte": "物価水準を補正した各国経済の規模を、国際ドルで。",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "nom": "一人当たりGDP",
            "nav": "一人当たりGDP", "nav_court": "GDP/人",
            "texte": "一人あたりが生み出す富を、名目ドルで。",
        },
        "pib-par-habitant-ppa": {
            "slug": "gdp-per-capita-ppp",
            "nom": "購買力平価の一人当たりGDP",
            "nav": "一人当たりGDP（PPP）", "nav_court": "GDP/人 PPP",
            "texte": "物価水準を補正した一人あたりの富を、国際ドルで。",
        },
        "croissance": {
            "slug": "gdp-growth",
            "nom": "GDP成長率",
            "nav": "成長率", "nav_court": "成長率",
            "texte": "実質GDPの前年からの変化を、パーセントで。",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "インフレ率",
            "nav": "インフレ率", "nav_court": "インフレ",
            "texte": "消費者物価の前年からの上昇を、パーセントで。",
        },
        "population": {
            "slug": "population",
            "nom": "人口",
            "nav": "人口", "nav_court": "人口",
            "texte": "各国に暮らす人の数を、百万人単位で。",
        },
    },
})

# ------------------------------------------------------------------- 한국어 ---
LANGUES.append({
    "code": "ko", "dossier": "ko", "hreflang": "ko", "sens": "ltr",
    "drapeau": "🇰🇷", "nom": "한국어", "nav_aria": "지도",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "언어", "theme_label": "테마 바꾸기",
    "theme_clair": "밝은 테마로", "theme_sombre": "어두운 테마로",
    "variantes_label": "단위",
    "modele_titre": "국가별 {nom} — 인터랙티브 세계 지도 | StatsMaps",
    "modele_titre_categorie": "{nom} — 지도 전체 | StatsMaps",
    "modele_description": (
        "{texte} 1980년부터 2031년까지 197개국의 인터랙티브 지도. IMF 공식 자료(World Economic Outlook)에 따른 세계 순위와 연도별 변화."),
    "accueil": {
        "titre": "StatsMaps — 세계 지도와 통계",
        "description": "세계 통계를 인터랙티브 지도로. 197개국의 GDP, 1인당 GDP, 성장률, 물가상승률, 인구를 1980년부터 2031년까지, IMF 공식 자료로.",
        "h1": "세계의 통계를 지도로.",
        "intro": "StatsMaps는 공식 통계를 바탕으로 세계의 주요 지표를 지도로 보여 줍니다. 범주를 고르면 그 안의 지도가 나옵니다. 지금은 경제와 인구 통계. 국제통화기금(IMF) 자료로 197개국, 1980년부터 2031년까지.",
        "bientot": "곧 공개: 인프라, 에너지, 교육, 보건.",
        "pied": "자료: IMF(World Economic Outlook) · 배경 지도: Natural Earth · 광고 없음, 추적 없음.",
    },
    "variantes": {"nominal": "명목", "ppa": "구매력 평가"},
    "categories": {
        "economie": {
            "slug": "economy",
            "nom": "경제",
            "texte": "GDP, 1인당 부, 성장률, 물가상승률.",
            "h1": "세계 경제를 지도로.",
            "intro": "국제통화기금(IMF)의 World Economic Outlook에서 뽑은 네 장의 지도. 197개국, 1980년부터 2031년까지, 전망 포함.",
        },
        "demographie": {
            "slug": "demographics",
            "nom": "인구 통계",
            "texte": "각 나라에 사는 사람 수를 해마다.",
            "h1": "세계 인구를 지도로.",
            "intro": "IMF는 각국의 인구도 발표합니다. 197개국, 1980년부터 2031년까지, 전망 포함.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "nom": "GDP",
            "nav": "GDP", "nav_court": "GDP",
            "texte": "각국 경제의 규모를 경상 십억 달러로.",
        },
        "pib-ppa": {
            "slug": "gdp-ppp",
            "nom": "구매력 평가 GDP",
            "nav": "GDP(PPP)", "nav_court": "GDP PPP",
            "texte": "물가 수준을 반영한 각국 경제의 규모를 국제 달러로.",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "nom": "1인당 GDP",
            "nav": "1인당 GDP", "nav_court": "GDP/인",
            "texte": "한 사람이 만들어 내는 부를 경상 달러로.",
        },
        "pib-par-habitant-ppa": {
            "slug": "gdp-per-capita-ppp",
            "nom": "구매력 평가 1인당 GDP",
            "nav": "1인당 GDP(PPP)", "nav_court": "GDP/인 PPP",
            "texte": "물가 수준을 반영한 1인당 부를 국제 달러로.",
        },
        "croissance": {
            "slug": "gdp-growth",
            "nom": "GDP 성장률",
            "nav": "성장률", "nav_court": "성장률",
            "texte": "실질 GDP의 전년 대비 변화를 백분율로.",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "물가상승률",
            "nav": "물가상승률", "nav_court": "물가",
            "texte": "소비자물가의 전년 대비 상승을 백분율로.",
        },
        "population": {
            "slug": "population",
            "nom": "인구",
            "nav": "인구", "nav_court": "인구",
            "texte": "각 나라에 사는 사람 수를 백만 명 단위로.",
        },
    },
})

# ---------------------------------------------------------------- Türkçe ---
LANGUES.append({
    "code": "tr", "dossier": "tr", "hreflang": "tr", "sens": "ltr",
    "drapeau": "🇹🇷", "nom": "Türkçe", "nav_aria": "Haritalar",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "Dil", "theme_label": "Temayı değiştir",
    "theme_clair": "Açık temaya geç", "theme_sombre": "Koyu temaya geç",
    "variantes_label": "Birim",
    "modele_titre": "Ülkelere göre {nom} — etkileşimli dünya haritası | StatsMaps",
    "modele_titre_categorie": "{nom} — bütün haritalar | StatsMaps",
    "modele_description": (
        "{texte} 1980’den 2031’e 197 ülkenin etkileşimli haritası. IMF’nin resmî verileriyle (World Economic Outlook) dünya sıralaması ve yıldan yıla değişim."),
    "accueil": {
        "titre": "StatsMaps — dünya haritaları ve istatistikler",
        "description": "Dünya istatistiklerinin etkileşimli haritaları: 197 ülkenin GSYİH’si, kişi başına GSYİH’si, büyümesi, enflasyonu ve nüfusu; 1980’den 2031’e, IMF’nin resmî verileriyle.",
        "h1": "Dünyanın istatistikleri, haritada.",
        "intro": "StatsMaps, resmî kaynaklardan yola çıkarak dünyanın büyük göstergelerini haritaya döker. Haritalarını görmek için bir kategori seç: bugün ekonomi ve demografi, Uluslararası Para Fonu verileriyle — 197 ülke, 1980’den 2031’e.",
        "bientot": "Yakında: altyapı, enerji, eğitim ve sağlık.",
        "pied": "Veriler: IMF (World Economic Outlook) · Altlık harita: Natural Earth · Reklamsız, izlemesiz.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Satın alma gücü paritesi"},
    "categories": {
        "economie": {
            "slug": "ekonomi",
            "nom": "Ekonomi",
            "texte": "GSYİH, kişi başına zenginlik, büyüme ve enflasyon.",
            "h1": "Dünya ekonomisi, haritada.",
            "intro": "Uluslararası Para Fonu’nun World Economic Outlook raporundan dört harita: 197 ülke, 1980’den 2031’e, projeksiyonlar dâhil.",
        },
        "demographie": {
            "slug": "demografi",
            "nom": "Demografi",
            "texte": "Her ülkede kaç kişi yaşadığı, yıl yıl.",
            "h1": "Dünya nüfusu, haritada.",
            "intro": "IMF her ülkenin nüfusunu da yayımlıyor: 197 ülke, 1980’den 2031’e, projeksiyonlar dâhil.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gsyih",
            "nom": "GSYİH",
            "nav": "GSYİH", "nav_court": "GSYİH",
            "texte": "Her ekonominin büyüklüğü, cari milyar dolar olarak.",
        },
        "pib-ppa": {
            "slug": "gsyih-sagp",
            "nom": "Satın alma gücü paritesine göre GSYİH",
            "nav": "GSYİH (SAGP)", "nav_court": "GSYİH SAGP",
            "texte": "Hayat pahalılığı düzeltildikten sonra her ekonominin büyüklüğü, uluslararası dolar olarak.",
        },
        "pib-par-habitant": {
            "slug": "kisi-basi-gsyih",
            "nom": "Kişi başına GSYİH",
            "nav": "Kişi başına GSYİH", "nav_court": "GSYİH/kişi",
            "texte": "Kişi başına üretilen zenginlik, cari dolar olarak.",
        },
        "pib-par-habitant-ppa": {
            "slug": "kisi-basi-gsyih-sagp",
            "nom": "Satın alma gücü paritesine göre kişi başına GSYİH",
            "nav": "Kişi başına GSYİH (SAGP)", "nav_court": "GSYİH/kişi SAGP",
            "texte": "Hayat pahalılığı düzeltildikten sonra kişi başına zenginlik, uluslararası dolar olarak.",
        },
        "croissance": {
            "slug": "gsyih-buyumesi",
            "nom": "GSYİH büyümesi",
            "nav": "Büyüme", "nav_court": "Büyüme",
            "texte": "Reel GSYİH’nin yıldan yıla değişimi, yüzde olarak.",
        },
        "inflation": {
            "slug": "enflasyon",
            "nom": "Enflasyon",
            "nav": "Enflasyon", "nav_court": "Enflasyon",
            "texte": "Tüketici fiyatlarının yıldan yıla artışı, yüzde olarak.",
        },
        "population": {
            "slug": "nufus",
            "nom": "Nüfus",
            "nav": "Nüfus", "nav_court": "Nüfus",
            "texte": "Her ülkede kaç kişi yaşadığı, milyon olarak.",
        },
    },
})

# ---------------------------------------------------------------- हिन्दी ---
LANGUES.append({
    "code": "hi", "dossier": "hi", "hreflang": "hi", "sens": "ltr",
    "drapeau": "🇮🇳", "nom": "हिन्दी", "nav_aria": "मानचित्र",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "भाषा", "theme_label": "थीम बदलें",
    "theme_clair": "हल्की थीम पर जाएँ", "theme_sombre": "गहरी थीम पर जाएँ",
    "variantes_label": "इकाई",
    "modele_titre": "देश के अनुसार {nom} — इंटरैक्टिव विश्व मानचित्र | StatsMaps",
    "modele_titre_categorie": "{nom} — सभी मानचित्र | StatsMaps",
    "modele_description": (
        "{texte} 1980 से 2031 तक 197 देशों का इंटरैक्टिव मानचित्र। IMF के आधिकारिक आँकड़ों (World Economic Outlook) पर आधारित विश्व रैंकिंग और वर्ष-दर-वर्ष बदलाव।"),
    "accueil": {
        "titre": "StatsMaps — विश्व मानचित्र और आँकड़े",
        "description": "विश्व के आँकड़ों के इंटरैक्टिव मानचित्र: 197 देशों की जीडीपी, प्रति व्यक्ति जीडीपी, वृद्धि दर, मुद्रास्फीति और जनसंख्या, 1980 से 2031 तक, IMF के आधिकारिक आँकड़ों से।",
        "h1": "दुनिया के आँकड़े, मानचित्र पर।",
        "intro": "StatsMaps आधिकारिक स्रोतों के आधार पर विश्व के प्रमुख संकेतकों को इंटरैक्टिव मानचित्रों में बदलता है। किसी श्रेणी को चुनें और उसके मानचित्र देखें: फ़िलहाल अर्थव्यवस्था और जनसांख्यिकी, अंतर्राष्ट्रीय मुद्रा कोष के आँकड़ों से — 197 देश, 1980 से 2031 तक।",
        "bientot": "जल्द ही: बुनियादी ढाँचा, ऊर्जा, शिक्षा और स्वास्थ्य।",
        "pied": "आँकड़े: IMF (World Economic Outlook) · आधार मानचित्र: Natural Earth · न विज्ञापन, न ट्रैकिंग।",
    },
    "variantes": {"nominal": "नाममात्र", "ppa": "क्रय शक्ति समता"},
    "categories": {
        "economie": {
            "slug": "economy",
            "nom": "अर्थव्यवस्था",
            "texte": "जीडीपी, प्रति व्यक्ति संपत्ति, वृद्धि दर और मुद्रास्फीति।",
            "h1": "दुनिया की अर्थव्यवस्था, मानचित्र पर।",
            "intro": "अंतर्राष्ट्रीय मुद्रा कोष की World Economic Outlook रिपोर्ट से चार मानचित्र: 197 देश, 1980 से 2031 तक, अनुमानों सहित।",
        },
        "demographie": {
            "slug": "demographics",
            "nom": "जनसांख्यिकी",
            "texte": "हर देश में कितने लोग रहते हैं, वर्ष-दर-वर्ष।",
            "h1": "दुनिया की जनसंख्या, मानचित्र पर।",
            "intro": "IMF हर देश की जनसंख्या भी प्रकाशित करता है: 197 देश, 1980 से 2031 तक, अनुमानों सहित।",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "nom": "जीडीपी",
            "nav": "जीडीपी", "nav_court": "जीडीपी",
            "texte": "हर अर्थव्यवस्था का आकार, चालू अरब डॉलर में।",
        },
        "pib-ppa": {
            "slug": "gdp-ppp",
            "nom": "क्रय शक्ति समता जीडीपी",
            "nav": "जीडीपी (पीपीपी)", "nav_court": "जीडीपी पीपीपी",
            "texte": "जीवन-यापन की लागत को समायोजित करने के बाद हर अर्थव्यवस्था का आकार, अंतर्राष्ट्रीय डॉलर में।",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "nom": "प्रति व्यक्ति जीडीपी",
            "nav": "प्रति व्यक्ति जीडीपी", "nav_court": "जीडीपी/व्यक्ति",
            "texte": "प्रति व्यक्ति उत्पादित संपत्ति, चालू डॉलर में।",
        },
        "pib-par-habitant-ppa": {
            "slug": "gdp-per-capita-ppp",
            "nom": "क्रय शक्ति समता पर प्रति व्यक्ति जीडीपी",
            "nav": "प्रति व्यक्ति जीडीपी (पीपीपी)", "nav_court": "जीडीपी/व्यक्ति पीपीपी",
            "texte": "जीवन-यापन की लागत को समायोजित करने के बाद प्रति व्यक्ति संपत्ति, अंतर्राष्ट्रीय डॉलर में।",
        },
        "croissance": {
            "slug": "gdp-growth",
            "nom": "जीडीपी वृद्धि दर",
            "nav": "वृद्धि दर", "nav_court": "वृद्धि",
            "texte": "वास्तविक जीडीपी में वर्ष-दर-वर्ष बदलाव, प्रतिशत में।",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "मुद्रास्फीति",
            "nav": "मुद्रास्फीति", "nav_court": "मुद्रास्फीति",
            "texte": "उपभोक्ता मूल्यों में वर्ष-दर-वर्ष वृद्धि, प्रतिशत में।",
        },
        "population": {
            "slug": "population",
            "nom": "जनसंख्या",
            "nav": "जनसंख्या", "nav_court": "जनसंख्या",
            "texte": "हर देश में कितने लोग रहते हैं, मिलियन में।",
        },
    },
})

# --------------------------------------------------------------- العربية ---
LANGUES.append({
    "code": "ar", "dossier": "ar", "hreflang": "ar", "sens": "rtl",
    "drapeau": "🇸🇦", "nom": "العربية", "nav_aria": "الخرائط",
    # Les libellés que lisent les lecteurs d'écran, et les infobulles.
    "langue_label": "اللغة", "theme_label": "تغيير السمة",
    "theme_clair": "التبديل إلى السمة الفاتحة", "theme_sombre": "التبديل إلى السمة الداكنة",
    "variantes_label": "الوحدة",
    "modele_titre": "{nom} حسب البلد — خريطة عالمية تفاعلية | StatsMaps",
    "modele_titre_categorie": "{nom} — كل الخرائط | StatsMaps",
    "modele_description": (
        "{texte} خريطة تفاعلية لـ197 بلدًا، من 1980 إلى 2031، اعتمادًا على بيانات صندوق النقد الدولي الرسمية (World Economic Outlook): الترتيب العالمي والتطور سنة بعد سنة."),
    "accueil": {
        "titre": "StatsMaps — خرائط وإحصاءات عالمية",
        "description": "خرائط تفاعلية للإحصاءات العالمية: الناتج المحلي الإجمالي، ونصيب الفرد منه، والنمو، والتضخم، وعدد السكان في 197 بلدًا، من 1980 إلى 2031، ببيانات صندوق النقد الدولي الرسمية.",
        "h1": "إحصاءات العالم، على الخريطة.",
        "intro": "يحوّل StatsMaps أبرز المؤشرات العالمية إلى خرائط تفاعلية، انطلاقًا من مصادر رسمية. اختر فئة لترى خرائطها: اليوم الاقتصاد والسكان، ببيانات صندوق النقد الدولي — 197 بلدًا، من 1980 إلى 2031.",
        "bientot": "قريبًا: البنية التحتية، والطاقة، والتعليم، والصحة.",
        "pied": "البيانات: صندوق النقد الدولي (World Economic Outlook) · خلفية الخريطة: Natural Earth · بلا إعلانات ولا تتبّع.",
    },
    "variantes": {"nominal": "اسمي", "ppa": "تعادل القوة الشرائية"},
    "categories": {
        "economie": {
            "slug": "economy",
            "nom": "الاقتصاد",
            "texte": "الناتج المحلي، وثروة الفرد، والنمو، والتضخم.",
            "h1": "اقتصاد العالم على الخريطة.",
            "intro": "أربع خرائط من تقرير World Economic Outlook الصادر عن صندوق النقد الدولي: 197 بلدًا، من 1980 إلى 2031، بما في ذلك التوقعات.",
        },
        "demographie": {
            "slug": "demographics",
            "nom": "السكان",
            "texte": "عدد الأشخاص الذين يعيشون في كل بلد، سنة بعد سنة.",
            "h1": "سكان العالم على الخريطة.",
            "intro": "ينشر صندوق النقد الدولي أيضًا عدد سكان كل بلد: 197 بلدًا، من 1980 إلى 2031، بما في ذلك التوقعات.",
        },
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "nom": "الناتج المحلي الإجمالي",
            "nav": "الناتج المحلي الإجمالي", "nav_court": "الناتج",
            "texte": "حجم كل اقتصاد، بمليارات الدولارات الجارية.",
        },
        "pib-ppa": {
            "slug": "gdp-ppp",
            "nom": "الناتج المحلي الإجمالي بتعادل القوة الشرائية",
            "nav": "الناتج (تعادل القوة الشرائية)", "nav_court": "الناتج ت.ق.ش",
            "texte": "حجم كل اقتصاد بعد تصحيح تكلفة المعيشة، بالدولارات الدولية.",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "nom": "نصيب الفرد من الناتج المحلي",
            "nav": "نصيب الفرد من الناتج", "nav_court": "نصيب الفرد",
            "texte": "الثروة المنتَجة لكل فرد، بالدولارات الجارية.",
        },
        "pib-par-habitant-ppa": {
            "slug": "gdp-per-capita-ppp",
            "nom": "نصيب الفرد من الناتج بتعادل القوة الشرائية",
            "nav": "نصيب الفرد (تعادل القوة الشرائية)", "nav_court": "نصيب الفرد ت.ق.ش",
            "texte": "الثروة المنتَجة لكل فرد بعد تصحيح تكلفة المعيشة، بالدولارات الدولية.",
        },
        "croissance": {
            "slug": "gdp-growth",
            "nom": "نمو الناتج المحلي",
            "nav": "النمو", "nav_court": "النمو",
            "texte": "تغيّر الناتج المحلي الحقيقي من سنة إلى أخرى، بالنسبة المئوية.",
        },
        "inflation": {
            "slug": "inflation",
            "nom": "التضخم",
            "nav": "التضخم", "nav_court": "التضخم",
            "texte": "ارتفاع أسعار المستهلك من سنة إلى أخرى، بالنسبة المئوية.",
        },
        "population": {
            "slug": "population",
            "nom": "عدد السكان",
            "nav": "السكان", "nav_court": "السكان",
            "texte": "عدد الأشخاص الذين يعيشون في كل بلد، بالملايين.",
        },
    },
})

# ==========================================================================
#  LES MODÈLES HTML
#
#  Écrits une seule fois. Les {accolades} sont remplies plus bas.
#  Attention en les modifiant : ce sont les 130 pages du site qui changent.
# ==========================================================================

MODELE_CARTE = """<!DOCTYPE html>
<html lang="{hreflang}"{rtl}>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{titre}</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#ffffff">
  <link rel="canonical" href="{url}">
{alternates}
  <link rel="icon" href="{base}favicon.svg" type="image/svg+xml">
  <meta property="og:title" content="{og_titre}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{url}">
  <link rel="preload" href="{base}data/pays.json" as="fetch" crossorigin>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/{maplibre}/maplibre-gl.css">
  <link rel="stylesheet" href="{base}assets/css/style.css">
  <script src="{base}assets/js/theme.js"></script>
</head>
<body class="page-carte" data-indicateur="{indicateur}" data-langue="{code}" data-base="{base}">

{entete}
  <div class="zone-carte">
    <div id="carte"></div>

    <button class="bouton-icone bouton-panneau" id="bouton-panneau" type="button" aria-expanded="false" aria-controls="panneau"></button>

    <aside class="panneau" id="panneau">
      <div class="panneau__entete">
        <h1 class="panneau__titre" id="titre-panneau">{h1}</h1>
        <div class="panneau__soustitre" id="compteur-pays"></div>
{variantes}        <input class="panneau__recherche" id="recherche" type="search" autocomplete="off" spellcheck="false">
      </div>
      <ul class="classement" id="classement"></ul>
      <div class="panneau__pied" id="source"></div>
    </aside>

    <div class="legende" id="legende"></div>

    <div class="annees">
      <div class="annees__haut">
        <span class="annees__valeur nombre" id="annee-valeur">—</span>
        <span class="annees__etiquette" id="annee-etiquette"></span>
      </div>
      <input type="range" id="curseur-annee" min="1980" max="2031" step="1" value="2025">
      <div class="annees__bornes"><span id="annee-min"></span><span id="annee-max"></span></div>
    </div>

    <div class="chargement" id="chargement">…</div>
  </div>

  <script src="{base}assets/js/i18n.js"></script>
  <script src="{base}assets/js/barre.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/{maplibre}/maplibre-gl.js"></script>
  <script src="{base}assets/js/comparateur.js"></script>
  <script src="{base}assets/js/carte.js"></script>
</body>
</html>
"""

# L'accueil et les pages de catégorie partagent le même modèle : une phrase
# d'introduction, puis une grille de vignettes. Seul ce qu'il y a DANS les
# vignettes change — des catégories sur l'accueil, des cartes ailleurs.
MODELE_VIGNETTES = """<!DOCTYPE html>
<html lang="{hreflang}"{rtl}>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titre}</title>
  <meta name="description" content="{description}">
  <meta name="theme-color" content="#ffffff">
  <link rel="canonical" href="{url}">
{alternates}
  <link rel="icon" href="{base}favicon.svg" type="image/svg+xml">
  <meta property="og:title" content="{titre}">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{url}">
  <link rel="stylesheet" href="{base}assets/css/style.css">
  <script src="{base}assets/js/theme.js"></script>
</head>
<body>

{entete}
  <main class="accueil">
    <h1 class="accueil__titre">{h1}</h1>
    <p class="accueil__intro">{intro}</p>

    <div class="vignettes">
{vignettes}
    </div>
{fin}
  </main>

  <footer class="pied">{pied}</footer>

  <script src="{base}assets/js/barre.js"></script>
</body>
</html>
"""

# Le mot « accueil » dans les treize langues, pour les boutons de la page 404.
# C'est le seul texte de cette page qui dépende de la langue : les trois
# phrases d'excuse, elles, restent en français, anglais et ukrainien, sinon
# la page deviendrait un mur de texte de treize lignes.
ACCUEIL_MOT = {
    "fr": "Accueil", "en": "Home", "uk": "Головна", "de": "Startseite",
    "es": "Inicio", "it": "Home", "pt": "Início", "pl": "Strona główna",
    "ja": "ホーム", "ko": "홈", "tr": "Ana sayfa", "hi": "मुखपृष्ठ",
    "ar": "الصفحة الرئيسية",
}

MODELE_ENTETE = """  <header class="barre">
    <a class="barre__logo" href="{accueil}">Stats<span>Maps</span></a>
{categorie}    <nav class="barre__nav" aria-label="{nav_aria}">
{liens}
    </nav>
    <div class="barre__droite">
      <details class="langues">
        <summary class="bouton-icone" title="{langue_label}" aria-label="{langue_label}">{drapeau}</summary>
        <div class="langues__menu">
{menu}
        </div>
      </details>
      <button class="bouton-icone" id="bouton-theme" type="button"
              aria-label="{theme_label}"
              data-vers-clair="{theme_clair}"
              data-vers-sombre="{theme_sombre}">☾</button>
    </div>
  </header>
"""


# ==========================================================================
#  LA FABRICATION
#
#  Une PAGE est désignée par un couple (genre, clef) :
#      ("accueil",   None)            l'accueil de la langue
#      ("categorie", "economie")      la page d'une rubrique
#      ("carte",     "pib-nominal")   une carte
#  Toutes les fonctions ci-dessous parlent ce langage-là.
# ==========================================================================

ACCUEIL = ("accueil", None)

# Toutes les pages d'une langue, dans l'ordre où elles comptent pour Google.
PAGES = ([ACCUEIL]
         + [("categorie", identifiant) for identifiant, _, _ in CATEGORIES]
         + [("carte", identifiant) for identifiant, _, _, _, _ in CARTES])


def echapper(texte):
    """Protège un texte destiné à un attribut HTML."""
    return (texte.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def slug(langue, page):
    """Le nom du dossier de la page, ou None pour l'accueil."""
    genre, clef = page
    if genre == "accueil":
        return None
    if genre == "categorie":
        return langue["categories"][clef]["slug"]
    return langue["cartes"][clef]["slug"]


def adresse(langue, page=ACCUEIL):
    """L'adresse d'une page, à partir de la racine du site : "/de/bip-pro-kopf/".
    L'accueil français est simplement "/"."""
    morceaux = [langue["dossier"]] if langue["dossier"] else []
    nom = slug(langue, page)
    if nom:
        morceaux.append(nom)
    return "/" + "".join(m + "/" for m in morceaux)


def profondeur(langue, page=ACCUEIL):
    """Combien de dossiers séparent la page de la racine du site."""
    return (1 if langue["dossier"] else 0) + (0 if page == ACCUEIL else 1)


def remonter(niveaux):
    """Le chemin relatif vers la racine : "./", "../", "../../"."""
    return "./" if niveaux == 0 else "../" * niveaux


def alternates(page):
    """Les balises qui disent à Google : « cette page existe aussi dans ces
    douze autres langues ». Le français fait aussi office de x-default, la
    version servie quand aucune langue du visiteur ne correspond."""
    lignes = []
    for langue in LANGUES:
        lignes.append('  <link rel="alternate" hreflang="%s" href="%s%s">'
                      % (langue["hreflang"], SITE, adresse(langue, page)))
    lignes.append('  <link rel="alternate" hreflang="x-default" href="%s%s">'
                  % (SITE, adresse(LANGUES[0], page)))
    return "\n".join(lignes)


def entete(langue, page=ACCUEIL):
    """La barre du haut : logo, menu, menu des langues, thème.

    Le menu montre le niveau où l'on se trouve, et pas tout le site (voir le
    commentaire de MENU plus haut) : les catégories sur l'accueil et sur une
    page de rubrique, les cartes de sa rubrique sur une carte."""
    genre, clef = page
    # Depuis l'accueil, un lien vers une carte s'écrit "croissance/" ; depuis
    # n'importe quelle autre page, on remonte d'un cran : "../croissance/".
    haut = "" if page == ACCUEIL else "../"

    liens = []
    categorie_ouverte = None

    if genre == "carte":
        # Les cartes de la catégorie de cette carte, et elles seules.
        categorie_ouverte = CATEGORIE_DE[clef]
        for identifiant in CARTES_DE[categorie_ouverte]:
            carte = langue["cartes"][identifiant]
            # La page de la VARIANTE d'une carte allume quand même son entrée :
            # sur /pib-ppa/, c'est bien « PIB » qu'on est en train de voir.
            meme = clef == identifiant or (
                FAMILLE_DE[clef] and FAMILLE_DE[clef] == FAMILLE_DE[identifiant])
            liens.append(lien_de_menu(haut + carte["slug"] + "/",
                                      carte["nav"], carte["nav_court"], meme))
    else:
        # L'accueil et les pages de rubrique montrent les rubriques.
        for identifiant, _, _ in CATEGORIES:
            categorie = langue["categories"][identifiant]
            liens.append(lien_de_menu(haut + categorie["slug"] + "/",
                                      categorie["nom"], categorie["nom"],
                                      genre == "categorie" and clef == identifiant))

    # Sur une carte, le nom de la rubrique ouvre sa page : c'est à la fois le
    # repère « où suis-je » et le chemin de retour vers les autres rubriques.
    fil = ""
    if categorie_ouverte:
        fil = ('    <a class="barre__categorie" href="%s%s/">%s</a>\n'
               % (haut, langue["categories"][categorie_ouverte]["slug"],
                  echapper(langue["categories"][categorie_ouverte]["nom"])))

    # Le menu des langues pointe vers la MÊME page dans chaque langue, en
    # adresses absolues : c'est ce qui permet de changer de langue sans perdre
    # la carte qu'on était en train de regarder.
    menu = []
    for autre in LANGUES:
        actuelle = ' aria-current="true"' if autre["code"] == langue["code"] else ""
        menu.append(
            '          <a href="%s" hreflang="%s" lang="%s"%s>'
            '<span class="drapeau" aria-hidden="true">%s</span>%s</a>'
            % (adresse(autre, page), autre["hreflang"], autre["hreflang"],
               actuelle, autre["drapeau"], echapper(autre["nom"])))

    return MODELE_ENTETE.format(
        # Le logo ramène à l'accueil DE LA LANGUE COURANTE, et non à la racine
        # du site : depuis /en/gdp/, il mène à /en/ et non à l'accueil français.
        # Ne pas confondre avec « base », qui vise la racine pour aller y
        # chercher assets/ et data/.
        accueil=haut or "./",
        categorie=fil,
        nav_aria=echapper(langue["nav_aria"]),
        liens="\n".join(liens),
        langue_label=echapper(langue["langue_label"]),
        drapeau=langue["drapeau"],
        menu="\n".join(menu),
        theme_label=echapper(langue["theme_label"]),
        theme_clair=echapper(langue["theme_clair"]),
        theme_sombre=echapper(langue["theme_sombre"]),
    )


def lien_de_menu(adresse_relative, long, court, courante):
    """Une entrée du menu du haut. Deux libellés : le long sur grand écran,
    le court sur téléphone (voir .barre__lien .long / .court dans le style)."""
    return ('        <a class="barre__lien" href="%s"%s>'
            '<span class="long">%s</span><span class="court">%s</span></a>'
            % (adresse_relative, ' aria-current="page"' if courante else "",
               echapper(long), echapper(court)))


def bascule_variantes(langue, id_carte):
    """Le bouton « Dollars US / Parité de pouvoir d'achat », en haut du panneau.

    Ce sont de VRAIS liens vers de VRAIES pages : chaque version a son adresse,
    son titre et sa place dans Google. Une carte qui n'a qu'une version — la
    croissance, l'inflation, la population — n'affiche rien du tout."""
    famille = FAMILLE_DE[id_carte]
    if not famille or len(FAMILLES[famille]) < 2:
        return ""

    boutons = []
    for autre_id, variante in FAMILLES[famille]:
        active = autre_id == id_carte
        boutons.append(
            '          <a class="variante%s" href="../%s/"%s>%s</a>'
            % (" est-active" if active else "",
               langue["cartes"][autre_id]["slug"],
               ' aria-current="page"' if active else "",
               echapper(langue["variantes"][variante])))

    return ('        <div class="variantes" role="group" aria-label="%s">\n%s\n'
            '        </div>\n'
            % (echapper(langue["variantes_label"]), "\n".join(boutons)))


def vignette(lien, pastille, titre, texte, liste=""):
    """Une carte cliquable de la grille : sur l'accueil comme sur les pages
    de catégorie, c'est toujours le même objet."""
    dedans = ""
    if liste:
        dedans = '        <div class="vignette__liste">%s</div>\n' % echapper(liste)
    return ('      <a class="vignette" href="%s">\n'
            '        <div class="vignette__pastille">%s</div>\n'
            '        <div class="vignette__titre">%s</div>\n'
            '        <p class="vignette__texte">%s</p>\n'
            '%s      </a>'
            % (lien, pastille, echapper(titre), echapper(texte), dedans))


def page_carte(langue, id_carte):
    carte = langue["cartes"][id_carte]
    base = remonter(profondeur(langue, ("carte", id_carte)))
    titre = langue["modele_titre"].format(nom=carte["nom"])
    # Le titre partagé sur les réseaux sociaux n'a pas besoin du « | StatsMaps »
    # final : le nom du site y est déjà affiché à part.
    og_titre = titre.split(" | StatsMaps")[0]

    return MODELE_CARTE.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(titre),
        description=echapper(langue["modele_description"].format(texte=carte["texte"])),
        url=SITE + adresse(langue, ("carte", id_carte)),
        alternates=alternates(("carte", id_carte)),
        base=base,
        og_titre=echapper(og_titre),
        maplibre=MAPLIBRE,
        indicateur=id_carte,
        code=langue["code"],
        entete=entete(langue, ("carte", id_carte)),
        h1=echapper(carte["nom"]),
        variantes=bascule_variantes(langue, id_carte),
    )


def page_accueil(langue):
    """L'accueil : les CATÉGORIES, et non les cartes. Chaque vignette annonce
    ce qu'elle contient, pour qu'on sache où l'on va avant de cliquer."""
    accueil = langue["accueil"]

    vignettes = []
    for identifiant, pastille, cartes in CATEGORIES:
        categorie = langue["categories"][identifiant]
        vignettes.append(vignette(
            categorie["slug"] + "/", pastille, categorie["nom"], categorie["texte"],
            liste=" · ".join(langue["cartes"][c]["nav"] for c in cartes)))

    return MODELE_VIGNETTES.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(accueil["titre"]),
        description=echapper(accueil["description"]),
        url=SITE + adresse(langue),
        alternates=alternates(ACCUEIL),
        base=remonter(profondeur(langue)),
        entete=entete(langue),
        h1=echapper(accueil["h1"]),
        intro=echapper(accueil["intro"]),
        vignettes="\n".join(vignettes),
        fin='\n    <p class="accueil__bientot">%s</p>\n' % echapper(accueil["bientot"]),
        pied=echapper(accueil["pied"]),
    )


def page_categorie(langue, id_categorie):
    """La page d'une rubrique : ses cartes, et rien d'autre."""
    categorie = langue["categories"][id_categorie]
    cartes = CARTES_DE[id_categorie]
    titre = langue["modele_titre_categorie"].format(nom=categorie["nom"])

    vignettes = []
    for id_carte in cartes:
        carte = langue["cartes"][id_carte]
        vignettes.append(vignette(
            "../" + carte["slug"] + "/", PASTILLES[id_carte],
            carte["nom"], carte["texte"]))

    return MODELE_VIGNETTES.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(titre),
        description=echapper(langue["modele_description"].format(texte=categorie["texte"])),
        url=SITE + adresse(langue, ("categorie", id_categorie)),
        alternates=alternates(("categorie", id_categorie)),
        base=remonter(profondeur(langue, ("categorie", id_categorie))),
        entete=entete(langue, ("categorie", id_categorie)),
        h1=echapper(categorie["h1"]),
        intro=echapper(categorie["intro"]),
        vignettes="\n".join(vignettes),
        fin="",
        pied=echapper(langue["accueil"]["pied"]),
    )


def sitemap():
    """La liste de toutes les pages, pour Google. Chaque adresse y déclare ses
    douze traductions : c'est ce qui évite que le site se fasse concurrence à
    lui-même dans les résultats de recherche.

    Volontairement sans <lastmod> : la date serait celle du jour où le script a
    tourné, pas celle du dernier vrai changement. Elle ferait donc bouger les
    130 lignes du fichier à chaque exécution, pour rien."""
    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
              '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    # Les accueils sont les portes d'entrée du site ; viennent ensuite les
    # catégories, puis les cartes elles-mêmes.
    priorites = {"accueil": "1.0", "categorie": "0.9", "carte": "0.8"}

    for page in PAGES:
        for langue in LANGUES:
            lignes.append("  <url>")
            lignes.append("    <loc>%s%s</loc>" % (SITE, adresse(langue, page)))
            for autre in LANGUES:
                lignes.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>'
                              % (autre["hreflang"], SITE, adresse(autre, page)))
            lignes.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>'
                          % (SITE, adresse(LANGUES[0], page)))
            lignes.append("    <priority>%s</priority>" % priorites[page[0]])
            lignes.append("  </url>")

    lignes.append("</urlset>")
    return "\n".join(lignes) + "\n"


def page_404(modele):
    """La page affichée quand une adresse n'existe pas. Son habillage est écrit
    à la main dans 404.html (elle a son propre style, pour s'afficher même si
    la feuille de style du site ne se charge pas) ; seule la rangée de boutons
    « accueil » est refaite ici, pour qu'elle suive la liste des langues."""
    boutons = []
    for langue in LANGUES:
        boutons.append('    <a href="%s" hreflang="%s" lang="%s">%s %s</a>'
                       % (adresse(langue), langue["hreflang"], langue["hreflang"],
                          langue["drapeau"], echapper(ACCUEIL_MOT[langue["code"]])))

    debut = modele.split("  <div>\n")[0]
    return debut + "  <div>\n" + "\n".join(boutons) + "\n  </div>\n</body>\n</html>\n"


def ecrire(chemin_relatif, contenu):
    chemin = os.path.join(RACINE, chemin_relatif)
    dossier = os.path.dirname(chemin)
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    with io.open(chemin, "w", encoding="utf-8", newline="\n") as fichier:
        fichier.write(contenu)


def ranger(dossiers_attendus):
    """Efface les dossiers de pages d'une version précédente du site.

    Sans ce ménage, les anciennes cartes « année record » resteraient en ligne
    indéfiniment, absentes du sitemap et des menus mais toujours accessibles —
    avec des chiffres que plus personne ne met à jour."""
    efface = 0
    for langue in LANGUES:
        racine_langue = os.path.join(RACINE, langue["dossier"])
        if not os.path.isdir(racine_langue):
            continue
        for nom in sorted(os.listdir(racine_langue)):
            chemin = os.path.join(racine_langue, nom)
            if not os.path.isdir(chemin) or nom in dossiers_attendus:
                continue
            # On ne touche qu'aux dossiers qui contiennent une page fabriquée,
            # et à rien d'autre : assets/, data/, scripts/ ne risquent rien.
            if os.path.isfile(os.path.join(chemin, "index.html")):
                os.remove(os.path.join(chemin, "index.html"))
                if not os.listdir(chemin):
                    os.rmdir(chemin)
                print("  supprimé (page d'une version précédente) : %s/%s"
                      % (langue["dossier"] or ".", nom))
                efface += 1
    return efface


def main():
    print("Fabrication des pages de StatsMaps")
    print("-" * 55)

    # Contrôle : chaque langue doit décrire toutes les cartes et toutes les
    # catégories, sans oubli.
    for langue in LANGUES:
        manquantes = [c[0] for c in CARTES if c[0] not in langue["cartes"]]
        manquantes += [c[0] for c in CATEGORIES if c[0] not in langue["categories"]]
        if manquantes:
            raise SystemExit("  ERREUR : la langue « %s » ne décrit pas %s"
                             % (langue["code"], ", ".join(manquantes)))

    # Contrôle : deux pages ne doivent jamais se retrouver à la même adresse.
    vues = {}
    for langue in LANGUES:
        for page in PAGES:
            url = adresse(langue, page)
            if url in vues:
                raise SystemExit("  ERREUR : l'adresse %s est utilisée deux fois "
                                 "(%s et %s)" % (url, vues[url], langue["code"]))
            vues[url] = "%s / %s" % (langue["code"], page[1] or "accueil")

    total = 0
    dossiers_attendus = set()
    for langue in LANGUES:
        ecrire(os.path.join(langue["dossier"], "index.html"), page_accueil(langue))
        total += 1
        for id_categorie, _, _ in CATEGORIES:
            nom = langue["categories"][id_categorie]["slug"]
            dossiers_attendus.add(nom)
            ecrire(os.path.join(langue["dossier"], nom, "index.html"),
                   page_categorie(langue, id_categorie))
            total += 1
        for id_carte, _, _, _, _ in CARTES:
            nom = langue["cartes"][id_carte]["slug"]
            dossiers_attendus.add(nom)
            ecrire(os.path.join(langue["dossier"], nom, "index.html"),
                   page_carte(langue, id_carte))
            total += 1
        print("  %-3s %-12s %d pages   %s…"
              % (langue["code"], "(" + (langue["dossier"] or "racine") + ")",
                 len(PAGES), adresse(langue)))

    # Les dossiers des autres langues ne sont pas des pages : on les protège.
    dossiers_attendus |= {l["dossier"] for l in LANGUES if l["dossier"]}
    dossiers_attendus |= {"assets", "data", "scripts", ".git", ".github", ".claude"}
    ranger(dossiers_attendus)

    ecrire("sitemap.xml", sitemap())

    chemin_404 = os.path.join(RACINE, "404.html")
    with io.open(chemin_404, encoding="utf-8") as fichier:
        ecrire("404.html", page_404(fichier.read()))

    print("-" * 55)
    print("  %d pages écrites, plus sitemap.xml (%d adresses) et 404.html."
          % (total, total))
    print("Terminé.")


if __name__ == "__main__":
    main()
