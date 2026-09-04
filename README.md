# StatsMaps

Cartes interactives des statistiques mondiales, à partir de sources officielles.
En ligne : **https://statsmaps.com**

Aujourd'hui : l'économie, avec les données du **FMI** (World Economic Outlook) —
197 pays, de 1980 à 2031.

---

## 🗺️ Les pages du site

Le site existe en **treize langues**, soit **78 pages** : l'accueil et les cinq
cartes, dans chacune. Le français est à la racine, les autres langues dans leur
dossier.

| | Langue | Dossier | Exemple d'adresse |
|---|---|---|---|
| 🇫🇷 | Français | *(racine)* | `/pib-par-habitant/` |
| 🇬🇧 | English | `/en/` | `/en/gdp-per-capita/` |
| 🇺🇦 | Українська | `/ua/` | `/ua/vvp-na-osobu/` |
| 🇩🇪 | Deutsch | `/de/` | `/de/bip-pro-kopf/` |
| 🇪🇸 | Español | `/es/` | `/es/pib-per-capita/` |
| 🇮🇹 | Italiano | `/it/` | `/it/pil-pro-capite/` |
| 🇵🇹 | Português | `/pt/` | `/pt/pib-per-capita/` |
| 🇵🇱 | Polski | `/pl/` | `/pl/pkb-na-mieszkanca/` |
| 🇯🇵 | 日本語 | `/ja/` | `/ja/gdp-per-capita/` |
| 🇰🇷 | 한국어 | `/ko/` | `/ko/gdp-per-capita/` |
| 🇹🇷 | Türkçe | `/tr/` | `/tr/kisi-basi-gsyih/` |
| 🇮🇳 | हिन्दी | `/hi/` | `/hi/gdp-per-capita/` |
| 🇸🇦 | العربية | `/ar/` | `/ar/gdp-per-capita/` |

Deux détails d'apparence bizarre, tous deux volontaires :

- le dossier ukrainien s'appelle `ua` parce que c'est ce qu'écrivent les
  Ukrainiens, mais le code de langue déclaré à Google reste `uk`, l'officiel ;
- les adresses sont **traduites** quand la langue s'écrit en alphabet latin
  (`/de/bip-pro-kopf/`), mais restent en anglais pour le japonais, le coréen,
  l'hindi et l'arabe. Une adresse en écriture native y deviendrait illisible
  une fois encodée par le navigateur (`/ja/%E4%B8%80%E4%BA%BA...`), et « GDP »
  est de toute façon la forme employée couramment dans ces langues.

L'arabe s'écrit de droite à gauche : sur ces six pages, **toute l'interface est
inversée** — le classement passe à droite, la légende à gauche. Seules trois
choses gardent leur sens de lecture : la barre de couleurs de la légende,
le curseur des années et le graphique du comparateur. Une échelle de valeurs et
un axe du temps se lisent dans le même sens dans toutes les langues ; les
retourner ferait dire à la légende l'inverse de ce que montre la carte.

Les 78 pages ne s'écrivent pas à la main : elles sortent toutes d'un seul
modèle, dans `scripts/build_pages.py`. Et les noms des 197 pays ne se
traduisent pas non plus — Natural Earth les fournit déjà dans les treize
langues.

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

### Comparer deux pays

Deux outils différents, qui partent tous les deux du **pays sur lequel on
clique**. Ce pays reste sélectionné quand on fait glisser le curseur des
années : ses chiffres défilent sous les yeux, dans la bulle qui reste ouverte.

**1. Le mode comparaison, sur la carte.** Une fois un pays choisi, le bouton
« Comparer à ce pays » de la légende repeint toute la carte : chaque pays prend
alors la couleur de son **écart** avec celui-là. Rouge = fait moins bien,
vert = fait mieux, jaune = à peu près au même niveau. Le pays de référence est
cerclé de bleu, et une croix dans la légende fait revenir à la carte normale.

L'écart ne se mesure pas de la même façon selon la carte — c'est le réglage
`ECARTS`, en haut de `assets/js/carte.js` :

| Carte | Écart mesuré en | Exemple |
|---|---|---|
| PIB nominal, PIB par habitant | **pourcentage** de la référence | l'Allemagne est à `+24 %` de la France |
| Croissance | **points** de croissance | l'Inde est à `+6,7 pt` de la France |
| Année record (×2) | **années** entre les deux records | l'Ukraine est à `−34 ans` de la France |

Dans les trois cas le signe dit la même chose : **positif = fait mieux que la
référence**. C'est pourquoi les cartes « année record », dont la palette est
retournée d'habitude, la remettent à l'endroit dans ce mode.

**2. Le comparateur, dans le panneau de gauche.** L'onglet « Comparer » met deux
pays face à face et répond à la question « de combien, et depuis quand ? » :

- l'écart pour l'année affichée, en grand ;
- un **graphique de cet écart de 1980 à 2031** — c'est là qu'on voit un pays
  rattraper l'autre, le dépasser, ou décrocher. On peut cliquer dedans pour
  déplacer le curseur des années ;
- les années remarquables : l'écart maximal, l'écart minimal, et la dernière
  fois que les deux pays se sont croisés.

Exemple, sur le PIB par habitant : le Royaume-Uni était **15 % en dessous** de
la France en 1980, l'a dépassée en 2012, et le FMI le voit **29 % au-dessus**
en 2031.

Ce comparateur vit dans son propre fichier, `assets/js/comparateur.js`, qui ne
sait rien du reste du site : `carte.js` lui passe les données et les quelques
fonctions dont il a besoin. C'est ce qui lui permet de marcher à l'identique
sur les cinq cartes, alors qu'un écart s'y mesure de trois façons différentes.

---

## 📁 Où se trouve quoi ?

> ⚠️ **Les 78 pages HTML et `sitemap.xml` ne se modifient pas à la main** :
> elles sont fabriquées par `scripts/build_pages.py` et toute retouche
> directe serait effacée à la prochaine exécution. Le dossier `data/` est
> dans le même cas, avec les deux autres scripts.

```
index.html               L'accueil en français ─┐
en/ ua/ de/ es/ it/ pt/                         ├─ 78 pages FABRIQUÉES par
pl/ ja/ ko/ tr/ hi/ ar/  Les douze autres       │  scripts/build_pages.py
pib-nominal/ ...         Les cartes en français ┘
sitemap.xml              La carte du site pour Google ─┘

assets/css/style.css     TOUTES les couleurs et l'apparence du site
assets/js/i18n.js        TOUS les textes des boutons, en 13 langues
assets/js/theme.js       Le bouton soleil / lune
assets/js/barre.js       Le menu déroulant des langues
assets/js/carte.js       Le moteur des cartes (partagé par les 65 pages)
assets/js/comparateur.js L'onglet « Comparer » du panneau de gauche

data/                    Les chiffres. FABRIQUÉS par les scripts.

scripts/build_geojson.py Prépare le fond de carte (frontières, noms des pays)
scripts/build_donnees.py Va chercher les chiffres chez le FMI
scripts/build_pages.py   Fabrique les 78 pages, le sitemap et la page 404
```

Où sont les textes, selon leur nature :

| Texte | Fichier |
|---|---|
| les boutons, la légende, les infobulles | `assets/js/i18n.js` |
| les titres de pages, les descriptions pour Google, les adresses | `scripts/build_pages.py` |
| les titres des cartes et leurs unités | `scripts/build_donnees.py` |
| les noms des 197 pays | personne : ils viennent de Natural Earth |

### Je veux changer…

| …quoi ? | …dans quel fichier ? |
|---|---|
| une couleur du site | `assets/css/style.css`, tout en haut (section « Couleurs ») |
| les couleurs des cartes | `assets/js/carte.js`, tout en haut : `PALETTE_CLAIR` et `PALETTE_SOMBRE` |
| les seuils entre deux couleurs | `assets/js/carte.js`, les `tranches` de la carte concernée |
| les seuils du mode comparaison | `assets/js/carte.js`, le bloc `ECARTS` |
| un texte de bouton | `assets/js/i18n.js` |
| un drapeau ou un nom de pays | `scripts/build_geojson.py`, puis relancer le script |
| le titre d'une page dans Google | `scripts/build_pages.py`, puis relancer le script |

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

Et pour refabriquer les 78 pages, après avoir touché à un titre, une adresse
ou la liste des langues :

```bash
python3 scripts/build_pages.py
```

Ce dernier ne dépend de rien : on peut le relancer autant de fois qu'on veut,
il réécrit toujours exactement la même chose.

Aucune installation n'est nécessaire : ces scripts n'utilisent que Python,
déjà présent sur macOS.

---

## ➕ Ajouter une nouvelle carte

Le FMI propose **132 indicateurs** (population, inflation, chômage, dette
publique…). Pour en ajouter un :

1. Dans `scripts/build_donnees.py`, ajouter un bloc dans la liste `INDICATEURS`
   (avec son titre et son unité dans les treize langues).
2. Dans `assets/js/carte.js`, ajouter ses tranches de couleur et sa façon de
   mesurer un écart dans `CARTES`.
3. Dans `scripts/build_pages.py`, ajouter la carte à la liste `CARTES`, puis
   son entrée `"cartes"` dans **chacun** des treize blocs de `LANGUES`.
4. Relancer :

```bash
python3 scripts/build_donnees.py && python3 scripts/build_pages.py
```

Les 13 nouvelles pages, les liens du menu sur les 78 pages, les vignettes des
13 accueils et le sitemap suivent tout seuls.

> Le travail est désormais celui de la **traduction**, pas de la recopie :
> l'étape 3 demande d'écrire un titre et une description par langue. Le reste
> (couleurs, classement, légende, curseur, comparateur) est partagé.

---

## 🌍 Ajouter une langue

1. Dans `scripts/build_geojson.py`, une ligne dans le tableau `LANGUES` : le
   code de la langue et le champ où Natural Earth range les noms de pays
   (`"sv": "NAME_SV"` pour le suédois, par exemple). Les 197 noms viennent de
   là — il n'y a rien à traduire à la main.
2. Dans `assets/js/i18n.js`, un bloc de textes, sur le modèle des treize autres.
3. Dans `scripts/build_donnees.py`, la langue dans les `titre` et `unite` de
   chaque indicateur.
4. Dans `scripts/build_pages.py`, son bloc dans `LANGUES` : les adresses, les
   titres et les descriptions des six pages.
5. Relancer les trois scripts.

Si la langue s'écrit de droite à gauche, mettre `"sens": "rtl"` dans son bloc :
le reste (panneau à droite, légende à gauche) se fait tout seul.

> Une seule chose à ne pas oublier : le navigateur connaît déjà les règles de
> pluriel de toutes les langues (« 1 an » / « 5 ans », et les quatre formes du
> polonais). Il suffit de remplir dans `i18n.js` les formes que la langue
> utilise vraiment ; les manquantes retombent sur `_other`.

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
