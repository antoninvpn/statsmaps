# StatsMaps

Cartes interactives des statistiques mondiales, à partir de sources officielles.
En ligne : **https://statsmaps.com**

Aujourd'hui : l'économie, avec les données du **FMI** (World Economic Outlook) —
197 pays, de 1980 à 2031.

---

## 🗺️ Les pages du site

Le site existe en **trois langues** : français à la racine, anglais dans `/en/`,
ukrainien dans `/ua/`. (Le dossier s'appelle `ua` parce que c'est ce qu'écrivent
les Ukrainiens ; le code de langue déclaré à Google reste `uk`, l'officiel.)

| Français | Anglais | Ukrainien | Contenu |
|---|---|---|---|
| `/` | `/en/` | `/ua/` | Accueil |
| `/pib-nominal/` | `/en/gdp/` | `/ua/vvp/` | PIB nominal |
| `/pib-par-habitant/` | `/en/gdp-per-capita/` | `/ua/vvp-na-osobu/` | PIB par habitant |
| `/croissance/` | `/en/growth/` | `/ua/zrostannia/` | Croissance du PIB réel |
| `/annee-record-pib/` | `/en/when-gdp-peaked/` | `/ua/rekordnyi-rik-vvp/` | Année record du PIB |
| `/annee-record-pib-par-habitant/` | `/en/when-gdp-per-capita-peaked/` | `/ua/rekordnyi-rik-vvp-na-osobu/` | Année record du PIB par habitant |

### Les 197 pays du classement

Le classement compte **197 pays** : les 193 États membres de l'ONU, plus le
Vatican, la Palestine, Taïwan et le Kosovo. Ce nombre ne bouge jamais, quelle
que soit l'année ou la carte affichée.

La liste du FMI ne correspond pas exactement à celle-là, d'où deux corrections,
toutes deux réglées en haut de `scripts/build_geojson.py` :

| Correction | Qui | Effet |
|---|---|---|
| `PAYS_HORS_FMI` | 🇨🇺 Cuba, 🇰🇵 Corée du Nord, 🇲🇨 Monaco, 🇻🇦 Vatican | Le FMI ne publie rien sur eux (les deux premiers ne transmettent pas leurs chiffres, les deux autres n'en sont pas membres). Ils figurent quand même dans le classement, à la ligne « donnée non disponible ». |
| `TERRITOIRES` | 🇺🇸🇵🇷 Puerto Rico, 🇨🇳🇭🇰 Hong Kong, 🇨🇳🇲🇴 Macao, 🇳🇱🇦🇼 Aruba | Le FMI les suit, mais ce ne sont pas des États souverains. Ils gardent leur chiffre et leur couleur sur la carte, à leur place dans la liste, mais **sans numéro de rang** et hors du décompte. Deux drapeaux : l'État dont ils dépendent, puis le leur. |

Les autres territoires dépendants — Groenland, Nouvelle-Calédonie, îles
Caïmans… — ne sont plus dessinés séparément : ils sont **rattachés à leur
État** et en prennent la couleur (voir plus bas).

Cas volontairement **laissés parmi les pays** : Taïwan (État de fait),
le Kosovo (reconnu par une centaine d'États) et la Palestine (État observateur
à l'ONU). Cas volontairement **laissés de côté** : Niue et les Îles Cook,
États librement associés à la Nouvelle-Zélande, absents de l'ONU.

Enfin, le site écrit **Puerto Rico** et non « Porto Rico » : la forme française
courante est une déformation d'un nom espagnol. Voir `NOMS_COURTS`.

### Le code couleur

Les cinq cartes partagent **une seule palette** de sept couleurs, du rouge
sombre au vert sombre en passant par l'orange et le jaune — la famille de
couleurs des cartes économiques de Wikipédia. Elle est écrite une seule fois
dans `assets/js/carte.js` (`PALETTE_CLAIR` et `PALETTE_SOMBRE`) : la modifier
change le site entier.

Le sens de lecture est toujours le même : **le vert est le côté favorable**
(pays riche, forte croissance, record tout récent), le rouge le côté
défavorable. Les cartes qui se lisent à l'envers — les deux cartes « année
record », où un petit nombre d'années est une bonne nouvelle — retournent la
palette avec `inverser()`.

Ce que chaque carte règle de son côté, ce sont seulement ses `tranches` :
les seuils qui séparent une couleur de la suivante.

### Les deux cartes « année record »

Elles répondent à la question : **en quelle année ce pays a-t-il été à son
maximum ?** Vert = le record date de l'année affichée, le pays va bien.
Rouge = le record est ancien, le pays ne l'a jamais retrouvé (Grèce 2008,
Japon 2012, Afrique du Sud 2011…).

Le curseur des années garde son rôle habituel : posé sur 2008, il montre le
record **atteint à cette date**. On voit ainsi la crise de 2008, puis le Covid,
arriver en faisant glisser le curseur — et, au-delà de 2025, les projections du
FMI jusqu'en 2031.

C'est la fin de la course qui est la plus parlante : en 2031, **11 pays** ne
sont toujours pas prévus pour retrouver leur record de PIB (Ukraine 1991,
Iran 2011, Japon 2012, Nigeria 2014, Russie 2026…), et **26** pour le PIB par
habitant (RD Congo 1980, Ghana 1982, Koweït 2008, Qatar 2012…).

Ces deux cartes ne sont pas téléchargées mais **calculées** à partir du PIB et
du PIB par habitant, par la fonction `annees_record()` de `build_donnees.py`.

---

## 📁 Où se trouve quoi ?

```
index.html               La page d'accueil en français
en/index.html            La page d'accueil en anglais
ua/index.html            La page d'accueil en ukrainien
pib-nominal/ ...         Les 15 pages de carte (5 cartes × 3 langues)

assets/css/style.css     TOUTES les couleurs et l'apparence du site
assets/js/i18n.js        TOUS les textes, en 3 langues
assets/js/theme.js       Le bouton soleil / lune
assets/js/barre.js       Le menu déroulant des langues
assets/js/carte.js       Le moteur des cartes (partagé par les 15 pages)

data/                    Les chiffres. NE PAS MODIFIER À LA MAIN :
                         ces fichiers sont fabriqués par les scripts.

scripts/build_geojson.py Prépare le fond de carte (frontières des pays)
scripts/build_donnees.py Va chercher les chiffres chez le FMI
```

### Je veux changer…

| …quoi ? | …dans quel fichier ? |
|---|---|
| une couleur du site | `assets/css/style.css`, tout en haut (section « Couleurs ») |
| les couleurs des cartes | `assets/js/carte.js`, tout en haut : `PALETTE_CLAIR` et `PALETTE_SOMBRE` |
| les seuils entre deux couleurs | `assets/js/carte.js`, les `tranches` de la carte concernée |
| un texte (bouton, titre…) | `assets/js/i18n.js` |
| un drapeau ou un nom de pays | `scripts/build_geojson.py`, puis relancer le script |
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
3. Dans `assets/js/i18n.js`, ajouter le nom de la carte dans les trois langues.
4. Dupliquer un dossier de carte existant (ex. `croissance/`) **une fois par
   langue** et adapter le `data-indicateur` de la balise `<body>`, le titre,
   la description et les balises `hreflang`.
5. Ajouter les liens dans la barre de navigation des 18 pages, la vignette des
   3 pages d'accueil, et les 3 adresses dans `sitemap.xml`.

> C'est la partie la plus fastidieuse du site : chaque nouvelle carte se
> multiplie par le nombre de langues. Tout le reste (couleurs, classement,
> légende, curseur) est partagé et n'a pas à être recopié.

---

## 🗓️ Quelle édition des chiffres ?

Le FMI publie le *World Economic Outlook* **deux fois par an, à la mi-avril et
à la mi-octobre**. Le site affiche l'édition d'où viennent les chiffres —
« World Economic Outlook (avril 2026) » — plutôt que la date à laquelle le
robot est allé les chercher : c'est l'édition qui date vraiment les projections.
La date de récupération reste visible en survolant la ligne du bas.

Cette mention se met à jour toute seule : `edition_weo()` dans
`build_donnees.py` en déduit l'édition à partir de la date du jour, et bascule
sur « octobre 2026 » dès le 15 octobre. Il n'y a rien à modifier à la main.

---

## 🧾 Sources et licences

- **Données économiques** : [FMI — World Economic Outlook](https://www.imf.org/external/datamapper/datasets/WEO)
- **Frontières** : [Natural Earth](https://www.naturalearthdata.com/), échelle 1:50 m (domaine public)

  Natural Earth dessine le monde « tel qu'il est contrôlé sur le terrain ».
  StatsMaps suit la **reconnaissance internationale**. Les écarts assumés,
  tous appliqués par `scripts/build_geojson.py` :

  | Écart | Pourquoi |
  |---|---|
  | La **Crimée** est ukrainienne | Résolution 68/262 de l'Assemblée générale de l'ONU (2014) |
  | Le **plateau du Golan** est syrien | Résolution 497 du Conseil de sécurité de l'ONU (1981), qui déclare l'annexion israélienne « nulle et non avenue » |
  | Les **Kouriles du Sud** sont japonaises | Etorofu, Kounachiri, Chikotan et les Habomai : occupées par l'URSS en 1945, revendiquées par le Japon, aucun traité de paix n'a jamais réglé la question |
  | **Chypre du Nord** est fondue dans Chypre | Reconnue par la seule Turquie |
  | Le **Somaliland** est fondu dans la Somalie | Reconnu par aucun État |
  | Le **Sahara occidental** est fondu dans le Maroc | **Choix éditorial**, et non application du droit : l'ONU le classe « territoire non autonome » et ne reconnaît pas la souveraineté marocaine |
  | L'**Antarctique** est retiré | Ce n'est pas un pays et il n'a aucune donnée |

  Trois opérations différentes, toutes vérifiées par un calcul de surface et
  annulées si le résultat n'est pas cohérent :

  - **déplacer** des îles (Kouriles) : rien à souder, elles changent de pays ;
  - **découper** un territoire dessiné à l'intérieur d'un pays (Golan), puis le
    souder au voisin — c'est la fonction `detacher()` ;
  - **fondre** un territoire dans un pays (Chypre du Nord, Somaliland, Sahara
    occidental) — c'est `fusionner()`, via la liste `FUSIONS`.

  Le contour du Golan vient d'un second fichier de Natural Earth, celui des
  territoires disputés : le fichier principal le dessine à l'intérieur d'Israël.

  Les territoires fusionnés sont **soudés** au pays qui les absorbe : aucun
  trait de frontière ne subsiste à l'intérieur. La soudure est contrôlée par
  un calcul de surface, et annulée si le résultat n'est pas cohérent.

  Pour en ajouter ou en retirer : la liste `FUSIONS`, en haut de
  `scripts/build_geojson.py`.

- **Territoires dépendants rattachés à leur État** — liste
  `TERRITOIRES_RATTACHES`, 36 territoires :

  | État | Territoires |
  |---|---|
  | 🇬🇧 Royaume-Uni | Anguilla, Bermudes, Caïmans, Malouines, Guernesey, Man, Jersey, Montserrat, Pitcairn, Sainte-Hélène, Géorgie du Sud, Turques-et-Caïques, Vierges britanniques, Territoire britannique de l'océan Indien |
  | 🇫🇷 France | Nouvelle-Calédonie, Polynésie française, Saint-Barthélemy, Saint-Martin, Saint-Pierre-et-Miquelon, Wallis-et-Futuna, Terres australes |
  | 🇺🇸 États-Unis | Guam, Samoa américaines, Mariannes du Nord, Vierges américaines |
  | 🇦🇺 Australie | Norfolk, Ashmore-et-Cartier, Heard-et-MacDonald, Territoires de l'océan Indien |
  | 🇩🇰 Danemark | Groenland, Féroé |
  | 🇳🇱 Pays-Bas | Curaçao, Saint-Martin |
  | 🇳🇿 Nouvelle-Zélande | Îles Cook, Niue |
  | 🇫🇮 Finlande | Åland |

  Sans ce rattachement, ces 36 territoires apparaissaient en gris « donnée non
  disponible », ce qui trouait la carte sans rien apprendre à personne.

  **Exception** : les quatre territoires que le FMI suit séparément — Hong Kong,
  Macao, Puerto Rico et Aruba — ne sont **pas** rattachés. Ils ont leurs propres
  chiffres, et les fondre reviendrait à les jeter. Ils gardent donc leur forme,
  leur couleur et leur double drapeau.

- **Trois enclaves ajoutées** — liste `ENCLAVES` : Gibraltar (au Royaume-Uni),
  Ceuta et Melilla (à l'Espagne). Elles n'existent pas dans le fichier 1:50 m,
  Natural Earth ne les dessine pas à cette échelle. Leurs contours sont recopiés
  depuis le fichier 1:10 m — 780 octets, plutôt que de télécharger 12 Mo pour
  trois formes qui ne changeront jamais. Elles gardent 4 décimales de précision
  (≈ 11 m) au lieu de 2 : à 1 km près, Gibraltar, qui fait 1,7 km sur 3,3 km,
  disparaîtrait purement et simplement.

  Attention : à l'échelle du monde entier, ces trois territoires font **un ou
  deux pixels**. Il faut zoomer pour les voir — c'est leur taille réelle, pas
  un défaut de la carte.

- **Cadrage au clic** — chaque pays porte une propriété `c` calculée par
  `cadrage_du_pays()` : la zone à afficher quand on clique dessus. Elle est
  calculée **avant** le rattachement des territoires, sinon cliquer sur le
  Danemark cadrerait sur le Groenland et cliquer sur la France sur Tahiti.
- **Carte** : [MapLibre GL JS](https://maplibre.org/) (licence BSD-3)

Le site est **statique** : pas de base de données, pas de serveur, pas de
publicité, pas de traceur.
