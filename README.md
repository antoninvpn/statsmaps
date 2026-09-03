# StatsMaps

Cartes interactives des statistiques mondiales, à partir de sources officielles.
En ligne : **https://statsmaps.com**

Aujourd'hui : l'économie, avec les données du **FMI** (World Economic Outlook) —
197 pays, de 1980 à 2031.

---

## 🗺️ Les pages du site

| Adresse | Contenu |
|---|---|
| `/` et `/en/` | Accueil (français / anglais) |
| `/pib-nominal/` · `/en/gdp/` | Carte du PIB nominal |
| `/pib-par-habitant/` · `/en/gdp-per-capita/` | Carte du PIB par habitant |
| `/croissance/` · `/en/growth/` | Carte de la croissance du PIB réel |

---

## 📁 Où se trouve quoi ?

```
index.html               La page d'accueil en français
en/index.html            La page d'accueil en anglais
pib-nominal/ ...         Les 6 pages de carte (3 cartes × 2 langues)

assets/css/style.css     TOUTES les couleurs et l'apparence du site
assets/js/i18n.js        TOUS les textes, en français et en anglais
assets/js/theme.js       Le bouton soleil / lune
assets/js/carte.js       Le moteur des cartes (partagé par les 6 pages)

data/                    Les chiffres. NE PAS MODIFIER À LA MAIN :
                         ces fichiers sont fabriqués par les scripts.

scripts/build_geojson.py Prépare le fond de carte (frontières des pays)
scripts/build_donnees.py Va chercher les chiffres chez le FMI
```

### Je veux changer…

| …quoi ? | …dans quel fichier ? |
|---|---|
| une couleur du site | `assets/css/style.css`, tout en haut (section « Couleurs ») |
| les couleurs d'une carte | `assets/js/carte.js`, tout en haut (section « Réglages des cartes ») |
| un texte (bouton, titre…) | `assets/js/i18n.js` |
| le titre d'une page dans Google | la balise `<title>` de la page concernée |

---

## 💻 Voir le site sur mon ordinateur avant de le publier

Ouvre le Terminal, place-toi dans ce dossier, puis lance :

```bash
python3 -m http.server 8000
```

Puis ouvre **http://localhost:8000** dans ton navigateur.
Pour arrêter : `Ctrl + C` dans le Terminal.

> ⚠️ Ouvrir `index.html` par un double-clic ne marche pas : le navigateur refuse
> alors de charger les fichiers du dossier `data/`. Il faut passer par la commande
> ci-dessus.

---

## 🔄 Mettre à jour les chiffres

**Automatiquement** — chaque lundi matin, GitHub relance tout seul le script et
enregistre les nouveaux chiffres s'il y en a. Tu n'as rien à faire.
(C'est réglé dans `.github/workflows/maj-donnees.yml`.)

**À la main**, si tu veux forcer une mise à jour :

```bash
python3 scripts/build_donnees.py
```

Le fond de carte, lui, ne change quasiment jamais. Si besoin :

```bash
python3 scripts/build_geojson.py
```

Aucune installation n'est nécessaire : ces scripts n'utilisent que Python,
déjà présent sur macOS.

---

## ➕ Ajouter une nouvelle carte

Le FMI propose **132 indicateurs** (population, inflation, chômage, dette
publique…). Pour en ajouter un :

1. Dans `scripts/build_donnees.py`, ajouter un bloc dans la liste `INDICATEURS`.
2. Dans `assets/js/carte.js`, ajouter les tranches et couleurs dans `CARTES`.
3. Dupliquer un dossier de carte existant (ex. `croissance/`) et adapter le
   `data-indicateur` de la balise `<body>`, le titre et la description.
4. Ajouter les liens dans la barre de navigation des 8 pages, et dans `sitemap.xml`.

---

## 🧾 Sources et licences

- **Données économiques** : [FMI — World Economic Outlook](https://www.imf.org/external/datamapper/datasets/WEO)
- **Frontières** : [Natural Earth](https://www.naturalearthdata.com/), échelle 1:50 m (domaine public)

  Deux écarts assumés par rapport au fichier d'origine, appliqués par
  `scripts/build_geojson.py` :
  - la **Crimée** est rattachée à l'Ukraine (résolution 68/262 de l'ONU),
    alors que Natural Earth la place côté russe dans sa vue « de fait » ;
  - l'**Antarctique** est retiré (aucune donnée, aucun pays).
- **Carte** : [MapLibre GL JS](https://maplibre.org/) (licence BSD-3)

Le site est **statique** : pas de base de données, pas de serveur, pas de
publicité, pas de traceur.
