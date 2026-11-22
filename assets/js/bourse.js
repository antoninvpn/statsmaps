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
     5. Le classement des pays
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
  /* Le gris des entreprises dont on ne connaît PAS le siège : elles sont
     posées au centre du pays de leur bourse (choix d'Antonin), pour qu'elles
     existent sur la carte, mais leur point ne dit rien de leur adresse. */
  var GRIS = "#8A94A6";

  /* La couleur d'une entreprise : p = 1 adresse exacte, 0 ville, 2 inconnu. */
  function couleurDe(e) {
    return e.p === 1 ? BLEU : e.p === 2 ? GRIS : JAUNE;
  }

  /* À partir de ce zoom, les logos remplacent les pastilles. */
  var ZOOM_LOGOS = 8;

  /* Le zoom auquel on arrive en ouvrant la fiche d'une entreprise : la rue
     quand l'adresse est exacte, la ville quand elle ne l'est pas. */
  var ZOOM_EXACT = 14;
  var ZOOM_VILLE = 11;

  /* LE FOND DE CARTE. Contrairement aux cartes du PIB, qui coloriaient des
     pays, celle-ci doit montrer OÙ est un siège : les rues, les bâtiments, les
     parcs, les noms des lieux. Elle utilise donc une carte détaillée tirée
     d'OpenStreetMap, servie gratuitement, sans compte ni publicité, par
     OpenFreeMap : « Liberty » en thème clair, « Dark » en thème sombre.
     (Une vraie vue SATELLITE n'existe pas gratuitement : les photos aériennes
     précises appartiennent à des entreprises privées.)
     C'est la seule carte du site qui va chercher son fond ailleurs pendant
     qu'on la regarde. Si OpenFreeMap ne répond pas, la carte s'affiche quand
     même, avec les pays du site en gris. */
  var STYLES = {
    clair: "https://tiles.openfreemap.org/styles/liberty",
    /* En mode sombre aussi, la carte CLAIRE : le fond « Dark » ne plaisait
       pas à Antonin (choix du 23 novembre 2026). Remettre ici
       ".../styles/dark" pour revenir à une carte de nuit. */
    sombre: "https://tiles.openfreemap.org/styles/liberty",
  };

  /* LES FRONTIÈRES. Le fond d'OpenFreeMap dessine celles d'OpenStreetMap, qui
     ne sont pas celles que le site a choisies (Crimée ukrainienne ; Chypre du
     Nord, Somaliland et Sahara occidental fondus dans leur pays, sans trait —
     voir FUSIONS dans scripts/build_geojson.py). On efface donc les siennes, et
     on dessine par-dessus celles du site. On retire aussi les NOMS de ces
     territoires, qu'OpenStreetMap écrit comme des pays. */
  var TERRITOIRES_SANS_NOM = ["Western Sahara", "Somaliland", "Northern Cyprus",
    "Turkish Republic of Northern Cyprus", "Sahrawi Arab Democratic Republic"];

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
  var classementDesPays = []; /* [{iso, n}], du pays qui en a le plus au moins */
  var choisie = null;        /* la Q de l'entreprise dont la fiche est ouverte */
  var vue = "classement";    /* "classement", "fiche" ou "ici" */

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

  /* Le thème du moment, lu sur la couleur de fond de la page : c'est elle que
     theme.js change, que le choix vienne du bouton ou du réglage du téléphone. */
  function themeSombre() {
    var m = /#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})/i.exec(couleurCSS("--fond"));
    if (!m) return false;
    return parseInt(m[1], 16) + parseInt(m[2], 16) + parseInt(m[3], 16) < 300;
  }

  /* Le style d'OpenFreeMap, téléchargé une fois par thème puis gardé. */
  var stylesTelecharges = {};
  function telechargerStyle(theme) {
    if (!stylesTelecharges[theme]) {
      stylesTelecharges[theme] = fetch(STYLES[theme])
        .then(function (r) {
          if (!r.ok) throw new Error(STYLES[theme] + " : " + r.status);
          return r.json();
        })
        .catch(function (e) {
          console.error("[StatsMaps] fond de carte :", e);
          return null;  /* repli : la carte sans fond détaillé */
        });
    }
    return stylesTelecharges[theme];
  }

  /* Dans une étiquette d'OpenFreeMap, le nom « latin » d'un lieu (souvent
     dans la langue du pays : « Deutschland ») est remplacé par son nom dans
     la langue de la page quand OpenStreetMap le connaît (« Allemagne »). */
  function nomDansLaLangue(expression) {
    if (Array.isArray(expression)) {
      if (expression[0] === "get" && expression[1] === "name:latin") {
        return ["coalesce", ["get", "name:" + langue], ["get", "name:latin"]];
      }
      return expression.map(nomDansLaLangue);
    }
    return expression;
  }

  /* Le style complet de la carte : le fond d'OpenFreeMap, retouché, puis par-
     dessus les couches du site (frontières et entreprises). On le refabrique
     entièrement au changement de thème. */
  function fabriquerStyle(fond, geoPays, geoFrontieres) {
    var style = fond ? JSON.parse(JSON.stringify(fond)) : {
      version: 8, sources: {},
      layers: [{ id: "mer", type: "background",
                 paint: { "background-color": couleurCSS("--fond-carte") } }],
    };

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

    style.sources.pays = { type: "geojson", data: geoPays };
    /* Les frontières précises (1:10m), sans les côtes : celles-ci sont
       dessinées par le fond OpenStreetMap, bien plus finement. */
    style.sources.frontieres = { type: "geojson", data: geoFrontieres || geoPays };
    style.sources.entreprises = { type: "geojson", data: entreprisesGeoJSON() };

    if (!fond) {
      style.layers.push({
        id: "pays-fond", type: "fill", source: "pays",
        paint: { "fill-color": couleurCSS("--pays-sans-donnee"), "fill-opacity": 0.55 },
      });
    }

    /* Les frontières du site : un trait fin, discret, qui se fond un peu
       quand on s'approche des rues. */
    style.layers.push({
      id: "pays-contour", type: "line", source: "frontieres",
      paint: {
        "line-color": "#7d8699",  /* la carte est toujours claire */
        "line-width": ["interpolate", ["linear"], ["zoom"], 1, 0.6, 6, 1.3, 12, 2],
        "line-opacity": ["interpolate", ["linear"], ["zoom"], 1, 0.9, 12, 0.75],
      },
    });

    /* Les pastilles : toujours là, à tous les zooms. De près, elles restent
       sous les logos et ne se voient que là où un logo n'a pas trouvé de
       place. Les plus connues sont dessinées en dernier, donc par-dessus. */
    style.layers.push({
      id: "points", type: "circle", source: "entreprises",
      layout: { "circle-sort-key": ["get", "r"] },
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"],
          0.5, 2, 4, 2.8, 8, 4.4, 12, 6, 16, 7],
        "circle-color": ["match", ["get", "p"], 1, BLEU, 2, GRIS, JAUNE],
        "circle-opacity": 0.95,
        "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 2, 0.5, 8, 1.2],
        "circle-stroke-color": "#ffffff",
      },
    });

    /* Les logos, à partir du zoom 8. Le nom de l'image est « logo-Q312 » :
       MapLibre ne l'a pas encore, il le demande à dessinerUnLogo(). Quand deux
       logos se chevauchent, le plus connu gagne (la clef la plus PETITE passe
       en premier, d'où le signe moins). */
    style.layers.push({
      id: "logos", type: "symbol", source: "entreprises",
      minzoom: ZOOM_LOGOS - 0.5,
      layout: {
        "icon-image": ["concat", "logo-", ["get", "q"]],
        "icon-size": ["interpolate", ["linear"], ["zoom"],
          ZOOM_LOGOS - 0.5, 0.6, 12, 0.85, 15, 1],
        "symbol-sort-key": ["-", 0, ["get", "r"]],
        "icon-padding": 1,
      },
      paint: {
        "icon-opacity": ["interpolate", ["linear"], ["zoom"],
          ZOOM_LOGOS - 0.5, 0, ZOOM_LOGOS + 0.3, 1],
      },
    });

    /* Le cercle autour de l'entreprise dont la fiche est ouverte. */
    style.layers.push({
      id: "choisie", type: "circle", source: "entreprises",
      filter: ["==", ["get", "q"], choisie || ""],
      paint: {
        "circle-radius": ["interpolate", ["linear"], ["zoom"], 2, 8, ZOOM_LOGOS, 12, 14, 22],
        "circle-color": "rgba(0,0,0,0)",
        "circle-stroke-width": 2.5,
        "circle-stroke-color": "#16191d",
      },
    });

    return style;
  }

  var geoPaysGarde = null, geoFrontieresGarde = null;

  function construireCarte(geoPays, fond, geoFrontieres) {
    geoPaysGarde = geoPays;
    geoFrontieresGarde = geoFrontieres;
    carte = new maplibregl.Map({
      container: "carte",
      style: fabriquerStyle(fond, geoPays, geoFrontieres),
      bounds: CADRAGE_MONDE,
      fitBoundsOptions: { padding: margesDuCadrage() },
      minZoom: 0.5,
      maxZoom: 18,
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
      customAttribution:
        /* OpenFreeMap, OpenMapTiles et OpenStreetMap n'ont pas à être écrits
           ici : le fond de carte apporte lui-même sa mention, et MapLibre
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
      brancherInteractions();
      dessinerLegende();
    });
  }

  /* Toutes les entreprises vont sur la carte (il n'y a plus de filtres). */
  function entreprisesGeoJSON() {
    return {
      type: "FeatureCollection",
      features: donnees.entreprises.map(function (e) {
        return {
          type: "Feature",
          properties: { q: e.q, p: e.p, r: e.r },
          geometry: { type: "Point", coordinates: [e.x, e.y] },
        };
      }),
    };
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
    c.strokeStyle = couleurDe(e);
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
        if (vue !== "classement") fermer();
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

  /* --- 5. Le classement des pays ----------------------------------------- */

  /* Le nombre d'entreprises cotées par pays, celui de leur siège (demande
     d'Antonin du 22 novembre 2026 : il remplace les cases à cocher des
     secteurs et des places boursières). Calculé une fois, au chargement. */
  function compterParPays() {
    var compte = {};
    donnees.entreprises.forEach(function (e) {
      if (e.i) compte[e.i] = (compte[e.i] || 0) + 1;
    });
    classementDesPays = Object.keys(compte).map(function (iso) {
      return { iso: iso, n: compte[iso] };
    }).sort(function (a, b) {
      return b.n - a.n || nomDuPays(a.iso).localeCompare(nomDuPays(b.iso), langue);
    });
  }

  /* Un clic sur un pays : la carte vole jusqu'à lui (son cadre est écrit
     dans data/pays.json, comme pour la carte des métros). */
  function volerVersPays(iso) {
    var cadre = (paysParIso[iso] || {}).c;
    if (!cadre || !carte) return;
    carte.fitBounds([[cadre[0], cadre[1]], [cadre[2], cadre[3]]],
                    { padding: margesDuCadrage(), maxZoom: 8 });
    fermerTiroirSurTelephone();
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
    return formater(donnees.entreprises.length) + " " + t("bourse_entreprises") +
      " · " + formater(classementDesPays.length) + " " + t("bourse_pays");
  }

  function dessinerPanneau() {
    if (vue !== "classement") return;
    panneau.titre.textContent = t("bourse_titre");
    panneau.soustitre.textContent = compteur();
    panneau.retour.hidden = true;
    panneau.recherche.hidden = false;

    var recherche = sansAccents(panneau.recherche.value.trim());
    if (recherche) {
      dessinerResultats(recherche);
    } else {
      dessinerClassement();
    }
  }

  /* Une liste d'entreprises : celles qu'on cherche, ou celles d'un même
     endroit. Chaque ligne porte la couleur de sa pastille sur la carte. */
  function ligneEntreprise(e) {
    return '<li class="entreprise" data-q="' + echapper(e.q) + '">' +
      '<span class="entreprise__point" style="background:' + couleurDe(e) + '"></span>' +
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
    /* La recherche trouve aussi les pays (« Ukraine »), en tête de liste. */
    var pays = [];
    classementDesPays.forEach(function (p, i) {
      if (sansAccents(nomDuPays(p.iso)).indexOf(recherche) >= 0) pays.push([p, i + 1]);
    });
    if (!trouvees.length && !pays.length) {
      panneau.liste.innerHTML = '<li class="vide">' + echapper(t("bourse_rien_trouve")) + "</li>";
      return;
    }
    panneau.liste.innerHTML = trouvees.map(ligneEntreprise).join("");
    pays.reverse().forEach(function (x) {
      panneau.liste.insertBefore(lignePays(x[0], x[1]), panneau.liste.firstChild);
    });
    brancherLignesEntreprises();
  }

  /* Le classement : un pays par ligne, avec son drapeau et son nombre
     d'entreprises, comme le classement des autres cartes. */
  function dessinerClassement() {
    panneau.liste.innerHTML = "";
    classementDesPays.forEach(function (p, i) {
      panneau.liste.appendChild(lignePays(p, i + 1));
    });
  }

  function lignePays(p, rang) {
    var li = document.createElement("li");
    li.className = "classement__pays";
    li.innerHTML =
      '<span class="rang">' + formater(rang) + "</span>" +
      '<span class="drapeau" aria-hidden="true">' + drapeauDuPays(p.iso) + "</span>" +
      '<span class="nom">' + echapper(nomDuPays(p.iso)) + "</span>" +
      '<span class="valeur">' + formater(p.n) + "</span>";
    li.addEventListener("click", function () { volerVersPays(p.iso); });
    return li;
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
    vue = "classement";
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
        /* La rue pour une adresse exacte, la ville pour un point jaune, et
           le pays entier pour un point gris : zoomer sur le centre d'un pays
           ne montrerait rien. */
        zoom: e.p === 2 ? Math.max(carte.getZoom(), 4.5)
            : Math.max(carte.getZoom(), e.p === 1 ? ZOOM_EXACT : ZOOM_VILLE),
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
    var precision = e.p === 1 ? t("bourse_exact")
      : e.p === 2 ? t("bourse_inconnu")
      : (e.v ? t("bourse_ville").replace("{ville}", e.v) : t("bourse_ville_seule"));
    h.push('<p class="fiche-entreprise__precision"><span class="entreprise__point" style="background:' +
      couleurDe(e) + '"></span>' + echapper(precision) + "</p>");
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
    /* Les entreprises connues de Wikidata ont un identifiant en « Q » ; celles
       que seul OpenFIGI connaît, un identifiant en « F », sans fiche Wikidata. */
    if (/^Q\d+$/.test(e.q)) {
      liens.push('<a href="https://www.wikidata.org/wiki/' + echapper(e.q) +
        '" target="_blank" rel="noopener">' + echapper(t("bourse_wikidata")) + " ↗</a>");
    }
    /* La fiche de l'entreprise au registre mondial GLEIF, d'où vient souvent
       l'adresse de son siège. */
    if (/^[A-Z0-9]{20}$/.test(e.g || "")) {
      liens.push('<a href="https://search.gleif.org/#/record/' + echapper(e.g) +
        '" target="_blank" rel="noopener">' + echapper(t("bourse_gleif")) + " ↗</a>");
    }
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
    tiroir.bouton.textContent = "☰ " + t("bourse_tiroir");
    tiroir.bouton.addEventListener("click", function () {
      var ouvert = tiroir.boite.classList.toggle("est-ouvert");
      tiroir.bouton.setAttribute("aria-expanded", ouvert ? "true" : "false");
      tiroir.bouton.textContent = ouvert ? "✕" : "☰ " + t("bourse_tiroir");
    });
  }

  /* Un clic sur la carte, sur téléphone, doit montrer la fiche : on ouvre le
     tiroir s'il était fermé. */
  function ouvrirTiroir() {
    if (!tiroir.boite || window.innerWidth > 860) return;
    if (!tiroir.boite.classList.contains("est-ouvert")) tiroir.bouton.click();
  }

  /* À l'inverse, un pays choisi dans le classement, sur téléphone : on
     referme le tiroir pour qu'on voie la carte voler jusqu'à lui. */
  function fermerTiroirSurTelephone() {
    if (!tiroir.boite || window.innerWidth > 860) return;
    if (tiroir.boite.classList.contains("est-ouvert")) tiroir.bouton.click();
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
      '<div class="legende__ligne"><span class="legende__pastille" style="background:' +
        GRIS + '"></span>' + echapper(t("bourse_leg_inconnu")) + "</div>" +
      '<div class="legende__note">' + echapper(t("bourse_leg_zoom")) + "</div>";
  }

  /* --- 9. Démarrage -------------------------------------------------------- */

  function demarrer() {
    var chargement = document.getElementById("chargement");
    chargement.textContent = t("chargement");
    if (panneau.onglets) panneau.onglets.hidden = true;

    Promise.all([charger("data/bourse/entreprises.json"), charger("data/pays.json"),
                 telechargerStyle(themeSombre() ? "sombre" : "clair"),
                 charger("data/frontieres.json")])
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
        r[1].features.forEach(function (f) { paysParIso[f.properties.iso] = f.properties; });
        compterParPays();

        panneau.recherche.placeholder = t("bourse_recherche");
        panneau.retour.textContent = t("bourse_retour");
        panneau.retour.addEventListener("click", fermer);
        panneau.recherche.addEventListener("input", dessinerPanneau);
        panneau.source.innerHTML = echapper(t("bourse_source"));

        dessinerPanneau();
        brancherTiroir();
        construireCarte(r[1], r[2], r[3]);
        chargement.hidden = true;
      })
      .catch(function (e) {
        console.error("[StatsMaps] entreprises :", e);
        chargement.textContent = t("erreur");
      });
  }

  /* Le thème clair/sombre repeint la carte sans la reconstruire. */
  /* Le thème clair/sombre change de fond de carte : « Liberty » ou « Dark ».
     On refabrique le style entier ; les entreprises et la fiche
     ouverte sont gardés, et les logos se redessinent d'eux-mêmes. */
  window.addEventListener("statsmaps:theme", function () {
    if (!carte || !geoPaysGarde) return;
    telechargerStyle(themeSombre() ? "sombre" : "clair").then(function (fond) {
      carte.setStyle(fabriquerStyle(fond, geoPaysGarde, geoFrontieresGarde));
      dessinerLegende();
    });
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", demarrer);
  } else {
    demarrer();
  }
})();
