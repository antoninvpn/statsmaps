#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pages.py — fabrique TOUTES les pages du site, en français et en anglais.

    python3 scripts/build_pages.py

Pourquoi ce script existe
-------------------------
Le site a une quinzaine de pages par langue — l'accueil, les pages de
catégorie et les cartes — et deux langues. Ces fichiers sont rigoureusement
identiques à quelques mots près : le titre, l'adresse, et la langue. Les écrire
à la main voudrait dire, à chaque petit changement — un lien dans le menu, une
balise pour Google — répéter la même retouche trente fois sans en oublier une.

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
    index.html + ses dossiers ................... le français, à la racine
    en/ ......................................... l'anglais
    ua/, de/, es/, it/, pt/, pl/,
    ja/, ko/, tr/, hi/, ar/ ..................... les anciennes langues : de
                                                  simples pages de renvoi vers
                                                  l'anglais (ANCIENNES_LANGUES)
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
       entrée "cartes" dans les DEUX blocs de LANGUES (français et anglais).
    4. Relancer ce script : les pages, les menus et le sitemap suivent.
"""

import io
import os
import shutil

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
    ("metro",                   "🚇", None,               None,      True),
    ("entreprises",             "🏢", None,               None,      True),
]

# Une carte peut n'exister QUE DANS CERTAINES LANGUES, le temps d'être
# traduite. C'est le cas d'une carte qui vient d'ouvrir : elle sort d'abord en
# français, l'anglais suit.
#
# Tant qu'une langue n'y figure pas, la carte n'y a ni page, ni entrée de menu,
# ni vignette, ni ligne dans le sitemap — plutôt qu'une page à moitié en
# français, qui desservirait le site auprès de Google comme du lecteur.
#
# Pour ouvrir la carte dans une langue : ajouter son bloc "cartes" dans
# LANGUES, puis son code ici. Une carte absente de cette liste existe, comme
# les autres, dans les deux langues.
LANGUES_DE = {
}

# Les cartes qui ne colorient pas des pays et ont donc leur propre moteur.
# La carte des métros dessine des lignes sur des villes : ni curseur des
# années, ni classement de pays coloriés, ni comparateur.
MOTEURS = {
    "metro": "metro.js",
    "entreprises": "bourse.js",
}

# Le gros fichier que chacune de ces cartes lit au démarrage. On le signale au
# navigateur dès la première ligne de la page (« preload ») pour qu'il commence
# à le télécharger sans attendre d'avoir lu tout le reste.
PRECHARGES = {
    "metro": "data/metro/monde.json",
    "entreprises": "data/bourse/entreprises.json",
}

# ----------------------------------------------------------- LES CATÉGORIES
#
# L'accueil montre ces rubriques ; chacune a sa page, qui montre ses cartes.
# Seules les cartes PRINCIPALES y figurent : on n'affiche pas deux vignettes
# pour le PIB, on entre dans la carte et on choisit son unité sur place.
# Une catégorie dont la liste de cartes est VIDE est une rubrique annoncée mais
# pas encore ouverte : elle apparaît sur l'accueil, grisée et marquée « bientôt »,
# mais n'a ni page, ni entrée de menu, ni ligne dans le sitemap. Le jour où on
# lui ajoute une carte, tout cela apparaît tout seul.
CATEGORIES = [
    ("economie", "💶", ["pib-nominal", "pib-par-habitant", "croissance", "inflation",
                        "entreprises"]),
    ("demographie", "👥", ["population"]),
    ("infrastructure", "🏗️", ["metro"]),
    ("armee", "🛡️", []),
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

# Les rubriques réellement ouvertes : celles qui ont au moins une carte.
# Ce sont les seules à avoir une page et à figurer dans les menus.
CATEGORIES_OUVERTES = [c for c in CATEGORIES if c[2]]

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
#  LES DEUX LANGUES
#
#  Le site a compté jusqu'à treize langues ; depuis le 20 novembre 2026, à la
#  demande d'Antonin, il n'en garde que deux : le français et l'anglais. Les
#  adresses des onze autres renvoient vers l'anglais (voir ANCIENNES_LANGUES).
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
#  - bientot .......... le mot de la pastille des rubriques pas encore ouvertes
#
#  Une rubrique annoncée mais vide (infrastructure, armée) n'a ni "slug", ni
#  "h1", ni "intro" : elle n'a pas de page. Le jour où on lui donne une carte,
#  il faudra les ajouter.
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
        "intro": "StatsMaps met en carte les grands indicateurs mondiaux à partir de sources officielles. Choisis une catégorie pour voir les cartes qu’elle contient : l’économie et la démographie, à partir des données du Fonds monétaire international — 197 pays, de 1980 à 2031 —, les entreprises cotées en bourse et les métros du monde.",
        "bientot": "Bientôt",
        "pied": "Données : FMI (World Economic Outlook) · Fond de carte : Natural Earth · Site sans publicité ni traceur.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Parité de pouvoir d’achat"},
    "categories": {
        "economie": {
            "slug": "economie",
            "nom": "Économie",
            "texte": "Le PIB, la richesse par habitant, la croissance et l’inflation.",
            "h1": "L’économie mondiale, en cartes.",
            "intro": "Quatre cartes tirées du World Economic Outlook du Fonds monétaire international — 197 pays, de 1980 à 2031, projections comprises — et la carte des entreprises cotées en bourse, chacune à l’adresse de son siège.",
        },
        "demographie": {
            "slug": "demographie",
            "nom": "Démographie",
            "texte": "Le nombre d’habitants de chaque pays, année par année.",
            "h1": "La démographie mondiale, en cartes.",
            "intro": "Le FMI publie aussi la population de chaque pays : 197 pays, de 1980 à 2031, projections comprises.",
        },
        "infrastructure": {
            "slug": "infrastructure",
            "nom": "Infrastructure",
            "texte": "Les réseaux qui font tenir une ville et un pays.",
            "h1": "Les infrastructures du monde, en cartes.",
            "intro": "Première carte de la rubrique : les métros du monde, ville par ville et ligne par ligne, dans leurs vraies couleurs.",
        },
        "armee": {
            "nom": "Armée",
            "texte": "Effectifs, budgets et matériels militaires.",
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
        # La carte des métros ne parle pas de pays mais de villes : ni le titre
        # type (« …, par pays »), ni la description type (« 197 pays, de 1980 à
        # 2031, données du FMI ») ne lui vont. Elle écrit donc les siens.
        "metro": {
            "slug": "metro",
            "nom": "Métros",
            "nav": "Métro", "nav_court": "Métro",
            "texte": "Toutes les villes du monde qui ont un métro, ligne par ligne et dans leurs vraies couleurs.",
            "titre": "Les métros du monde — carte interactive de toutes les lignes | StatsMaps",
            "description": "La carte de tous les métros du monde : 200 villes, chaque ligne dans sa couleur officielle, et les tronçons en construction. Classement des pays par nombre de réseaux, kilomètres, stations et lignes.",
        },
        # Comme les métros, les entreprises sont des POINTS et non des pays
        # coloriés : elles ont leur propre titre et leur propre description.
        "entreprises": {
            "slug": "entreprises-cotees",
            "nom": "Entreprises cotées en bourse",
            "nav": "Entreprises", "nav_court": "Entreprises",
            "texte": "Chaque entreprise cotée en bourse, à l’adresse de son siège, avec son logo.",
            "titre": "Les entreprises cotées en bourse — carte mondiale de leurs sièges | StatsMaps",
            "description": "La carte de plus de 10 000 entreprises cotées en bourse dans le monde, chacune à l’adresse de son siège social, avec son logo. Filtre par secteur (banque, médias, intelligence artificielle…) et par place boursière (New York, Paris, Tokyo…).",
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
        "intro": "StatsMaps turns major global indicators into interactive maps, using official sources. Pick a category to see the maps inside it: the economy and demographics, based on International Monetary Fund data — 197 countries, from 1980 to 2031 — the world’s listed companies, and its metro systems.",
        "bientot": "Coming soon",
        "pied": "Data: IMF (World Economic Outlook) · Basemap: Natural Earth · No ads, no trackers.",
    },
    "variantes": {"nominal": "Nominal", "ppa": "Purchasing power parity"},
    "categories": {
        "economie": {
            "slug": "economy",
            "nom": "Economy",
            "texte": "GDP, wealth per person, growth and inflation.",
            "h1": "The world economy, mapped.",
            "intro": "Four maps drawn from the International Monetary Fund’s World Economic Outlook — 197 countries, from 1980 to 2031, projections included — and the map of listed companies, each one at the address of its headquarters.",
        },
        "demographie": {
            "slug": "demographics",
            "nom": "Demographics",
            "texte": "How many people live in each country, year by year.",
            "h1": "World demographics, mapped.",
            "intro": "The IMF also publishes each country’s population: 197 countries, from 1980 to 2031, projections included.",
        },
        "infrastructure": {
            "slug": "infrastructure",
            "nom": "Infrastructure",
            "texte": "The networks that hold a city and a country together.",
            "h1": "The world’s infrastructure, mapped.",
            "intro": "The first map in this section: the world’s metro systems, city by city and line by line, in their real colours.",
        },
        "armee": {
            "nom": "Military",
            "texte": "Troop numbers, budgets and equipment.",
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
        "metro": {
            "slug": "metro",
            "nom": "Metros",
            "nav": "Metro", "nav_court": "Metro",
            "texte": "Every city in the world with a metro, line by line and in its real colours.",
            "titre": "Metro systems of the world — interactive map of every line | StatsMaps",
            "description": "A map of every metro system in the world: 200 cities, each line in its official colour, and the sections under construction. Countries ranked by number of systems, kilometres, stations and lines.",
        },
        "entreprises": {
            "slug": "listed-companies",
            "nom": "Listed companies",
            "nav": "Companies", "nav_court": "Companies",
            "texte": "Every company listed on a stock exchange, at the address of its headquarters, with its logo.",
            "titre": "Listed companies — world map of their headquarters | StatsMaps",
            "description": "A map of more than 10,000 companies listed on stock exchanges around the world, each one at the address of its headquarters, with its logo. Filter by sector (banking, media, artificial intelligence…) and by stock exchange (New York, Paris, Tokyo…).",
        },
    },
})

# ==========================================================================
#  LES ANCIENNES LANGUES
#
#  Jusqu'au 20 novembre 2026, le site existait aussi en ukrainien, allemand,
#  espagnol, italien, portugais, polonais, japonais, coréen, turc, hindi et
#  arabe. Google connaît ces adresses, et des gens les ont peut-être gardées
#  en favori. Plutôt qu'une page d'erreur, chacune devient une petite page de
#  RENVOI vers la même page en anglais : on y arrive, et on repart aussitôt.
#
#  Le renvoi est écrit de trois façons, pour qu'il marche partout :
#    · <meta http-equiv="refresh"> ... que Google lit comme un déménagement
#                                      définitif, et qui marche sans JavaScript ;
#    · location.replace() ............ plus rapide, et qui ne laisse pas la
#                                      page de renvoi dans l'historique (le
#                                      bouton « retour » ne ramène pas dessus) ;
#    · un lien ordinaire ............. au cas où les deux premiers échouent.
#
#  Le tableau : dossier de la langue -> { adresse de la page dans ce dossier :
#  clef de la page anglaise }. "" est l'accueil de la langue.
# ==========================================================================

ANCIENNES_LANGUES = {}
for _dossier, _pages in [
    ("ua", ["", "ekonomika", "demohrafiia", "vvp", "vvp-pks", "vvp-na-osobu",
            "vvp-na-osobu-pks", "zrostannia", "infliatsiia", "naselennia"]),
    ("de", ["", "wirtschaft", "demografie", "nominales-bip", "bip-kkp", "bip-pro-kopf",
            "bip-pro-kopf-kkp", "bip-wachstum", "inflation", "bevoelkerung"]),
    ("es", ["", "economia", "demografia", "pib-nominal", "pib-ppa", "pib-per-capita",
            "pib-per-capita-ppa", "crecimiento-pib", "inflacion", "poblacion"]),
    ("it", ["", "economia", "demografia", "pil-nominale", "pil-ppa", "pil-pro-capite",
            "pil-pro-capite-ppa", "crescita-pil", "inflazione", "popolazione"]),
    ("pt", ["", "economia", "demografia", "pib-nominal", "pib-ppc", "pib-per-capita",
            "pib-per-capita-ppc", "crescimento-pib", "inflacao", "populacao"]),
    ("pl", ["", "gospodarka", "demografia", "pkb-nominalne", "pkb-psn", "pkb-na-mieszkanca",
            "pkb-na-mieszkanca-psn", "wzrost-pkb", "inflacja", "ludnosc"]),
    ("ja", ["", "economy", "demographics", "nominal-gdp", "gdp-ppp", "gdp-per-capita",
            "gdp-per-capita-ppp", "gdp-growth", "inflation", "population"]),
    ("ko", ["", "economy", "demographics", "nominal-gdp", "gdp-ppp", "gdp-per-capita",
            "gdp-per-capita-ppp", "gdp-growth", "inflation", "population"]),
    ("tr", ["", "ekonomi", "demografi", "nominal-gsyih", "gsyih-sagp", "kisi-basi-gsyih",
            "kisi-basi-gsyih-sagp", "gsyih-buyumesi", "enflasyon", "nufus"]),
    ("hi", ["", "economy", "demographics", "nominal-gdp", "gdp-ppp", "gdp-per-capita",
            "gdp-per-capita-ppp", "gdp-growth", "inflation", "population"]),
    ("ar", ["", "economy", "demographics", "nominal-gdp", "gdp-ppp", "gdp-per-capita",
            "gdp-per-capita-ppp", "gdp-growth", "inflation", "population"]),
]:
    # Les dix pages étaient, dans cet ordre, dans toutes les langues :
    # l'accueil, deux rubriques, puis les sept cartes.
    _cibles = [("accueil", None), ("categorie", "economie"), ("categorie", "demographie"),
               ("carte", "pib-nominal"), ("carte", "pib-ppa"),
               ("carte", "pib-par-habitant"), ("carte", "pib-par-habitant-ppa"),
               ("carte", "croissance"), ("carte", "inflation"), ("carte", "population")]
    ANCIENNES_LANGUES[_dossier] = dict(zip(_pages, _cibles))

MODELE_RENVOI = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>StatsMaps</title>
  <link rel="canonical" href="{url}">
  <meta http-equiv="refresh" content="0; url={cible}">
  <script>location.replace("{cible}");</script>
</head>
<body>
  <a href="{cible}">StatsMaps</a>
</body>
</html>
"""


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

# La carte des métros a son propre modèle. Elle ressemble beaucoup aux autres —
# même barre du haut, même panneau, même légende — mais trois choses en moins et
# une en plus :
#   · PAS de curseur des années : un réseau de métro n'a pas de série annuelle,
#     il a un état, celui d'aujourd'hui ;
#   · PAS de comparateur ni d'onglets « Pic » : on ne compare pas deux métros
#     comme deux PIB ;
#   · une rangée de CRITÈRES à la place, pour classer les pays de cinq façons ;
#   · un bouton de retour, qui ramène de la fiche d'une ville au classement.
MODELE_METRO = """<!DOCTYPE html>
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
  <link rel="preload" href="{base}{precharge}" as="fetch" crossorigin>
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
        <div class="onglets onglets--criteres" id="criteres" role="group"></div>
        <button class="panneau__retour" id="retour" type="button" hidden></button>
        <input class="panneau__recherche" id="recherche" type="search" autocomplete="off" spellcheck="false">
      </div>
      <ul class="classement" id="classement"></ul>
      <div class="panneau__pied" id="source"></div>
    </aside>

    <div class="legende" id="legende"></div>

    <div class="chargement" id="chargement">…</div>
  </div>

  <script src="{base}assets/js/i18n.js"></script>
  <script src="{base}assets/js/barre.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/maplibre-gl/{maplibre}/maplibre-gl.js"></script>
  <script src="{base}assets/js/{moteur}"></script>
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
{tete}

    <div class="vignettes">
{vignettes}
    </div>
  </main>

  <footer class="pied">{pied}</footer>

  <script src="{base}assets/js/barre.js"></script>
</body>
</html>
"""

# Le mot « accueil » dans chaque langue, pour les boutons de la page 404.
ACCUEIL_MOT = {"fr": "Accueil", "en": "Home"}

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

# Toutes les pages du site, dans l'ordre où elles comptent pour Google.
# Attention : une langue n'a pas forcément toutes ces pages — voir LANGUES_DE
# et la fonction pages_de() juste en dessous.
PAGES = ([ACCUEIL]
         + [("categorie", identifiant) for identifiant, _, _ in CATEGORIES_OUVERTES]
         + [("carte", identifiant) for identifiant, _, _, _, _ in CARTES])


def carte_dans(id_carte, code_langue):
    """Cette carte existe-t-elle dans cette langue ? (voir LANGUES_DE)"""
    return code_langue in LANGUES_DE.get(id_carte, [l["code"] for l in LANGUES])


def cartes_de(id_categorie, langue):
    """Les cartes d'une rubrique qui existent DANS CETTE LANGUE."""
    return [c for c in CARTES_DE[id_categorie] if carte_dans(c, langue["code"])]


def categories_ouvertes_de(langue):
    """Les rubriques qui ont au moins une carte dans cette langue.

    Une rubrique dont l'unique carte n'est pas encore traduite reste donc
    « Bientôt » dans cette langue, et ouverte dans les autres."""
    return [c for c in CATEGORIES_OUVERTES if cartes_de(c[0], langue)]


def pages_de(langue):
    """Les pages qui existent réellement dans cette langue."""
    return ([ACCUEIL]
            + [("categorie", i) for i, _, _ in categories_ouvertes_de(langue)]
            + [("carte", i) for i, _, _, _, _ in CARTES
               if carte_dans(i, langue["code"])])


def langues_de_la_page(page):
    """Les langues dans lesquelles cette page existe."""
    return [l for l in LANGUES if page in pages_de(l)]


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
    autres langues ». Le français fait aussi office de x-default, la version
    servie quand aucune langue du visiteur ne correspond.

    Seules les langues où la page existe VRAIMENT sont déclarées : annoncer à
    Google une traduction qui n'existe pas est la meilleure façon de récolter
    des erreurs 404 dans ses rapports."""
    langues = langues_de_la_page(page)
    lignes = []
    for langue in langues:
        lignes.append('  <link rel="alternate" hreflang="%s" href="%s%s">'
                      % (langue["hreflang"], SITE, adresse(langue, page)))
    lignes.append('  <link rel="alternate" hreflang="x-default" href="%s%s">'
                  % (SITE, adresse(langues[0], page)))
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
        for identifiant in cartes_de(categorie_ouverte, langue):
            carte = langue["cartes"][identifiant]
            # La page de la VARIANTE d'une carte allume quand même son entrée :
            # sur /pib-ppa/, c'est bien « PIB » qu'on est en train de voir.
            meme = clef == identifiant or (
                FAMILLE_DE[clef] and FAMILLE_DE[clef] == FAMILLE_DE[identifiant])
            liens.append(lien_de_menu(haut + carte["slug"] + "/",
                                      carte["nav"], carte["nav_court"], meme))
    else:
        # L'accueil et les pages de rubrique montrent les rubriques ouvertes.
        for identifiant, _, _ in categories_ouvertes_de(langue):
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
        # Si la page n'existe pas encore dans cette langue-là (une carte en
        # cours de traduction), son drapeau mène à l'accueil de cette langue
        # plutôt qu'à une adresse qui n'existe pas.
        cible = page if page in pages_de(autre) else ACCUEIL
        menu.append(
            '          <a href="%s" hreflang="%s" lang="%s"%s>'
            '<span class="drapeau" aria-hidden="true">%s</span>%s</a>'
            % (adresse(autre, cible), autre["hreflang"], autre["hreflang"],
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


def vignette(lien, pastille, titre, texte, liste="", bientot=""):
    """Une carte de la grille : sur l'accueil comme sur les pages de catégorie,
    c'est toujours le même objet.

    Sans lien, ce n'est plus un <a> mais un <div> : une rubrique annoncée et pas
    encore ouverte ne doit pas être cliquable. Un lien qui ne mène nulle part est
    la plus sûre façon de faire croire à une panne."""
    dedans = ""
    if liste:
        dedans = '        <div class="vignette__liste">%s</div>\n' % echapper(liste)
    if bientot:
        dedans = '        <div class="vignette__bientot">%s</div>\n' % echapper(bientot)

    # Pas de phrase de description dans la vignette (demande d'Antonin du
    # 20 novembre 2026) : le nom, et en dessous la liste des cartes, suffisent.
    # La phrase (« texte ») sert encore ailleurs : elle ouvre la description
    # que lit Google.
    corps = ('        <div class="vignette__pastille">%s</div>\n'
             '        <div class="vignette__titre">%s</div>\n'
             '%s'
             % (pastille, echapper(titre), dedans))

    if not lien:
        return '      <div class="vignette est-bientot">\n%s      </div>' % corps
    return '      <a class="vignette" href="%s">\n%s      </a>' % (lien, corps)


def page_carte(langue, id_carte):
    carte = langue["cartes"][id_carte]
    base = remonter(profondeur(langue, ("carte", id_carte)))
    # Les cartes des pays ont toutes le même titre type (« …, par pays ») ;
    # celle des métros parle de villes et porte donc le sien, écrit en toutes
    # lettres dans son bloc de langue.
    titre = carte.get("titre") or langue["modele_titre"].format(nom=carte["nom"])
    # Le titre partagé sur les réseaux sociaux n'a pas besoin du « | StatsMaps »
    # final : le nom du site y est déjà affiché à part.
    og_titre = titre.split(" | StatsMaps")[0]
    description = carte.get("description") or \
        langue["modele_description"].format(texte=carte["texte"])

    if id_carte in MOTEURS:
        return MODELE_METRO.format(
            hreflang=langue["hreflang"],
            rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
            titre=echapper(titre),
            description=echapper(description),
            url=SITE + adresse(langue, ("carte", id_carte)),
            alternates=alternates(("carte", id_carte)),
            base=base,
            og_titre=echapper(og_titre),
            maplibre=MAPLIBRE,
            indicateur=id_carte,
            code=langue["code"],
            entete=entete(langue, ("carte", id_carte)),
            h1=echapper(carte["nom"]),
            moteur=MOTEURS[id_carte],
            precharge=PRECHARGES[id_carte],
        )

    return MODELE_CARTE.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(titre),
        description=echapper(description),
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


def nom_dans_la_liste(langue, id_carte):
    """Le nom d'une carte dans la liste d'une vignette de l'accueil.

    Une carte qui existe en plusieurs versions annonce ses versions entre
    parenthèses : « PIB (Nominal/Parité de pouvoir d'achat) » plutôt que
    « PIB » tout court (demande d'Antonin du 20 novembre 2026). On sait ainsi,
    avant même de cliquer, qu'on trouvera les deux."""
    nom = langue["cartes"][id_carte]["nav"]
    famille = FAMILLE_DE[id_carte]
    if famille and len(FAMILLES[famille]) > 1:
        versions = "/".join(langue["variantes"][variante]
                            for _, variante in FAMILLES[famille])
        nom += " (%s)" % versions
    return nom


def page_accueil(langue):
    """L'accueil : les CATÉGORIES, et non les cartes. Chaque vignette annonce
    ce qu'elle contient, pour qu'on sache où l'on va avant de cliquer."""
    accueil = langue["accueil"]

    vignettes = []
    for identifiant, pastille, _ in CATEGORIES:
        categorie = langue["categories"][identifiant]
        cartes = cartes_de(identifiant, langue)
        if cartes:
            vignettes.append(vignette(
                categorie["slug"] + "/", pastille, categorie["nom"], categorie["texte"],
                liste=" · ".join(nom_dans_la_liste(langue, c) for c in cartes)))
        else:
            # Rubrique annoncée, pas encore ouverte : ni lien, ni page.
            vignettes.append(vignette(
                None, pastille, categorie["nom"], categorie["texte"],
                bientot=langue["accueil"]["bientot"]))

    return MODELE_VIGNETTES.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(accueil["titre"]),
        description=echapper(accueil["description"]),
        url=SITE + adresse(langue),
        alternates=alternates(ACCUEIL),
        base=remonter(profondeur(langue)),
        entete=entete(langue),
        # Sur l'accueil, ni grand titre ni phrase d'introduction (demande
        # d'Antonin du 20 novembre 2026) : on arrive directement sur les
        # rubriques. Le « h1 » reste écrit dans le bloc de chaque langue, au
        # cas où on voudrait le remettre, mais n'est plus mis dans la page.
        tete="",
        vignettes="\n".join(vignettes),
        pied=echapper(accueil["pied"]),
    )


def page_categorie(langue, id_categorie):
    """La page d'une rubrique : ses cartes, et rien d'autre."""
    categorie = langue["categories"][id_categorie]
    cartes = cartes_de(id_categorie, langue)
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
        # Le titre de la rubrique est son simple nom (« Économie »), sans
        # phrase d'introduction (demande d'Antonin du 20 novembre 2026). Le
        # « h1 » long (« L'économie mondiale, en cartes. ») et l'« intro »
        # restent écrits dans chaque langue, mais ne sont plus affichés.
        tete='    <h1 class="accueil__titre">%s</h1>\n' % echapper(categorie["nom"]),
        vignettes="\n".join(vignettes),
        pied=echapper(langue["accueil"]["pied"]),
    )


def sitemap():
    """La liste de toutes les pages, pour Google. Chaque adresse y déclare ses
    traduction : c'est ce qui évite que le site se fasse concurrence à
    lui-même dans les résultats de recherche.

    Volontairement sans <lastmod> : la date serait celle du jour où le script a
    tourné, pas celle du dernier vrai changement. Elle ferait donc bouger les
    lignes du fichier à chaque exécution, pour rien."""
    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
              '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    # Les accueils sont les portes d'entrée du site ; viennent ensuite les
    # catégories, puis les cartes elles-mêmes.
    priorites = {"accueil": "1.0", "categorie": "0.9", "carte": "0.8"}

    for page in PAGES:
        langues = langues_de_la_page(page)
        for langue in langues:
            lignes.append("  <url>")
            lignes.append("    <loc>%s%s</loc>" % (SITE, adresse(langue, page)))
            for autre in langues:
                lignes.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>'
                              % (autre["hreflang"], SITE, adresse(autre, page)))
            lignes.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>'
                          % (SITE, adresse(langues[0], page)))
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

    # Contrôle : chaque langue doit décrire toutes les cartes qu'elle propose
    # et toutes les catégories, sans oubli. Une carte pas encore traduite
    # (LANGUES_DE) n'est évidemment pas exigée.
    for langue in LANGUES:
        manquantes = [c[0] for c in CARTES
                      if carte_dans(c[0], langue["code"]) and c[0] not in langue["cartes"]]
        manquantes += [c[0] for c in CATEGORIES if c[0] not in langue["categories"]]
        if manquantes:
            raise SystemExit("  ERREUR : la langue « %s » ne décrit pas %s"
                             % (langue["code"], ", ".join(manquantes)))

    # Contrôle : une rubrique ouverte doit avoir son adresse et ses textes.
    for langue in LANGUES:
        for identifiant, _, _ in categories_ouvertes_de(langue):
            categorie = langue["categories"][identifiant]
            absents = [c for c in ("slug", "h1", "intro") if c not in categorie]
            if absents:
                raise SystemExit(
                    "  ERREUR : la rubrique « %s » est ouverte en %s mais il lui "
                    "manque %s" % (identifiant, langue["code"], ", ".join(absents)))

    # Contrôle : deux pages ne doivent jamais se retrouver à la même adresse.
    vues = {}
    for langue in LANGUES:
        for page in pages_de(langue):
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
        for id_categorie, _, _ in categories_ouvertes_de(langue):
            nom = langue["categories"][id_categorie]["slug"]
            dossiers_attendus.add(nom)
            ecrire(os.path.join(langue["dossier"], nom, "index.html"),
                   page_categorie(langue, id_categorie))
            total += 1
        for id_carte, _, _, _, _ in CARTES:
            if not carte_dans(id_carte, langue["code"]):
                continue
            nom = langue["cartes"][id_carte]["slug"]
            dossiers_attendus.add(nom)
            ecrire(os.path.join(langue["dossier"], nom, "index.html"),
                   page_carte(langue, id_carte))
            total += 1
        print("  %-3s %-12s %d pages   %s…"
              % (langue["code"], "(" + (langue["dossier"] or "racine") + ")",
                 len(pages_de(langue)), adresse(langue)))

    # Les anciennes langues : une page de renvoi vers l'anglais à chacune de
    # leurs anciennes adresses. On vide d'abord leurs dossiers, pour qu'il n'y
    # reste aucune vieille page qui ne serait plus mise à jour.
    anglais = [l for l in LANGUES if l["code"] == "en"][0]
    renvois = 0
    for dossier, pages in ANCIENNES_LANGUES.items():
        racine = os.path.join(RACINE, dossier)
        if os.path.isdir(racine):
            shutil.rmtree(racine)
        for chemin, page in pages.items():
            cible = adresse(anglais, page)
            ecrire(os.path.join(dossier, chemin, "index.html"), MODELE_RENVOI.format(
                url=SITE + cible, cible=cible))
            renvois += 1
    print("  %d anciennes adresses renvoient vers l'anglais (%s)"
          % (renvois, ", ".join(ANCIENNES_LANGUES)))

    # Les dossiers des langues ne sont pas des pages : on les protège.
    dossiers_attendus |= {l["dossier"] for l in LANGUES if l["dossier"]}
    dossiers_attendus |= set(ANCIENNES_LANGUES)
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
