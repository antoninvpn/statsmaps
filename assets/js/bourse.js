/* ==========================================================================
   bourse.js — le moteur de la carte des entreprises cotées en bourse.

   Chaque entreprise est un POINT posé sur son siège :
       bleu .... l'adresse exacte est connue ;
       jaune ... on ne connaît que la ville : le point est au centre-ville.

   DEUX ÉCHELLES DE LECTURE, comme sur la carte des métros :

     de loin ...... de simples pastilles bleues et jaunes. Dix mille logos à
                    l'échelle du monde ne seraient qu'une bouillie illisible,
                    et coûteraient des dizaines de mégaoctets.
     de près ...... à partir du zoom 8, le LOGO de l'entreprise apparaît dans
                    un rond cerclé de bleu ou de jaune. Quand deux logos se
                    chevauchent, c'est l'entreprise la plus connue qui passe
                    devant ; l'autre reste une pastille, et réapparaît en
                    logo quand on zoome encore. Chaque logo n'est téléchargé
                    qu'au moment où il doit s'afficher.

   Le panneau de gauche sert à TRIER : des cases à cocher par secteur et par
   place boursière. Une entreprise s'affiche si l'un au moins de ses secteurs
   ET l'une au moins de ses bourses sont cochés.

   Comme les autres cartes, il lit sur la balise <body> :
       data-langue="fr"   → dans quelle langue
       data-base="../"    → où trouver le dossier data/

   Déroulé du fichier :
     1. Réglages
     2. Petits outils
     3. Fabrication de la carte
     4. Les logos, dessinés à la demande
     5. Les filtres
     6. Le panneau de gauche
     7. La fiche d'une entreprise
     8. La légende
     9. Démarrage
   ========================================================================== */

(function () {
  "use strict";

  /* --- 1. Réglages --------------------------------------------------------- */

  /* Les deux couleurs, choisies par Antonin. Le jaune est un jaune d'or plutôt
     qu'un jaune citron : un jaune trop clair disparaît sur le gris clair des
     pays en thème clair. */
  var BLEU = "#2563EB";
  var JAUNE = "#F2B705";

  /* À partir de ce zoom, les logos remplacent les pastilles. */
  var ZOOM_LOGOS = 8;

  /* Le zoom auquel on arrive en ouvrant la fiche d'une entreprise : la rue
     quand l'adresse est exacte, la ville quand elle ne l'est pas. */
  var ZOOM_EXACT = 14;
  var ZOOM_VILLE = 11;

  /* LE FOND DE RUES. C'est la seule carte du site qui va chercher quelque
     chose ailleurs pendant qu'on la regarde : les rues, les bâtiments et
     l'eau, chez OpenFreeMap — un service gratuit, sans compte ni publicité,
     qui redistribue les données d'OpenStreetMap. Il n'est appelé que quand on
     zoome sur une ville (à partir du zoom 10) : la vue du monde, elle, reste
     entièrement servie par le site. Si OpenFreeMap ne répond pas, la carte
     marche quand même, simplement sans les rues.
     Sans ce fond, un point « à l'adresse exacte » flotte sur du gris uni, et
     on ne voit pas dans quelle rue il est. */
  var RUES = "https://tiles.openfreemap.org/planet";
  var POLICES = "https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf";
  var ZOOM_RUES = 10;
  /* Les noms des rues n'apparaissent qu'à l'échelle du quartier. */
  var ZOOM_NOMS = 14;

  /* Combien de places boursières on montre avant le bouton « Voir les autres » :
     il y en a deux cents, dont la moitié n'ont qu'une ou deux entreprises. */
  var BOURSES_VISIBLES = 15;

  /* Combien de résultats au plus quand on cherche un nom. */
  var RESULTATS_MAX = 120;

  /* La taille du rond d'un logo, en pixels d'image. Il est dessiné deux fois
     plus grand qu'affiché (pixelRatio 2) pour rester net sur un écran Retina. */
  var TAILLE_ROND = 72;

  /* --- 2. Petits outils ---------------------------------------------------- */

  var corps = document.body;
  var langue = corps.getAttribute("data-langue") || "fr";
  var base = corps.getAttribute("data-base") || "./";
  var tousLesTextes = window.StatsMapsTextes || {};
  var textes = tousLesTextes[langue] || tousLesTextes.fr || {};

  function t(clef) {
    return textes[clef] !== undefined ? textes[clef] : clef;
  }

  var LOCALE = langue + "-u-nu-latn";

  function formater(valeur, decimales) {
    if (valeur === null || valeur === undefined) return "—";
    var texte = new Intl.NumberFormat(LOCALE, {
      minimumFractionDigits: 0,
      maximumFractionDigits: decimales || 0,
    }).format(valeur);
    return texte.replace(/ /g, " ");
  }

  /* « 416 161 000 000 USD » se lit mal : on écrit « 416,2 Md USD ». */
  function montant(valeur, monnaie) {
    var texte;
    if (valeur >= 1e9) {
      texte = t("bourse_milliards").replace("{n}", formater(valeur / 1e9, 1));
    } else if (valeur >= 1e6) {
      texte = t("bourse_millions").replace("{n}", formater(valeur / 1e6, 1));
    } else {
      texte = formater(valeur, 0);
    }
    return texte + (monnaie ? " " + monnaie : "");
  }

  function sansAccents(texte) {
    return String(texte || "")
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase();
  }

  function echapper(texte) {
    return String(texte === null || texte === undefined ? "" : texte)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  /* Un lien vers l'extérieur n'est écrit que s'il commence par http(s) : une
     adresse bizarre recopiée de Wikidata ne doit rien pouvoir exécuter. */
  function lienSur(url) {
    return /^https?:\/\//i.test(url || "") ? url : null;
  }

  function couleurCSS(nom) {
    return getComputedStyle(document.documentElement).getPropertyValue(nom).trim();
  }

  function charger(chemin) {
    return fetch(base + chemin).then(function (r) {
      if (!r.ok) throw new Error(chemin + " : " + r.status);
      return r.json();
    });
  }

  /* Les initiales d'une entreprise, pour celles qui n'ont pas de logo :
     « Manchester United FC » -> « MU ». */
  function initiales(nom) {
    var mots = String(nom || "?")
      .replace(/\(.*?\)/g, "")
      .split(/[\s\-–&,.]+/)
      .filter(function (m) { return m && /[A-Za-zÀ-ÿ0-9Ͱ-￿]/.test(m); })
      .filter(function (m) { return !/^(the|groupe|group|de|du|des|la|le|and|of|sa|ag|inc|plc|ltd|co|corp|corporation|company|holdings?)$/i.test(m); });
    if (!mots.length) return String(nom || "?").slice(0, 2).toUpperCase();
    if (mots.length === 1) return Array.from(mots[0]).slice(0, 2).join("").toUpperCase();
    return (Array.from(mots[0])[0] + Array.from(mots[1])[0]).toUpperCase();
  }

  /* --- Les données --------------------------------------------------------- */

  var carte = null;
  var donnees = null;        /* data/bourse/entreprises.json */
  var parQid = {};           /* "Q312" -> Apple */
  var paysParIso = {};       /* "FRA" -> {nom, drapeau} */
  var secteursCoches = {};   /* "banque" -> true */
  var boursesCochees = {};   /* 0 -> true (numéro dans donnees.bourses) */
  var toutesLesBourses = false;  /* la liste des bourses est-elle dépliée ? */
  var choisie = null;        /* la Q de l'entreprise dont la fiche est ouverte */
  var vue = "filtres";       /* "filtres", "fiche" ou "ici" */

  function nomDuPays(iso) {
    var p = paysParIso[iso] || {};
    return p[langue] || p.en || iso || "";
  }

  function drapeauDuPays(iso) {
    return (paysParIso[iso] || {}).d || "";
  }

  function nomDuSecteur(id) {
    return t("bourse_sec_" + id);
  }

  /* --- 3. Fabrication de la carte ------------------------------------------ */

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

  function styleDeBase() {
    return {
      version: 8,
      name: "StatsMaps",
      /* Les lettres des noms de rues. Rien n'est téléchargé tant qu'aucun nom
         n'est à afficher, c'est-à-dire avant le zoom 14. */
      glyphs: POLICES,
      sources: {},
      layers: [{
        id: "mer",
        type: "background",
        paint: { "background-color": couleurDuFond() },
      }],
    };
  }

  /* Le fond change de rôle avec le zoom. De loin, c'est la MER, et les pays
     sont dessinés par-dessus. De près, c'est la TERRE, et c'est l'eau du fond
     de rues qui est dessinée par-dessus : les contours des pays du site sont
     simplifiés pour le monde entier, et à l'échelle d'une rue ils mettraient
     la moitié de Hong Kong dans la mer. */
  function couleurDuFond() {
    return ["interpolate", ["linear"], ["zoom"],
      ZOOM_RUES - 1, couleurCSS("--fond-carte"),
      ZOOM_RUES, couleurCSS("--rue-terre")];
  }

  /* Le fond de rues apparaît en fondu entre les zooms 9 et 10, pendant que
     les pays du site s'effacent : l'œil ne voit aucune coupure. */
  function apparitionDesRues() {
    return ["interpolate", ["linear"], ["zoom"], ZOOM_RUES - 1, 0, ZOOM_RUES, 1];
  }

  /* L'épaisseur d'une rue selon son importance : une autoroute est plus
     large qu'une ruelle, et toutes s'élargissent quand on s'approche. */
  function largeurDesRues(bordure) {
    var plus = bordure ? 1.6 : 0;
    function selon(grandes, moyennes, petites) {
      return ["+", plus, ["match", ["get", "class"],
        ["motorway", "trunk"], grandes,
        ["primary", "secondary"], moyennes,
        petites]];
    }
    return ["interpolate", ["exponential", 1.6], ["zoom"],
      ZOOM_RUES, selon(1.4, 0.8, 0.2),
      14, selon(5, 3.5, 1.8),
      18, selon(18, 14, 9)];
  }

  function ajouterLesRues() {
    carte.addSource("rues", { type: "vector", url: RUES });
    var classes = ["motorway", "trunk", "primary", "secondary", "tertiary",
                   "minor", "service"];
    var filtreRues = ["match", ["get", "class"], classes, true, false];

    carte.addLayer({
      id: "rues-eau", type: "fill", source: "rues", "source-layer": "water",
      minzoom: ZOOM_RUES - 1,
      paint: { "fill-color": couleurCSS("--rue-eau"), "fill-opacity": apparitionDesRues() },
    });
    carte.addLayer({
      id: "rues-batiments", type: "fill", source: "rues", "source-layer": "building",
      minzoom: 13,
      paint: {
        "fill-color": couleurCSS("--rue-batiment"),
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], 13, 0, 14, 1],
      },
    });
    carte.addLayer({
      id: "rues-bordures", type: "line", source: "rues", "source-layer": "transportation",
      minzoom: ZOOM_RUES - 1, filter: filtreRues,
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": couleurCSS("--rue-bordure"),
        "line-width": largeurDesRues(true),
        "line-opacity": apparitionDesRues(),
      },
    });
    carte.addLayer({
      id: "rues-traits", type: "line", source: "rues", "source-layer": "transportation",
      minzoom: ZOOM_RUES - 1, filter: filtreRues,
      layout: { "line-cap": "round", "line-join": "round" },
      paint: {
        "line-color": couleurCSS("--rue"),
        "line-width": largeurDesRues(false),
        "line-opacity": apparitionDesRues(),
      },
    });
    /* Le nom des rues, dans la langue du pays : c'est celui qu'on lit sur la
       plaque, et celui qu'on retrouve dans l'adresse de la fiche. */
    carte.addLayer({
      id: "rues-noms", type: "symbol", source: "rues", "source-layer": "transportation_name",
      minzoom: ZOOM_NOMS,
      layout: {
        "symbol-placement": "line",
        "text-field": ["get", "name"],
        "text-font": ["Noto Sans Regular"],
        "text-size": ["interpolate", ["linear"], ["zoom"], ZOOM_NOMS, 10.5, 18, 13],
        "text-max-angle": 30,
      },
      paint: {
        "text-color": couleurCSS("--rue-nom"),
        "text-halo-color": couleurCSS("--rue"),
        "text-halo-width": 1.4,
      },
    });
  }

  function repeindreLesRues() {
    if (!carte.getLayer("rues-eau")) return;
    carte.setPaintProperty("rues-eau", "fill-color", couleurCSS("--rue-eau"));
    carte.setPaintProperty("rues-batiments", "fill-color", couleurCSS("--rue-batiment"));
    carte.setPaintProperty("rues-bordures", "line-color", couleurCSS("--rue-bordure"));
    carte.setPaintProperty("rues-traits", "line-color", couleurCSS("--rue"));
    carte.setPaintProperty("rues-noms", "text-color", couleurCSS("--rue-nom"));
    carte.setPaintProperty("rues-noms", "text-halo-color", couleurCSS("--rue"));
  }

  function construireCarte(geoPays) {
    carte = new maplibregl.Map({
      container: "carte",
      style: styleDeBase(),
      bounds: CADRAGE_MONDE,
      fitBoundsOptions: { padding: margesDuCadrage() },
      minZoom: 0.5,
      maxZoom: 18,
      attributionControl: false,
      dragRotate: false,
      pitchWithRotate: false,
    });

    carte.touchZoomRotate.disableRotation();
    carte.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    carte.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution:
        /* OpenFreeMap, OpenMapTiles et OpenStreetMap n'ont pas à être écrits
           ici : le fond de rues apporte lui-même sa mention, et MapLibre
           l'ajoute tout seul à cette ligne. */
        '<a href="https://www.naturalearthdata.com/">Natural Earth</a> · ' +
        '<a href="https://www.wikidata.org/">Wikidata</a> · ' +
        '<a href="https://commons.wikimedia.org/">Wikimedia Commons</a>',
    }), "bottom-right");

    carte.on("error", function (e) {
      console.error("[StatsMaps] carte :", (e && e.error && e.error.message) || e);
    });

    carte.on("styleimagemissing", dessinerUnLogo);

    carte.on("load", function () {
      carte.addSource("pays", { type: "geojson", data: geoPays });
      carte.addSource("entreprises", { type: "geojson", data: entreprisesGeoJSON() });

      /* Les pays du site s'effacent quand le fond de rues prend le relais. */
      carte.addLayer({
        id: "pays-fond", type: "fill", source: "pays",
        paint: {
          "fill-color": couleurCSS("--pays-sans-donnee"),
          "fill-opacity": ["interpolate", ["linear"], ["zoom"],
            ZOOM_RUES - 1, 0.55, ZOOM_RUES, 0],
        },
      });
      carte.addLayer({
        id: "pays-contour", type: "line", source: "pays",
        paint: {
          "line-color": couleurCSS("--contour-pays"),
          "line-width": 0.4,
          "line-opacity": ["interpolate", ["linear"], ["zoom"],
            ZOOM_RUES - 1, 1, ZOOM_RUES, 0],
        },
      });

      ajouterLesRues();

      /* Les pastilles : toujours là, à tous les zooms. De près, elles restent
         sous les logos et ne se voient que là où un logo n'a pas trouvé de
         place. */
      carte.addLayer({
        id: "points", type: "circle", source: "entreprises",
        layout: {
          /* Les plus connues sont dessinées en dernier, donc par-dessus. */
          "circle-sort-key": ["get", "r"],
        },
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"],
            0.5, 1.8, 4, 2.6, 8, 4.2, 12, 6, 16, 7],
          "circle-color": ["case", ["==", ["get", "p"], 1], BLEU, JAUNE],
          "circle-opacity": 0.92,
          "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 2, 0.3, 8, 1],
          "circle-stroke-color": couleurCSS("--panneau"),
        },
      });

      /* Les logos, à partir du zoom 8. Le nom de l'image est « logo-Q312 » :
         MapLibre ne l'a pas encore, il le demande à dessinerUnLogo(). */
      carte.addLayer({
        id: "logos", type: "symbol", source: "entreprises",
        minzoom: ZOOM_LOGOS - 0.5,
        layout: {
          "icon-image": ["concat", "logo-", ["get", "q"]],
          "icon-size": ["interpolate", ["linear"], ["zoom"],
            ZOOM_LOGOS - 0.5, 0.6, 12, 0.85, 15, 1],
          /* Quand deux logos se chevauchent, le plus connu gagne (la clef la
             plus PETITE passe en premier, d'où le signe moins). */
          "symbol-sort-key": ["-", 0, ["get", "r"]],
          "icon-padding": 1,
        },
        paint: {
          "icon-opacity": ["interpolate", ["linear"], ["zoom"],
            ZOOM_LOGOS - 0.5, 0, ZOOM_LOGOS + 0.3, 1],
        },
      });

      /* Le cercle autour de l'entreprise dont la fiche est ouverte. */
      carte.addLayer({
        id: "choisie", type: "circle", source: "entreprises",
        filter: ["==", ["get", "q"], ""],
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 8, ZOOM_LOGOS, 12, 14, 22],
          "circle-color": "rgba(0,0,0,0)",
          "circle-stroke-width": 2.5,
          "circle-stroke-color": couleurCSS("--texte"),
        },
      });

      brancherInteractions();
      dessinerLegende();
      if (choisie) marquerChoisie(choisie);
    });
  }

  /* Seules les entreprises qui passent les filtres vont sur la carte. On
     refait la liste à chaque case cochée : dix mille points, le navigateur
     s'en acquitte en quelques millisecondes. */
  function entreprisesGeoJSON() {
    return {
      type: "FeatureCollection",
      features: donnees.entreprises.filter(estVisible).map(function (e) {
        return {
          type: "Feature",
          properties: { q: e.q, p: e.p, r: e.r },
          geometry: { type: "Point", coordinates: [e.x, e.y] },
        };
      }),
    };
  }

  function redessinerLesPoints() {
    if (carte && carte.getSource("entreprises")) {
      carte.getSource("entreprises").setData(entreprisesGeoJSON());
    }
  }

  /* --- 4. Les logos, dessinés à la demande --------------------------------- */

  /* Un rond blanc, cerclé de bleu ou de jaune, avec dedans le logo, ou à
     défaut les initiales de l'entreprise. Le fond reste blanc même en thème
     sombre : les logos sont dessinés par leurs auteurs pour un fond clair, et
     un logo noir sur fond sombre disparaîtrait. */
  function dessinerRond(e, image) {
    var toile = document.createElement("canvas");
    toile.width = toile.height = TAILLE_ROND;
    var c = toile.getContext("2d");
    var milieu = TAILLE_ROND / 2;
    var epaisseur = 6;

    c.beginPath();
    c.arc(milieu, milieu, milieu - epaisseur / 2 - 1, 0, 2 * Math.PI);
    c.fillStyle = "#ffffff";
    c.fill();
    c.lineWidth = epaisseur;
    c.strokeStyle = e.p ? BLEU : JAUNE;
    c.stroke();

    if (image && image.width && image.height) {
      /* Le logo tient dans le carré inscrit dans le rond, sans être déformé. */
      var cote = (milieu - epaisseur - 2) * Math.SQRT2;
      var echelle = Math.min(cote / image.width, cote / image.height);
      var l = image.width * echelle, h = image.height * echelle;
      c.drawImage(image, milieu - l / 2, milieu - h / 2, l, h);
    } else {
      var lettres = initiales(e.n);
      c.fillStyle = "#3b4350";
      c.font = "700 " + (lettres.length > 1 ? 24 : 28) +
        "px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
      c.textAlign = "center";
      c.textBaseline = "middle";
      c.fillText(lettres, milieu, milieu + 1);
    }
    return c.getImageData(0, 0, TAILLE_ROND, TAILLE_ROND);
  }

  /* MapLibre appelle cette fonction chaque fois qu'il doit afficher un logo
     qu'il n'a pas encore. On lui donne TOUT DE SUITE un rond avec les
     initiales (il ne sait pas attendre), puis on remplace ce rond par le vrai
     logo dès que celui-ci est arrivé. */
  function dessinerUnLogo(evenement) {
    var id = evenement.id || "";
    if (id.indexOf("logo-") !== 0 || carte.hasImage(id)) return;
    var e = parQid[id.slice(5)];
    if (!e) return;
    carte.addImage(id, dessinerRond(e, null), { pixelRatio: 2 });
    if (!e.l) return;
    var image = new Image();
    image.onload = function () {
      if (carte.hasImage(id)) carte.updateImage(id, dessinerRond(e, image));
    };
    image.src = base + "data/bourse/logos/" + e.q + ".png";
  }

  /* --- Les clics sur la carte ---------------------------------------------- */

  function brancherInteractions() {
    ["points", "logos"].forEach(function (couche) {
      carte.on("mouseenter", couche, function () {
        carte.getCanvas().style.cursor = "pointer";
      });
      carte.on("mouseleave", couche, function () {
        carte.getCanvas().style.cursor = "";
      });
    });

    carte.on("click", function (e) {
      /* On regarde un petit carré autour du doigt, et non le seul pixel
         touché : une pastille fait quelques pixels, on la manquerait. */
      var marge = 5;
      var dessus = carte.queryRenderedFeatures(
        [[e.point.x - marge, e.point.y - marge], [e.point.x + marge, e.point.y + marge]],
        { layers: ["points", "logos"] });
      var vues = {}, qids = [];
      dessus.forEach(function (f) {
        var q = f.properties.q;
        if (!vues[q]) { vues[q] = true; qids.push(q); }
      });
      if (!qids.length) {
        if (vue !== "filtres") fermer();
        return;
      }
      /* De près, un logo cliqué l'emporte sur ses voisines… sauf si d'autres
         entreprises sont EXACTEMENT au même point que lui (toutes celles
         posées au centre d'une ville) : on montre alors toute la pile. */
      var logo = dessus.filter(function (f) { return f.layer.id === "logos"; })[0];
      if (logo && carte.getZoom() >= 13) {
        var e0 = parQid[logo.properties.q];
        qids = qids.filter(function (q) {
          var e1 = parQid[q];
          return e1 && e1.x === e0.x && e1.y === e0.y;
        });
        if (qids.indexOf(e0.q) < 0) qids.unshift(e0.q);
      }
      var premiere = parQid[qids[0]];
      var memePoint = qids.every(function (q) {
        var e1 = parQid[q];
        return e1 && e1.x === premiere.x && e1.y === premiere.y;
      });
      if (qids.length === 1) {
        ouvrirFiche(qids[0], false);
      } else if (memePoint || carte.getZoom() >= 12) {
        montrerIci(qids, memePoint);
      } else {
        /* De loin, cinq pixels couvrent toute une région : plutôt qu'une
           liste de 370 entreprises d'Osaka à Kobe, on s'approche. */
        carte.flyTo({ center: e.lngLat, zoom: Math.min(carte.getZoom() + 3, 12), speed: 1.4 });
      }
    });
  }

  /* --- 5. Les filtres ------------------------------------------------------ */

  function estVisible(e) {
    return e.s.some(function (s) { return secteursCoches[s]; }) &&
           e.b.some(function (b) { return boursesCochees[b]; });
  }

  function toutCocher(liste, valeur) {
    Object.keys(liste).forEach(function (k) { liste[k] = valeur; });
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

  function compteur() {
    var affichees = donnees.entreprises.filter(estVisible).length;
    var total = donnees.entreprises.length;
    var texte = formater(total) + " " + t("bourse_entreprises");
    if (affichees !== total) texte += " · " + formater(affichees) + " " + t("bourse_affichees");
    return texte;
  }

  function dessinerPanneau() {
    if (vue !== "filtres") return;
    panneau.titre.textContent = t("bourse_titre");
    panneau.soustitre.textContent = compteur();
    panneau.retour.hidden = true;
    panneau.recherche.hidden = false;

    var recherche = sansAccents(panneau.recherche.value.trim());
    if (recherche) {
      dessinerResultats(recherche);
    } else {
      dessinerFiltres();
    }
  }

  /* Une liste d'entreprises : celles qu'on cherche, ou celles d'un même
     endroit. Chaque ligne porte la couleur de sa pastille sur la carte. */
  function ligneEntreprise(e) {
    return '<li class="entreprise" data-q="' + echapper(e.q) + '">' +
      '<span class="entreprise__point" style="background:' + (e.p ? BLEU : JAUNE) + '"></span>' +
      '<span class="nom">' + echapper(e.n) + "</span>" +
      '<span class="valeur">' + echapper(e.v || nomDuPays(e.i)) + "</span></li>";
  }

  function brancherLignesEntreprises() {
    Array.prototype.forEach.call(panneau.liste.querySelectorAll("[data-q]"), function (li) {
      li.addEventListener("click", function () {
        ouvrirFiche(li.getAttribute("data-q"), true);
      });
    });
  }

  function dessinerResultats(recherche) {
    var trouvees = donnees.entreprises.filter(function (e) {
      return sansAccents(e.n).indexOf(recherche) >= 0 ||
        (e.na && sansAccents(e.na).indexOf(recherche) >= 0) ||
        (e.t || []).some(function (s) { return sansAccents(s) === recherche; });
    }).slice(0, RESULTATS_MAX);
    if (!trouvees.length) {
      panneau.liste.innerHTML = '<li class="vide">' + echapper(t("bourse_rien_trouve")) + "</li>";
      return;
    }
    panneau.liste.innerHTML = trouvees.map(ligneEntreprise).join("");
    brancherLignesEntreprises();
  }

  /* Les cases à cocher : les secteurs, puis les places boursières. */
  function dessinerFiltres() {
    var h = [];

    h.push(enteteDeGroupe("bourse_secteurs", "secteurs"));
    donnees.secteurs.forEach(function (s) {
      h.push(caseACocher("secteur", s.id, nomDuSecteur(s.id), s.c, secteursCoches[s.id]));
    });

    h.push(enteteDeGroupe("bourse_bourses", "bourses"));
    var bourses = donnees.bourses;
    var montrees = toutesLesBourses ? bourses : bourses.slice(0, BOURSES_VISIBLES);
    montrees.forEach(function (b, n) {
      h.push(caseACocher("bourse", n, b.n, b.c, boursesCochees[n]));
    });
    if (bourses.length > BOURSES_VISIBLES) {
      h.push('<li class="filtres__plus"><button type="button" id="plus-de-bourses">' +
        echapper(toutesLesBourses ? t("bourse_voir_moins")
          : t("bourse_voir_plus").replace("{n}", formater(bourses.length - BOURSES_VISIBLES))) +
        "</button></li>");
    }

    panneau.liste.innerHTML = h.join("");

    Array.prototype.forEach.call(panneau.liste.querySelectorAll("input[data-genre]"), function (c) {
      c.addEventListener("change", function () {
        var liste = c.getAttribute("data-genre") === "secteur" ? secteursCoches : boursesCochees;
        liste[c.getAttribute("data-id")] = c.checked;
        redessinerLesPoints();
        panneau.soustitre.textContent = compteur();
      });
    });
    Array.prototype.forEach.call(panneau.liste.querySelectorAll("[data-tout]"), function (b) {
      b.addEventListener("click", function () {
        var liste = b.getAttribute("data-groupe") === "secteurs" ? secteursCoches : boursesCochees;
        toutCocher(liste, b.getAttribute("data-tout") === "1");
        redessinerLesPoints();
        dessinerPanneau();
      });
    });
    var plus = document.getElementById("plus-de-bourses");
    if (plus) {
      plus.addEventListener("click", function () {
        toutesLesBourses = !toutesLesBourses;
        dessinerPanneau();
      });
    }
  }

  function enteteDeGroupe(clef, groupe) {
    return '<li class="filtres__entete"><span>' + echapper(t(clef)) + "</span>" +
      '<button type="button" data-groupe="' + groupe + '" data-tout="1">' +
        echapper(t("bourse_tout")) + "</button>" +
      '<button type="button" data-groupe="' + groupe + '" data-tout="0">' +
        echapper(t("bourse_rien")) + "</button></li>";
  }

  function caseACocher(genre, id, nom, nombre, coche) {
    var identifiant = "f-" + genre + "-" + id;
    return '<li class="filtre"><input type="checkbox" id="' + identifiant + '"' +
      ' data-genre="' + genre + '" data-id="' + echapper(id) + '"' + (coche ? " checked" : "") + ">" +
      '<label class="nom" for="' + identifiant + '">' + echapper(nom) + "</label>" +
      '<span class="valeur">' + formater(nombre) + "</span></li>";
  }

  /* Plusieurs entreprises au même endroit : c'est le cas de toutes celles
     dont on ne connaît que la ville — cinq cents à Tokyo, au même point. */
  function montrerIci(qids, memePoint) {
    vue = "ici";
    marquerChoisie(null);
    var liste = qids.map(function (q) { return parQid[q]; }).filter(Boolean)
      .sort(function (a, b) { return b.r - a.r; });
    panneau.titre.textContent = t("bourse_ici").replace("{n}", formater(liste.length));
    /* Le nom de la ville n'a de sens que si elles sont toutes au même point. */
    panneau.soustitre.textContent = memePoint && liste[0] && liste[0].v ? liste[0].v : "";
    panneau.retour.hidden = false;
    panneau.recherche.hidden = true;
    panneau.liste.innerHTML = liste.map(ligneEntreprise).join("");
    brancherLignesEntreprises();
    ouvrirTiroir();
  }

  function fermer() {
    vue = "filtres";
    marquerChoisie(null);
    dessinerPanneau();
  }

  /* --- 7. La fiche d'une entreprise ---------------------------------------- */

  function marquerChoisie(q) {
    choisie = q;
    if (carte && carte.getLayer("choisie")) {
      carte.setFilter("choisie", ["==", ["get", "q"], q || ""]);
    }
  }

  function ouvrirFiche(q, voler) {
    var e = parQid[q];
    if (!e) return;
    vue = "fiche";
    marquerChoisie(q);
    if (voler) {
      carte.flyTo({
        center: [e.x, e.y],
        zoom: Math.max(carte.getZoom(), e.p ? ZOOM_EXACT : ZOOM_VILLE),
        padding: margesDuCadrage(),
        speed: 1.4,
      });
    }
    dessinerFiche(e);
    ouvrirTiroir();
  }

  function dessinerFiche(e) {
    panneau.titre.textContent = e.n;
    panneau.soustitre.innerHTML = e.i
      ? '<span class="drapeau" aria-hidden="true">' + drapeauDuPays(e.i) + "</span> " +
        echapper(nomDuPays(e.i))
      : "";
    panneau.retour.hidden = false;
    panneau.recherche.hidden = true;

    var h = ['<li class="fiche fiche-entreprise">'];

    /* Le logo en grand, ou les initiales. */
    h.push('<div class="fiche-entreprise__logo">' +
      (e.l ? '<img src="' + base + "data/bourse/logos/" + echapper(e.q) + '.png" alt=""' +
             ' data-initiales="' + echapper(initiales(e.n)) + '">'
           : "<span>" + echapper(initiales(e.n)) + "</span>") + "</div>");

    /* Où est le siège, et à quel point on en est sûr. */
    var precision = e.p ? t("bourse_exact")
      : (e.v ? t("bourse_ville").replace("{ville}", e.v) : t("bourse_ville_seule"));
    h.push('<p class="fiche-entreprise__precision"><span class="entreprise__point" style="background:' +
      (e.p ? BLEU : JAUNE) + '"></span>' + echapper(precision) + "</p>");
    var adresse = [e.a, e.v].filter(Boolean);
    /* Pas deux fois la ville quand l'adresse la contient déjà. */
    if (e.a && e.v && sansAccents(e.a).indexOf(sansAccents(e.v)) >= 0) adresse = [e.a];
    if (adresse.length) {
      h.push('<p class="fiche__phrase">' + echapper(adresse.join(", ")) + "</p>");
    }

    /* Les chiffres, chacun avec son année : ils ne sont pas tous de la même. */
    var chiffres = [];
    if (e.cb) chiffres.push(chiffre(montant(e.cb[0], e.cb[1]), t("bourse_capi"), e.cb[2]));
    if (e.ca) chiffres.push(chiffre(montant(e.ca[0], e.ca[1]), t("bourse_ca"), e.ca[2]));
    if (e.ef) chiffres.push(chiffre(formater(e.ef[0]), t("bourse_effectifs"), e.ef[1]));
    if (chiffres.length) h.push('<div class="fiche__chiffres">' + chiffres.join("") + "</div>");

    /* Où elle est cotée, et sous quel symbole. */
    var bourses = e.b.map(function (n) { return donnees.bourses[n].n; });
    h.push('<p class="fiche-entreprise__ligne"><b>' + echapper(t("bourse_cotee")) + "</b> " +
      echapper(bourses.join(" · ")) +
      (e.t ? ' <span class="fiche-entreprise__symboles">' + echapper(e.t.join(" · ")) + "</span>" : "") +
      "</p>");

    h.push('<p class="fiche-entreprise__ligne"><b>' + echapper(t("bourse_secteur")) + "</b> " +
      echapper(e.s.map(nomDuSecteur).join(" · ")) + "</p>");

    var liens = [];
    var site = lienSur(e.w);
    if (site) {
      liens.push('<a href="' + echapper(site) + '" target="_blank" rel="noopener">' +
        echapper(t("bourse_site")) + " ↗</a>");
    }
    liens.push('<a href="https://www.wikidata.org/wiki/' + echapper(e.q) +
      '" target="_blank" rel="noopener">' + echapper(t("bourse_wikidata")) + " ↗</a>");
    h.push('<p class="fiche-entreprise__liens">' + liens.join("") + "</p>");

    h.push("</li>");
    panneau.liste.innerHTML = h.join("");
    panneau.liste.scrollTop = 0;

    /* Si le logo manque malgré tout, on remet les initiales plutôt qu'un
       cadre blanc vide. */
    var logo = panneau.liste.querySelector(".fiche-entreprise__logo img");
    if (logo) {
      logo.addEventListener("error", function () {
        var lettres = document.createElement("span");
        lettres.textContent = logo.getAttribute("data-initiales");
        logo.replaceWith(lettres);
      });
    }
  }

  function chiffre(texte, mot, annee) {
    return '<span class="fiche__chiffre"><b class="nombre">' + echapper(texte) + "</b>" +
      "<i>" + echapper(mot) + (annee ? " (" + annee + ")" : "") + "</i></span>";
  }

  /* Sur téléphone, le panneau est un tiroir qui monte du bas. */
  var tiroir = { bouton: null, boite: null };

  function brancherTiroir() {
    tiroir.bouton = document.getElementById("bouton-panneau");
    tiroir.boite = document.getElementById("panneau");
    if (!tiroir.bouton || !tiroir.boite) return;
    tiroir.bouton.textContent = "☰ " + t("bourse_titre");
    tiroir.bouton.addEventListener("click", function () {
      var ouvert = tiroir.boite.classList.toggle("est-ouvert");
      tiroir.bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
      tiroir.bouton.textContent = ouvert ? "✕" : "☰ " + t("bourse_titre");
    });
  }

  /* Un clic sur la carte, sur téléphone, doit montrer la fiche : on ouvre le
     tiroir s'il était fermé. */
  function ouvrirTiroir() {
    if (!tiroir.boite || window.innerWidth > 860) return;
    if (!tiroir.boite.classList.contains("est-ouvert")) tiroir.bouton.click();
  }

  /* --- 8. La légende ------------------------------------------------------- */

  function dessinerLegende() {
    var legende = document.getElementById("legende");
    if (!legende) return;
    legende.innerHTML =
      '<div class="legende__titre">' + echapper(t("legende")) + "</div>" +
      '<div class="legende__ligne"><span class="legende__pastille" style="background:' +
        BLEU + '"></span>' + echapper(t("bourse_leg_exact")) + "</div>" +
      '<div class="legende__ligne"><span class="legende__pastille" style="background:' +
        JAUNE + '"></span>' + echapper(t("bourse_leg_ville")) + "</div>" +
      '<div class="legende__note">' + echapper(t("bourse_leg_zoom")) + "</div>";
  }

  /* --- 9. Démarrage -------------------------------------------------------- */

  function demarrer() {
    var chargement = document.getElementById("chargement");
    chargement.textContent = t("chargement");
    if (panneau.onglets) panneau.onglets.hidden = true;

    Promise.all([charger("data/bourse/entreprises.json"), charger("data/pays.json")])
      .then(function (r) {
        donnees = r[0];
        /* Les noms anglais (« ne », « ve ») ne sont écrits dans le fichier que
           lorsqu'ils diffèrent du français. Sur la page anglaise, on les met à
           la place des noms français une fois pour toutes, en gardant l'autre
           nom de côté (« na ») : une recherche « Groupe Samsung » trouve ainsi
           « Samsung Group », et inversement. */
        if (langue === "en") {
          donnees.entreprises.forEach(function (e) {
            if (e.ne) { e.na = e.n; e.n = e.ne; }
            if (e.ve) e.v = e.ve;
          });
          donnees.bourses.forEach(function (b) { if (b.ne) b.n = b.ne; });
        } else {
          donnees.entreprises.forEach(function (e) { if (e.ne) e.na = e.ne; });
        }
        donnees.entreprises.forEach(function (e) { parQid[e.q] = e; });
        donnees.secteurs.forEach(function (s) { secteursCoches[s.id] = true; });
        donnees.bourses.forEach(function (b, n) { boursesCochees[n] = true; });
        r[1].features.forEach(function (f) { paysParIso[f.properties.iso] = f.properties; });

        panneau.recherche.placeholder = t("bourse_recherche");
        panneau.retour.textContent = t("bourse_retour");
        panneau.retour.addEventListener("click", fermer);
        panneau.recherche.addEventListener("input", dessinerPanneau);
        panneau.source.innerHTML = echapper(t("bourse_source"));

        dessinerPanneau();
        brancherTiroir();
        construireCarte(r[1]);
        chargement.hidden = true;
      })
      .catch(function (e) {
        console.error("[StatsMaps] entreprises :", e);
        chargement.textContent = t("erreur");
      });
  }

  /* Le thème clair/sombre repeint la carte sans la reconstruire. */
  window.addEventListener("statsmaps:theme", function () {
    if (!carte || !carte.isStyleLoaded()) return;
    carte.setPaintProperty("mer", "background-color", couleurDuFond());
    carte.setPaintProperty("pays-fond", "fill-color", couleurCSS("--pays-sans-donnee"));
    carte.setPaintProperty("pays-contour", "line-color", couleurCSS("--contour-pays"));
    repeindreLesRues();
    carte.setPaintProperty("points", "circle-stroke-color", couleurCSS("--panneau"));
    carte.setPaintProperty("choisie", "circle-stroke-color", couleurCSS("--texte"));
    dessinerLegende();
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarrer);
  } else {
    demarrer();
  }
})();
