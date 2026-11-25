/* ==========================================================================
   frontieres-fines.js — les frontières précises, quand on s'approche.

   De loin, les cartes détaillées (métros, entreprises) dessinent les frontières
   de data/frontieres.json, légères mais justes à un ou deux kilomètres près :
   le terminus du métro de Lille tombait en Belgique. De près, ce fichier prend
   le relais avec des frontières justes à quelques mètres, téléchargées carré
   par carré dans data/frontieres/ (voir scripts/build_frontieres.py).
   ========================================================================== */

window.StatsMapsFrontieres = (function () {
  "use strict";

  var CARREAU = 5;      /* degrés : la taille des carrés, comme dans le script */
  var ZOOM = 5.5;       /* à partir d'ici, les fines remplacent les grosses */
  var GROSSE = "pays-contour", FINE = "pays-contour-fin", SOURCE = "frontieres-fines";

  var liste = null;     /* les carrés qui existent */
  var traits = {};      /* carré -> ses traits, déjà téléchargés */
  var demandes = {};

  function adresse(nom) {
    var base = document.body.getAttribute("data-base") || "./";
    return base + "data/frontieres/" + nom + ".json";
  }

  function lire(nom) {
    return fetch(adresse(nom)).then(function (r) {
      if (!r.ok) throw new Error(nom + " : " + r.status);
      return r.json();
    });
  }

  function geojson() {
    var tous = [];
    Object.keys(traits).forEach(function (c) { tous = tous.concat(traits[c]); });
    return { type: "Feature", properties: {},
             geometry: { type: "MultiLineString", coordinates: tous } };
  }

  function redessiner(carte) {
    var source = carte.getSource(SOURCE);
    if (source) source.setData(geojson());
  }

  /* Télécharge les carrés visibles qui ne le sont pas encore. */
  function charger(carte) {
    if (carte.getZoom() < ZOOM - 0.5) return;
    if (!liste) {
      if (!demandes.liste) {
        demandes.liste = lire("liste").then(function (l) {
          liste = {};
          l.forEach(function (c) { liste[c] = true; });
          charger(carte);
        }).catch(function (e) {
          console.warn("[StatsMaps] frontières :", e.message);
        });
      }
      return;
    }
    var v = carte.getBounds();
    var x0 = Math.floor(v.getWest() / CARREAU), x1 = Math.floor(v.getEast() / CARREAU);
    var y0 = Math.floor(v.getSouth() / CARREAU), y1 = Math.floor(v.getNorth() / CARREAU);
    for (var x = x0; x <= x1; x++) {
      for (var y = y0; y <= y1; y++) {
        /* La carte se répète vers la droite et la gauche : -190° est 170°. */
        var tour = 360 / CARREAU;
        var nom = (((x + tour / 2) % tour + tour) % tour - tour / 2) + "_" + y;
        if (liste[nom] && !demandes[nom]) demander(carte, nom);
      }
    }
  }

  function demander(carte, nom) {
    demandes[nom] = lire(nom).then(function (t) {
      traits[nom] = t;
      redessiner(carte);
    }).catch(function (e) {
      console.warn("[StatsMaps] frontières :", e.message);
      demandes[nom] = null;
    });
  }

  /* À appeler quand les couches de la carte viennent d'être posées (au
     démarrage, et de nouveau à chaque changement de fond). « avant » : la
     couche sous laquelle glisser les frontières fines. */
  function poser(carte, avant) {
    if (!carte.getLayer(GROSSE) || carte.getLayer(FINE)) return;
    carte.addSource(SOURCE, { type: "geojson", data: geojson(), tolerance: 0.2 });
    carte.addLayer({
      id: FINE, type: "line", source: SOURCE, minzoom: ZOOM,
      layout: { "line-join": "round" },
      paint: {
        "line-color": carte.getPaintProperty(GROSSE, "line-color"),
        "line-width": ["interpolate", ["linear"], ["zoom"], 5, 1.2, 12, 2],
        "line-opacity": 0.85,
      },
    }, avant && carte.getLayer(avant) ? avant : undefined);
    carte.setLayerZoomRange(GROSSE, 0, ZOOM);
    charger(carte);
    if (!carte._frontieresFines) {
      carte._frontieresFines = true;
      carte.on("moveend", function () { charger(carte); });
    }
  }

  return { poser: poser };
})();
