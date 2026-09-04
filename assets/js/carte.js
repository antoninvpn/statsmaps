/* ==========================================================================
   carte.js — le moteur des cartes de StatsMaps.

   Ce SEUL fichier fait fonctionner les 65 pages de carte (5 cartes × 13 langues).
   Chaque page lui dit quoi faire grâce à 3 informations posées sur la balise
   <body> :
       data-indicateur="pib-nominal"   → quelle carte afficher
       data-langue="fr"                → dans quelle langue
       data-base="../"                 → où trouver le dossier data/

   Déroulé du fichier :
     1. Réglages des cartes (couleurs et tranches)
     2. Petits outils (mise en forme des nombres)
     3. Chargement des données
     4. Fabrication de la carte
     5. Le classement à gauche
     6. La légende
     7. Le curseur des années
     8. Le mode comparaison (« et par rapport à la France ? »)
     9. Démarrage
   ========================================================================== */

(function () {
  "use strict";

  /* --- 1. Réglages des cartes -------------------------------------------

     LA PALETTE DU SITE, écrite une seule fois pour les cinq cartes.

     Sept couleurs, du rouge sombre au vert sombre en passant par l'orange et
     le jaune : la famille de couleurs des cartes économiques de Wikipédia.

     Le sens de lecture est TOUJOURS le même sur tout le site :
         le VERT est le côté favorable (pays riche, forte croissance,
         record tout récent) et le ROUGE le côté défavorable.

     Comme les cartes ne se lisent pas toutes dans le même sens, la palette est
     écrite ici une fois du rouge vers le vert, et les cartes qui en ont besoin
     la retournent avec inverser().

     Pour changer les couleurs du site entier, c'est ici et nulle part ailleurs. */

  var PALETTE_CLAIR = [
    "#8c1119", // rouge sombre
    "#d9603c", // rouge orangé
    "#f2a25c", // orange
    "#f3dd6a", // jaune
    "#9ed468", // vert clair
    "#54a848", // vert
    "#1a7a35", // vert sombre
  ];

  /* La même palette, éclaircie pour rester lisible sur fond noir. */
  var PALETTE_SOMBRE = [
    "#a02a2a", "#cf5e3a", "#e39a4a", "#e8cf5c", "#a8d96a", "#67c25c", "#2ea45a",
  ];

  /* Retourne une liste de couleurs (le premier devient le dernier). */
  function inverser(couleurs) {
    return couleurs.slice().reverse();
  }

  /* Pour chaque carte : les "tranches" (les seuils qui séparent les couleurs)
     et le sens de lecture de la palette.
     Il y a toujours 1 couleur de plus que de tranches.

     Ces tranches sont FIXES : elles ne changent pas d'une année à l'autre.
     C'est volontaire : ainsi, quand on fait défiler les années, on voit
     vraiment les pays changer de couleur en s'enrichissant.

     À savoir : le rouge et le vert sont les deux couleurs que confondent les
     daltoniens (environ 8 % des hommes). Le passage par l'orange et le jaune,
     et l'écart de clarté d'une tranche à l'autre, font qu'ils distinguent
     quand même « clair » de « sombre ». C'est un choix assumé.             */

  /* LES TROIS FAÇONS DE MESURER UN ÉCART ENTRE DEUX PAYS.

     Quand on choisit un pays de référence (« et par rapport à la France ? »),
     la carte ne montre plus la valeur de chaque pays mais son ÉCART avec ce
     pays-là. Cet écart ne se mesure pas de la même façon selon la carte :

       ratio  — de combien de POUR CENT le pays est au-dessus ou en dessous.
                C'est la bonne lecture pour une richesse : dire que le
                Luxembourg dépasse la France de 145 % parle ; dire qu'il la
                dépasse de 71 000 dollars, beaucoup moins.
       points — la simple soustraction, pour la croissance : deux taux en %
                se comparent en POINTS, jamais en pourcentage de pourcentage.
       annees — la simple soustraction aussi, pour les cartes « année record ».

     Dans les trois cas, le signe a toujours le même sens : POSITIF = le pays
     fait MIEUX que la référence. La palette n'est donc jamais retournée ici,
     même sur les cartes « année record » : le vert reste du côté favorable.
     Le milieu (jaune) est la zone « à peu près au même niveau ».            */

  var ECARTS = {
    ratio:  { tranches: [-60, -30, -10, 10, 30, 60], decimales: 0 },
    points: { tranches: [-4, -2, -0.5, 0.5, 2, 4],   decimales: 1 },
    annees: { tranches: [-10, -5, -1, 1, 5, 10],     decimales: 0 },
  };

  var CARTES = {
    /* Plus l'économie est grosse, plus c'est vert. */
    "pib-nominal": {
      ecart: "ratio",
      tranches: [10, 50, 200, 1000, 3000, 10000],
      clair: PALETTE_CLAIR,
      sombre: PALETTE_SOMBRE,
    },

    /* Plus le pays est riche par habitant, plus c'est vert. C'est exactement
       la lecture de la carte de Wikipédia sur le PIB par habitant. */
    "pib-par-habitant": {
      ecart: "ratio",
      tranches: [1500, 5000, 15000, 30000, 50000, 70000],
      clair: PALETTE_CLAIR,
      sombre: PALETTE_SOMBRE,
    },

    /* Échelle "divergente" : rouge quand l'économie recule, vert quand elle
       avance. Point important : le ZÉRO est une frontière entre deux couleurs,
       et non le milieu d'une tranche. Ainsi un pays à -0,5 % tombe forcément
       du côté chaud (orange) et un pays à +0,5 % du côté clair (jaune).
       L'intensité augmente en s'éloignant de zéro : plus c'est vif, plus le
       mouvement est fort, dans un sens comme dans l'autre.                 */
    croissance: {
      ecart: "points",
      tranches: [-4, -1.5, 0, 1.5, 4, 7],
      clair: PALETTE_CLAIR,
      sombre: PALETTE_SOMBRE,
    },

    /* Les deux cartes « année record » fonctionnent différemment des trois
       autres : le chiffre affiché est une ANNÉE (« 2008 »), mais la couleur
       ne dépend pas de cette année — elle dépend du TEMPS ÉCOULÉ depuis.
       Vu depuis 2025, un record de 2008 date de 17 ans : il sera rouge.
       Vu depuis 2010, le même record date de 2 ans : il sera vert.
       C'est le rôle du réglage "ecart_annees" ci-dessous.

       Les tranches se lisent donc en années écoulées :
         0 = record battu cette année même (le pays va bien) ... vert sombre
         26 et plus = le pays n'a jamais retrouvé son niveau .. rouge sombre

       Ici « petit » veut dire « bon » : la palette est donc retournée, pour
       que le vert reste du côté favorable comme sur toutes les autres cartes. */
    "annee-record-pib": {
      ecart: "annees",
      ecart_annees: true,
      /* Ici le classement se lit à l'envers des autres cartes : on met en
         premier les pays dont le record est le PLUS ANCIEN, c'est-à-dire ceux
         qui reculent depuis le plus longtemps. C'est là qu'est l'information ;
         à l'endroit, il faudrait faire défiler 150 pays « 2025 » avant de
         trouver quoi que ce soit d'intéressant. */
      classement_croissant: true,
      tranches: [1, 3, 6, 11, 16, 26],
      clair: inverser(PALETTE_CLAIR),
      sombre: inverser(PALETTE_SOMBRE),
    },
    "annee-record-pib-par-habitant": {
      ecart: "annees",
      ecart_annees: true,
      classement_croissant: true,
      tranches: [1, 3, 6, 11, 16, 26],
      clair: inverser(PALETTE_CLAIR),
      sombre: inverser(PALETTE_SOMBRE),
    },
  };

  /* --- 2. Petits outils --------------------------------------------------- */

  var corps = document.body;
  var idCarte = corps.getAttribute("data-indicateur");
  var langue = corps.getAttribute("data-langue") || "fr";
  var base = corps.getAttribute("data-base") || "./";
  var t = window.StatsMapsT(langue);
  /* La « locale » dit au navigateur comment écrire les nombres : 1 234,5 en
     français, 1,234.5 en anglais, 12,34,567 en hindi (le groupement indien).
     Cas particulier de l'arabe : « ar » seul afficherait ١٢٣٤ — les chiffres
     arabes orientaux. Sur un site de statistiques, où l'on compare des nombres
     d'un pays à l'autre et d'une langue à l'autre, on garde les chiffres 0-9,
     c'est le sens de « -u-nu-latn ». Enlever ce suffixe suffirait à revenir
     aux chiffres orientaux. */
  var locale = {
    fr: "fr-FR", en: "en-US", uk: "uk-UA",
    de: "de-DE", es: "es-ES", it: "it-IT", pt: "pt-PT", pl: "pl-PL",
    ja: "ja-JP", ko: "ko-KR", tr: "tr-TR", hi: "hi-IN",
    ar: "ar-u-nu-latn",
  }[langue] || "fr-FR";
  var reglages = CARTES[idCarte];

  /* Écrit un nombre proprement : 3 368 au lieu de 3368.925 */
  function formater(valeur, decimales) {
    return valeur.toLocaleString(locale, {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    });
  }

  /* Version courte pour la légende : 10 000 devient "10 k" */
  function formaterCourt(valeur) {
    var abs = Math.abs(valeur);
    if (abs >= 1000) {
      var milliers = valeur / 1000;
      return formater(milliers, milliers % 1 === 0 ? 0 : 1) + " k";
    }
    return formater(valeur, abs > 0 && abs < 10 && valeur % 1 !== 0 ? 1 : 0);
  }

  /* « il y a 17 ans », mais « il y a 1 an » — et en ukrainien « 1 рік »,
     « 3 роки », « 5 років ». Plutôt que d'écrire ces règles à la main, on
     demande au navigateur quelle forme employer : il connaît les règles de
     toutes les langues (c'est le rôle de Intl.PluralRules).                */
  var reglePluriel =
    window.Intl && Intl.PluralRules ? new Intl.PluralRules(locale) : null;

  function texteEcart(nombre) {
    var forme = reglePluriel ? reglePluriel.select(nombre) : "other";
    var modele = t("ecart_" + forme);
    /* Si la langue n'a pas cette forme-là, on retombe sur la forme générale. */
    if (modele === "ecart_" + forme) modele = t("ecart_other");
    return modele.replace("{n}", nombre);
  }

  /* Enlève les accents d'un texte : "Viêt Nam" devient "viet nam".
     Sans ça, chercher "vietnam" ou "coree" ne trouverait rien.            */
  function sansAccents(texte) {
    return String(texte)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  /* La valeur affichée partout (classement, infobulle) avec son unité.
     Cas particulier : sur les cartes « année record », la valeur EST une année.
     On l'écrit telle quelle, sinon l'ordinateur afficherait « 2 008 ».      */
  function valeurLisible(valeur, donnees) {
    if (donnees.format === "annee") return String(valeur);
    var unite = donnees.unite[langue] || donnees.unite.fr;
    var texte = formater(valeur, donnees.decimales);
    if (idCarte === "croissance" && valeur > 0) texte = "+" + texte;
    return texte + " " + unite;
  }

  function couleursActuelles() {
    var sombre =
      window.StatsMapsTheme && window.StatsMapsTheme.actuel() === "dark";
    return sombre ? reglages.sombre : reglages.clair;
  }

  /* Lit une couleur définie dans le fichier CSS (pour rester cohérent). */
  function couleurCSS(nom) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(nom)
      .trim();
  }

  /* Ce qui décide de la couleur d'un pays.
     Sur presque toutes les cartes, c'est la valeur elle-même. Sur les cartes
     « année record », c'est le nombre d'années écoulées depuis ce record :
     un record de 2008 vaut 17 quand on regarde depuis 2025.                */
  function valeurDeCouleur(valeur) {
    return reglages.ecart_annees ? anneeAffichee - valeur : valeur;
  }

  /* La couleur d'un pays, utilisée pour le liseré coloré du classement. */
  function couleurDeLaValeur(valeur) {
    var couleurs = couleursActuelles();
    var pour_couleur = valeurDeCouleur(valeur);
    var index = 0;
    for (var i = 0; i < reglages.tranches.length; i++) {
      if (pour_couleur >= reglages.tranches[i]) index = i + 1;
    }
    return couleurs[index];
  }

  /* --- Les outils de la comparaison ---------------------------------------

     Tant qu'aucun pays de référence n'est choisi, tout ce qui suit dort et la
     carte se lit normalement. Dès qu'on en choisit un, la carte bascule : elle
     ne montre plus « combien », mais « combien de plus ou de moins que lui ». */

  /* Un pays de référence est-il désigné ? C'est ce qui décide de l'affichage
     du bouton, de la croix de sortie et de la ligne « pays de référence ». */
  function enComparaison() {
    return isoReference !== null && !!reglages.ecart;
  }

  /* La comparaison est-elle CALCULABLE pour l'année affichée ?

     Ce n'est pas la même question. Un pays peut être désigné comme référence
     et n'avoir aucun chiffre l'année où l'on se trouve — la Syrie après 2011,
     ou n'importe quel pays si l'on remonte assez loin. Il n'y a alors aucun
     écart à calculer, et la carte doit revenir à ses valeurs habituelles.

     Sans cette distinction, l'échelle et les valeurs se désaccordaient : la
     carte peignait des dollars sur une échelle de pourcentages, et le monde
     entier virait au vert sombre. */
  function comparaisonPossible() {
    return enComparaison() && valeurReference() !== null;
  }

  /* Les réglages de l'écart pour la carte affichée (tranches, décimales). */
  function reglagesEcart() {
    return ECARTS[reglages.ecart];
  }

  /* L'écart entre un pays et la référence, dans l'unité de la carte.
     Renvoie null quand le calcul n'a pas de sens : pays sans chiffre cette
     année-là, ou référence à zéro (on ne divise pas par zéro). */
  function calculerEcart(valeur, reference) {
    if (valeur === null || reference === null || reference === undefined) return null;
    if (reglages.ecart === "ratio") {
      if (!reference) return null;
      return (valeur / reference - 1) * 100;
    }
    /* "points" comme "annees" : une simple soustraction. */
    return valeur - reference;
  }

  /* La valeur de la référence pour l'année affichée (null si elle n'en a pas). */
  function valeurReference() {
    var ligne = ligneDuClassement(isoReference);
    return ligne ? ligne.valeur : null;
  }

  /* La couleur d'un écart, sur la palette rouge → vert non retournée :
     négatif (le pays fait moins bien) = rouge, positif = vert.             */
  function couleurDeLEcart(ecart) {
    var couleurs = couleursActuelles();
    /* Sur les cartes « année record », la palette du site est retournée pour
       la lecture habituelle. Ici on la remet à l'endroit : l'écart se lit
       toujours dans le même sens. */
    if (reglages.classement_croissant) couleurs = inverser(couleurs);
    var tranches = reglagesEcart().tranches;
    var index = 0;
    for (var i = 0; i < tranches.length; i++) {
      if (ecart >= tranches[i]) index = i + 1;
    }
    return couleurs[index];
  }

  /* « +24 % », « −1,8 pt », « +3 ans ». Toujours avec son signe : c'est lui
     qui porte l'information. */
  function ecartLisible(ecart) {
    if (ecart === null) return "—";
    var mesure = reglages.ecart;
    var texte = formater(Math.abs(ecart), reglagesEcart().decimales);
    /* Le signe moins typographique (−), et non le trait d'union du clavier. */
    var signe = ecart > 0 ? "+" : ecart < 0 ? "\u2212" : "";

    if (mesure === "ratio") return signe + texte + " %";
    if (mesure === "points") return signe + texte + " " + t("unite_points");
    return signe + motAnnees(Math.abs(ecart));
  }

  /* « 1 an », « 3 ans » — et les formes propres à chaque langue, comme pour
     texteEcart() plus haut. */
  function motAnnees(nombre) {
    var forme = reglePluriel ? reglePluriel.select(nombre) : "other";
    var modele = t("an_" + forme);
    if (modele === "an_" + forme) modele = t("an_other");
    return modele.replace("{n}", formater(nombre, 0));
  }

  /* Les deux bouts de l'échelle d'écart : le rouge du côté « fait moins bien »
     et le vert du côté « fait mieux ». Le comparateur s'en sert pour teinter
     son graphique des mêmes couleurs que la carte. */
  function couleursExtremes() {
    var couleurs = couleursActuelles();
    if (reglages.classement_croissant) couleurs = inverser(couleurs);
    return { rouge: couleurs[0], vert: couleurs[couleurs.length - 1] };
  }

  /* Se placer sur une année, curseur compris. Le comparateur appelle ceci
     quand on clique dans son graphique. */
  function allerAAnnee(annee) {
    var curseur = document.getElementById("curseur-annee");
    if (curseur) curseur.value = annee;
    if (annee !== anneeAffichee) appliquerAnnee(annee);
  }

  /* --- 3. Chargement des données ----------------------------------------- */

  function charger(chemin) {
    return fetch(base + chemin, { cache: "no-cache" }).then(function (reponse) {
      if (!reponse.ok) throw new Error(chemin + " : " + reponse.status);
      return reponse.json();
    });
  }

  /* --- État de la page (ce qui change quand on bouge le curseur) ---------- */

  var carte = null;
  var geo = null;
  var donnees = null;
  var meta = null;
  var anneeAffichee = null;
  var classementActuel = []; // [{iso, nom, valeur, rang}, ...] — les 197 pays
  var nbClasses = 0;         // parmi eux, ceux qui ont un chiffre cette année
  var nomsParIso = {};
  var nomsCherchablesParIso = {}; // les mêmes noms, sans accents
  var drapeauxParIso = {};        // 🇫🇷, 🇺🇦 ... préparés par le script Python
  var isoSurvole = null;  // le pays sous la souris
  var isoChoisi = null;   // le pays sur lequel on a cliqué
  var infobulle = null;
  var positionInfobulle = null; // l'endroit de la carte où la bulle est posée
  var isoReference = null;      // le pays auquel on compare tous les autres

  /* --- 4. Fabrication de la carte ----------------------------------------- */

  function styleDeBase() {
    return {
      version: 8,
      name: "StatsMaps",
      sources: {},
      layers: [
        {
          id: "mer",
          type: "background",
          paint: { "background-color": couleurCSS("--fond-carte") },
        },
      ],
    };
  }

  /* Construit la règle de couleur que MapLibre applique à chaque pays.
     Traduction en français : "si le pays a une donnée, colorie-le selon sa
     valeur en suivant les tranches ; sinon, colorie-le en gris".           */
  function regleDeCouleur() {
    var couleurs = couleursActuelles();
    var tranches = reglages.tranches;

    /* En comparaison, la carte change d'échelle : ce ne sont plus les tranches
       de richesse (ou de croissance) mais celles de l'écart, et la palette est
       remise à l'endroit sur les cartes « année record ». */
    if (comparaisonPossible()) {
      tranches = reglagesEcart().tranches;
      if (reglages.classement_croissant) couleurs = inverser(couleurs);
    }

    var etapes = ["step", ["to-number", ["feature-state", "valeur"], 0], couleurs[0]];
    for (var i = 0; i < tranches.length; i++) {
      etapes.push(tranches[i], couleurs[i + 1]);
    }
    return [
      "case",
      ["==", ["feature-state", "aDonnee"], 1],
      etapes,
      couleurCSS("--pays-sans-donnee"),
    ];
  }

  /* La couleur et l'épaisseur du trait de frontière. Trois cas, du plus fort
     au plus faible : le pays de référence de la comparaison (cerclé de bleu),
     le pays survolé, et tous les autres.
     Ces deux règles servent à deux endroits — à la construction de la carte et
     au changement de thème — d'où le fait qu'elles soient écrites ici. */
  function regleContourCouleur() {
    return [
      "case",
      ["boolean", ["feature-state", "reference"], false], couleurCSS("--accent"),
      ["boolean", ["feature-state", "survol"], false], couleurCSS("--texte"),
      couleurCSS("--contour-pays"),
    ];
  }

  function regleContourEpaisseur() {
    return [
      "case",
      ["boolean", ["feature-state", "reference"], false], 2.4,
      ["boolean", ["feature-state", "survol"], false], 1.6,
      0.4,
    ];
  }

  /* Le cadrage de départ : le monde entier, sans l'Antarctique (qui, sur une
     carte plate, prend une place énorme pour rien).
     Attention : une longitude doit rester entre -180 et 180.               */
  var CADRAGE_MONDE = [[-179, -56], [179, 81]];

  /* On laisse de la place pour le panneau et le curseur, afin qu'aucun pays
     ne se retrouve caché derrière eux. */
  function margesDuCadrage() {
    var large = window.innerWidth > 860;
    var placeDuPanneau = large ? 340 : 24;
    /* En arabe, le panneau passe à droite : la marge le suit, sinon la carte
       se cadrerait derrière lui. */
    var droiteAGauche = document.documentElement.dir === "rtl";
    return {
      top: 24,
      right: droiteAGauche ? placeDuPanneau : 24,
      bottom: large ? 130 : 150,
      left: droiteAGauche ? 24 : placeDuPanneau,
    };
  }

  function construireCarte() {
    carte = new maplibregl.Map({
      container: "carte",
      style: styleDeBase(),
      bounds: CADRAGE_MONDE,
      fitBoundsOptions: { padding: margesDuCadrage() },
      minZoom: 0.5,
      maxZoom: 7,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    });

    carte.touchZoomRotate.disableRotation();
    carte.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    carte.addControl(
      new maplibregl.AttributionControl({
        compact: true,
        customAttribution:
          '<a href="https://www.naturalearthdata.com/">Natural Earth</a> · ' +
          '<a href="https://www.imf.org/external/datamapper/">' +
          (langue === "fr" ? "FMI" : "IMF") +
          "</a>",
      }),
      "bottom-right"
    );

    /* Si MapLibre rencontre un problème, on le voit dans la console du
       navigateur au lieu d'avoir une page qui reste bloquée sans explication. */
    carte.on("error", function (evenement) {
      console.error(
        "[StatsMaps] carte :",
        (evenement && evenement.error && evenement.error.message) || evenement
      );
    });

    carte.on("load", function () {
      carte.addSource("pays", {
        type: "geojson",
        data: geo,
        promoteId: "iso", // le code du pays sert d'identifiant
      });

      carte.addLayer({
        id: "pays-fond",
        type: "fill",
        source: "pays",
        paint: {
          "fill-color": regleDeCouleur(),
          "fill-opacity": [
            "case",
            ["boolean", ["feature-state", "survol"], false],
            1,
            0.92,
          ],
        },
      });

      carte.addLayer({
        id: "pays-contour",
        type: "line",
        source: "pays",
        paint: {
          "line-color": regleContourCouleur(),
          "line-width": regleContourEpaisseur(),
        },
      });

      brancherInteractions();
      /* La carte est prête : on lui envoie les valeurs de l'année affichée. */
      appliquerEtatsCarte();
    });
  }

  function brancherInteractions() {
    carte.on("mousemove", "pays-fond", function (evenement) {
      if (!evenement.features.length) return;
      var iso = evenement.features[0].properties.iso;
      if (iso === isoSurvole) return;
      surligner(iso);
      carte.getCanvas().style.cursor = "pointer";
    });

    carte.on("mouseleave", "pays-fond", function () {
      surligner(null);
      carte.getCanvas().style.cursor = "";
    });

    carte.on("click", "pays-fond", function (evenement) {
      if (!evenement.features.length) return;
      ouvrirInfobulle(evenement.features[0].properties.iso, evenement.lngLat);
    });
  }

  function surligner(iso) {
    if (isoSurvole) {
      carte.setFeatureState({ source: "pays", id: isoSurvole }, { survol: false });
      var ancien = document.querySelector('.classement li[data-iso="' + isoSurvole + '"]');
      if (ancien) ancien.classList.remove("est-actif");
    }
    isoSurvole = iso;
    if (iso) {
      carte.setFeatureState({ source: "pays", id: iso }, { survol: true });
      var ligne = document.querySelector('.classement li[data-iso="' + iso + '"]');
      if (ligne) ligne.classList.add("est-actif");
    }
  }

  /* Retrouve la ligne d'un pays dans le classement de l'année affichée.
     Renvoie null si le pays n'y figure pas du tout (un territoire dépendant,
     par exemple, qui est dessiné sur la carte mais pas classé). */
  function ligneDuClassement(iso) {
    for (var i = 0; i < classementActuel.length; i++) {
      if (classementActuel[i].iso === iso) return classementActuel[i];
    }
    return null;
  }

  /* Le contenu de la bulle d'un pays, pour l'année affichée.

     Cette fabrication est séparée de l'ouverture de la bulle, parce qu'elle
     sert deux fois : au clic, et à chaque fois qu'on bouge le curseur des
     années — la bulle reste alors en place et son texte seul est réécrit. */
  function contenuInfobulle(iso) {
    var ligne = ligneDuClassement(iso);
    var nom = nomsParIso[iso] || iso;
    var emoji = drapeauxParIso[iso] || "";
    var contenu =
      '<div class="popup__nom">' +
      (emoji ? '<span class="drapeau" aria-hidden="true">' + echapper(emoji) + "</span>" : "") +
      echapper(nom) +
      "</div>";

    if (ligne && ligne.valeur !== null) {
      /* Sur les cartes « année record », le rang n'apprendrait rien : plus de
         cent pays sont à égalité. On dit plutôt depuis combien de temps le
         record tient. */
      var detail;
      if (reglages.ecart_annees) {
        var ecart = anneeAffichee - ligne.valeur;
        detail = ecart === 0 ? t("ecart_zero") : texteEcart(ecart);
      } else if (ligne.territoire) {
        detail = String(anneeAffichee); // un territoire n'a pas de rang
      } else {
        detail =
          anneeAffichee + " · " + t("rang") + " " + ligne.rang +
          " " + t("sur") + " " + nbClasses;
      }
      if (ligne.territoire) detail += " · " + t("territoire");
      contenu +=
        '<div class="popup__valeur nombre">' +
        echapper(valeurLisible(ligne.valeur, donnees)) +
        "</div>" +
        '<div class="popup__detail">' + echapper(detail) + "</div>";
    } else {
      contenu += '<div class="popup__detail">' + t("pas_de_donnee") + "</div>";
    }

    /* En comparaison, c'est l'écart qui intéresse : on l'écrit en clair sous
       la valeur, plutôt que de laisser deviner la couleur. */
    if (enComparaison()) {
      var nomReference = nomsParIso[isoReference] || isoReference;
      if (iso === isoReference) {
        contenu +=
          '<div class="popup__ecart est-reference">' + t("reference_pays") + "</div>";
      } else {
        var ecart = ligne ? calculerEcart(ligne.valeur, valeurReference()) : null;
        if (ecart !== null) {
          contenu +=
            '<div class="popup__ecart">' +
            '<span class="drapeau" aria-hidden="true">' +
            echapper(drapeauxParIso[isoReference] || "") + "</span>" +
            echapper(nomReference + t("deux_points")) +
            "<b>" + echapper(ecartLisible(ecart)) + "</b>" +
            "</div>";
        }
      }
    }
    return contenu;
  }

  function ouvrirInfobulle(iso, position) {
    if (infobulle) infobulle.remove();
    positionInfobulle = position;
    infobulle = new maplibregl.Popup({ closeButton: true, maxWidth: "240px" })
      .setLngLat(position)
      .setHTML(contenuInfobulle(iso))
      .addTo(carte);

    /* Quand on ferme l'infobulle, le pays n'est plus « choisi ». */
    infobulle.on("close", function () {
      if (isoChoisi === iso) {
        isoChoisi = null;
        positionInfobulle = null;
        montrerDansClassement(null);
        dessinerLegende();
      }
    });

    isoChoisi = iso;
    montrerDansClassement(iso);
    dessinerLegende();

    /* Quand l'onglet « Comparer » est ouvert, un clic sur la carte remplit
       l'une de ses deux fentes plutôt que de rester sans suite. */
    if (window.StatsMapsComparateur && window.StatsMapsComparateur.estOuvert()) {
      window.StatsMapsComparateur.choisirPays(iso);
    }
  }

  /* Réécrit le texte de la bulle sans la déplacer ni la refermer.
     C'est ce qui permet de cliquer sur la France, puis de faire défiler les
     années en gardant son chiffre sous les yeux. */
  function rafraichirInfobulle() {
    if (!infobulle || !isoChoisi) return;
    infobulle.setHTML(contenuInfobulle(isoChoisi));
  }

  /* Fait apparaître dans le classement le pays sur lequel on vient de cliquer.
     Sans ça, cliquer sur le Japon sur la carte ne montrait rien : la liste
     restait sur les dix premiers pays. */
  function montrerDansClassement(iso) {
    var liste = document.getElementById("classement");
    if (!liste) return;

    var ancien = liste.querySelector("li.est-choisi");
    if (ancien) ancien.classList.remove("est-choisi");
    if (!iso) return;

    /* Si une recherche en cours masque ce pays, on efface la recherche :
       le visiteur vient de demander à le voir. */
    if (
      champRecherche &&
      champRecherche.value.trim() &&
      !liste.querySelector('li[data-iso="' + iso + '"]')
    ) {
      champRecherche.value = "";
      dessinerClassement();
    }

    var ligne = liste.querySelector('li[data-iso="' + iso + '"]');
    if (!ligne) return;
    ligne.classList.add("est-choisi");
    centrerSurLigne(iso);
  }

  /* Ramène la ligne d'un pays au milieu du panneau — mais seulement si elle
     est sortie de l'écran. Sinon, faire glisser le curseur des années ferait
     sautiller la liste à chaque pas, alors que la ligne est déjà sous les yeux.
     Le calcul est fait à la main plutôt qu'avec scrollIntoView, qui ferait
     aussi bouger toute la page. */
  function centrerSurLigne(iso) {
    var liste = document.getElementById("classement");
    if (!liste) return;
    var ligne = liste.querySelector('li[data-iso="' + iso + '"]');
    if (!ligne) return;

    var cadreListe = liste.getBoundingClientRect();
    var cadreLigne = ligne.getBoundingClientRect();
    if (cadreLigne.top >= cadreListe.top && cadreLigne.bottom <= cadreListe.bottom) return;
    liste.scrollTop +=
      cadreLigne.top - cadreListe.top - (cadreListe.height - cadreLigne.height) / 2;
  }

  function echapper(texte) {
    return String(texte).replace(/[&<>"]/g, function (caractere) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[caractere];
    });
  }

  /* --- Appliquer une année : le cœur du mécanisme ------------------------- */

  /* Colorie la carte à partir du classement déjà calculé.
     Peut être appelée à tout moment : si la carte n'est pas encore dessinée,
     elle ne fait rien, et sera rappelée dès que la carte sera prête.        */
  function appliquerEtatsCarte() {
    if (!carte || !carte.getSource("pays")) return;

    var comparaison = comparaisonPossible();
    var reference = comparaison ? valeurReference() : null;

    /* L'échelle de couleurs et les valeurs envoyées à chaque pays doivent
       toujours parler de la même chose. On les pose donc au même endroit,
       plutôt que de laisser deux fonctions décider chacune de son côté. */
    if (carte.isStyleLoaded()) {
      carte.setPaintProperty("pays-fond", "fill-color", regleDeCouleur());
    }

    var avecDonnee = {};
    classementActuel.forEach(function (element) {
      /* Un pays sans chiffre cette année-là reste gris sur la carte, même
         s'il figure quand même dans le classement. */
      if (element.valeur === null) return;

      var pourLaCouleur = comparaison
        ? calculerEcart(element.valeur, reference)
        : valeurDeCouleur(element.valeur);
      if (pourLaCouleur === null) return;

      avecDonnee[element.iso] = true;
      carte.setFeatureState(
        { source: "pays", id: element.iso },
        {
          valeur: pourLaCouleur,
          aDonnee: 1,
          reference: element.iso === isoReference,
        }
      );
    });
    geo.features.forEach(function (pays) {
      var iso = pays.properties.iso;
      if (!avecDonnee[iso]) {
        carte.setFeatureState(
          { source: "pays", id: iso },
          { valeur: 0, aDonnee: 0, reference: iso === isoReference }
        );
      }
    });
  }

  function appliquerAnnee(annee) {
    anneeAffichee = annee;
    var clef = String(annee);
    var valeurs = donnees.valeurs;

    /* Le classement contient TOUS les pays — 197 — et pas seulement ceux qui
       ont un chiffre cette année-là. On les range en deux groupes : ceux qui
       ont un chiffre, numérotés ; puis ceux qui n'en ont pas, à la suite, par
       ordre alphabétique.

       Qui a le droit d'y figurer ?
         - les pays suivis par le FMI ;
         - les quatre pays souverains que le FMI ne suit pas, marqués "p" par
           le script Python : Cuba, Corée du Nord, Monaco, Vatican ;
         - les quatre territoires suivis par le FMI, marqués "t" : Hong Kong,
           Macao, Puerto Rico et Aruba. Ils sont montrés à titre indicatif,
           mais ne prennent pas de numéro et ne sont pas comptés : ce ne sont
           pas des États souverains.
       Tout le reste du fond de carte — Groenland, Nouvelle-Calédonie, îles
       Caïmans, glacier de Siachen... — n'a rien à faire dans un classement
       de pays et reste simplement dessiné sur la carte.                    */
    var avecChiffre = [];
    var sansChiffre = [];
    geo.features.forEach(function (pays) {
      var iso = pays.properties.iso;
      var parAnnee = valeurs[iso];
      if (!parAnnee && pays.properties.p !== 1) return;

      var element = {
        iso: iso,
        nom: nomsParIso[iso],
        valeur: null,
        rang: 0,
        territoire: pays.properties.t === 1,
      };
      if (parAnnee && typeof parAnnee[clef] === "number") {
        element.valeur = parAnnee[clef];
        avecChiffre.push(element);
      } else {
        sansChiffre.push(element);
      }
    });

    /* Du plus grand au plus petit — sauf sur les cartes « année record », qui
       demandent l'inverse (voir classement_croissant tout en haut du fichier).
       En cas d'égalité — fréquent sur ces cartes-là, où plus de cent pays
       battent leur record la même année — on départage par ordre alphabétique,
       sinon l'ordre serait au hasard. */
    avecChiffre.sort(function (a, b) {
      if (b.valeur !== a.valeur) {
        return reglages.classement_croissant
          ? a.valeur - b.valeur
          : b.valeur - a.valeur;
      }
      return a.nom.localeCompare(b.nom, locale);
    });
    /* Les territoires gardent leur place dans la liste, à leur valeur, mais
       sautent la numérotation : le classement compte les pays. */
    var rang = 0;
    avecChiffre.forEach(function (element) {
      if (!element.territoire) {
        rang += 1;
        element.rang = rang;
      }
    });
    sansChiffre.sort(function (a, b) {
      return a.nom.localeCompare(b.nom, locale);
    });

    nbClasses = rang;
    classementActuel = avecChiffre.concat(sansChiffre);

    /* On envoie sa valeur à chaque pays de la carte (si elle est prête). */
    appliquerEtatsCarte();

    dessinerClassement();
    majEtiquetteAnnee();

    /* Le pays choisi, lui, ne change pas quand on bouge le curseur : c'est
       tout l'intérêt. On garde donc la bulle ouverte, à la même place, et on
       se contente d'y réécrire les chiffres de la nouvelle année. */
    rafraichirInfobulle();
    /* Son rang, lui, a pu bouger : on le suit du regard dans la liste. */
    if (isoChoisi) centrerSurLigne(isoChoisi);
    if (window.StatsMapsComparateur) window.StatsMapsComparateur.majAnnee(annee);
  }

  /* --- 5. Le classement à gauche ------------------------------------------ */

  var champRecherche = null;

  function dessinerClassement() {
    var liste = document.getElementById("classement");
    if (!liste) return;

    var filtre = champRecherche ? sansAccents(champRecherche.value.trim()) : "";
    var affiches = filtre
      ? classementActuel.filter(function (element) {
          return nomsCherchablesParIso[element.iso].indexOf(filtre) !== -1;
        })
      : classementActuel;

    if (!affiches.length) {
      liste.innerHTML = '<li class="vide">' + t("aucun_resultat") + "</li>";
      return;
    }

    /* La couleur du pays devient un fin liseré sur le bord gauche de la ligne
       (voir .classement li dans le fichier de style). Ça laisse la place au
       drapeau sans rogner les noms longs.

       Les pays sans chiffre pour l'année affichée sont toujours à la fin de la
       liste. On les annonce par une ligne de séparation, une seule fois : la
       phrase complète ne tiendrait pas dans la colonne de droite, qui fait
       60 pixels, et l'écrire sur chaque ligne écraserait les noms de pays. */
    var separationPosee = false;
    var morceaux = [];

    /* En comparaison, la colonne de droite n'affiche plus la valeur du pays
       mais son écart avec la référence, et le liseré prend la couleur de cet
       écart. L'ordre des lignes, lui, ne change pas : classer par écart avec
       un pays donné revient exactement à classer par valeur. */
    var reference = comparaisonPossible() ? valeurReference() : null;

    affiches.forEach(function (element) {
      var sansChiffre = element.valeur === null;
      var ecart = reference === null ? null : calculerEcart(element.valeur, reference);

      if (sansChiffre && !separationPosee) {
        morceaux.push('<li class="separation">' + t("pas_de_donnee") + "</li>");
        separationPosee = true;
      }

      var classes = [];
      if (sansChiffre) classes.push("sans-chiffre");
      if (element.territoire) classes.push("territoire");
      if (element.iso === isoChoisi) classes.push("est-choisi");
      if (element.iso === isoReference) classes.push("est-reference");

      var couleur = couleurCSS("--pays-sans-donnee");
      if (ecart !== null) couleur = couleurDeLEcart(ecart);
      else if (!sansChiffre) couleur = couleurDeLaValeur(element.valeur);

      var affichage = "—";
      if (reference !== null) affichage = ecartLisible(ecart);
      else if (!sansChiffre) affichage = valeurLisible(element.valeur, donnees);

      morceaux.push(
        '<li data-iso="' + element.iso + '"' +
        (classes.length ? ' class="' + classes.join(" ") + '"' : "") +
        ' style="--couleur-pays:' + couleur + '">' +
        '<span class="rang">' + (element.rang || "") + "</span>" +
        '<span class="drapeau" aria-hidden="true">' +
        echapper(drapeauxParIso[element.iso] || "") + "</span>" +
        '<span class="nom">' + echapper(element.nom) + "</span>" +
        '<span class="valeur">' + echapper(affichage) + "</span>" +
        "</li>"
      );
    });
    liste.innerHTML = morceaux.join("");

    /* Sous le titre : « 193 pays classés · 4 sans donnée ». On ne montre la
       seconde moitié que s'il y a effectivement des pays sans chiffre. */
    var compteur = document.getElementById("compteur-pays");
    if (compteur) {
      /* On ne compte que les pays : les quatre territoires sont hors sujet. */
      var sansDonnee = 0;
      classementActuel.forEach(function (element) {
        if (element.valeur === null && !element.territoire) sansDonnee += 1;
      });
      compteur.textContent =
        nbClasses + " " + t("pays_classes") +
        (sansDonnee ? " · " + sansDonnee + " " + t("sans_donnee_compte") : "");
    }
  }

  function brancherClassement() {
    var liste = document.getElementById("classement");
    champRecherche = document.getElementById("recherche");

    if (champRecherche) {
      champRecherche.placeholder = t("recherche");
      champRecherche.addEventListener("input", dessinerClassement);
    }

    if (liste) {
      liste.addEventListener("click", function (evenement) {
        var ligne = evenement.target.closest("li[data-iso]");
        if (ligne) volerVers(ligne.getAttribute("data-iso"));
      });
      liste.addEventListener("mouseover", function (evenement) {
        var ligne = evenement.target.closest("li[data-iso]");
        if (ligne) surligner(ligne.getAttribute("data-iso"));
      });
      liste.addEventListener("mouseleave", function () { surligner(null); });
    }

    /* Bouton du tiroir sur téléphone */
    var bouton = document.getElementById("bouton-panneau");
    var panneau = document.getElementById("panneau");
    if (bouton && panneau) {
      bouton.addEventListener("click", function () {
        var ouvert = panneau.classList.toggle("est-ouvert");
        bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
        bouton.textContent = ouvert ? "✕" : "☰ " + t("voir_classement");
      });
      bouton.textContent = "☰ " + t("voir_classement");
    }
  }

  /* Le cadrage utilisé quand on clique sur un pays.

     La zone à afficher est calculée une fois pour toutes par le script Python
     et rangée dans la propriété "c" de chaque pays. Elle exclut volontairement
     les territoires lointains : cliquer sur le Danemark montre le Danemark et
     non le Groenland, cliquer sur la France montre la France et non Tahiti.
     Voir cadrage_du_pays() dans scripts/build_geojson.py.                   */
  function limitesDuPays(pays) {
    var limites = new maplibregl.LngLatBounds();
    var cadre = pays.properties.c;

    if (cadre) {
      limites.extend([cadre[0], cadre[1]]);
      limites.extend([cadre[2], cadre[3]]);
      return limites;
    }

    /* Secours, si le fond de carte est plus ancien que ce fichier. */
    (function parcourir(coordonnees) {
      if (typeof coordonnees[0] === "number") limites.extend(coordonnees);
      else coordonnees.forEach(parcourir);
    })(pays.geometry.coordinates);
    return limites;
  }

  /* Zoome sur un pays et ouvre son infobulle. */
  function volerVers(iso) {
    var pays = null;
    for (var i = 0; i < geo.features.length; i++) {
      if (geo.features[i].properties.iso === iso) { pays = geo.features[i]; break; }
    }
    if (!pays || !carte) return;

    var limites = limitesDuPays(pays);

    /* maxZoom assez élevé pour que les tout petits pays (Singapour, Malte,
       Nauru...) remplissent quand même l'écran quand on clique dessus. */
    carte.fitBounds(limites, { padding: 60, maxZoom: 6.5, duration: 700 });
    ouvrirInfobulle(iso, limites.getCenter());
  }

  /* --- 6. La légende ------------------------------------------------------ */

  function dessinerLegende() {
    var boite = document.getElementById("legende");
    if (!boite) return;

    /* La légende décrit ce que la carte montre VRAIMENT : si la référence n'a
       pas de chiffre cette année-là, la carte est revenue à ses valeurs, et la
       légende avec elle. La ligne « pays de référence » et la croix de sortie,
       elles, restent : le pays reste désigné. */
    var comparaison = comparaisonPossible();
    var couleurs = couleursActuelles();
    var titre, unite, etiquettes;

    if (comparaison) {
      /* La palette est remise à l'endroit sur les cartes « année record »,
         comme pour le fond de carte : en écart, le vert est toujours du côté
         du pays qui fait mieux. */
      if (reglages.classement_croissant) couleurs = inverser(couleurs);

      titre = t("ecart_titre");
      unite =
        reglages.ecart === "ratio" ? "%" :
        reglages.ecart === "points" ? t("unite_points") : t("unite_annees");

      /* Les seuils de l'écart s'écrivent avec leur signe : c'est lui qui dit
         de quel côté de la référence on se trouve. */
      etiquettes = reglagesEcart().tranches.map(function (seuil) {
        var texte = formater(Math.abs(seuil), seuil % 1 === 0 ? 0 : 1);
        return (seuil > 0 ? "+" : seuil < 0 ? "\u2212" : "") + texte;
      });
    } else {
      titre = donnees.titre[langue] || donnees.titre.fr;
      /* Ce qu'on écrit entre parenthèses sous le titre. Sur les cartes « année
         record » ce n'est pas l'unité de la valeur (une année n'en a pas) mais
         ce que mesurent les tranches : « années écoulées depuis le record ». */
      unite = donnees.legende_unite
        ? donnees.legende_unite[langue] || donnees.legende_unite.fr
        : donnees.unite[langue] || donnees.unite.fr;
      etiquettes = reglages.tranches.map(formaterCourt);
    }

    var cases = couleurs
      .map(function (couleur) {
        return '<span class="legende__case" style="background:' + couleur + '"></span>';
      })
      .join("");

    /* Les repères chiffrés sous la barre. On les affiche tous s'ils sont
       courts ; sinon un sur deux, pour éviter qu'ils se chevauchent.
       Pour la croissance, le repère « 0 » est essentiel : c'est lui qui
       sépare les pays qui reculent de ceux qui avancent.                   */
    var toutesCourtes = etiquettes.every(function (texte) {
      return texte.length <= 5;
    });

    var reperes = etiquettes
      .map(function (texte, index) {
        var montrer =
          toutesCourtes ||
          index % 2 === 0 ||
          index === etiquettes.length - 1;
        return "<span>" + (montrer ? texte : "") + "</span>";
      })
      .join("");

    boite.innerHTML =
      '<div class="legende__titre">' + echapper(titre) +
      " (" + echapper(unite) + ")</div>" +
      '<div class="legende__barre">' + cases + "</div>" +
      '<div class="legende__valeurs nombre"><span></span>' + reperes + "<span></span></div>" +
      ligneDeReference() +
      '<div class="legende__nd"><i></i>' + t("non_disponible") + "</div>" +
      boutonComparaison();
  }

  /* « 🇫🇷 France — pays de référence », sous la barre de la légende.
     Le nom reste au nominatif : aucune langue n'a à le décliner. */
  function ligneDeReference() {
    if (!enComparaison()) return "";
    return (
      '<div class="legende__reference">' +
      '<span class="drapeau" aria-hidden="true">' +
      echapper(drapeauxParIso[isoReference] || "") + "</span>" +
      echapper((nomsParIso[isoReference] || isoReference) + " — " + t("reference_pays")) +
      '<button type="button" class="legende__sortir" id="bouton-sortir-comparaison"' +
      ' title="' + echapper(t("comparer_stop")) + '"' +
      ' aria-label="' + echapper(t("comparer_stop")) + '">\u2715</button>' +
      "</div>" +
      /* Le pays est bien désigné, mais il n'a pas de chiffre cette année-là :
         la carte est revenue à ses valeurs. Sans ce mot, le visiteur aurait
         cliqué sur « Comparer » et rien ne se serait passé. */
      (comparaisonPossible()
        ? ""
        : '<div class="legende__note">' + echapper(t("pas_de_donnee")) + "</div>")
    );
  }

  /* --- 8. Le mode comparaison ---------------------------------------------

     Un seul bouton, sous la légende, qui prend le sens de la situation :
       - aucun pays choisi ............ grisé, avec l'invite « clique un pays » ;
       - un pays choisi ............... « Comparer à ce pays » ;
       - comparaison en cours, sur ce
         pays-là même ................. « Revenir aux valeurs » (on arrête) ;
       - comparaison en cours, mais un
         AUTRE pays est choisi ........ « Comparer à ce pays » (on change de
                                        référence, sans repasser par l'arrêt).

     Les cartes « année record » comparées à un pays donné gardent tout leur
     sens : l'écart se lit alors en années entre deux records.               */

  function boutonComparaison() {
    /* Les cartes sans mesure d'écart — il n'y en a pas aujourd'hui, mais une
       future carte pourrait s'en passer — n'affichent pas le bouton. */
    if (!reglages.ecart) return "";

    /* Le bouton ne fait qu'une chose : désigner le pays choisi comme
       référence. En sortir est le rôle de la croix, sur la ligne juste
       au-dessus. Il est donc inutile quand le pays choisi EST déjà la
       référence — dans ce cas on le grise, plutôt que de le voir proposer
       une comparaison du pays avec lui-même. */
    var utilisable = isoChoisi !== null && isoChoisi !== isoReference;
    return (
      '<button type="button" class="legende__comparer" id="bouton-comparer"' +
      (utilisable ? "" : " disabled") +
      (isoChoisi ? "" : ' title="' + echapper(t("comparer_invite")) + '"') +
      ">" + echapper(t("comparer")) + "</button>"
    );
  }

  /* Le clic est écouté sur la boîte de légende entière, et non sur le bouton :
     la légende est réécrite à chaque année, ce qui remplacerait le bouton et
     emporterait son écouteur avec lui. */
  function brancherComparaison() {
    var boite = document.getElementById("legende");
    if (!boite) return;
    boite.addEventListener("click", function (evenement) {
      var cible = evenement.target;
      if (!cible.closest) return;

      if (cible.closest("#bouton-sortir-comparaison")) {
        isoReference = null;
      } else {
        var bouton = cible.closest("#bouton-comparer");
        if (!bouton || bouton.disabled || !isoChoisi) return;
        isoReference = isoChoisi;
      }
      majComparaison();
    });
  }

  /* Tout ce qu'il faut redessiner quand on entre ou sort de la comparaison :
     l'échelle de couleurs de la carte, les valeurs envoyées à chaque pays,
     la légende, le classement et la bulle ouverte. */
  function majComparaison() {
    /* appliquerEtatsCarte pose aussi la nouvelle échelle de couleurs. */
    appliquerEtatsCarte();
    dessinerLegende();
    dessinerClassement();
    rafraichirInfobulle();
  }

  /* --- 7. Le curseur des années ------------------------------------------- */

  function brancherAnnees() {
    var curseur = document.getElementById("curseur-annee");
    if (!curseur) return;

    var annees = donnees.annees;
    curseur.min = annees[0];
    curseur.max = annees[annees.length - 1];
    curseur.step = 1;
    curseur.value = anneeAffichee;
    curseur.setAttribute("aria-label", t("annee"));

    var minimum = document.getElementById("annee-min");
    var maximum = document.getElementById("annee-max");
    if (minimum) minimum.textContent = annees[0];
    if (maximum) maximum.textContent = annees[annees.length - 1];

    /* On attend la fin du mouvement de doigt/souris avant de recalculer,
       pour que le glissement reste fluide.                                 */
    var enAttente = false;
    curseur.addEventListener("input", function () {
      var valeur = Number(curseur.value);
      if (enAttente) return;
      enAttente = true;
      requestAnimationFrame(function () {
        enAttente = false;
        if (valeur !== anneeAffichee) appliquerAnnee(Number(curseur.value));
      });
    });
  }

  function majEtiquetteAnnee() {
    var affichage = document.getElementById("annee-valeur");
    if (affichage) affichage.textContent = anneeAffichee;

    var etiquette = document.getElementById("annee-etiquette");
    if (!etiquette) return;

    var derniereReelle = donnees.derniere_annee_reelle;
    if (anneeAffichee > derniereReelle) {
      etiquette.innerHTML = '<span class="annees__projection">▲ ' + t("projection") + "</span>";
    } else if (anneeAffichee === derniereReelle) {
      etiquette.textContent = t("estimation");
    } else {
      etiquette.textContent = t("donnee_reelle");
    }
  }

  /* --- Réaction au changement de thème ------------------------------------ */

  window.addEventListener("statsmaps:theme", function () {
    if (!carte || !carte.isStyleLoaded()) return;
    carte.setPaintProperty("mer", "background-color", couleurCSS("--fond-carte"));
    carte.setPaintProperty("pays-fond", "fill-color", regleDeCouleur());
    carte.setPaintProperty("pays-contour", "line-color", regleContourCouleur());
    dessinerLegende();
    dessinerClassement();
    if (window.StatsMapsComparateur) window.StatsMapsComparateur.redessiner();
  });

  /* --- 9. Démarrage -------------------------------------------------------- */

  function masquerChargement() {
    var ecran = document.getElementById("chargement");
    if (!ecran) return;
    ecran.classList.add("est-fini");
    setTimeout(function () { ecran.hidden = true; }, 320);
  }

  function afficherErreur(erreur) {
    var ecran = document.getElementById("chargement");
    if (ecran) { ecran.hidden = false; ecran.textContent = t("erreur"); }
    console.error("[StatsMaps]", erreur);
  }

  function demarrer() {
    var ecran = document.getElementById("chargement");
    if (ecran) ecran.textContent = t("chargement");

    Promise.all([
      charger("data/pays.json"),
      charger("data/" + idCarte + ".json"),
      charger("data/meta.json"),
    ])
      .then(function (resultats) {
        geo = resultats[0];
        donnees = resultats[1];
        meta = resultats[2];

        geo.features.forEach(function (pays) {
          var iso = pays.properties.iso;
          var nom = pays.properties[langue] || pays.properties.fr || iso;
          nomsParIso[iso] = nom;
          drapeauxParIso[iso] = pays.properties.d || "";
          /* On garde aussi le nom dans l'autre langue : ainsi un visiteur
             francophone retrouve "Germany" et l'inverse.                  */
          nomsCherchablesParIso[iso] =
            sansAccents(nom) + " " +
            sansAccents(pays.properties.fr || "") + " " +
            sansAccents(pays.properties.en || "") + " " + iso.toLowerCase();
        });

        /* Année de départ : la dernière année réellement constatée. */
        var annees = donnees.annees;
        anneeAffichee = donnees.derniere_annee_reelle;
        if (annees.indexOf(anneeAffichee) === -1) anneeAffichee = annees[annees.length - 1];

        var titre = document.getElementById("titre-panneau");
        if (titre) titre.textContent = donnees.titre[langue] || donnees.titre.fr;

        var source = document.getElementById("source");
        if (source) {
          var nomSource = meta.source[langue] || meta.source.fr;

          /* Le FMI publie ce rapport deux fois par an, en avril et en octobre.
             On affiche l'ÉDITION d'où viennent les chiffres plutôt que la date
             à laquelle le site est allé les chercher : c'est l'édition qui date
             vraiment les projections. La date de récupération reste accessible
             en survolant la ligne. */
          var edition = "";
          if (meta.edition) {
            edition =
              " (" +
              t(meta.edition.mois === 4 ? "weo_avril" : "weo_octobre") +
              " " + meta.edition.annee + ")";
          }

          source.innerHTML =
            t("source") + t("deux_points") +
            '<a href="' + meta.source_url + '" target="_blank" rel="noopener">' +
            echapper(nomSource + edition) + "</a>";
          source.title =
            t("mis_a_jour") + " " +
            new Date(meta.mis_a_jour_le).toLocaleDateString(locale, {
              day: "numeric", month: "long", year: "numeric",
            });
        }

        brancherClassement();
        brancherAnnees();
        brancherComparaison();
        dessinerLegende();

        /* L'onglet « Comparer » du panneau. Il ne sait rien du site : on lui
           passe ici les données, les noms des pays et les quelques fonctions
           dont il a besoin. Il fabrique lui-même son HTML. */
        if (window.StatsMapsComparateur) {
          window.StatsMapsComparateur.demarrer({
            donnees: donnees,
            locale: locale,
            anneeAffichee: anneeAffichee,
            pays: { noms: nomsParIso, drapeaux: drapeauxParIso },
            outils: {
              t: t,
              echapper: echapper,
              couleurCSS: couleurCSS,
              couleursExtremes: couleursExtremes,
              calculerEcart: calculerEcart,
              ecartLisible: ecartLisible,
              valeurLisible: function (valeur) { return valeurLisible(valeur, donnees); },
            },
            paysChoisi: function () { return isoChoisi; },
            surAnneeChoisie: allerAAnnee,
          });
        }
        appliquerAnnee(anneeAffichee);

        /* Les données sont là : on retire l'écran de chargement tout de suite.
           On n'attend PAS que la carte soit dessinée — sinon un visiteur qui
           ouvre la page dans un onglet d'arrière-plan resterait bloqué sur
           « Chargement… », car le navigateur met les onglets cachés en pause. */
        masquerChargement();
        construireCarte();
      })
      .catch(afficherErreur);
  }

  if (!reglages) {
    console.error("[StatsMaps] indicateur inconnu :", idCarte);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarrer);
  } else {
    demarrer();
  }
})();
