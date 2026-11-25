/* ==========================================================================
   metro.js — le moteur de la carte des métros du monde.

   C'est la première carte du site qui ne colorie PAS les pays : elle pose des
   pastilles sur les villes, et dessine les lignes de métro dans leur vraie
   couleur officielle dès qu'on s'approche.

   Comme carte.js, elle lit deux informations sur la balise <body> :
       data-langue="fr"                → dans quelle langue
       data-base="../"                 → où trouver le dossier data/

   DEUX ÉCHELLES DE LECTURE, et c'est tout le principe :

     de loin ...... une PASTILLE par ville, d'autant plus grosse que le
                    réseau est long, POSÉE SUR l'aperçu du monde entier :
                    toutes les lignes de tous les métros, chacune dans sa
                    couleur, dessinées au quart de kilomètre près. Cet aperçu
                    est un seul fichier de quelques centaines de kilo-octets,
                    chargé au démarrage : les lignes sont donc là dès l'arrivée
                    sur la carte, sans rien cliquer ni attendre.
     de près ...... à partir du zoom 7, l'aperçu s'efface et les VRAIS tracés
                    prennent le relais, au mètre près, avec les tronçons en
                    construction en pointillés. Le tracé détaillé d'une ville
                    n'est téléchargé qu'au moment où l'on s'en approche.

   IL N'Y A AUCUN NOM ÉCRIT SUR LA CARTE, et c'est volontaire : afficher du
   texte dans MapLibre demande d'aller chercher des polices sur un serveur
   extérieur, ce que ce site ne fait nulle part. Les noms sont donc dans le
   panneau de gauche et dans la bulle qui s'ouvre au clic — c'est déjà la règle
   des sept autres cartes, où aucun nom de pays n'est écrit non plus.

   Déroulé du fichier :
     1. Réglages
     2. Petits outils
     3. Chargement des données
     4. Fabrication de la carte
     5. Les tracés, téléchargés à la demande
     6. Le panneau de gauche
     7. La fiche d'une ville
     8. La légende
     9. Démarrage
   ========================================================================== */

(function () {
  "use strict";

  /* --- 1. Réglages --------------------------------------------------------- */

  /* À partir de ce zoom, l'aperçu du monde s'efface et les tracés détaillés,
     téléchargés ville par ville, prennent sa place. En dessous, le détail au
     mètre près ne se verrait pas et coûterait plusieurs mégaoctets. */
  var ZOOM_LIGNES = 7;

  /* LE FOND DE CARTE : le même que sur la carte des entreprises cotées, des
     photos satellite (Esri, voir fond-satellite.js), demandées par Antonin le
     25 novembre 2026. Si Esri ne répond pas : la carte OpenStreetMap
     d'OpenFreeMap. Et si elle ne répond pas non plus, les pays du site en
     gris. */
  var STYLES = {
    clair: "https://tiles.openfreemap.org/styles/liberty",
    /* En mode sombre aussi, la carte CLAIRE : le fond « Dark » ne plaisait
       pas à Antonin (choix du 23 novembre 2026). Remettre ici
       ".../styles/dark" pour revenir à une carte de nuit. */
    sombre: "https://tiles.openfreemap.org/styles/liberty",
  };

  /* Ses frontières sont celles d'OpenStreetMap, pas celles du site : on les
     efface et on dessine les nôtres (data/frontieres.json), et on retire les
     noms des territoires qu'OpenStreetMap écrit comme des pays. Mêmes règles
     que bourse.js. */
  var TERRITOIRES_SANS_NOM = ["Western Sahara", "Somaliland", "Northern Cyprus",
    "Turkish Republic of Northern Cyprus", "Sahrawi Arab Democratic Republic"];

  /* Le zoom auquel on arrive quand on choisit une ville. */
  var ZOOM_VILLE = 10.4;

  /* Les stations : les points apparaissent à partir du premier zoom, leurs
     noms à partir du second (avant, ils se marcheraient dessus). */
  var ZOOM_STATIONS = 10.8;
  var ZOOM_NOMS_STATIONS = 12.3;

  /* La couleur des chantiers : le orange des panneaux de travaux. Elle sert
     aux pastilles des villes qui construisent leur premier métro, aux tracés
     en pointillés, et à la légende. */
  var COULEUR_CHANTIER = "#E8833A";

  /* Les cinq façons de classer les pays, dans l'ordre des onglets.
       clef ....... le champ du fichier data/metro/monde.json
       unite ...... ce qui s'écrit après le nombre
       texte ...... la clef du libellé dans i18n.js                        */
  var CRITERES = [
    { clef: "sys", texte: "metro_par_reseaux", unite: "" },
    { clef: "km", texte: "metro_par_km", unite: " km" },
    { clef: "st", texte: "metro_par_stations", unite: "" },
    { clef: "lg", texte: "metro_par_lignes", unite: "" },
    { clef: "kmc", texte: "metro_par_chantiers", unite: " km" },
  ];

  /* --- 2. Petits outils ---------------------------------------------------- */

  var corps = document.body;
  var langue = corps.getAttribute("data-langue") || "fr";
  var base = corps.getAttribute("data-base") || "./";
  var tousLesTextes = window.StatsMapsTextes || {};
  var textes = tousLesTextes[langue] || tousLesTextes.fr || {};

  function t(clef) {
    return textes[clef] !== undefined ? textes[clef] : clef;
  }

  /* Les chiffres suivent les usages de la langue : « 1 234 » en français,
     « 1,234 » en anglais, « 12,34,567 » en hindi. Le suffixe -u-nu-latn impose
     les chiffres 0-9 même en arabe, sur un site où l'on compare des nombres
     d'une langue à l'autre. */
  var LOCALE = langue + "-u-nu-latn";

  function formater(valeur, decimales) {
    if (valeur === null || valeur === undefined) return "—";
    var texte = new Intl.NumberFormat(LOCALE, {
      minimumFractionDigits: 0,
      maximumFractionDigits: decimales || 0,
    }).format(valeur);
    /* Même correction que sur les autres cartes : l'espace fine insécable des
       polices d'Apple est si étroite qu'on ne la voit pas. */
    return texte.replace(/ /g, " ");
  }

  /* Une ANNÉE n'est pas un nombre à séparer par milliers : « 1900 » et non
     « 1 900 ». C'est l'usage de toutes les langues du site, et l'espace
     faisait lire « mille neuf cents » là où il fallait lire « dix-neuf
     cents ». */
  function annee(valeur) {
    return valeur ? String(valeur) : "—";
  }

  function sansAccents(texte) {
    return String(texte || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  function echapper(texte) {
    return String(texte === null || texte === undefined ? "" : texte)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function couleurCSS(nom) {
    return getComputedStyle(document.documentElement).getPropertyValue(nom).trim();
  }

  /* Le nom d'une ville ou d'un réseau dans la langue de la page, avec repli
     sur l'anglais : Wikipédia n'a pas d'article dans les treize langues pour
     chacune des 234 villes. */
  function nomTraduit(noms) {
    if (!noms) return "";
    return noms[langue] || noms.en || noms.fr || "";
  }

  /* Noir ou blanc sur la couleur d'une ligne ? On calcule la clarté PERÇUE
     (l'œil est bien plus sensible au vert qu'au bleu) et non la moyenne des
     trois canaux : sur le jaune vif de la ligne 4 de Séoul, la moyenne dirait
     « clair » de justesse, la clarté perçue dit « très clair ». */
  function texteSurCouleur(hex) {
    var m = /^#([0-9a-f]{6})$/i.exec(hex || "");
    if (!m) return "#ffffff";
    var n = parseInt(m[1], 16);
    var r = (n >> 16) & 255, v = (n >> 8) & 255, b = n & 255;
    return 0.2126 * r + 0.7152 * v + 0.0722 * b > 150 ? "#16191d" : "#ffffff";
  }

  /* --- 3. Chargement des données ------------------------------------------- */

  function charger(chemin) {
    return fetch(base + chemin).then(function (r) {
      if (!r.ok) throw new Error(chemin + " : " + r.status);
      return r.json();
    });
  }

  var carte = null;          /* la carte MapLibre */
  var monde = null;          /* data/metro/monde.json */
  var villeParSlug = {};     /* "paris" -> sa fiche */
  var paysParIso = {};       /* "FRA" -> {nom, drapeau} */
  var apercu = null;         /* data/metro/apercu.json : le monde entier */
  var traces = {};           /* "paris" -> ses lignes, une fois téléchargées */
  var demandes = {};         /* les villes dont le tracé est en route */
  var critere = CRITERES[0];
  var paysDeplie = null;     /* le pays dont on voit la liste des villes */
  var villeChoisie = null;   /* la ville dont la fiche est ouverte */
  var ligneSurvolee = null;
  var bulle = null;

  /* --- 4. Fabrication de la carte ------------------------------------------ */

  /* Le thème du moment, lu sur la couleur de fond de la page (comme bourse.js). */
  function themeSombre() {
    var m = /#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})/i.exec(couleurCSS("--fond"));
    if (!m) return false;
    return parseInt(m[1], 16) + parseInt(m[2], 16) + parseInt(m[3], 16) < 300;
  }

  /* Le fond de carte, téléchargé une fois par thème puis gardé : le satellite
     (voir fond-satellite.js), ou à défaut OpenFreeMap. */
  var stylesTelecharges = {};
  function telechargerStyle(theme) {
    if (!stylesTelecharges[theme]) {
      var satellite = window.StatsMapsSatellite
        ? window.StatsMapsSatellite.telecharger(langue, true)
        : Promise.reject(new Error("pas de fond satellite"));
      stylesTelecharges[theme] = satellite
        .catch(function (e) {
          console.warn("[StatsMaps] satellite :", e.message);
          return fetch(STYLES[theme]).then(function (r) {
            if (!r.ok) throw new Error(STYLES[theme] + " : " + r.status);
            return r.json();
          });
        })
        .catch(function (e) {
          console.error("[StatsMaps] fond de carte :", e);
          return null;  /* repli : la carte sans fond détaillé */
        });
    }
    return stylesTelecharges[theme];
  }

  /* Le nom d'un lieu dans la langue de la page quand OpenStreetMap le connaît
     (« Allemagne » plutôt que « Deutschland »). */
  function nomDansLaLangue(expression) {
    if (Array.isArray(expression)) {
      if (expression[0] === "get" && expression[1] === "name:latin") {
        return ["coalesce", ["get", "name:" + langue], ["get", "name:latin"]];
      }
      return expression.map(nomDansLaLangue);
    }
    return expression;
  }

  /* Le fond seul : celui d'OpenFreeMap, retouché, ou à défaut une mer unie.
     Les couches du site (pays, lignes, villes) sont posées par-dessus dans
     ajouterCouches(). */
  var fondActuel = null;
  function fabriquerFond(fond) {
    fondActuel = fond;
    if (!fond) {
      return {
        version: 8,
        name: "StatsMaps",
        sources: {},
        layers: [{
          id: "mer",
          type: "background",
          paint: { "background-color": couleurCSS("--fond-carte") },
        }],
      };
    }
    var style = JSON.parse(JSON.stringify(fond));
    delete style.satellite;  /* notre marque, que MapLibre ne connaît pas */
    style.layers = style.layers.filter(function (couche) {
      return couche["source-layer"] !== "boundary";  /* leurs frontières */
    }).map(function (couche) {
      if (couche.layout && couche.layout["text-field"]) {
        couche.layout["text-field"] = nomDansLaLangue(couche.layout["text-field"]);
      }
      if (couche["source-layer"] === "place") {
        var sansTerritoires = ["!", ["in", ["coalesce", ["get", "name:en"], ""],
                                     ["literal", TERRITOIRES_SANS_NOM]]];
        couche.filter = couche.filter ? ["all", couche.filter, sansTerritoires]
                                      : sansTerritoires;
      }
      return couche;
    });
    return style;
  }

  var CADRAGE_MONDE = [[-179, -56], [179, 81]];

  function margesDuCadrage() {
    var large = window.innerWidth > 860;
    var placeDuPanneau = large ? 340 : 24;
    var droiteAGauche = document.documentElement.dir === "rtl";
    return {
      top: 24,
      right: droiteAGauche ? placeDuPanneau : 24,
      bottom: large ? 90 : 120,
      left: droiteAGauche ? 24 : placeDuPanneau,
    };
  }

  /* La taille d'une pastille : la RACINE de la longueur du réseau, et non la
     longueur elle-même. C'est la règle de toutes les cartes à pastilles :
     l'œil compare des SURFACES, et un réseau dix fois plus long doit occuper
     dix fois plus de surface — donc un rayon trois fois plus grand seulement.
     Sans cette racine, Shanghai ferait cent fois le diamètre de Lausanne et
     couvrirait la moitié de la Chine. */
  function rayonDesPastilles() {
    /* MapLibre n'accepte « zoom » que comme entrée DIRECTE d'un interpolate :
       le mettre sous une multiplication fait rejeter la couche entière, et
       plus aucune pastille ne s'affiche. On écrit donc l'interpolation au
       premier étage, et c'est le grossissement qui se répète à chaque palier. */
    var rayon = ["+", 2.4,
      ["*", 0.44, ["sqrt", ["max", ["coalesce", ["get", "km"], 8], 4]]]];
    return ["interpolate", ["linear"], ["zoom"],
      0.5, ["*", 0.62, rayon],
      3, ["*", 0.85, rayon],
      6, ["*", 1.25, rayon],
      9, ["*", 1.6, rayon]];
  }

  /* Les lignes s'épaississent avec le zoom, mais moins vite que la carte : à
     l'échelle d'un quartier, un trait de 5 px suffit à se suivre du doigt. */
  function epaisseurDesLignes(facteur) {
    var f = facteur || 1;
    return ["interpolate", ["exponential", 1.5], ["zoom"],
      ZOOM_LIGNES, 0.9 * f, 10, 2.4 * f, 13, 4.2 * f, 16, 7 * f];
  }

  /* L'aperçu du monde est dessiné très fin : à l'échelle du monde, un réseau
     entier tient dans quelques pixels, et un trait épais ferait une tache. On
     l'épaissit à mesure qu'on descend, jusqu'à rejoindre l'épaisseur des vrais
     tracés au moment où ils prennent le relais. */
  function epaisseurDeLApercu() {
    return ["interpolate", ["exponential", 1.4], ["zoom"],
      0.5, 0.7, 3, 1, 5, 1.5, ZOOM_LIGNES + 0.4, 2.6];
  }

  /* L'aperçu s'efface exactement là où les tracés détaillés apparaissent :
     l'un monte pendant que l'autre descend, et l'œil ne voit aucune coupure.
     Il reste un peu transparent de loin, pour que les pastilles des villes
     restent lisibles par-dessus. */
  function disparitionDeLApercu() {
    return ["interpolate", ["linear"], ["zoom"],
      0.5, 0.75, 4, 0.9, ZOOM_LIGNES - 0.6, 0.9, ZOOM_LIGNES + 0.4, 0];
  }

  /* Les lignes n'apparaissent pas d'un coup au zoom 7 : elles se dévoilent
     entre 6,4 et 7,4, sinon la carte « clignote » quand on zoome doucement. */
  function apparitionDesLignes() {
    return ["interpolate", ["linear"], ["zoom"],
      ZOOM_LIGNES - 0.6, 0, ZOOM_LIGNES + 0.4, 1];
  }

  var geoPaysGarde = null, geoFrontieresGarde = null;

  function construireCarte(geoPays, fond, geoFrontieres) {
    geoPaysGarde = geoPays;
    geoFrontieresGarde = geoFrontieres;
    carte = new maplibregl.Map({
      container: "carte",
      style: fabriquerFond(fond),
      bounds: CADRAGE_MONDE,
      fitBoundsOptions: { padding: margesDuCadrage() },
      minZoom: 0.5,
      maxZoom: 16,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    });

    carte.touchZoomRotate.disableRotation();
    /* Cacher la carte le temps qu'elle soit entièrement dessinée (voir
       « en-attente » dans style.css), puis la montrer. Au plus tard après
       4 secondes, au cas où une tuile se ferait attendre. */
    var boite = document.getElementById("carte");
    boite.classList.add("en-attente");
    var montrer = function () { boite.classList.remove("en-attente"); };
    carte.once("idle", montrer);
    setTimeout(montrer, 4000);

    carte.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    carte.addControl(new maplibregl.AttributionControl({
      compact: true,
      /* Avec le fond d'OpenFreeMap, MapLibre ajoute lui-même sa mention
         (OpenFreeMap, OpenMapTiles, OpenStreetMap). On garde quand même
         OpenStreetMap ici : les tracés des lignes en viennent aussi. */
      customAttribution:
        '<a href="https://www.naturalearthdata.com/">Natural Earth</a> · ' +
        '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · ' +
        '<a href="https://www.wikidata.org/">Wikidata</a>',
    }), "bottom-right");

    carte.on("error", function (e) {
      console.error("[StatsMaps] carte :", (e && e.error && e.error.message) || e);
    });

    carte.on("load", function () {
      if (fond && fond.satellite) window.StatsMapsSatellite.ajouterMention();
      ajouterCouches();
      brancherInteractions();
      chargerCeQuOnVoit();
      dessinerLegende();
    });

    carte.on("moveend", chargerCeQuOnVoit);
  }

  /* Les couches du site, posées sur le fond. Appelée au démarrage, puis de
     nouveau à chaque changement de thème : changer de fond (« Liberty » ou
     « Dark ») efface tout ce qui était posé dessus. On remet alors les
     données déjà là (aperçu, tracés téléchargés, ville choisie). */
  function ajouterCouches() {
    var geoPays = geoPaysGarde;
    var satellite = !!(fondActuel && fondActuel.satellite);
    carte.addSource("pays", { type: "geojson", data: geoPays, promoteId: "iso" });
    carte.addSource("frontieres", { type: "geojson", data: geoFrontieresGarde || geoPays });
    carte.addSource("apercu", { type: "geojson", data: videGeoJSON() });
    carte.addSource("traces", { type: "geojson", data: videGeoJSON() });
    carte.addSource("chantiers", { type: "geojson", data: videGeoJSON() });
    carte.addSource("stations", { type: "geojson", data: videGeoJSON() });
    carte.addSource("villes", { type: "geojson", data: villesGeoJSON(), promoteId: "s" });

    if (fondActuel) {
      /* Sur une photo ou sur OpenStreetMap : seulement les frontières du site,
         un trait fin et discret, comme sur la carte des entreprises. Blanches
         sur les photos, grises sur OpenStreetMap. */
      carte.addLayer({
        id: "pays-contour", type: "line", source: "frontieres",
        paint: {
          "line-color": satellite ? "rgba(255, 255, 255, 0.75)" : "#7d8699",
          "line-width": ["interpolate", ["linear"], ["zoom"], 1, 0.6, 6, 1.3, 12, 2],
          "line-opacity": ["interpolate", ["linear"], ["zoom"], 1, 0.9, 12, 0.75],
        },
      });
    } else {
      /* Sans fond (OpenFreeMap injoignable) : les pays, tous de la même
         couleur, qui situent — c'est une toile de fond, pas la carte. */
      carte.addLayer({
        id: "pays-fond", type: "fill", source: "pays",
        paint: { "fill-color": couleurCSS("--pays-sans-donnee"), "fill-opacity": 0.55 },
      });
      carte.addLayer({
        id: "pays-contour", type: "line", source: "pays",
        paint: { "line-color": couleurCSS("--contour-pays"), "line-width": 0.4 },
      });
    }

    /* Sur une photo, les noms des lieux restent AU-DESSUS des lignes (elles
       sont glissées sous la première couche de noms), sinon elles les barrent. */
    var sousLesNoms;
    if (satellite) {
      var noms = fondActuel.layers.filter(function (c) { return c.type === "symbol"; });
      if (noms.length) sousLesNoms = noms[0].id;
    }

    /* L'aperçu du monde entier : toutes les lignes de tous les métros, dans
       leur couleur, visibles dès la vue du monde. Il passe sous les tracés
       détaillés, auxquels il cède la place en fondu au zoom 7. */
    carte.addLayer({
      id: "apercu", type: "line", source: "apercu",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": ["get", "couleur"],
        "line-width": epaisseurDeLApercu(),
        "line-opacity": disparitionDeLApercu(),
      },
    }, sousLesNoms);

    /* Les chantiers passent SOUS les lignes en service : là où une extension
       prolonge une ligne existante, c'est la ligne ouverte qu'on veut voir
       en entier. */
    carte.addLayer({
      id: "chantiers", type: "line", source: "chantiers",
      layout: { "line-cap": "butt", "line-join": "round" },
      paint: {
        "line-color": ["get", "couleur"],
        "line-width": epaisseurDesLignes(),
        "line-opacity": apparitionDesLignes(),
        "line-dasharray": [1.5, 1.3],
      },
    }, sousLesNoms);

    /* Sur une photo, un liseré blanc sous chaque ligne : sans lui, les lignes
       foncées (bleu, vert, marron) se perdaient dans les toits et les parcs. */
    if (satellite) {
      carte.addLayer({
        id: "lignes-lisere", type: "line", source: "traces",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": "#ffffff",
          "line-width": epaisseurDesLignes(1.7),
          "line-opacity": apparitionDesLignes(),
        },
      }, "chantiers");
    }

    carte.addLayer({
      id: "lignes", type: "line", source: "traces",
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": ["get", "couleur"],
        "line-width": epaisseurDesLignes(),
        "line-opacity": apparitionDesLignes(),
      },
    }, sousLesNoms);

    /* La ligne survolée dans le panneau : la même, en plus épais. */
    carte.addLayer({
      id: "ligne-surbrillance", type: "line", source: "traces",
      filter: ["==", ["get", "id"], ""],
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": ["get", "couleur"],
        "line-width": epaisseurDesLignes(2.4),
        "line-opacity": 0.45,
      },
    }, sousLesNoms);

    carte.addLayer({
      id: "villes", type: "circle", source: "villes",
      paint: {
        "circle-radius": rayonDesPastilles(),
        "circle-color": ["case",
          ["==", ["get", "enService"], 0], COULEUR_CHANTIER, couleurCSS("--accent")],
        /* Les pastilles s'effacent progressivement : de loin elles portent
           le classement (leur taille suit la longueur du réseau), mais dès
           qu'on descend elles cacheraient les lignes qui sont dessous, et au
           zoom 11 elles cacheraient tout le centre-ville. */
        "circle-opacity": ["interpolate", ["linear"], ["zoom"],
          0.5, 0.9, 3, 0.8, 5, 0.5, ZOOM_LIGNES, 0.35, ZOOM_LIGNES + 3, 0.12],
        "circle-stroke-width": ["case",
          ["boolean", ["feature-state", "choisie"], false], 2.6,
          [">", ["coalesce", ["get", "kmc"], 0], 0], 1.8, 1],
        /* La ville choisie : contour blanc sur les photos, sombre sur le fond
           OpenStreetMap, toujours clair. Sans fond, les couleurs du thème. */
        "circle-stroke-color": ["case",
          ["boolean", ["feature-state", "choisie"], false],
          satellite ? "#ffffff" : fondActuel ? "#16191d" : couleurCSS("--texte"),
          [">", ["coalesce", ["get", "kmc"], 0], 0], COULEUR_CHANTIER,
          fondActuel ? "#ffffff" : couleurCSS("--panneau")],
        "circle-stroke-opacity": ["interpolate", ["linear"], ["zoom"],
          ZOOM_LIGNES, 1, ZOOM_LIGNES + 3, 0.25],
      },
    });

    ajouterStations(satellite);

    if (window.StatsMapsFrontieres && fondActuel) {
      window.StatsMapsFrontieres.poser(carte, "apercu");
    }
    if (apercu) carte.getSource("apercu").setData(apercu);
    redessinerLesTraces();
    if (villeChoisie) {
      carte.setFeatureState({ source: "villes", id: villeChoisie }, { choisie: true });
    }
  }

  /* Les stations, par-dessus les lignes : un point blanc cerclé de noir, comme
     sur un plan de métro, plus gros quand plusieurs lignes s'y croisent. */
  function ajouterStations(satellite) {
    var correspondance = [">", ["get", "nb"], 1];
    carte.addLayer({
      id: "stations", type: "circle", source: "stations", minzoom: ZOOM_STATIONS,
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"],
          ZOOM_STATIONS, ["case", correspondance, 2.2, 1.5],
          13, ["case", correspondance, 4.6, 3.2],
          16, ["case", correspondance, 8, 6]],
        "circle-color": "#ffffff",
        "circle-stroke-color": "#16191d",
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"],
          ZOOM_STATIONS, 0.6, 13, 1.4, 16, 2.2],
        "circle-opacity": ["interpolate", ["linear"], ["zoom"],
          ZOOM_STATIONS, 0, ZOOM_STATIONS + 0.5, 1],
        "circle-stroke-opacity": ["interpolate", ["linear"], ["zoom"],
          ZOOM_STATIONS, 0, ZOOM_STATIONS + 0.5, 1],
      },
    });
    if (!fondActuel) return;  /* sans fond, pas de police : pas de noms */
    carte.addLayer({
      id: "stations-noms", type: "symbol", source: "stations",
      minzoom: ZOOM_NOMS_STATIONS,
      filter: ["!=", ["get", "nom"], ""],
      layout: {
        "text-field": ["get", "nom"],
        /* Chaque fond fournit sa propre police. */
        "text-font": satellite ? ["Arial Bold"] : ["Noto Sans Bold"],
        "text-size": ["interpolate", ["linear"], ["zoom"], ZOOM_NOMS_STATIONS, 10.5, 16, 14],
        "text-variable-anchor": ["left", "right", "top", "bottom"],
        "text-radial-offset": 0.75,
        "text-max-width": 9,
        "text-justify": "auto",
        /* Les correspondances d'abord, quand la place manque. */
        "symbol-sort-key": ["-", 0, ["get", "nb"]],
      },
      paint: {
        "text-color": satellite ? "#ffffff" : "#16191d",
        "text-halo-color": satellite ? "rgba(0, 0, 0, 0.85)" : "#ffffff",
        "text-halo-width": 1.5,
      },
    });
  }

  function videGeoJSON() {
    return { type: "FeatureCollection", features: [] };
  }

  function villesGeoJSON() {
    return {
      type: "FeatureCollection",
      features: monde.villes.map(function (v) {
        return {
          type: "Feature",
          properties: {
            s: v.s, km: v.km, kmc: v.kmc, enService: v.enService, iso: v.iso,
          },
          geometry: { type: "Point", coordinates: [v.lon, v.lat] },
        };
      }),
    };
  }

  /* L'aperçu est écrit au plus court — [couleur, [[lon,lat], ...]] — parce
     qu'un GeoJSON complet, avec ses « type », « properties » et « geometry »
     répétés cinq mille fois, pèserait le double pour le même dessin. On le
     déplie ici, une fois, à l'arrivée. */
  function apercuGeoJSON(donnees) {
    return {
      type: "FeatureCollection",
      features: (donnees.l || []).map(function (trace) {
        return {
          type: "Feature",
          properties: { couleur: trace[0], ville: trace[2] },
          geometry: { type: "LineString", coordinates: trace[1] },
        };
      }),
    };
  }

  /* --- 5. Les tracés, téléchargés à la demande ----------------------------- */

  /* On ne télécharge le tracé d'une ville que lorsqu'elle entre à l'écran, et
     seulement une fois qu'on est assez près pour le voir. Le fichier de
     Shanghai pèse à lui seul plus que la carte du monde entier : les charger
     tous d'avance ferait attendre une minute pour rien. */
  function chargerCeQuOnVoit() {
    if (!carte || carte.getZoom() < ZOOM_LIGNES - 1) return;
    var vue = carte.getBounds();
    var aFaire = monde.villes.filter(function (v) {
      return !traces[v.s] && !demandes[v.s] &&
        v.lon > vue.getWest() - 0.6 && v.lon < vue.getEast() + 0.6 &&
        v.lat > vue.getSouth() - 0.5 && v.lat < vue.getNorth() + 0.5;
    });
    aFaire.forEach(function (v) { chargerVille(v.s); });
  }

  function chargerVille(slug) {
    if (traces[slug]) return Promise.resolve(traces[slug]);
    if (demandes[slug]) return demandes[slug];
    demandes[slug] = charger("data/metro/villes/" + slug + ".json")
      .then(function (d) {
        traces[slug] = d;
        redessinerLesTraces();
        if (villeChoisie === slug) dessinerFicheVille(villeParSlug[slug]);
        return d;
      })
      .catch(function (e) {
        console.error("[StatsMaps] métro :", e);
        traces[slug] = { lignes: [], chantiers: [] };
        return traces[slug];
      });
    return demandes[slug];
  }

  /* Toutes les villes déjà téléchargées, réunies en deux couches. On refait
     l'ensemble à chaque ajout : c'est un tableau de quelques milliers de
     tracés, le navigateur le refabrique en quelques millisecondes. */
  function redessinerLesTraces() {
    var lignes = [], chantiers = [], stations = [];
    Object.keys(traces).forEach(function (slug) {
      var d = traces[slug];
      (d.lignes || []).forEach(function (l, i) {
        l.t.forEach(function (trace) {
          lignes.push({
            type: "Feature",
            properties: { couleur: l.couleur, id: slug + "/" + i, ville: slug },
            geometry: { type: "LineString", coordinates: trace },
          });
        });
      });
      (d.stations || []).forEach(function (s, i) {
        stations.push({
          type: "Feature",
          properties: { nom: s[2], nb: s[3].length, ville: slug, i: i },
          geometry: { type: "Point", coordinates: [s[0], s[1]] },
        });
      });
      (d.chantiers || []).forEach(function (c) {
        chantiers.push({
          type: "Feature",
          properties: { couleur: c.couleur || COULEUR_CHANTIER, ville: slug },
          geometry: { type: "LineString", coordinates: c.t },
        });
      });
    });
    if (carte.getSource("traces")) {
      carte.getSource("traces").setData({ type: "FeatureCollection", features: lignes });
      carte.getSource("chantiers").setData({ type: "FeatureCollection", features: chantiers });
      carte.getSource("stations").setData({ type: "FeatureCollection", features: stations });
    }
  }

  /* --- Interactions sur la carte ------------------------------------------- */

  function brancherInteractions() {
    carte.on("mouseenter", "villes", function () {
      carte.getCanvas().style.cursor = "pointer";
    });
    carte.on("mouseleave", "villes", function () {
      carte.getCanvas().style.cursor = "";
    });
    carte.on("click", "villes", function (e) {
      var f = e.features && e.features[0];
      if (f) ouvrirVille(f.properties.s, true);
    });
    /* Une station : son nom et ses lignes, dans une petite bulle. */
    carte.on("mouseenter", "stations", function () {
      carte.getCanvas().style.cursor = "pointer";
    });
    carte.on("mouseleave", "stations", function () {
      carte.getCanvas().style.cursor = "";
    });
    carte.on("click", "stations", function (e) {
      var f = e.features && e.features[0];
      if (f) ouvrirStation(f.properties.ville, f.properties.i);
    });
    /* Un clic sur une ligne ouvre la ville à laquelle elle appartient : quand
       on est zoomé, la pastille de la ville est souvent hors de l'écran. */
    carte.on("click", "lignes", function (e) {
      var f = e.features && e.features[0];
      if (f && f.properties.ville !== villeChoisie) ouvrirVille(f.properties.ville, false);
    });
    /* De loin, c'est l'aperçu qu'on a sous le doigt et non le tracé détaillé,
       qui n'est pas encore téléchargé : il ouvre la même fiche, et cadre sur
       la ville puisqu'on en est encore trop loin pour la voir. */
    carte.on("click", "apercu", function (e) {
      var f = e.features && e.features[0];
      if (f && f.properties.ville && f.properties.ville !== villeChoisie) {
        ouvrirVille(f.properties.ville, true);
      }
    });
    carte.on("click", function (e) {
      /* MapLibre continue de « voir » une couche rendue totalement
         transparente : sans ce tri, un clic dans le vide au-dessus d'un tracé
         d'aperçu invisible ne refermerait jamais la fiche. */
      var couches = ["villes", "lignes", "chantiers", "stations"];
      if (carte.getZoom() < ZOOM_LIGNES + 0.4) couches.push("apercu");
      var dessus = carte.queryRenderedFeatures(e.point, { layers: couches });
      if (!dessus.length) fermerVille();
    });
  }

  function ouvrirStation(slug, i) {
    var d = traces[slug];
    var s = d && d.stations && d.stations[i];
    if (!s) return;
    if (bulle) bulle.remove();
    var lignes = s[3].map(function (n) { return d.lignes[n]; }).filter(Boolean);
    bulle = new maplibregl.Popup({ closeButton: false, offset: 10, maxWidth: "260px" })
      .setLngLat([s[0], s[1]])
      .setHTML((s[2] ? '<div class="popup__nom">' + echapper(s[2]) + "</div>" : "") +
        '<div class="station__lignes">' + lignes.map(function (l) {
          return '<span class="ligne-metro__pastille" style="background:' +
            echapper(l.couleur) + ";color:" + texteSurCouleur(l.couleur) + '">' +
            echapper(l.ref || l.nom || "") + "</span>";
        }).join("") + "</div>")
      .addTo(carte);
  }

  /* --- 6. Le panneau de gauche --------------------------------------------- */

  var panneau = {
    titre: document.getElementById("titre-panneau"),
    soustitre: document.getElementById("compteur-pays"),
    recherche: document.getElementById("recherche"),
    liste: document.getElementById("classement"),
    onglets: document.getElementById("criteres"),
    source: document.getElementById("source"),
    retour: document.getElementById("retour"),
  };

  function fabriquerOnglets() {
    panneau.onglets.innerHTML = "";
    CRITERES.forEach(function (c) {
      var b = document.createElement("button");
      b.type = "button";
      b.className = "onglet";
      b.textContent = t(c.texte);
      b.setAttribute("aria-selected", c === critere ? "true" : "false");
      b.addEventListener("click", function () {
        critere = c;
        fabriquerOnglets();
        dessinerClassement();
      });
      panneau.onglets.appendChild(b);
    });
  }

  /* Le classement des PAYS. Cliquer sur un pays déplie ses villes : c'est la
     même liste, à un étage de plus. On ne fait pas deux listes, parce que la
     question « quels pays ont le plus de métros ? » et la question « lesquels,
     en Chine ? » se posent l'une après l'autre. */
  function dessinerClassement() {
    var recherche = sansAccents(panneau.recherche.value.trim());
    var liste = panneau.liste;
    liste.innerHTML = "";

    var pays = monde.pays.slice().filter(function (p) {
      return (p[critere.clef] || 0) > 0;
    });
    pays.sort(function (a, b) {
      return (b[critere.clef] || 0) - (a[critere.clef] || 0);
    });

    if (recherche) {
      pays = pays.filter(function (p) {
        if (sansAccents(nomDuPays(p.iso)).indexOf(recherche) >= 0) return true;
        return p.villes.some(function (s) {
          return sansAccents(nomTraduit((villeParSlug[s] || {}).n)).indexOf(recherche) >= 0;
        });
      });
    }

    if (!pays.length) {
      liste.innerHTML = '<li class="vide">' + echapper(t("metro_rien_trouve")) + "</li>";
      return;
    }

    pays.forEach(function (p, i) {
      liste.appendChild(lignePays(p, i + 1));
      if (paysDeplie === p.iso || (recherche && pays.length <= 3)) {
        villesDuPays(p).forEach(function (v) {
          liste.appendChild(ligneVille(v));
        });
      }
    });

    panneau.soustitre.textContent =
      formater(monde.pays.filter(function (p) { return p.sys > 0; }).length) + " " +
      t("metro_pays_avec_metro") + " · " +
      formater(monde.villes.filter(function (v) { return v.enService; }).length) + " " +
      t("metro_villes");
  }

  function villesDuPays(p) {
    return monde.villes.filter(function (v) {
      return v.iso === p.iso;
    }).sort(function (a, b) {
      return (b[critere.clef === "sys" ? "km" : critere.clef] || 0) -
             (a[critere.clef === "sys" ? "km" : critere.clef] || 0);
    });
  }

  function nomDuPays(iso) {
    return (paysParIso[iso] || {})[langue] || (paysParIso[iso] || {}).en || iso;
  }

  /* Le drapeau dessiné (voir assets/js/drapeaux.js), et non plus l'émoji. */
  function drapeauDuPays(iso) {
    return window.StatsMapsDrapeau((paysParIso[iso] || {}).d);
  }

  function valeurDuCritere(objet) {
    var v = objet[critere.clef];
    if (v === null || v === undefined || v === 0) return "—";
    return formater(v, critere.clef === "km" || critere.clef === "kmc" ? 0 : 0) +
           critere.unite;
  }

  function lignePays(p, rang) {
    var li = document.createElement("li");
    li.className = "classement__pays" + (paysDeplie === p.iso ? " est-actif" : "");
    li.innerHTML =
      '<span class="rang">' + formater(rang) + "</span>" +
      '<span class="drapeau" aria-hidden="true">' + drapeauDuPays(p.iso) + "</span>" +
      '<span class="nom">' + echapper(nomDuPays(p.iso)) + "</span>" +
      '<span class="valeur">' + echapper(valeurDuCritere(p)) + "</span>";
    li.addEventListener("click", function () {
      paysDeplie = paysDeplie === p.iso ? null : p.iso;
      dessinerClassement();
      if (paysDeplie) volerVersPays(p.iso);
    });
    return li;
  }

  /* Le chiffre écrit en face d'une ville. Le critère « Réseaux » n'a pas de
     sens ici — une ville en a presque toujours un seul, et une colonne de
     « 1 » n'apprend rien : on montre alors sa longueur de lignes. */
  function valeurDeLaVille(v) {
    if (critere.clef === "sys") {
      return v.km ? formater(v.km, 0) + " km" : "—";
    }
    return valeurDuCritere(v);
  }

  function ligneVille(v) {
    var li = document.createElement("li");
    li.className = "classement__ville" + (villeChoisie === v.s ? " est-choisi" : "");
    var valeur = v.enService ? valeurDeLaVille(v)
                             : t("metro_en_construction");
    li.innerHTML =
      '<span class="rang"></span>' +
      '<span class="nom">' + echapper(nomTraduit(v.n)) + "</span>" +
      '<span class="valeur">' + echapper(valeur) + "</span>";
    li.addEventListener("click", function () { ouvrirVille(v.s, true); });
    return li;
  }

  /* --- 7. La fiche d'une ville --------------------------------------------- */

  function ouvrirVille(slug, voler) {
    var v = villeParSlug[slug];
    if (!v) return;
    if (villeChoisie && carte.getSource("villes")) {
      carte.setFeatureState({ source: "villes", id: villeChoisie }, { choisie: false });
    }
    villeChoisie = slug;
    paysDeplie = v.iso;
    if (carte.getSource("villes")) {
      carte.setFeatureState({ source: "villes", id: slug }, { choisie: true });
    }
    if (voler) {
      carte.flyTo({ center: [v.lon, v.lat], zoom: Math.max(carte.getZoom(), ZOOM_VILLE),
                    padding: margesDuCadrage(), speed: 1.1 });
    }
    chargerVille(slug);
    dessinerFicheVille(v);
  }

  function fermerVille() {
    if (villeChoisie && carte.getSource("villes")) {
      carte.setFeatureState({ source: "villes", id: villeChoisie }, { choisie: false });
    }
    villeChoisie = null;
    ligneSurvolee = null;
    surbrillance(null);
    panneau.retour.hidden = true;
    panneau.titre.textContent = t("metro_titre");
    panneau.recherche.hidden = false;
    panneau.onglets.hidden = false;
    dessinerClassement();
  }

  /* La fiche remplace le classement dans le panneau : ses chiffres, ses
     réseaux, et la liste de ses lignes avec leur pastille de couleur. C'est
     la seule page du site où l'on voit la couleur officielle à côté du nom. */
  function dessinerFicheVille(v) {
    panneau.titre.textContent = nomTraduit(v.n);
    panneau.soustitre.innerHTML =
      '<span class="drapeau" aria-hidden="true">' + drapeauDuPays(v.iso) + "</span> " +
      echapper(nomDuPays(v.iso));
    panneau.recherche.hidden = true;
    panneau.onglets.hidden = true;
    panneau.retour.hidden = false;

    var d = traces[v.s];
    var h = ['<li class="fiche">'];

    h.push('<div class="fiche__chiffres">');
    h.push(chiffre(v.km, t("metro_km"), " km"));
    h.push(chiffre(v.st, t("metro_stations"), ""));
    h.push(chiffre(v.lg, t("metro_lignes"), ""));
    if (v.kmc) h.push(chiffre(v.kmc, t("metro_chantier"), " km", true));
    h.push("</div>");

    if (v.depuis) {
      h.push('<p class="fiche__phrase">' +
        echapper(t("metro_depuis").replace("{annee}", annee(v.depuis))) + "</p>");
    }
    if (v.vy) {
      h.push('<p class="fiche__phrase">' +
        echapper(t("metro_voyageurs").replace("{n}", formater(v.vy))) + "</p>");
    }

    (v.sys || []).forEach(function (s) {
      h.push('<p class="fiche__reseau">' + echapper(nomTraduit(s.n)) +
        (s.depuis ? ' <span class="fiche__annee">' + annee(s.depuis) + "</span>" : "") +
        "</p>");
    });
    (v.futur || []).forEach(function (s) {
      h.push('<p class="fiche__reseau fiche__reseau--chantier">' +
        echapper(nomTraduit(s.n)) +
        (s.prevu ? ' <span class="fiche__annee">' +
          echapper(t("metro_prevu").replace("{annee}", annee(s.prevu))) + "</span>" : "") +
        "</p>");
    });
    h.push("</li>");

    if (!d) {
      h.push('<li class="vide">' + echapper(t("chargement")) + "</li>");
    } else if (d.lignes.length) {
      h.push('<li class="separation">' + echapper(t("metro_ses_lignes")) + "</li>");
      d.lignes.forEach(function (l, i) {
        h.push(ligneDeMetro(l, v.s + "/" + i));
      });
    }
    if (d && d.chantiers && d.chantiers.length) {
      h.push('<li class="separation">' + echapper(t("metro_ses_chantiers")) + "</li>");
    }

    panneau.liste.innerHTML = h.join("");
    brancherSurvolDesLignes();
  }

  function chiffre(valeur, mot, unite, chantier) {
    if (!valeur) return "";
    return '<span class="fiche__chiffre' + (chantier ? " est-chantier" : "") + '">' +
      '<b class="nombre">' + echapper(formater(valeur, 0) + unite) + "</b>" +
      "<i>" + echapper(mot) + "</i></span>";
  }

  function ligneDeMetro(l, id) {
    var etiquette = l.ref || l.nom || "";
    var titre = l.nom || l.ref || "";
    return '<li class="ligne-metro" data-ligne="' + echapper(id) + '">' +
      '<span class="ligne-metro__pastille" style="background:' + echapper(l.couleur) +
      ";color:" + texteSurCouleur(l.couleur) + '">' + echapper(etiquette) + "</span>" +
      '<span class="nom">' + echapper(titre) + "</span>" +
      '<span class="valeur">' + echapper(formater(l.km, 0) + " km") + "</span></li>";
  }

  function brancherSurvolDesLignes() {
    var elements = panneau.liste.querySelectorAll("[data-ligne]");
    Array.prototype.forEach.call(elements, function (el) {
      var id = el.getAttribute("data-ligne");
      el.addEventListener("mouseenter", function () { surbrillance(id); });
      el.addEventListener("mouseleave", function () { surbrillance(null); });
      el.addEventListener("click", function () { cadrerSurLigne(id); });
    });
  }

  function surbrillance(id) {
    ligneSurvolee = id;
    if (carte.getLayer("ligne-surbrillance")) {
      carte.setFilter("ligne-surbrillance", ["==", ["get", "id"], id || ""]);
    }
  }

  function cadrerSurLigne(id) {
    var morceaux = id.split("/");
    var d = traces[morceaux[0]];
    if (!d) return;
    var l = d.lignes[Number(morceaux[1])];
    if (!l) return;
    var b = new maplibregl.LngLatBounds();
    l.t.forEach(function (trace) {
      trace.forEach(function (p) { b.extend(p); });
    });
    carte.fitBounds(b, { padding: margesDuCadrage(), maxZoom: 14 });
  }

  function volerVersPays(iso) {
    var cadre = (paysParIso[iso] || {}).c;
    if (!cadre) return;
    carte.fitBounds([[cadre[0], cadre[1]], [cadre[2], cadre[3]]],
                    { padding: margesDuCadrage(), maxZoom: 8 });
  }

  /* Sur téléphone, le panneau est un tiroir qui monte du bas. Même bouton et
     même mécanique que sur les sept autres cartes. */
  function brancherTiroir() {
    var bouton = document.getElementById("bouton-panneau");
    var boite = document.getElementById("panneau");
    if (!bouton || !boite) return;
    bouton.textContent = "☰ " + t("metro_titre");
    bouton.addEventListener("click", function () {
      var ouvert = boite.classList.toggle("est-ouvert");
      bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
      bouton.textContent = ouvert ? "✕" : "☰ " + t("metro_titre");
    });
  }

  /* --- 8. La légende ------------------------------------------------------- */

  function dessinerLegende() {
    var legende = document.getElementById("legende");
    if (!legende) return;
    legende.innerHTML =
      '<div class="legende__titre">' + echapper(t("legende")) + "</div>" +
      '<div class="legende__ligne"><span class="legende__trait legende__trait--couleurs"' +
        '></span>' + echapper(t("metro_leg_couleurs")) + "</div>" +
      '<div class="legende__ligne"><span class="legende__pastille" style="background:' +
        couleurCSS("--accent") + '"></span>' + echapper(t("metro_leg_ville")) + "</div>" +
      '<div class="legende__ligne"><span class="legende__pastille" style="background:' +
        COULEUR_CHANTIER + '"></span>' + echapper(t("metro_leg_chantier")) + "</div>" +

      '<div class="legende__ligne"><span class="legende__trait legende__trait--pointille"' +
        ' style="border-color:' + COULEUR_CHANTIER + '"></span>' +
        echapper(t("metro_leg_pointilles")) + "</div>" +
      '<div class="legende__note">' + echapper(t("metro_leg_zoom")) + "</div>";
  }

  /* --- 9. Démarrage -------------------------------------------------------- */

  function demarrer() {
    var chargement = document.getElementById("chargement");
    chargement.textContent = t("chargement");

    /* L'aperçu part en même temps que le reste mais ne bloque rien : la carte
       s'affiche sans l'attendre, et il se pose dessus dès qu'il arrive. */
    charger("data/metro/apercu.json")
      .then(function (d) {
        apercu = apercuGeoJSON(d);
        if (carte && carte.getSource("apercu")) carte.getSource("apercu").setData(apercu);
      })
      .catch(function (e) { console.error("[StatsMaps] aperçu métro :", e); });

    Promise.all([charger("data/metro/monde.json"), charger("data/pays.json"),
                 telechargerStyle(themeSombre() ? "sombre" : "clair"),
                 charger("data/frontieres.json").catch(function () { return null; })])
      .then(function (r) {
        monde = r[0];
        r[0].villes.forEach(function (v) { villeParSlug[v.s] = v; });
        r[1].features.forEach(function (f) { paysParIso[f.properties.iso] = f.properties; });

        panneau.titre.textContent = t("metro_titre");
        panneau.recherche.placeholder = t("metro_recherche");
        panneau.retour.textContent = t("metro_retour");
        panneau.retour.hidden = true;
        panneau.retour.addEventListener("click", fermerVille);
        panneau.recherche.addEventListener("input", dessinerClassement);
        panneau.source.innerHTML = t("metro_source");

        fabriquerOnglets();
        dessinerClassement();
        brancherTiroir();
        construireCarte(r[1], r[2], r[3]);
        chargement.hidden = true;
      })
      .catch(function (e) {
        console.error("[StatsMaps] métro :", e);
        chargement.textContent = t("erreur");
      });
  }

  /* Le thème clair/sombre repeint la carte sans la reconstruire. */
  /* Le thème clair/sombre change de fond de carte : « Liberty » ou « Dark ».
     Le nouveau fond efface les couches du site : on les repose dès qu'il est
     prêt (« style.load »). La ville ouverte et les tracés sont gardés. */
  window.addEventListener("statsmaps:theme", function () {
    if (!carte || !geoPaysGarde) return;
    telechargerStyle(themeSombre() ? "sombre" : "clair").then(function (fond) {
      carte.once("style.load", function () {
        ajouterCouches();
        dessinerLegende();
      });
      carte.setStyle(fabriquerFond(fond), { diff: false });
    });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarrer);
  } else {
    demarrer();
  }
})();
