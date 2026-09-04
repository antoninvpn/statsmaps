# StatsMaps

Cartes interactives des statistiques mondiales, à partir de sources officielles.
En ligne : **https://statsmaps.com**

Aujourd'hui : l'économie et la démographie, avec les données du **FMI**
(World Economic Outlook) — 197 pays, de 1980 à 2031.

---

## 🗺️ Comment le site est rangé

Trois étages, du général au particulier :

```
l'accueil ............ les CATÉGORIES        Économie · Démographie
                                             Infrastructure · Armée (à venir)
  une catégorie ...... ses CARTES            PIB · PIB/hab. · Croissance · Inflation
    une carte ........ ses VARIANTES         Nominal ⇄ Parité de pouvoir d'achat
```

Une **variante** est une autre façon de mesurer la *même* chose : le PIB en
dollars courants, ou le PIB corrigé du coût de la vie. Les deux ont leur propre
adresse — c'est ce que Google indexe — et un interrupteur passe de l'une à
l'autre en haut du panneau de gauche. Comme les deux cartes du PIB partagent
la même échelle de couleurs, on voit littéralement les pays changer de couleur
en basculant : l'Inde, 4ᵉ économie en dollars, est 3ᵉ en pouvoir d'achat.

### Les rubriques annoncées

Deux rubriques figurent sur l'accueil sans être ouvertes : **Infrastructure** et
**Armée**. Elles apparaissent en pointillés, grisées, avec une pastille
« Bientôt ».

Ce ne sont **pas des liens**, et elles n'ont ni page, ni entrée de menu, ni ligne
dans le sitemap : un lien qui ne mène nulle part est la plus sûre façon de faire
croire à une panne, et une page vide indexée par Google dessert le site.

C'est le fait d'avoir une liste de cartes **vide** qui les marque, dans
`CATEGORIES` :

```python
("economie",       "💶", ["pib-nominal", "pib-par-habitant", "croissance", "inflation"]),
("demographie",    "👥", ["population"]),
("infrastructure", "🏗️", []),          # annoncée, pas encore ouverte
("armee",          "🛡️", []),
```

Le jour où l'une reçoit sa première carte, la vignette devient cliquable, la
page apparaît, le menu et le sitemap suivent — il faut alors seulement ajouter
son `slug`, son `h1` et son `intro` dans les treize blocs de `LANGUES`.

### Le menu du haut ne montre jamais tout le site

Il montre **l'étage où l'on se trouve**, et rien d'autre :

| Où l'on est | Ce que montre le menu |
|---|---|
| l'accueil | les catégories **ouvertes** — Économie · Démographie |
| une page de catégorie | les catégories aussi : on est encore à cet étage, et on peut passer à la rubrique voisine |
| une carte | les cartes de **sa** catégorie, et elles seules |

Sur la carte de la population, le menu n'affiche donc pas le PIB ni l'inflation :
ils appartiennent à une autre rubrique. En échange, le nom de la rubrique
apparaît en pastille juste après le logo (« Économie ») — il dit où l'on est, et
il ramène à la page de la rubrique, d'où l'on atteint les autres.

Le menu ne montre que les cartes **principales** : la version en parité de
pouvoir d'achat se choisit dans le panneau de gauche, une fois la carte ouverte.
Mettre les deux ferait un menu où « PIB » apparaîtrait deux fois. Tout cela est
décidé par la fonction `entete()` de `build_pages.py`.

### Les sept cartes

| Carte | Indicateur du FMI | Variantes | Onglet Pic |
|---|---|---|:---:|
| PIB | `NGDPD` / `PPPGDP` | nominal · parité de pouvoir d'achat | ✅ |
| PIB par habitant | `NGDPDPC` / `PPPPC` | nominal · parité de pouvoir d'achat | ✅ |
| Croissance du PIB | `NGDP_RPCH` | — | ✅ |
| Inflation | `PCPIPCH` | — | ✅ |
| Population | `LP` | — | ✅ |

Les sept cartes ont un onglet « Pic » : la question « en quelle année ce pays
a-t-il été à son maximum ? » a un sens partout — le pic du PIB, mais aussi le
pic d'inflation (le Venezuela en 2018) ou le pic de population (le Japon en
2011). C'est le champ `pic` de `build_donnees.py` qui le décide, au cas où une
future carte s'y prêterait mal.

### Le vocabulaire est celui du FMI

Les titres et les unités sont **recopiés de la source**
([sa fiche pays](https://www.imf.org/external/datamapper/profile/AUT)), puis
traduits. Le site écrit donc « PIB, prix courants » et non « PIB nominal ».

Conséquence surprenante mais voulue : les deux versions du PIB portent
**exactement le même titre**, et seule leur unité les distingue — c'est ainsi
que le FMI les présente.

| | Titre | Unité (légende) |
|---|---|---|
| dollars | PIB, prix courants | milliards de dollars US |
| PPA | PIB, prix courants | parité de pouvoir d'achat ; milliards de dollars internationaux |

Les noms courts (« PIB nominal », « PIB en parité de pouvoir d'achat ») ne
servent qu'au menu du haut, aux vignettes et aux titres que lit Google : ils
vivent dans `build_pages.py`.

---

## 🌍 Les pages du site

Le site existe en **treize langues**, soit **130 pages** : l'accueil, les deux
catégories et les sept cartes, dans chacune. Le français est à la racine, les
autres langues dans leur dossier.

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

L'arabe s'écrit de droite à gauche : sur ces dix pages, **toute l'interface est
inversée** — le panneau passe à droite, la légende à gauche. Seules trois
choses gardent leur sens de lecture : la barre de couleurs de la légende,
le curseur des années et le graphique du comparateur. Une échelle de valeurs et
un axe du temps se lisent dans le même sens dans toutes les langues ; les
retourner ferait dire à la légende l'inverse de ce que montre la carte.

Les 130 pages ne s'écrivent pas à la main : elles sortent toutes de deux
modèles, dans `scripts/build_pages.py`. Et les noms des 197 pays ne se
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

---

## 🔢 Comment les chiffres sont écrits

Deux règles, dans la fonction `formater()` de `assets/js/carte.js`.

**1. Toute la précision disponible, sans zéro inutile.** Les fichiers de
`data/` contiennent trois décimales : le site les affiche toutes, mais
n'écrit pas les zéros qui ne servent à rien.

| Donnée brute | Affiché |
|---|---|
| `32383.92` | 32 383,92 Md$ |
| `94429.753` | 94 429,753 $/hab. |
| `2.3` | +2,3 % |

**2. Une espace insécable ordinaire entre les milliers.** En français, le
navigateur sépare naturellement les milliers par une *espace fine* insécable
(le caractère `U+202F`). Les polices d'Apple la dessinent si étroite qu'on ne
la voit pas : « 30 767 » finissait par ressembler à « 30767 ». On la remplace
donc par une espace insécable ordinaire, visible dans toutes les polices — et
qui interdit toujours de couper un nombre en fin de ligne.

Chaque langue garde évidemment ses propres usages : `1,234.5` en anglais,
`12,34,567` en hindi (le groupement indien), et les chiffres 0-9 en arabe
plutôt que ١٢٣٤ — c'est le rôle du suffixe `-u-nu-latn`, sur un site où l'on
compare des nombres d'une langue à l'autre.

---

## 🎨 Le code couleur

Les sept cartes partagent **une seule palette** de sept couleurs, du rouge
sombre au vert sombre en passant par l'orange et le jaune — la famille de
couleurs des cartes économiques de Wikipédia. Elle est écrite une seule fois
dans `assets/js/carte.js` (`PALETTE_CLAIR` et `PALETTE_SOMBRE`) : la modifier
change le site entier.

Le sens de lecture est toujours le même : **le vert est le côté favorable**
(pays riche, forte croissance, pic tout récent), le rouge le côté défavorable.
La carte qui se lit à l'envers — l'inflation, où un petit nombre est la bonne
nouvelle — retourne la palette avec `inverser()` et porte la mention
`ecart_inverse`.

Ce que chaque carte règle de son côté, ce sont seulement ses `tranches` :
les seuils qui séparent une couleur de la suivante.

Deux choix de seuils méritent une explication :

- **PIB par habitant** : les deux variantes n'ont *pas* les mêmes tranches, à
  la différence du PIB total. La parité de pouvoir d'achat relève fortement les
  pays pauvres — l'Inde passe de 2 900 à 12 800 dollars —, et avec les seuils du
  nominal la moitié du monde basculerait d'un coup dans le vert.
- **Inflation** : les seuils suivent la lecture des banques centrales (2 % est
  la cible, 10 % un vrai problème, 20 % le sujet principal d'une économie). Les
  rares pays en *déflation* tombent dans la tranche la plus verte : c'est une
  simplification assumée, la déflation n'est pas une bonne nouvelle non plus,
  mais elle est trop rare pour mériter une couleur à elle sur les sept.

---

## 🖱️ Les trois onglets du panneau

Le panneau de gauche porte trois vues, sous une rangée d'onglets.

**Classement.** Les 197 pays pour l'année affichée, avec leur rang, leur
drapeau et leur chiffre. Un champ de recherche ignore les accents : chercher
« coree » trouve la Corée, et « Germany » trouve l'Allemagne.

**Comparer.** Deux pays face à face, et surtout un **graphique de leur écart de
1980 à 2031** — c'est là qu'on voit un pays rattraper l'autre, le dépasser, ou
décrocher. On peut cliquer dans le graphique pour déplacer le curseur des
années. Exemple, sur le PIB par habitant : le Royaume-Uni était 15 % en dessous
de la France en 1980, l'a dépassée en 2012, et le FMI le voit 29 % au-dessus
en 2031.

**Pic.** « En quelle année ce pays a-t-il été à son maximum ? » L'onglet fait
deux choses en même temps :

- il **repeint la carte** en années écoulées depuis le pic ;
- il affiche la **fiche du pays choisi** : son pic, l'année où il l'a atteint,
  et le chemin qui lui reste à faire.

Le point important, c'est que **le sens de lecture suit la carte** :

| Carte | Un pic tout récent veut dire… | Couleur | En tête du classement |
|---|---|---|---|
| PIB, PIB/hab., croissance, population | le pays est à son sommet | 🟩 vert | les pics les plus **anciens** (Ukraine 1991, Grèce 2008, Japon 2012) |
| Inflation | les prix s'envolent en ce moment | 🟥 rouge | les pics les plus **récents** (Burundi 2025, Iran 2025, Argentine 2024) |

C'est calculé, et non écrit à la main : `reglagesPic()` dans `carte.js` part du
réglage `ecart_inverse` de la carte ouverte et en déduit la palette, l'ordre du
classement et le sens de la comparaison. Ajouter demain une carte du chômage
donnerait automatiquement la bonne lecture.

Le curseur des années garde son rôle habituel : posé sur 2008, il montre le pic
**atteint à cette date**. On voit ainsi la crise de 2008, puis le Covid, arriver
en faisant glisser le curseur — et, au-delà de 2025, les projections du FMI
jusqu'en 2031. C'est la fin de la course qui est la plus parlante : en 2031,
**11 pays** ne sont toujours pas prévus pour retrouver leur pic de PIB, et
**26** pour le PIB par habitant.

La ligne « écart au pic » de la fiche se mesure dans l'unité de la carte de
départ : en **pourcentage** pour le PIB (le Japon est 30 % en dessous de son pic
de 2012), en **points** pour la croissance et l'inflation (la France est
5,9 points en dessous de son pic de croissance de 2021). Comparer deux taux en
pourcentage de pourcentage n'aurait aucun sens.

> Ces années ne sont **pas téléchargées** : le navigateur les calcule à partir
> des chiffres déjà chargés, à la première ouverture de l'onglet
> (`calculerPics()` dans `carte.js`). C'est pourquoi l'onglet marche sur
> n'importe quelle carte sans qu'il y ait un fichier de plus dans `data/`.

> **Pourquoi « Pic » ?** Parce que « record » se dit d'une performance, et que
> l'onglet parle aussi bien du pic d'inflation du Venezuela — qui n'a rien
> d'un exploit. En anglais l'onglet s'appelle **Peaked**.

---

## ⚖️ Comparer deux pays sur la carte

**Il n'y a aucun bouton à trouver : cliquer sur un pays suffit.** La carte cesse
alors de montrer « combien » et montre « combien de plus ou de moins que lui » :
rouge = ce pays fait moins bien que celui qu'on a cliqué, vert = il fait mieux,
jaune = ils sont au même niveau. Le pays de référence est cerclé de bleu, et
rappelé en haut du panneau de gauche.

Pour revenir aux valeurs, trois chemins, tous naturels : refermer la bulle du
pays, cliquer sur la mer, ou la croix de la ligne « pays de référence ».

L'écart ne se mesure pas de la même façon selon la carte — c'est le réglage
`ECARTS`, en haut de `assets/js/carte.js` :

| Carte | Écart mesuré en | Exemple |
|---|---|---|
| PIB, PIB par habitant, population | **pourcentage** de la référence | l'Allemagne est à `+24 %` de la France |
| Croissance, inflation | **points** | l'Inde est à `+6,7 pt` de la France |
| Onglet Pic | **années** entre les deux pics | l'Ukraine est à `−34 ans` de la France |

Dans les trois cas, le signe dit toujours la même chose : **positif = ce pays a
un chiffre plus grand que la référence**. Reste à savoir si « plus grand » est
une bonne nouvelle, et cela dépend de la carte : sur le PIB oui, sur l'inflation
non. C'est tout ce que dit `ecart_inverse`, le seul réglage de sens du fichier.
Sur l'inflation, dépasser l'autre reste rouge — sur la carte comme dans le
graphique du comparateur.

Le comparateur vit dans son propre fichier, `assets/js/comparateur.js`, qui ne
sait rien du reste du site : `carte.js` lui passe les données et les quelques
fonctions dont il a besoin. C'est ce qui lui permet de marcher à l'identique
sur les sept cartes, alors qu'un écart s'y mesure de trois façons différentes.

---

## 📁 Où se trouve quoi ?

> ⚠️ **Les 130 pages HTML et `sitemap.xml` ne se modifient pas à la main** :
> elles sont fabriquées par `scripts/build_pages.py` et toute retouche
> directe serait effacée à la prochaine exécution. Le dossier `data/` est
> dans le même cas, avec les deux autres scripts.

```
index.html               L'accueil en français ─────────┐
economie/ demographie/   Les catégories en français     │
pib-nominal/ pib-ppa/                                   ├─ 130 pages FABRIQUÉES
pib-par-habitant/ ...    Les 7 cartes en français       │  par build_pages.py
en/ ua/ de/ es/ it/ pt/                                 │
pl/ ja/ ko/ tr/ hi/ ar/  Les douze autres langues ──────┘
sitemap.xml              La carte du site pour Google ──┘

assets/css/style.css     TOUTES les couleurs et l'apparence du site
assets/js/i18n.js        TOUS les textes des boutons, en 13 langues
assets/js/theme.js       Le bouton soleil / lune
assets/js/barre.js       Le menu déroulant des langues
assets/js/carte.js       Le moteur des cartes (partagé par les 91 pages)
assets/js/comparateur.js L'onglet « Comparer » du panneau de gauche

data/                    Les chiffres. FABRIQUÉS par les scripts.

scripts/build_geojson.py Prépare le fond de carte (frontières, noms des pays)
scripts/build_donnees.py Va chercher les chiffres chez le FMI
scripts/build_pages.py   Fabrique les 130 pages, le sitemap et la page 404
```

Où sont les textes, selon leur nature :

| Texte | Fichier |
|---|---|
| les boutons, les onglets, la légende, les infobulles | `assets/js/i18n.js` |
| les titres du FMI et leurs unités | `scripts/build_donnees.py` |
| les noms courts, les adresses, les descriptions pour Google, les catégories, les libellés « nominal / parité de pouvoir d'achat » | `scripts/build_pages.py` |
| les noms des 197 pays | personne : ils viennent de Natural Earth |

### Je veux changer…

| …quoi ? | …dans quel fichier ? |
|---|---|
| une couleur du site | `assets/css/style.css`, tout en haut (section « Couleurs ») |
| les couleurs des cartes | `assets/js/carte.js`, tout en haut : `PALETTE_CLAIR` et `PALETTE_SOMBRE` |
| les seuils entre deux couleurs | `assets/js/carte.js`, les `tranches` de la carte concernée |
| les seuils du mode comparaison | `assets/js/carte.js`, le bloc `ECARTS` |
| le nombre de décimales affichées | `scripts/build_donnees.py`, `decimales` de la carte |
| un texte de bouton ou d'onglet | `assets/js/i18n.js` |
| le titre d'une carte, son unité | `scripts/build_donnees.py`, puis relancer le script |
| une catégorie de l'accueil | `scripts/build_pages.py`, `CATEGORIES` et le bloc `"categories"` de chaque langue |
| le mot « Bientôt » des rubriques à venir | `scripts/build_pages.py`, la clé `bientot` de chaque langue |
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

Et pour refabriquer les 130 pages, après avoir touché à un titre, une adresse
ou la liste des langues :

```bash
python3 scripts/build_pages.py
```

Ce dernier ne dépend de rien : on peut le relancer autant de fois qu'on veut,
il réécrit toujours exactement la même chose. Il fait aussi le ménage : si une
carte disparaît de la liste, son dossier est effacé dans les treize langues,
pour qu'aucune page fantôme ne reste en ligne avec des chiffres périmés.

Aucune installation n'est nécessaire : ces scripts n'utilisent que Python,
déjà présent sur macOS.

### Le FMI refuse les requêtes de Python

Depuis 2025, l'API du FMI est protégée contre les robots, et répond
**403 Access Denied** à qui ne ressemble pas à un vrai navigateur. Deux filtres
se cumulent :

1. **les en-têtes** — une simple ligne `User-Agent: StatsMaps` ne passe plus ;
2. **la poignée de main chiffrée elle-même** — le serveur reconnaît le logiciel
   qui se connecte à la *forme* de sa négociation TLS, avant même de lire la
   moindre en-tête. Python a une signature reconnaissable et se fait refouler
   quels que soient ses en-têtes ; `curl` passe.

D'où la façon de faire, dans `_telecharger()` : le script appelle **curl**,
présent partout (macOS, Linux, les serveurs de GitHub), et ne se rabat sur
Python que si curl manque. Si un jour la mise à jour automatique se met à
échouer avec « 403 », c'est de ce côté qu'il faut regarder — les en-têtes de
`EN_TETES` auront sans doute vieilli.

---

## ➕ Ajouter une nouvelle carte

Le FMI propose **132 indicateurs** (chômage, dette publique, balance
courante…). Pour en ajouter un :

1. Dans `scripts/build_donnees.py`, ajouter un bloc dans la liste `INDICATEURS` :
   son code FMI, sa catégorie, et son titre et ses unités dans les treize
   langues (le titre **court** et le titre **long**, comme les écrit le FMI).
2. Dans `assets/js/carte.js`, ajouter ses tranches de couleur et sa façon de
   mesurer un écart dans `CARTES`.
3. Dans `scripts/build_pages.py` : une ligne dans `CARTES`, l'identifiant dans
   la catégorie voulue de `CATEGORIES`, puis son entrée `"cartes"` dans
   **chacun** des treize blocs de `LANGUES` (adresse, nom, libellés du menu et
   phrase de présentation).
4. Relancer :

```bash
python3 scripts/build_donnees.py && python3 scripts/build_pages.py
```

Les 13 nouvelles pages, les liens du menu sur les 130 pages, les vignettes de
la catégorie et le sitemap suivent tout seuls.

> Le travail est celui de la **traduction**, pas de la recopie : l'étape 3
> demande cinq courtes phrases par langue. Le reste (couleurs, classement,
> légende, curseur, comparateur, pic) est partagé.

**Pour ajouter une simple variante** à une carte existante — le PIB en euros,
par exemple — c'est le même chemin, avec la même `famille` et une `variante`
différente : l'interrupteur du panneau apparaît tout seul dès qu'une famille
compte deux membres, et son libellé se prend dans le bloc `"variantes"` de
chaque langue.

**Pour ajouter une catégorie**, une ligne dans `CATEGORIES` et un bloc
`"categories"` dans chaque langue. La vignette de l'accueil, sa page et le
sitemap suivent. Pour l'annoncer sans l'ouvrir, laisser sa liste de cartes vide
et n'écrire que son `nom` et son `texte` : elle s'affichera en « Bientôt ».

---

## 🌍 Ajouter une langue

1. Dans `scripts/build_geojson.py`, une ligne dans le tableau `LANGUES` : le
   code de la langue et le champ où Natural Earth range les noms de pays
   (`"sv": "NAME_SV"` pour le suédois, par exemple). Les 197 noms viennent de
   là — il n'y a rien à traduire à la main.
2. Dans `assets/js/i18n.js`, un bloc de textes, sur le modèle des treize autres.
3. Dans `scripts/build_donnees.py`, la langue dans les `titre`, `unite` et
   `unite_longue` de chaque indicateur.
4. Dans `scripts/build_pages.py`, son bloc dans `LANGUES` : les modèles de
   titre, les adresses, les catégories et les sept cartes.
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

- **Données** : [FMI — World Economic Outlook](https://www.imf.org/external/datamapper/datasets/WEO)
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

  **L'ordre de peinture, pour Ceuta et Melilla.** Ces deux contours détaillés se
  superposent au Maroc : au 1:50 m, sa côte est lissée au kilomètre près et
  englobe les deux villes. Les deux formes se chevauchent donc réellement, et le
  navigateur peint les pays dans l'ordre du fichier — le Maroc, qui venait
  après l'Espagne, les recouvrait et leur donnait sa couleur.

  La fonction `remonter_les_hotes_denclaves()` place donc l'Espagne et le
  Royaume-Uni **en dernier** dans `data/pays.json` : ils sont peints par-dessus
  leur voisin, et les enclaves gardent leur couleur.

  Pourquoi pas un découpage propre du Maroc, comme pour le Golan ? Parce que
  `detacher()` a besoin que les deux contours partagent des sommets — ce qui
  suppose qu'ils viennent du même fichier. Ici plusieurs sommets des enclaves
  tombent même en mer, hors du contour marocain simplifié : il n'y a rien à
  découper, seulement un ordre à respecter.

  Le clic et le survol suivent la même règle, dans `paysDuDessus()` de
  `carte.js` : quand plusieurs pays se superposent sous le curseur, c'est celui
  qui est écrit en dernier — donc celui qu'on voit — qui est désigné. Sans cela,
  on cliquerait sur une Ceuta espagnole et la bulle du Maroc s'ouvrirait.

- **Cadrage au clic** — chaque pays porte une propriété `c` calculée par
  `cadrage_du_pays()` : la zone à afficher quand on clique dessus. Elle est
  calculée **avant** le rattachement des territoires, sinon cliquer sur le
  Danemark cadrerait sur le Groenland et cliquer sur la France sur Tahiti.
- **Carte** : [MapLibre GL JS](https://maplibre.org/) (licence BSD-3)

Le site est **statique** : pas de base de données, pas de serveur, pas de
publicité, pas de traceur.
