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

  /* Le zoom auquel on arrive quand on choisit une ville. */
  var ZOOM_VILLE = 10.4;

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

  function styleDeBase() {
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

  function construireCarte(geoPays) {
    carte = new maplibregl.Map({
      container: "carte",
      style: styleDeBase(),
      bounds: CADRAGE_MONDE,
      fitBoundsOptions: { padding: margesDuCadrage() },
      minZoom: 0.5,
      maxZoom: 16,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    });

    carte.touchZoomRotate.disableRotation();
    carte.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    carte.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution:
        '<a href="https://www.naturalearthdata.com/">Natural Earth</a> · ' +
        '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · ' +
        '<a href="https://www.wikidata.org/">Wikidata</a>',
    }), "bottom-right");

    carte.on("error", function (e) {
      console.error("[StatsMaps] carte :", (e && e.error && e.error.message) || e);
    });

    carte.on("load", function () {
      carte.addSource("pays", { type: "geojson", data: geoPays, promoteId: "iso" });
      carte.addSource("apercu", { type: "geojson", data: videGeoJSON() });
      carte.addSource("traces", { type: "geojson", data: videGeoJSON() });
      carte.addSource("chantiers", { type: "geojson", data: videGeoJSON() });
      carte.addSource("villes", { type: "geojson", data: villesGeoJSON(), promoteId: "s" });

      /* Le fond : les pays, tous de la même couleur. Ici ils ne portent
         aucune donnée, ils situent — c'est une toile de fond, pas la carte. */
      carte.addLayer({
        id: "pays-fond", type: "fill", source: "pays",
        paint: { "fill-color": couleurCSS("--pays-sans-donnee"), "fill-opacity": 0.55 },
      });
      carte.addLayer({
        id: "pays-contour", type: "line", source: "pays",
        paint: { "line-color": couleurCSS("--contour-pays"), "line-width": 0.4 },
      });

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
      });

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
      });

      carte.addLayer({
        id: "lignes", type: "line", source: "traces",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": ["get", "couleur"],
          "line-width": epaisseurDesLignes(),
          "line-opacity": apparitionDesLignes(),
        },
      });

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
      });

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
          "circle-stroke-color": ["case",
            ["boolean", ["feature-state", "choisie"], false], couleurCSS("--texte"),
            [">", ["coalesce", ["get", "kmc"], 0], 0], COULEUR_CHANTIER,
            couleurCSS("--panneau")],
          "circle-stroke-opacity": ["interpolate", ["linear"], ["zoom"],
            ZOOM_LIGNES, 1, ZOOM_LIGNES + 3, 0.25],
        },
      });

      if (apercu) carte.getSource("apercu").setData(apercu);

      brancherInteractions();
      chargerCeQuOnVoit();
      dessinerLegende();
    });

    carte.on("moveend", chargerCeQuOnVoit);
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
    var lignes = [], chantiers = [];
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
      var couches = ["villes", "lignes", "chantiers"];
      if (carte.getZoom() < ZOOM_LIGNES + 0.4) couches.push("apercu");
      var dessus = carte.queryRenderedFeatures(e.point, { layers: couches });
      if (!dessus.length) fermerVille();
    });
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

  function drapeauDuPays(iso) {
    return (paysParIso[iso] || {}).d || "";
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

    Promise.all([charger("data/metro/monde.json"), charger("data/pays.json")])
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
        construireCarte(r[1]);
        chargement.hidden = true;
      })
      .catch(function (e) {
        console.error("[StatsMaps] métro :", e);
        chargement.textContent = t("erreur");
      });
  }

  /* Le thème clair/sombre repeint la carte sans la reconstruire. */
  window.addEventListener("statsmaps:theme", function () {
    if (!carte || !carte.isStyleLoaded()) return;
    carte.setPaintProperty("mer", "background-color", couleurCSS("--fond-carte"));
    carte.setPaintProperty("pays-fond", "fill-color", couleurCSS("--pays-sans-donnee"));
    carte.setPaintProperty("pays-contour", "line-color", couleurCSS("--contour-pays"));
    dessinerLegende();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarrer);
  } else {
    demarrer();
  }
})();
