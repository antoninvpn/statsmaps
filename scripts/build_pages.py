#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_pages.py — fabrique TOUTES les pages du site, dans les treize langues.

    python3 scripts/build_pages.py

Pourquoi ce script existe
-------------------------
Le site a 6 pages (l'accueil et les 5 cartes) et 13 langues, soit 78 fichiers
HTML. Ces 78 fichiers sont rigoureusement identiques à quelques mots près : le
titre, l'adresse, et la langue. Les écrire à la main voudrait dire, à chaque
petit changement — un lien dans le menu, une balise pour Google — répéter la
même retouche 78 fois sans en oublier une seule.

Ici, tout est écrit UNE fois : le modèle HTML en bas du fichier, et les textes
de chaque langue dans la grande liste LANGUES juste en dessous.

Ce que ce script fabrique
-------------------------
    index.html + 5 dossiers de carte ............ le français, à la racine
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
       traduire les titres et les descriptions).
    2. Ajouter son bloc dans assets/js/i18n.js (les textes des boutons).
    3. Ajouter son code dans le tableau LANGUES de build_geojson.py, puis
       relancer ce script-là : les noms des 197 pays viennent de Natural Earth
       et n'ont pas à être traduits à la main.
    4. Relancer ce script.

Pour ajouter une carte
----------------------
    1. Une ligne dans INDICATEURS de build_donnees.py.
    2. Les tranches de couleur dans CARTES de assets/js/carte.js.
    3. Son entrée "cartes" dans CHACUN des blocs de LANGUES ci-dessous.
    4. Relancer ce script : les 13 pages, les menus et le sitemap suivent.
"""

import io
import os

SITE = "https://statsmaps.com"
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# L'ordre des cartes, tel qu'il apparaît dans le menu et sur l'accueil.
# La pastille est l'emoji de la vignette ; il ne dépend pas de la langue.
CARTES = [
    ("pib-nominal", "💰"),
    ("pib-par-habitant", "👤"),
    ("croissance", "📈"),
    ("annee-record-pib", "🏔️"),
    ("annee-record-pib-par-habitant", "⛰️"),
]

# La version de MapLibre, écrite une seule fois pour les 65 pages de carte.
MAPLIBRE = "5.6.1"


# ==========================================================================
#  LES TREIZE LANGUES
#
#  Un bloc par langue, avec TOUT ce qui la concerne. C'est volontairement
#  répétitif : pour corriger une faute en allemand, on ouvre le bloc "de" et
#  tout y est, sans avoir à sauter d'un fichier à l'autre.
#
#  - code ........ celui de i18n.js et de build_geojson.py
#  - dossier ..... le dossier du site ("" pour le français, à la racine)
#  - hreflang .... le code que lit Google (celui de l'ukrainien est "uk",
#                  alors que son dossier s'appelle "ua" — c'est voulu)
#  - sens ........ "rtl" pour les langues qui s'écrivent de droite à gauche
#  - slug ........ l'adresse de la page. Traduite quand la langue s'écrit en
#                  alphabet latin ; en anglais pour le japonais, le coréen,
#                  l'hindi et l'arabe, où une adresse en écriture native
#                  deviendrait illisible une fois encodée par le navigateur
#                  (%E4%B8%80%E4%BA%BA...), et où « GDP » est de toute façon
#                  la forme employée couramment.
# ==========================================================================

LANGUES = []

# --------------------------------------------------------------- Français ---
LANGUES.append({
    "code": "fr", "dossier": "", "hreflang": "fr", "sens": "ltr",
    "drapeau": "🇫🇷", "nom": "Français", "nav_aria": "Cartes",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Langue", "theme_label": "Changer de thème",
    "theme_clair": "Passer en thème clair", "theme_sombre": "Passer en thème sombre",
    "accueil": {
        "titre": "StatsMaps — cartes et statistiques mondiales",
        "description": "Cartes interactives des statistiques mondiales : PIB nominal, PIB par habitant, croissance et années record de 197 pays, de 1980 à 2031, à partir des données officielles du FMI.",
        "h1": "Les statistiques du monde, en cartes.",
        "intro": "StatsMaps met en carte les grands indicateurs mondiaux à partir de sources officielles. Aujourd’hui l’économie, à partir des données du Fonds monétaire international : 197 pays, de 1980 à 2031.",
        "bientot": "Bientôt : démographie, infrastructures, énergie, éducation et santé.",
        "pied": "Données : FMI (World Economic Outlook) · Fond de carte : Natural Earth · Site sans publicité ni traceur.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pib-nominal",
            "titre": "PIB nominal par pays — carte mondiale interactive | StatsMaps",
            "description": "Carte interactive du PIB nominal de 197 pays, de 1980 à 2031. Données officielles du FMI (World Economic Outlook), classement mondial et évolution année par année.",
            "h1": "PIB nominal", "nav": "PIB nominal", "nav_court": "PIB",
            "vignette": "PIB nominal",
            "vignette_texte": "La taille de chaque économie, en milliards de dollars courants.",
        },
        "pib-par-habitant": {
            "slug": "pib-par-habitant",
            "titre": "PIB par habitant par pays — carte mondiale interactive | StatsMaps",
            "description": "Carte interactive du PIB par habitant de 197 pays, de 1980 à 2031. Données officielles du FMI, classement mondial et niveau de richesse par personne.",
            "h1": "PIB par habitant", "nav": "PIB par habitant", "nav_court": "PIB/hab.",
            "vignette": "PIB par habitant",
            "vignette_texte": "La richesse produite par personne, en dollars courants.",
        },
        "croissance": {
            "slug": "croissance",
            "titre": "Croissance du PIB par pays — carte mondiale interactive | StatsMaps",
            "description": "Carte interactive de la croissance du PIB réel de 197 pays, de 1980 à 2031. Données officielles du FMI : récessions en rouge, expansions en vert.",
            "h1": "Croissance", "nav": "Croissance", "nav_court": "Croissance",
            "vignette": "Croissance du PIB",
            "vignette_texte": "L’évolution du PIB réel d’une année sur l’autre, en pourcentage.",
        },
        "annee-record-pib": {
            "slug": "annee-record-pib",
            "titre": "Année record du PIB par pays — carte mondiale interactive | StatsMaps",
            "description": "Carte interactive de l’année où le PIB de chaque pays a été le plus élevé, de 1980 à 2031, projections du FMI comprises. En vert les pays au sommet aujourd’hui, en rouge ceux qui n’ont jamais retrouvé leur record. Données officielles du FMI.",
            "h1": "Année record du PIB", "nav": "Année record du PIB", "nav_court": "Record PIB",
            "vignette": "Année record du PIB",
            "vignette_texte": "L’année où chaque pays a été à son maximum — et ceux qui n’y sont jamais revenus.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "annee-record-pib-par-habitant",
            "titre": "Année record du PIB par habitant — carte mondiale interactive | StatsMaps",
            "description": "Carte interactive de l’année où le PIB par habitant de chaque pays a été le plus élevé, de 1980 à 2031, projections du FMI comprises. En vert les pays au sommet aujourd’hui, en rouge ceux qui n’ont jamais retrouvé leur record. Données officielles du FMI.",
            "h1": "Année record du PIB par hab.",
            "nav": "Année record du PIB par hab.", "nav_court": "Record PIB/hab.",
            "vignette": "Année record du PIB par hab.",
            "vignette_texte": "L’année où chaque habitant a été le plus riche, en moyenne.",
        },
    },
})

# ---------------------------------------------------------------- Anglais ---
LANGUES.append({
    "code": "en", "dossier": "en", "hreflang": "en", "sens": "ltr",
    "drapeau": "🇬🇧", "nom": "English", "nav_aria": "Maps",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Language", "theme_label": "Change theme",
    "theme_clair": "Switch to light theme", "theme_sombre": "Switch to dark theme",
    "accueil": {
        "titre": "StatsMaps — world statistics on interactive maps",
        "description": "Interactive maps of world statistics: nominal GDP, GDP per capita, growth and peak years for 197 countries, from 1980 to 2031, based on official IMF data.",
        "h1": "The world’s statistics, mapped.",
        "intro": "StatsMaps turns major global indicators into interactive maps, using official sources. Starting with the economy, based on International Monetary Fund data: 197 countries, from 1980 to 2031.",
        "bientot": "Coming soon: demographics, infrastructure, energy, education and health.",
        "pied": "Data: IMF (World Economic Outlook) · Basemap: Natural Earth · No ads, no trackers.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "gdp",
            "titre": "Nominal GDP by country — interactive world map | StatsMaps",
            "description": "Interactive map of nominal GDP for 197 countries, from 1980 to 2031. Official IMF data (World Economic Outlook), world ranking and year-by-year evolution.",
            "h1": "Nominal GDP", "nav": "Nominal GDP", "nav_court": "GDP",
            "vignette": "Nominal GDP",
            "vignette_texte": "The size of each economy, in billions of current US dollars.",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "titre": "GDP per capita by country — interactive world map | StatsMaps",
            "description": "Interactive map of GDP per capita for 197 countries, from 1980 to 2031. Official IMF data, world ranking and wealth level per person.",
            "h1": "GDP per capita", "nav": "GDP per capita", "nav_court": "GDP/cap.",
            "vignette": "GDP per capita",
            "vignette_texte": "Wealth produced per person, in current US dollars.",
        },
        "croissance": {
            "slug": "growth",
            "titre": "GDP growth by country — interactive world map | StatsMaps",
            "description": "Interactive map of real GDP growth for 197 countries, from 1980 to 2031. Official IMF data: recessions in red, expansions in green.",
            "h1": "Growth", "nav": "Growth", "nav_court": "Growth",
            "vignette": "GDP growth",
            "vignette_texte": "Year-on-year change in real GDP, as a percentage.",
        },
        "annee-record-pib": {
            "slug": "when-gdp-peaked",
            "titre": "When GDP peaked, by country — interactive world map | StatsMaps",
            "description": "Interactive map showing the year each country’s GDP peaked, from 1980 to 2031, including IMF projections. Green for countries at their peak today, red for those that never recovered. Official IMF data.",
            "h1": "When GDP peaked", "nav": "When GDP peaked", "nav_court": "GDP peak",
            "vignette": "When GDP peaked",
            "vignette_texte": "The year each country hit its maximum — and those that never got back there.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "when-gdp-per-capita-peaked",
            "titre": "When GDP per capita peaked, by country — interactive world map | StatsMaps",
            "description": "Interactive map showing the year each country’s GDP per capita peaked, from 1980 to 2031, including IMF projections. Green for countries at their peak today, red for those that never recovered. Official IMF data.",
            "h1": "When GDP per capita peaked",
            "nav": "When GDP per capita peaked", "nav_court": "GDP/cap. peak",
            "vignette": "When GDP per capita peaked",
            "vignette_texte": "The year each country’s people were at their richest, on average.",
        },
    },
})

# -------------------------------------------------------------- Ukrainien ---
# Le dossier s'appelle "ua" — ce qu'écrivent les Ukrainiens — mais le code
# déclaré à Google reste "uk", le seul officiel.
LANGUES.append({
    "code": "uk", "dossier": "ua", "hreflang": "uk", "sens": "ltr",
    "drapeau": "🇺🇦", "nom": "Українська", "nav_aria": "Карти",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Мова", "theme_label": "Змінити тему",
    "theme_clair": "Перемкнути на світлу тему", "theme_sombre": "Перемкнути на темну тему",
    "accueil": {
        "titre": "StatsMaps — світова статистика на інтерактивних картах",
        "description": "Інтерактивні карти світової статистики: номінальний ВВП, ВВП на душу населення, зростання та рекордні роки для 197 країн, від 1980 до 2031 року, за офіційними даними МВФ.",
        "h1": "Статистика світу — на картах.",
        "intro": "StatsMaps перетворює головні світові показники на інтерактивні карти, спираючись на офіційні джерела. Починаємо з економіки, за даними Міжнародного валютного фонду: 197 країн, від 1980 до 2031 року.",
        "bientot": "Незабаром: демографія, інфраструктура, енергетика, освіта та охорона здоров’я.",
        "pied": "Дані: МВФ (World Economic Outlook) · Основа карти: Natural Earth · Без реклами та стеження.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "vvp",
            "titre": "Номінальний ВВП за країнами — інтерактивна карта світу | StatsMaps",
            "description": "Інтерактивна карта номінального ВВП 197 країн, від 1980 до 2031 року. Офіційні дані МВФ (World Economic Outlook), світовий рейтинг і зміни рік за роком.",
            "h1": "Номінальний ВВП", "nav": "Номінальний ВВП", "nav_court": "ВВП",
            "vignette": "Номінальний ВВП",
            "vignette_texte": "Розмір кожної економіки, у мільярдах доларів у поточних цінах.",
        },
        "pib-par-habitant": {
            "slug": "vvp-na-osobu",
            "titre": "ВВП на душу населення за країнами — інтерактивна карта світу | StatsMaps",
            "description": "Інтерактивна карта ВВП на душу населення 197 країн, від 1980 до 2031 року. Офіційні дані МВФ, світовий рейтинг і рівень багатства на особу.",
            "h1": "ВВП на душу населення",
            "nav": "ВВП на душу населення", "nav_court": "ВВП/особу",
            "vignette": "ВВП на душу населення",
            "vignette_texte": "Багатство, вироблене на одну особу, у доларах у поточних цінах.",
        },
        "croissance": {
            "slug": "zrostannia",
            "titre": "Зростання ВВП за країнами — інтерактивна карта світу | StatsMaps",
            "description": "Інтерактивна карта зростання реального ВВП 197 країн, від 1980 до 2031 року. Офіційні дані МВФ: спад — червоним, зростання — зеленим.",
            "h1": "Зростання", "nav": "Зростання", "nav_court": "Зростання",
            "vignette": "Зростання ВВП",
            "vignette_texte": "Зміна реального ВВП рік до року, у відсотках.",
        },
        "annee-record-pib": {
            "slug": "rekordnyi-rik-vvp",
            "titre": "Рекордний рік ВВП за країнами — інтерактивна карта світу | StatsMaps",
            "description": "Інтерактивна карта року, коли ВВП кожної країни був найвищим, від 1980 до 2031 року, включно з прогнозами МВФ. Зеленим — країни на піку сьогодні, червоним — ті, що так і не повернулися до рекорду. Офіційні дані МВФ.",
            "h1": "Рекордний рік ВВП", "nav": "Рекордний рік ВВП", "nav_court": "Рекорд ВВП",
            "vignette": "Рекордний рік ВВП",
            "vignette_texte": "Рік, коли кожна країна досягла свого максимуму — і ті, що туди так і не повернулися.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "rekordnyi-rik-vvp-na-osobu",
            "titre": "Рекордний рік ВВП на душу населення — інтерактивна карта світу | StatsMaps",
            "description": "Інтерактивна карта року, коли ВВП на душу населення кожної країни був найвищим, від 1980 до 2031 року, включно з прогнозами МВФ. Зеленим — країни на піку сьогодні, червоним — ті, що так і не повернулися до рекорду. Офіційні дані МВФ.",
            "h1": "Рекордний рік ВВП на особу",
            "nav": "Рекордний рік ВВП на особу", "nav_court": "Рекорд ВВП/особу",
            "vignette": "Рекордний рік ВВП на особу",
            "vignette_texte": "Рік, коли мешканці кожної країни були найбагатшими в середньому.",
        },
    },
})

# --------------------------------------------------------------- Allemand ---
LANGUES.append({
    "code": "de", "dossier": "de", "hreflang": "de", "sens": "ltr",
    "drapeau": "🇩🇪", "nom": "Deutsch", "nav_aria": "Karten",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Sprache", "theme_label": "Design wechseln",
    "theme_clair": "Zum hellen Design wechseln", "theme_sombre": "Zum dunklen Design wechseln",
    "accueil": {
        "titre": "StatsMaps — Weltstatistiken auf interaktiven Karten",
        "description": "Interaktive Karten der Weltwirtschaft: nominales BIP, BIP pro Kopf, Wachstum und Höchststände von 197 Ländern, von 1980 bis 2031, auf Grundlage offizieller IWF-Daten.",
        "h1": "Die Statistiken der Welt, als Karte.",
        "intro": "StatsMaps bringt die großen weltweiten Kennzahlen auf interaktive Karten, aus offiziellen Quellen. Den Anfang macht die Wirtschaft, mit Daten des Internationalen Währungsfonds: 197 Länder, von 1980 bis 2031.",
        "bientot": "Demnächst: Bevölkerung, Infrastruktur, Energie, Bildung und Gesundheit.",
        "pied": "Daten: IWF (World Economic Outlook) · Kartengrundlage: Natural Earth · Ohne Werbung, ohne Tracker.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominales-bip",
            "titre": "Nominales BIP nach Ländern — interaktive Weltkarte | StatsMaps",
            "description": "Interaktive Karte des nominalen BIP von 197 Ländern, von 1980 bis 2031. Offizielle IWF-Daten (World Economic Outlook), weltweite Rangliste und Entwicklung Jahr für Jahr.",
            "h1": "Nominales BIP", "nav": "Nominales BIP", "nav_court": "BIP",
            "vignette": "Nominales BIP",
            "vignette_texte": "Die Größe jeder Volkswirtschaft, in Milliarden US-Dollar zu jeweiligen Preisen.",
        },
        "pib-par-habitant": {
            "slug": "bip-pro-kopf",
            "titre": "BIP pro Kopf nach Ländern — interaktive Weltkarte | StatsMaps",
            "description": "Interaktive Karte des BIP pro Kopf von 197 Ländern, von 1980 bis 2031. Offizielle IWF-Daten, weltweite Rangliste und Wohlstandsniveau je Person.",
            "h1": "BIP pro Kopf", "nav": "BIP pro Kopf", "nav_court": "BIP/Kopf",
            "vignette": "BIP pro Kopf",
            "vignette_texte": "Die je Person erwirtschaftete Leistung, in US-Dollar zu jeweiligen Preisen.",
        },
        "croissance": {
            "slug": "bip-wachstum",
            "titre": "BIP-Wachstum nach Ländern — interaktive Weltkarte | StatsMaps",
            "description": "Interaktive Karte des realen BIP-Wachstums von 197 Ländern, von 1980 bis 2031. Offizielle IWF-Daten: Rezessionen in Rot, Aufschwünge in Grün.",
            "h1": "Wachstum", "nav": "Wachstum", "nav_court": "Wachstum",
            "vignette": "BIP-Wachstum",
            "vignette_texte": "Die Veränderung des realen BIP von Jahr zu Jahr, in Prozent.",
        },
        "annee-record-pib": {
            "slug": "bip-hoechststand",
            "titre": "BIP-Höchststand nach Ländern — interaktive Weltkarte | StatsMaps",
            "description": "Interaktive Karte des Jahres, in dem das BIP jedes Landes am höchsten war, von 1980 bis 2031, IWF-Prognosen inbegriffen. Grün für Länder, die heute auf ihrem Höchststand sind, rot für jene, die ihn nie wieder erreicht haben. Offizielle IWF-Daten.",
            "h1": "BIP-Höchststand", "nav": "BIP-Höchststand", "nav_court": "BIP-Höchst.",
            "vignette": "BIP-Höchststand",
            "vignette_texte": "Das Jahr, in dem jedes Land sein Maximum erreichte — und jene, die nie dorthin zurückkehrten.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "bip-pro-kopf-hoechststand",
            "titre": "Höchststand des BIP pro Kopf — interaktive Weltkarte | StatsMaps",
            "description": "Interaktive Karte des Jahres, in dem das BIP pro Kopf jedes Landes am höchsten war, von 1980 bis 2031, IWF-Prognosen inbegriffen. Grün für Länder, die heute auf ihrem Höchststand sind, rot für jene, die ihn nie wieder erreicht haben. Offizielle IWF-Daten.",
            "h1": "Höchststand BIP pro Kopf",
            "nav": "Höchststand BIP pro Kopf", "nav_court": "BIP/Kopf-Höchst.",
            "vignette": "Höchststand BIP pro Kopf",
            "vignette_texte": "Das Jahr, in dem die Menschen jedes Landes im Schnitt am wohlhabendsten waren.",
        },
    },
})

# --------------------------------------------------------------- Espagnol ---
LANGUES.append({
    "code": "es", "dossier": "es", "hreflang": "es", "sens": "ltr",
    "drapeau": "🇪🇸", "nom": "Español", "nav_aria": "Mapas",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Idioma", "theme_label": "Cambiar de tema",
    "theme_clair": "Cambiar al tema claro", "theme_sombre": "Cambiar al tema oscuro",
    "accueil": {
        "titre": "StatsMaps — estadísticas mundiales en mapas interactivos",
        "description": "Mapas interactivos de la economía mundial: PIB nominal, PIB per cápita, crecimiento y años récord de 197 países, de 1980 a 2031, a partir de datos oficiales del FMI.",
        "h1": "Las estadísticas del mundo, en mapas.",
        "intro": "StatsMaps lleva los grandes indicadores mundiales a mapas interactivos, a partir de fuentes oficiales. Empezamos por la economía, con datos del Fondo Monetario Internacional: 197 países, de 1980 a 2031.",
        "bientot": "Próximamente: demografía, infraestructuras, energía, educación y salud.",
        "pied": "Datos: FMI (World Economic Outlook) · Mapa base: Natural Earth · Sin publicidad ni rastreadores.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pib-nominal",
            "titre": "PIB nominal por país — mapa mundial interactivo | StatsMaps",
            "description": "Mapa interactivo del PIB nominal de 197 países, de 1980 a 2031. Datos oficiales del FMI (World Economic Outlook), clasificación mundial y evolución año a año.",
            "h1": "PIB nominal", "nav": "PIB nominal", "nav_court": "PIB",
            "vignette": "PIB nominal",
            "vignette_texte": "El tamaño de cada economía, en miles de millones de dólares corrientes.",
        },
        "pib-par-habitant": {
            "slug": "pib-per-capita",
            "titre": "PIB per cápita por país — mapa mundial interactivo | StatsMaps",
            "description": "Mapa interactivo del PIB per cápita de 197 países, de 1980 a 2031. Datos oficiales del FMI, clasificación mundial y nivel de riqueza por persona.",
            "h1": "PIB per cápita", "nav": "PIB per cápita", "nav_court": "PIB/hab.",
            "vignette": "PIB per cápita",
            "vignette_texte": "La riqueza producida por persona, en dólares corrientes.",
        },
        "croissance": {
            "slug": "crecimiento-pib",
            "titre": "Crecimiento del PIB por país — mapa mundial interactivo | StatsMaps",
            "description": "Mapa interactivo del crecimiento del PIB real de 197 países, de 1980 a 2031. Datos oficiales del FMI: recesiones en rojo, expansiones en verde.",
            "h1": "Crecimiento", "nav": "Crecimiento", "nav_court": "Crecimiento",
            "vignette": "Crecimiento del PIB",
            "vignette_texte": "La variación del PIB real de un año a otro, en porcentaje.",
        },
        "annee-record-pib": {
            "slug": "ano-record-pib",
            "titre": "Año récord del PIB por país — mapa mundial interactivo | StatsMaps",
            "description": "Mapa interactivo del año en que el PIB de cada país alcanzó su máximo, de 1980 a 2031, proyecciones del FMI incluidas. En verde los países que hoy están en su máximo, en rojo los que nunca lo recuperaron. Datos oficiales del FMI.",
            "h1": "Año récord del PIB", "nav": "Año récord del PIB", "nav_court": "Récord PIB",
            "vignette": "Año récord del PIB",
            "vignette_texte": "El año en que cada país alcanzó su máximo — y los que nunca volvieron a él.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "ano-record-pib-per-capita",
            "titre": "Año récord del PIB per cápita — mapa mundial interactivo | StatsMaps",
            "description": "Mapa interactivo del año en que el PIB per cápita de cada país alcanzó su máximo, de 1980 a 2031, proyecciones del FMI incluidas. En verde los países que hoy están en su máximo, en rojo los que nunca lo recuperaron. Datos oficiales del FMI.",
            "h1": "Año récord del PIB per cápita",
            "nav": "Año récord del PIB per cápita", "nav_court": "Récord PIB/hab.",
            "vignette": "Año récord del PIB per cápita",
            "vignette_texte": "El año en que los habitantes de cada país fueron, de media, más ricos.",
        },
    },
})

# ---------------------------------------------------------------- Italien ---
LANGUES.append({
    "code": "it", "dossier": "it", "hreflang": "it", "sens": "ltr",
    "drapeau": "🇮🇹", "nom": "Italiano", "nav_aria": "Mappe",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Lingua", "theme_label": "Cambia tema",
    "theme_clair": "Passa al tema chiaro", "theme_sombre": "Passa al tema scuro",
    "accueil": {
        "titre": "StatsMaps — statistiche mondiali su mappe interattive",
        "description": "Mappe interattive dell’economia mondiale: PIL nominale, PIL pro capite, crescita e anni record di 197 paesi, dal 1980 al 2031, dai dati ufficiali del FMI.",
        "h1": "Le statistiche del mondo, in mappa.",
        "intro": "StatsMaps trasforma i grandi indicatori mondiali in mappe interattive, a partire da fonti ufficiali. Si comincia dall’economia, con i dati del Fondo Monetario Internazionale: 197 paesi, dal 1980 al 2031.",
        "bientot": "Prossimamente: demografia, infrastrutture, energia, istruzione e sanità.",
        "pied": "Dati: FMI (World Economic Outlook) · Mappa di base: Natural Earth · Senza pubblicità né tracciamento.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pil-nominale",
            "titre": "PIL nominale per paese — mappa mondiale interattiva | StatsMaps",
            "description": "Mappa interattiva del PIL nominale di 197 paesi, dal 1980 al 2031. Dati ufficiali del FMI (World Economic Outlook), classifica mondiale ed evoluzione anno per anno.",
            "h1": "PIL nominale", "nav": "PIL nominale", "nav_court": "PIL",
            "vignette": "PIL nominale",
            "vignette_texte": "La dimensione di ogni economia, in miliardi di dollari correnti.",
        },
        "pib-par-habitant": {
            "slug": "pil-pro-capite",
            "titre": "PIL pro capite per paese — mappa mondiale interattiva | StatsMaps",
            "description": "Mappa interattiva del PIL pro capite di 197 paesi, dal 1980 al 2031. Dati ufficiali del FMI, classifica mondiale e livello di ricchezza per persona.",
            "h1": "PIL pro capite", "nav": "PIL pro capite", "nav_court": "PIL/ab.",
            "vignette": "PIL pro capite",
            "vignette_texte": "La ricchezza prodotta per persona, in dollari correnti.",
        },
        "croissance": {
            "slug": "crescita-pil",
            "titre": "Crescita del PIL per paese — mappa mondiale interattiva | StatsMaps",
            "description": "Mappa interattiva della crescita del PIL reale di 197 paesi, dal 1980 al 2031. Dati ufficiali del FMI: recessioni in rosso, espansioni in verde.",
            "h1": "Crescita", "nav": "Crescita", "nav_court": "Crescita",
            "vignette": "Crescita del PIL",
            "vignette_texte": "La variazione del PIL reale da un anno all’altro, in percentuale.",
        },
        "annee-record-pib": {
            "slug": "anno-record-pil",
            "titre": "Anno record del PIL per paese — mappa mondiale interattiva | StatsMaps",
            "description": "Mappa interattiva dell’anno in cui il PIL di ogni paese ha toccato il massimo, dal 1980 al 2031, proiezioni del FMI comprese. In verde i paesi oggi al massimo, in rosso quelli che non l’hanno più ritrovato. Dati ufficiali del FMI.",
            "h1": "Anno record del PIL", "nav": "Anno record del PIL", "nav_court": "Record PIL",
            "vignette": "Anno record del PIL",
            "vignette_texte": "L’anno in cui ogni paese ha toccato il massimo — e quelli che non ci sono più tornati.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "anno-record-pil-pro-capite",
            "titre": "Anno record del PIL pro capite — mappa mondiale interattiva | StatsMaps",
            "description": "Mappa interattiva dell’anno in cui il PIL pro capite di ogni paese ha toccato il massimo, dal 1980 al 2031, proiezioni del FMI comprese. In verde i paesi oggi al massimo, in rosso quelli che non l’hanno più ritrovato. Dati ufficiali del FMI.",
            "h1": "Anno record del PIL pro capite",
            "nav": "Anno record del PIL pro capite", "nav_court": "Record PIL/ab.",
            "vignette": "Anno record del PIL pro capite",
            "vignette_texte": "L’anno in cui gli abitanti di ogni paese sono stati mediamente più ricchi.",
        },
    },
})

# -------------------------------------------------------------- Portugais ---
LANGUES.append({
    "code": "pt", "dossier": "pt", "hreflang": "pt", "sens": "ltr",
    "drapeau": "🇵🇹", "nom": "Português", "nav_aria": "Mapas",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Idioma", "theme_label": "Mudar de tema",
    "theme_clair": "Mudar para o tema claro", "theme_sombre": "Mudar para o tema escuro",
    "accueil": {
        "titre": "StatsMaps — estatísticas mundiais em mapas interativos",
        "description": "Mapas interativos da economia mundial: PIB nominal, PIB per capita, crescimento e anos recorde de 197 países, de 1980 a 2031, a partir dos dados oficiais do FMI.",
        "h1": "As estatísticas do mundo, em mapas.",
        "intro": "O StatsMaps transforma os grandes indicadores mundiais em mapas interativos, a partir de fontes oficiais. Começamos pela economia, com os dados do Fundo Monetário Internacional: 197 países, de 1980 a 2031.",
        "bientot": "Em breve: demografia, infraestruturas, energia, educação e saúde.",
        "pied": "Dados: FMI (World Economic Outlook) · Mapa base: Natural Earth · Sem publicidade nem rastreadores.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pib-nominal",
            "titre": "PIB nominal por país — mapa mundial interativo | StatsMaps",
            "description": "Mapa interativo do PIB nominal de 197 países, de 1980 a 2031. Dados oficiais do FMI (World Economic Outlook), classificação mundial e evolução ano a ano.",
            "h1": "PIB nominal", "nav": "PIB nominal", "nav_court": "PIB",
            "vignette": "PIB nominal",
            "vignette_texte": "O tamanho de cada economia, em mil milhões de dólares correntes.",
        },
        "pib-par-habitant": {
            "slug": "pib-per-capita",
            "titre": "PIB per capita por país — mapa mundial interativo | StatsMaps",
            "description": "Mapa interativo do PIB per capita de 197 países, de 1980 a 2031. Dados oficiais do FMI, classificação mundial e nível de riqueza por pessoa.",
            "h1": "PIB per capita", "nav": "PIB per capita", "nav_court": "PIB/hab.",
            "vignette": "PIB per capita",
            "vignette_texte": "A riqueza produzida por pessoa, em dólares correntes.",
        },
        "croissance": {
            "slug": "crescimento-pib",
            "titre": "Crescimento do PIB por país — mapa mundial interativo | StatsMaps",
            "description": "Mapa interativo do crescimento do PIB real de 197 países, de 1980 a 2031. Dados oficiais do FMI: recessões a vermelho, expansões a verde.",
            "h1": "Crescimento", "nav": "Crescimento", "nav_court": "Crescimento",
            "vignette": "Crescimento do PIB",
            "vignette_texte": "A variação do PIB real de um ano para o outro, em percentagem.",
        },
        "annee-record-pib": {
            "slug": "ano-recorde-pib",
            "titre": "Ano recorde do PIB por país — mapa mundial interativo | StatsMaps",
            "description": "Mapa interativo do ano em que o PIB de cada país atingiu o máximo, de 1980 a 2031, projeções do FMI incluídas. A verde os países hoje no máximo, a vermelho os que nunca o recuperaram. Dados oficiais do FMI.",
            "h1": "Ano recorde do PIB", "nav": "Ano recorde do PIB", "nav_court": "Recorde PIB",
            "vignette": "Ano recorde do PIB",
            "vignette_texte": "O ano em que cada país atingiu o seu máximo — e aqueles que nunca lá voltaram.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "ano-recorde-pib-per-capita",
            "titre": "Ano recorde do PIB per capita — mapa mundial interativo | StatsMaps",
            "description": "Mapa interativo do ano em que o PIB per capita de cada país atingiu o máximo, de 1980 a 2031, projeções do FMI incluídas. A verde os países hoje no máximo, a vermelho os que nunca o recuperaram. Dados oficiais do FMI.",
            "h1": "Ano recorde do PIB per capita",
            "nav": "Ano recorde do PIB per capita", "nav_court": "Recorde PIB/hab.",
            "vignette": "Ano recorde do PIB per capita",
            "vignette_texte": "O ano em que os habitantes de cada país foram, em média, mais ricos.",
        },
    },
})

# --------------------------------------------------------------- Polonais ---
LANGUES.append({
    "code": "pl", "dossier": "pl", "hreflang": "pl", "sens": "ltr",
    "drapeau": "🇵🇱", "nom": "Polski", "nav_aria": "Mapy",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Język", "theme_label": "Zmień motyw",
    "theme_clair": "Przełącz na jasny motyw", "theme_sombre": "Przełącz na ciemny motyw",
    "accueil": {
        "titre": "StatsMaps — światowe statystyki na interaktywnych mapach",
        "description": "Interaktywne mapy gospodarki świata: PKB nominalne, PKB na mieszkańca, wzrost i rekordowe lata 197 krajów, od 1980 do 2031 roku, na podstawie oficjalnych danych MFW.",
        "h1": "Statystyki świata na mapach.",
        "intro": "StatsMaps przedstawia najważniejsze światowe wskaźniki na interaktywnych mapach, w oparciu o oficjalne źródła. Zaczynamy od gospodarki, na podstawie danych Międzynarodowego Funduszu Walutowego: 197 krajów, od 1980 do 2031 roku.",
        "bientot": "Wkrótce: demografia, infrastruktura, energetyka, edukacja i zdrowie.",
        "pied": "Dane: MFW (World Economic Outlook) · Podkład mapowy: Natural Earth · Bez reklam i śledzenia.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "pkb-nominalne",
            "titre": "PKB nominalne według krajów — interaktywna mapa świata | StatsMaps",
            "description": "Interaktywna mapa PKB nominalnego 197 krajów, od 1980 do 2031 roku. Oficjalne dane MFW (World Economic Outlook), ranking światowy i zmiany rok po roku.",
            "h1": "PKB nominalne", "nav": "PKB nominalne", "nav_court": "PKB",
            "vignette": "PKB nominalne",
            "vignette_texte": "Wielkość każdej gospodarki, w miliardach dolarów bieżących.",
        },
        "pib-par-habitant": {
            "slug": "pkb-na-mieszkanca",
            "titre": "PKB na mieszkańca według krajów — interaktywna mapa świata | StatsMaps",
            "description": "Interaktywna mapa PKB na mieszkańca 197 krajów, od 1980 do 2031 roku. Oficjalne dane MFW, ranking światowy i poziom zamożności na osobę.",
            "h1": "PKB na mieszkańca", "nav": "PKB na mieszkańca", "nav_court": "PKB/mieszk.",
            "vignette": "PKB na mieszkańca",
            "vignette_texte": "Bogactwo wytworzone na osobę, w dolarach bieżących.",
        },
        "croissance": {
            "slug": "wzrost-pkb",
            "titre": "Wzrost PKB według krajów — interaktywna mapa świata | StatsMaps",
            "description": "Interaktywna mapa wzrostu realnego PKB 197 krajów, od 1980 do 2031 roku. Oficjalne dane MFW: recesje na czerwono, wzrost na zielono.",
            "h1": "Wzrost", "nav": "Wzrost", "nav_court": "Wzrost",
            "vignette": "Wzrost PKB",
            "vignette_texte": "Zmiana realnego PKB z roku na rok, w procentach.",
        },
        "annee-record-pib": {
            "slug": "rekordowy-rok-pkb",
            "titre": "Rekordowy rok PKB według krajów — interaktywna mapa świata | StatsMaps",
            "description": "Interaktywna mapa roku, w którym PKB każdego kraju było najwyższe, od 1980 do 2031 roku, wraz z prognozami MFW. Na zielono kraje dziś na szczycie, na czerwono te, które nigdy nie wróciły do rekordu. Oficjalne dane MFW.",
            "h1": "Rekordowy rok PKB", "nav": "Rekordowy rok PKB", "nav_court": "Rekord PKB",
            "vignette": "Rekordowy rok PKB",
            "vignette_texte": "Rok, w którym każdy kraj osiągnął maksimum — i te, które już do niego nie wróciły.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "rekordowy-rok-pkb-na-mieszkanca",
            "titre": "Rekordowy rok PKB na mieszkańca — interaktywna mapa świata | StatsMaps",
            "description": "Interaktywna mapa roku, w którym PKB na mieszkańca każdego kraju było najwyższe, od 1980 do 2031 roku, wraz z prognozami MFW. Na zielono kraje dziś na szczycie, na czerwono te, które nigdy nie wróciły do rekordu. Oficjalne dane MFW.",
            "h1": "Rekordowy rok PKB na mieszkańca",
            "nav": "Rekordowy rok PKB na mieszkańca", "nav_court": "Rekord PKB/mieszk.",
            "vignette": "Rekordowy rok PKB na mieszkańca",
            "vignette_texte": "Rok, w którym mieszkańcy każdego kraju byli średnio najzamożniejsi.",
        },
    },
})

# --------------------------------------------------------------- Japonais ---
LANGUES.append({
    "code": "ja", "dossier": "ja", "hreflang": "ja", "sens": "ltr",
    "drapeau": "🇯🇵", "nom": "日本語", "nav_aria": "地図",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "言語", "theme_label": "テーマを切り替える",
    "theme_clair": "ライトテーマに切り替える", "theme_sombre": "ダークテーマに切り替える",
    "accueil": {
        "titre": "StatsMaps — 世界の統計をインタラクティブな地図で",
        "description": "世界経済のインタラクティブ地図。名目GDP、一人当たりGDP、成長率、最高年を197か国について1980年から2031年まで、IMFの公式データにもとづいて表示します。",
        "h1": "世界の統計を、地図で。",
        "intro": "StatsMapsは、公式統計をもとに世界の主要な指標を地図にします。まずは経済から。国際通貨基金（IMF）のデータで、197か国、1980年から2031年まで。",
        "bientot": "近日公開：人口、インフラ、エネルギー、教育、保健。",
        "pied": "データ：IMF（World Economic Outlook）· 地図：Natural Earth · 広告なし、追跡なし。",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "titre": "国別の名目GDP — インタラクティブ世界地図 | StatsMaps",
            "description": "197か国の名目GDPをたどるインタラクティブ地図。1980年から2031年まで。IMFの公式データ（World Economic Outlook）、世界ランキングと年ごとの推移。",
            "h1": "名目GDP", "nav": "名目GDP", "nav_court": "GDP",
            "vignette": "名目GDP",
            "vignette_texte": "各国経済の規模を、名目の十億ドルで。",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "titre": "国別の一人当たりGDP — インタラクティブ世界地図 | StatsMaps",
            "description": "197か国の一人当たりGDPをたどるインタラクティブ地図。1980年から2031年まで。IMFの公式データ、世界ランキングと一人あたりの豊かさ。",
            "h1": "一人当たりGDP", "nav": "一人当たりGDP", "nav_court": "GDP/人",
            "vignette": "一人当たりGDP",
            "vignette_texte": "一人あたりが生み出す富を、名目ドルで。",
        },
        "croissance": {
            "slug": "gdp-growth",
            "titre": "国別のGDP成長率 — インタラクティブ世界地図 | StatsMaps",
            "description": "197か国の実質GDP成長率をたどるインタラクティブ地図。1980年から2031年まで。IMFの公式データ。景気後退は赤、拡大は緑。",
            "h1": "成長率", "nav": "成長率", "nav_court": "成長率",
            "vignette": "GDP成長率",
            "vignette_texte": "実質GDPの前年からの変化を、パーセントで。",
        },
        "annee-record-pib": {
            "slug": "gdp-peak-year",
            "titre": "国別のGDP最高年 — インタラクティブ世界地図 | StatsMaps",
            "description": "各国のGDPが最も高かった年を示すインタラクティブ地図。1980年から2031年まで、IMFの予測を含みます。今が最高の国は緑、いまだ最高値に戻っていない国は赤。IMFの公式データ。",
            "h1": "GDPの最高年", "nav": "GDPの最高年", "nav_court": "GDP最高年",
            "vignette": "GDPの最高年",
            "vignette_texte": "各国が最高値をつけた年 — そして、そこへ戻れないままの国々。",
        },
        "annee-record-pib-par-habitant": {
            "slug": "gdp-per-capita-peak-year",
            "titre": "一人当たりGDPの最高年 — インタラクティブ世界地図 | StatsMaps",
            "description": "各国の一人当たりGDPが最も高かった年を示すインタラクティブ地図。1980年から2031年まで、IMFの予測を含みます。今が最高の国は緑、いまだ最高値に戻っていない国は赤。IMFの公式データ。",
            "h1": "一人当たりGDPの最高年",
            "nav": "一人当たりGDPの最高年", "nav_court": "GDP/人 最高年",
            "vignette": "一人当たりGDPの最高年",
            "vignette_texte": "各国の人々が平均として最も豊かだった年。",
        },
    },
})

# ----------------------------------------------------------------- Coréen ---
LANGUES.append({
    "code": "ko", "dossier": "ko", "hreflang": "ko", "sens": "ltr",
    "drapeau": "🇰🇷", "nom": "한국어", "nav_aria": "지도",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "언어", "theme_label": "테마 변경",
    "theme_clair": "밝은 테마로 전환", "theme_sombre": "어두운 테마로 전환",
    "accueil": {
        "titre": "StatsMaps — 인터랙티브 지도로 보는 세계 통계",
        "description": "세계 경제를 보여 주는 인터랙티브 지도. 명목 GDP, 1인당 GDP, 성장률, 최고 연도를 197개국에 대해 1980년부터 2031년까지, IMF 공식 자료를 바탕으로 제공합니다.",
        "h1": "세계의 통계를 지도로.",
        "intro": "StatsMaps는 공식 통계를 바탕으로 세계의 주요 지표를 지도로 보여 줍니다. 먼저 경제부터. 국제통화기금(IMF) 자료로 197개국, 1980년부터 2031년까지.",
        "bientot": "곧 공개: 인구, 인프라, 에너지, 교육, 보건.",
        "pied": "자료: IMF(World Economic Outlook) · 배경 지도: Natural Earth · 광고 없음, 추적 없음.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "titre": "국가별 명목 GDP — 인터랙티브 세계 지도 | StatsMaps",
            "description": "197개국의 명목 GDP를 보여 주는 인터랙티브 지도. 1980년부터 2031년까지. IMF 공식 자료(World Economic Outlook), 세계 순위와 연도별 변화.",
            "h1": "명목 GDP", "nav": "명목 GDP", "nav_court": "GDP",
            "vignette": "명목 GDP",
            "vignette_texte": "각국 경제의 규모를 경상 십억 달러로.",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "titre": "국가별 1인당 GDP — 인터랙티브 세계 지도 | StatsMaps",
            "description": "197개국의 1인당 GDP를 보여 주는 인터랙티브 지도. 1980년부터 2031년까지. IMF 공식 자료, 세계 순위와 1인당 소득 수준.",
            "h1": "1인당 GDP", "nav": "1인당 GDP", "nav_court": "GDP/인",
            "vignette": "1인당 GDP",
            "vignette_texte": "한 사람이 만들어 내는 부를 경상 달러로.",
        },
        "croissance": {
            "slug": "gdp-growth",
            "titre": "국가별 GDP 성장률 — 인터랙티브 세계 지도 | StatsMaps",
            "description": "197개국의 실질 GDP 성장률을 보여 주는 인터랙티브 지도. 1980년부터 2031년까지. IMF 공식 자료: 경기 침체는 빨강, 확장은 초록.",
            "h1": "성장률", "nav": "성장률", "nav_court": "성장률",
            "vignette": "GDP 성장률",
            "vignette_texte": "실질 GDP의 전년 대비 변화를 백분율로.",
        },
        "annee-record-pib": {
            "slug": "gdp-peak-year",
            "titre": "국가별 GDP 최고 연도 — 인터랙티브 세계 지도 | StatsMaps",
            "description": "각국의 GDP가 가장 높았던 해를 보여 주는 인터랙티브 지도. 1980년부터 2031년까지, IMF 전망 포함. 오늘 최고치인 나라는 초록, 아직 회복하지 못한 나라는 빨강. IMF 공식 자료.",
            "h1": "GDP 최고 연도", "nav": "GDP 최고 연도", "nav_court": "GDP 최고",
            "vignette": "GDP 최고 연도",
            "vignette_texte": "각 나라가 최고치에 이른 해 — 그리고 다시 돌아가지 못한 나라들.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "gdp-per-capita-peak-year",
            "titre": "1인당 GDP 최고 연도 — 인터랙티브 세계 지도 | StatsMaps",
            "description": "각국의 1인당 GDP가 가장 높았던 해를 보여 주는 인터랙티브 지도. 1980년부터 2031년까지, IMF 전망 포함. 오늘 최고치인 나라는 초록, 아직 회복하지 못한 나라는 빨강. IMF 공식 자료.",
            "h1": "1인당 GDP 최고 연도",
            "nav": "1인당 GDP 최고 연도", "nav_court": "GDP/인 최고",
            "vignette": "1인당 GDP 최고 연도",
            "vignette_texte": "각 나라 사람들이 평균적으로 가장 부유했던 해.",
        },
    },
})

# ------------------------------------------------------------------- Turc ---
LANGUES.append({
    "code": "tr", "dossier": "tr", "hreflang": "tr", "sens": "ltr",
    "drapeau": "🇹🇷", "nom": "Türkçe", "nav_aria": "Haritalar",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "Dil", "theme_label": "Temayı değiştir",
    "theme_clair": "Açık temaya geç", "theme_sombre": "Koyu temaya geç",
    "accueil": {
        "titre": "StatsMaps — etkileşimli haritalarla dünya istatistikleri",
        "description": "Dünya ekonomisinin etkileşimli haritaları: nominal GSYİH, kişi başına GSYİH, büyüme ve zirve yılları; 197 ülke, 1980’den 2031’e, IMF’nin resmî verileriyle.",
        "h1": "Dünyanın istatistikleri, haritada.",
        "intro": "StatsMaps, resmî kaynaklardan yola çıkarak dünyanın büyük göstergelerini haritaya döker. Başlangıç ekonomiyle: Uluslararası Para Fonu verileriyle 197 ülke, 1980’den 2031’e.",
        "bientot": "Yakında: nüfus, altyapı, enerji, eğitim ve sağlık.",
        "pied": "Veriler: IMF (World Economic Outlook) · Altlık harita: Natural Earth · Reklamsız, izlemesiz.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gsyih",
            "titre": "Ülkelere göre nominal GSYİH — etkileşimli dünya haritası | StatsMaps",
            "description": "197 ülkenin nominal GSYİH’sini gösteren etkileşimli harita, 1980’den 2031’e. IMF’nin resmî verileri (World Economic Outlook), dünya sıralaması ve yıl yıl değişim.",
            "h1": "Nominal GSYİH", "nav": "Nominal GSYİH", "nav_court": "GSYİH",
            "vignette": "Nominal GSYİH",
            "vignette_texte": "Her ekonominin büyüklüğü, cari milyar dolar olarak.",
        },
        "pib-par-habitant": {
            "slug": "kisi-basi-gsyih",
            "titre": "Ülkelere göre kişi başına GSYİH — etkileşimli dünya haritası | StatsMaps",
            "description": "197 ülkenin kişi başına GSYİH’sini gösteren etkileşimli harita, 1980’den 2031’e. IMF’nin resmî verileri, dünya sıralaması ve kişi başına refah düzeyi.",
            "h1": "Kişi başına GSYİH",
            "nav": "Kişi başına GSYİH", "nav_court": "GSYİH/kişi",
            "vignette": "Kişi başına GSYİH",
            "vignette_texte": "Kişi başına üretilen zenginlik, cari dolar olarak.",
        },
        "croissance": {
            "slug": "gsyih-buyumesi",
            "titre": "Ülkelere göre GSYİH büyümesi — etkileşimli dünya haritası | StatsMaps",
            "description": "197 ülkenin reel GSYİH büyümesini gösteren etkileşimli harita, 1980’den 2031’e. IMF’nin resmî verileri: durgunluklar kırmızı, büyümeler yeşil.",
            "h1": "Büyüme", "nav": "Büyüme", "nav_court": "Büyüme",
            "vignette": "GSYİH büyümesi",
            "vignette_texte": "Reel GSYİH’nin yıldan yıla değişimi, yüzde olarak.",
        },
        "annee-record-pib": {
            "slug": "gsyih-zirve-yili",
            "titre": "Ülkelere göre GSYİH zirve yılı — etkileşimli dünya haritası | StatsMaps",
            "description": "Her ülkenin GSYİH’sinin en yüksek olduğu yılı gösteren etkileşimli harita, 1980’den 2031’e, IMF öngörüleri dâhil. Bugün zirvede olan ülkeler yeşil, zirveye bir daha dönemeyenler kırmızı. IMF’nin resmî verileri.",
            "h1": "GSYİH zirve yılı", "nav": "GSYİH zirve yılı", "nav_court": "GSYİH zirve",
            "vignette": "GSYİH zirve yılı",
            "vignette_texte": "Her ülkenin en yüksek noktaya ulaştığı yıl — ve oraya bir daha dönemeyenler.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "kisi-basi-gsyih-zirve-yili",
            "titre": "Kişi başına GSYİH zirve yılı — etkileşimli dünya haritası | StatsMaps",
            "description": "Her ülkenin kişi başına GSYİH’sinin en yüksek olduğu yılı gösteren etkileşimli harita, 1980’den 2031’e, IMF öngörüleri dâhil. Bugün zirvede olan ülkeler yeşil, zirveye bir daha dönemeyenler kırmızı. IMF’nin resmî verileri.",
            "h1": "Kişi başına GSYİH zirve yılı",
            "nav": "Kişi başına GSYİH zirve yılı", "nav_court": "GSYİH/kişi zirve",
            "vignette": "Kişi başına GSYİH zirve yılı",
            "vignette_texte": "Her ülkenin insanlarının ortalama olarak en zengin olduğu yıl.",
        },
    },
})

# ------------------------------------------------------------------ Hindi ---
LANGUES.append({
    "code": "hi", "dossier": "hi", "hreflang": "hi", "sens": "ltr",
    "drapeau": "🇮🇳", "nom": "हिन्दी", "nav_aria": "मानचित्र",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "भाषा", "theme_label": "थीम बदलें",
    "theme_clair": "हल्की थीम पर जाएँ", "theme_sombre": "गहरी थीम पर जाएँ",
    "accueil": {
        "titre": "StatsMaps — इंटरैक्टिव मानचित्रों पर विश्व के आँकड़े",
        "description": "विश्व अर्थव्यवस्था के इंटरैक्टिव मानचित्र: नाममात्र जीडीपी, प्रति व्यक्ति जीडीपी, वृद्धि दर और शिखर वर्ष — 197 देश, 1980 से 2031 तक, IMF के आधिकारिक आँकड़ों पर आधारित।",
        "h1": "दुनिया के आँकड़े, मानचित्र पर।",
        "intro": "StatsMaps आधिकारिक स्रोतों के आधार पर विश्व के प्रमुख संकेतकों को इंटरैक्टिव मानचित्रों में बदलता है। शुरुआत अर्थव्यवस्था से — अंतर्राष्ट्रीय मुद्रा कोष के आँकड़ों के साथ: 197 देश, 1980 से 2031 तक।",
        "bientot": "जल्द ही: जनसांख्यिकी, बुनियादी ढाँचा, ऊर्जा, शिक्षा और स्वास्थ्य।",
        "pied": "आँकड़े: IMF (World Economic Outlook) · आधार मानचित्र: Natural Earth · न विज्ञापन, न ट्रैकिंग।",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "titre": "देशवार नाममात्र जीडीपी — इंटरैक्टिव विश्व मानचित्र | StatsMaps",
            "description": "197 देशों की नाममात्र जीडीपी का इंटरैक्टिव मानचित्र, 1980 से 2031 तक। IMF के आधिकारिक आँकड़े (World Economic Outlook), विश्व क्रम और वर्ष-दर-वर्ष बदलाव।",
            "h1": "नाममात्र जीडीपी", "nav": "नाममात्र जीडीपी", "nav_court": "जीडीपी",
            "vignette": "नाममात्र जीडीपी",
            "vignette_texte": "हर अर्थव्यवस्था का आकार, चालू अरब डॉलर में।",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "titre": "देशवार प्रति व्यक्ति जीडीपी — इंटरैक्टिव विश्व मानचित्र | StatsMaps",
            "description": "197 देशों की प्रति व्यक्ति जीडीपी का इंटरैक्टिव मानचित्र, 1980 से 2031 तक। IMF के आधिकारिक आँकड़े, विश्व क्रम और प्रति व्यक्ति समृद्धि का स्तर।",
            "h1": "प्रति व्यक्ति जीडीपी",
            "nav": "प्रति व्यक्ति जीडीपी", "nav_court": "जीडीपी/व्यक्ति",
            "vignette": "प्रति व्यक्ति जीडीपी",
            "vignette_texte": "प्रति व्यक्ति उत्पादित संपत्ति, चालू डॉलर में।",
        },
        "croissance": {
            "slug": "gdp-growth",
            "titre": "देशवार जीडीपी वृद्धि दर — इंटरैक्टिव विश्व मानचित्र | StatsMaps",
            "description": "197 देशों की वास्तविक जीडीपी वृद्धि दर का इंटरैक्टिव मानचित्र, 1980 से 2031 तक। IMF के आधिकारिक आँकड़े: मंदी लाल रंग में, विस्तार हरे रंग में।",
            "h1": "वृद्धि दर", "nav": "वृद्धि दर", "nav_court": "वृद्धि",
            "vignette": "जीडीपी वृद्धि दर",
            "vignette_texte": "वास्तविक जीडीपी में वर्ष-दर-वर्ष बदलाव, प्रतिशत में।",
        },
        "annee-record-pib": {
            "slug": "gdp-peak-year",
            "titre": "देशवार जीडीपी का शिखर वर्ष — इंटरैक्टिव विश्व मानचित्र | StatsMaps",
            "description": "वह वर्ष दिखाने वाला इंटरैक्टिव मानचित्र जब हर देश की जीडीपी सर्वोच्च थी, 1980 से 2031 तक, IMF के अनुमानों सहित। आज शिखर पर मौजूद देश हरे, कभी न लौट पाने वाले लाल। IMF के आधिकारिक आँकड़े।",
            "h1": "जीडीपी का शिखर वर्ष",
            "nav": "जीडीपी का शिखर वर्ष", "nav_court": "जीडीपी शिखर",
            "vignette": "जीडीपी का शिखर वर्ष",
            "vignette_texte": "वह वर्ष जब हर देश अपने चरम पर था — और वे देश जो वहाँ कभी नहीं लौटे।",
        },
        "annee-record-pib-par-habitant": {
            "slug": "gdp-per-capita-peak-year",
            "titre": "प्रति व्यक्ति जीडीपी का शिखर वर्ष — इंटरैक्टिव विश्व मानचित्र | StatsMaps",
            "description": "वह वर्ष दिखाने वाला इंटरैक्टिव मानचित्र जब हर देश की प्रति व्यक्ति जीडीपी सर्वोच्च थी, 1980 से 2031 तक, IMF के अनुमानों सहित। आज शिखर पर मौजूद देश हरे, कभी न लौट पाने वाले लाल। IMF के आधिकारिक आँकड़े।",
            "h1": "प्रति व्यक्ति जीडीपी का शिखर वर्ष",
            "nav": "प्रति व्यक्ति जीडीपी का शिखर वर्ष", "nav_court": "जीडीपी/व्यक्ति शिखर",
            "vignette": "प्रति व्यक्ति जीडीपी का शिखर वर्ष",
            "vignette_texte": "वह वर्ष जब हर देश के लोग औसतन सबसे समृद्ध थे।",
        },
    },
})

# ------------------------------------------------------------------ Arabe ---
# La seule langue du site qui s'écrit de droite à gauche : "sens" vaut "rtl",
# ce qui pose dir="rtl" sur la page et retourne toute la mise en page.
LANGUES.append({
    "code": "ar", "dossier": "ar", "hreflang": "ar", "sens": "rtl",
    "drapeau": "🇸🇦", "nom": "العربية", "nav_aria": "الخرائط",
    # Les libellés que lisent les lecteurs d'écran, et l'infobulle du menu.
    "langue_label": "اللغة", "theme_label": "تغيير المظهر",
    "theme_clair": "التبديل إلى المظهر الفاتح", "theme_sombre": "التبديل إلى المظهر الداكن",
    "accueil": {
        "titre": "StatsMaps — إحصاءات العالم على خرائط تفاعلية",
        "description": "خرائط تفاعلية للاقتصاد العالمي: الناتج المحلي الإجمالي الاسمي، ونصيب الفرد منه، والنمو، وسنوات الذروة، لـ197 بلدًا من 1980 إلى 2031، استنادًا إلى بيانات صندوق النقد الدولي الرسمية.",
        "h1": "إحصاءات العالم، على الخريطة.",
        "intro": "يحوّل StatsMaps أبرز المؤشرات العالمية إلى خرائط تفاعلية، انطلاقًا من مصادر رسمية. نبدأ بالاقتصاد، ببيانات صندوق النقد الدولي: 197 بلدًا، من 1980 إلى 2031.",
        "bientot": "قريبًا: السكان، والبنية التحتية، والطاقة، والتعليم، والصحة.",
        "pied": "البيانات: صندوق النقد الدولي (World Economic Outlook) · خلفية الخريطة: Natural Earth · بلا إعلانات ولا تتبّع.",
    },
    "cartes": {
        "pib-nominal": {
            "slug": "nominal-gdp",
            "titre": "الناتج المحلي الإجمالي الاسمي حسب البلد — خريطة عالمية تفاعلية | StatsMaps",
            "description": "خريطة تفاعلية للناتج المحلي الإجمالي الاسمي في 197 بلدًا، من 1980 إلى 2031. بيانات رسمية من صندوق النقد الدولي (World Economic Outlook)، مع الترتيب العالمي والتغير سنة بعد سنة.",
            "h1": "الناتج المحلي الإجمالي",
            "nav": "الناتج المحلي الإجمالي", "nav_court": "الناتج",
            "vignette": "الناتج المحلي الإجمالي",
            "vignette_texte": "حجم كل اقتصاد، بمليارات الدولارات الجارية.",
        },
        "pib-par-habitant": {
            "slug": "gdp-per-capita",
            "titre": "نصيب الفرد من الناتج المحلي حسب البلد — خريطة عالمية تفاعلية | StatsMaps",
            "description": "خريطة تفاعلية لنصيب الفرد من الناتج المحلي الإجمالي في 197 بلدًا، من 1980 إلى 2031. بيانات رسمية من صندوق النقد الدولي، مع الترتيب العالمي ومستوى الثروة للفرد.",
            "h1": "نصيب الفرد من الناتج",
            "nav": "نصيب الفرد من الناتج", "nav_court": "نصيب الفرد",
            "vignette": "نصيب الفرد من الناتج",
            "vignette_texte": "الثروة المنتَجة لكل فرد، بالدولارات الجارية.",
        },
        "croissance": {
            "slug": "gdp-growth",
            "titre": "نمو الناتج المحلي حسب البلد — خريطة عالمية تفاعلية | StatsMaps",
            "description": "خريطة تفاعلية لنمو الناتج المحلي الإجمالي الحقيقي في 197 بلدًا، من 1980 إلى 2031. بيانات رسمية من صندوق النقد الدولي: الركود بالأحمر والتوسّع بالأخضر.",
            "h1": "النمو", "nav": "النمو", "nav_court": "النمو",
            "vignette": "نمو الناتج المحلي",
            "vignette_texte": "تغيّر الناتج المحلي الحقيقي من سنة إلى أخرى، بالنسبة المئوية.",
        },
        "annee-record-pib": {
            "slug": "gdp-peak-year",
            "titre": "سنة ذروة الناتج المحلي حسب البلد — خريطة عالمية تفاعلية | StatsMaps",
            "description": "خريطة تفاعلية للسنة التي بلغ فيها الناتج المحلي الإجمالي لكل بلد أعلى مستوياته، من 1980 إلى 2031، بما في ذلك توقعات صندوق النقد الدولي. بالأخضر البلدان في ذروتها اليوم، وبالأحمر تلك التي لم تستعدها قط. بيانات رسمية من صندوق النقد الدولي.",
            "h1": "سنة ذروة الناتج",
            "nav": "سنة ذروة الناتج", "nav_court": "ذروة الناتج",
            "vignette": "سنة ذروة الناتج",
            "vignette_texte": "السنة التي بلغ فيها كل بلد أقصاه — والبلدان التي لم تعد إليها أبدًا.",
        },
        "annee-record-pib-par-habitant": {
            "slug": "gdp-per-capita-peak-year",
            "titre": "سنة ذروة نصيب الفرد من الناتج — خريطة عالمية تفاعلية | StatsMaps",
            "description": "خريطة تفاعلية للسنة التي بلغ فيها نصيب الفرد من الناتج المحلي أعلى مستوياته في كل بلد، من 1980 إلى 2031، بما في ذلك توقعات صندوق النقد الدولي. بالأخضر البلدان في ذروتها اليوم، وبالأحمر تلك التي لم تستعدها قط. بيانات رسمية من صندوق النقد الدولي.",
            "h1": "سنة ذروة نصيب الفرد",
            "nav": "سنة ذروة نصيب الفرد", "nav_court": "ذروة نصيب الفرد",
            "vignette": "سنة ذروة نصيب الفرد",
            "vignette_texte": "السنة التي كان فيها سكان كل بلد الأكثر ثراءً في المتوسط.",
        },
    },
})


# ==========================================================================
#  LES MODÈLES HTML
#
#  Écrits une seule fois. Les {accolades} sont remplies plus bas.
#  Attention en les modifiant : ce sont les 78 pages du site qui changent.
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
        <input class="panneau__recherche" id="recherche" type="search" autocomplete="off" spellcheck="false">
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

MODELE_ACCUEIL = """<!DOCTYPE html>
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

    <p class="accueil__bientot">{bientot}</p>
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
    <nav class="barre__nav" aria-label="{nav_aria}">
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
# ==========================================================================

def echapper(texte):
    """Protège un texte destiné à un attribut HTML."""
    return (texte.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def adresse(langue, id_carte=None):
    """L'adresse d'une page, à partir de la racine du site : "/de/bip-pro-kopf/".
    L'accueil français est simplement "/"."""
    morceaux = [langue["dossier"]] if langue["dossier"] else []
    if id_carte:
        morceaux.append(langue["cartes"][id_carte]["slug"])
    return "/" + "".join(m + "/" for m in morceaux)


def profondeur(langue, id_carte=None):
    """Combien de dossiers séparent la page de la racine du site."""
    return (1 if langue["dossier"] else 0) + (1 if id_carte else 0)


def remonter(niveaux):
    """Le chemin relatif vers la racine : "./", "../", "../../"."""
    return "./" if niveaux == 0 else "../" * niveaux


def alternates(id_carte):
    """Les balises qui disent à Google : « cette page existe aussi dans ces
    douze autres langues ». Le français fait aussi office de x-default, la
    version servie quand aucune langue du visiteur ne correspond."""
    lignes = []
    for langue in LANGUES:
        lignes.append('  <link rel="alternate" hreflang="%s" href="%s%s">'
                      % (langue["hreflang"], SITE, adresse(langue, id_carte)))
    lignes.append('  <link rel="alternate" hreflang="x-default" href="%s%s">'
                  % (SITE, adresse(LANGUES[0], id_carte)))
    return "\n".join(lignes)


def entete(langue, id_carte=None):
    """La barre du haut : logo, menu des cartes, menu des langues, thème."""
    # Les liens vers les cartes, dans la langue de la page. Depuis une carte on
    # remonte d'un cran ("../croissance/") ; depuis l'accueil, non ("croissance/").
    liens = []
    for autre_id, _ in CARTES:
        carte = langue["cartes"][autre_id]
        courante = ' aria-current="page"' if autre_id == id_carte else ""
        liens.append(
            '        <a class="barre__lien" href="%s%s/"%s>'
            '<span class="long">%s</span><span class="court">%s</span></a>'
            % ("../" if id_carte else "", carte["slug"], courante,
               echapper(carte["nav"]), echapper(carte["nav_court"])))

    # Le menu des langues pointe vers la MÊME page dans chaque langue, en
    # adresses absolues : c'est ce qui permet de changer de langue sans perdre
    # la carte qu'on était en train de regarder.
    menu = []
    for autre in LANGUES:
        actuelle = ' aria-current="true"' if autre["code"] == langue["code"] else ""
        menu.append(
            '          <a href="%s" hreflang="%s" lang="%s"%s>'
            '<span class="drapeau" aria-hidden="true">%s</span>%s</a>'
            % (adresse(autre, id_carte), autre["hreflang"], autre["hreflang"],
               actuelle, autre["drapeau"], echapper(autre["nom"])))

    return MODELE_ENTETE.format(
        # Le logo ramène à l'accueil DE LA LANGUE COURANTE, et non à la racine
        # du site : depuis /en/gdp/, il mène à /en/ et non à l'accueil français.
        # Depuis une carte c'est donc toujours un cran plus haut, quelle que
        # soit la langue — ne pas confondre avec « base », qui vise la racine
        # pour aller y chercher assets/ et data/.
        accueil="../" if id_carte else "./",
        nav_aria=echapper(langue["nav_aria"]),
        liens="\n".join(liens),
        langue_label=echapper(langue["langue_label"]),
        drapeau=langue["drapeau"],
        menu="\n".join(menu),
        theme_label=echapper(langue["theme_label"]),
        theme_clair=echapper(langue["theme_clair"]),
        theme_sombre=echapper(langue["theme_sombre"]),
    )


def page_carte(langue, id_carte):
    carte = langue["cartes"][id_carte]
    base = remonter(profondeur(langue, id_carte))
    # Le titre partagé sur les réseaux sociaux n'a pas besoin du « | StatsMaps »
    # final : le nom du site y est déjà affiché à part.
    og_titre = carte["titre"].split(" | StatsMaps")[0]

    return MODELE_CARTE.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(carte["titre"]),
        description=echapper(carte["description"]),
        url=SITE + adresse(langue, id_carte),
        alternates=alternates(id_carte),
        base=base,
        og_titre=echapper(og_titre),
        maplibre=MAPLIBRE,
        indicateur=id_carte,
        code=langue["code"],
        entete=entete(langue, id_carte),
        h1=echapper(carte["h1"]),
    )


def page_accueil(langue):
    base = remonter(profondeur(langue))
    accueil = langue["accueil"]

    vignettes = []
    for id_carte, pastille in CARTES:
        carte = langue["cartes"][id_carte]
        vignettes.append(
            '      <a class="vignette" href="%s/">\n'
            '        <div class="vignette__pastille">%s</div>\n'
            '        <div class="vignette__titre">%s</div>\n'
            '        <p class="vignette__texte">%s</p>\n'
            '      </a>'
            % (carte["slug"], pastille,
               echapper(carte["vignette"]), echapper(carte["vignette_texte"])))

    return MODELE_ACCUEIL.format(
        hreflang=langue["hreflang"],
        rtl=' dir="rtl"' if langue["sens"] == "rtl" else "",
        titre=echapper(accueil["titre"]),
        description=echapper(accueil["description"]),
        url=SITE + adresse(langue),
        alternates=alternates(None),
        base=base,
        entete=entete(langue),
        h1=echapper(accueil["h1"]),
        intro=echapper(accueil["intro"]),
        vignettes="\n".join(vignettes),
        bientot=echapper(accueil["bientot"]),
        pied=echapper(accueil["pied"]),
    )


def sitemap():
    """La liste de toutes les pages, pour Google. Chaque adresse y déclare ses
    douze traductions : c'est ce qui évite que le site se fasse concurrence à
    lui-même dans les résultats de recherche.

    Volontairement sans <lastmod> : la date serait celle du jour où le script a
    tourné, pas celle du dernier vrai changement. Elle ferait donc bouger les
    78 lignes du fichier à chaque exécution, pour rien."""
    lignes = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
              '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    for id_carte in [None] + [c[0] for c in CARTES]:
        for langue in LANGUES:
            lignes.append("  <url>")
            lignes.append("    <loc>%s%s</loc>" % (SITE, adresse(langue, id_carte)))
            for autre in LANGUES:
                lignes.append('    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>'
                              % (autre["hreflang"], SITE, adresse(autre, id_carte)))
            lignes.append('    <xhtml:link rel="alternate" hreflang="x-default" href="%s%s"/>'
                          % (SITE, adresse(LANGUES[0], id_carte)))
            # Les accueils sont les portes d'entrée du site, les cartes viennent
            # juste après : c'est l'ordre déjà retenu avant ce script.
            lignes.append("    <priority>%s</priority>"
                          % ("1.0" if id_carte is None else "0.9"))
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


def main():
    print("Fabrication des pages de StatsMaps")
    print("-" * 55)

    # Contrôle : chaque langue doit décrire les cinq cartes, sans oubli.
    for langue in LANGUES:
        manquantes = [c for c, _ in CARTES if c not in langue["cartes"]]
        if manquantes:
            raise SystemExit("  ERREUR : la langue « %s » ne décrit pas %s"
                             % (langue["code"], ", ".join(manquantes)))

    # Contrôle : deux pages ne doivent jamais se retrouver à la même adresse.
    vues = {}
    for langue in LANGUES:
        for id_carte in [None] + [c[0] for c in CARTES]:
            url = adresse(langue, id_carte)
            if url in vues:
                raise SystemExit("  ERREUR : l'adresse %s est utilisée deux fois "
                                 "(%s et %s)" % (url, vues[url], langue["code"]))
            vues[url] = langue["code"]

    total = 0
    for langue in LANGUES:
        chemins = []
        ecrire(os.path.join(langue["dossier"], "index.html"), page_accueil(langue))
        chemins.append(adresse(langue))
        total += 1
        for id_carte, _ in CARTES:
            slug = langue["cartes"][id_carte]["slug"]
            ecrire(os.path.join(langue["dossier"], slug, "index.html"),
                   page_carte(langue, id_carte))
            total += 1
        print("  %-3s %-12s %d pages   %s…"
              % (langue["code"], "(" + (langue["dossier"] or "racine") + ")",
                 len(CARTES) + 1, adresse(langue)))

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
