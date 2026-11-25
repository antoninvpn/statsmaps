/* ==========================================================================
   fond-satellite.js — le fond SATELLITE des cartes détaillées.

   Des photos aériennes et satellite (Esri, « World Imagery »), avec par-dessus
   les routes et les noms des lieux dans la langue de la page. Choix d'Antonin
   du 24 novembre 2026, à la place du fond OpenStreetMap.

   Il faut une clé : elle est dans assets/js/cle-esri.js. Offre gratuite
   d'Esri (ArcGIS Location Platform) : 2 millions d'images par mois, sites qui
   gagnent de l'argent autorisés, mention d'Esri obligatoire sur la carte (elle
   est posée par ajouterMention(), plus bas : ne pas la retirer).

   Si Esri ne répond pas (panne, quota du mois épuisé, clé arrivée à sa date de
   fin), telecharger() échoue, et la carte reprend son fond OpenStreetMap.
   ========================================================================== */

window.StatsMapsSatellite = (function () {
  "use strict";

  var SERVICE = "https://basemapstyles-api.arcgis.com/arcgis/rest/services/styles/v2/styles/arcgis/imagery";

  /* LES FRONTIÈRES. Celles d'Esri ne sont pas celles que le site a choisies
     (voir TERRITOIRES_SANS_NOM dans bourse.js) : on les retire, et chaque carte
     dessine celles du site. On retire aussi les noms des territoires disputés. */
  var COUCHES_RETIREES = ["Boundary line", "Disputed label point"];

  var TERRITOIRES_SANS_NOM = [
    "Western Sahara", "Sahara occidental", "Somaliland", "Northern Cyprus",
    "Chypre du Nord", "Turkish Republic of Northern Cyprus"];

  /* Les traits des routes, des voies ferrées et des bateaux. La carte des
     métros les retire (leurs noms restent) : orange et rouges, on les prendrait
     pour des lignes de métro. */
  var TRAITS_RETIRABLES = /^(Road|Railroad|Ferry)/;

  function preparer(style, sansRoutes) {
    Object.keys(style.sources).forEach(function (nom) {
      var source = style.sources[nom];
      /* « url » désigne une fiche descriptive que MapLibre ne sait pas lire ;
         l'adresse des images (« tiles ») suffit. */
      delete source.url;
      delete source.copyrightText;
    });
    style.layers = style.layers.filter(function (couche) {
      var origine = couche["source-layer"] || "";
      /* Les noms de gares d'Esri feraient double emploi avec les stations. */
      if (sansRoutes && couche.id === "Point of interest/Rail station") return false;
      if (sansRoutes && couche.type === "line" && TRAITS_RETIRABLES.test(origine)) {
        return false;
      }
      return COUCHES_RETIREES.indexOf(origine) < 0;
    }).map(function (couche) {
      if (/^Admin[01] /.test(couche["source-layer"] || "")) {
        var filtre = ["all"];
        if (couche.filter) filtre.push(couche.filter);
        ["_name", "_name_fr", "_name_en", "_name_local"].forEach(function (champ) {
          filtre.push(["!in", champ].concat(TERRITOIRES_SANS_NOM));
        });
        couche.filter = filtre;
      }
      return couche;
    });
    style.satellite = true;  /* pour que la carte sache sur quel fond elle est */
    return style;
  }

  function telecharger(langue, sansRoutes) {
    var cle = window.StatsMapsCleEsri || "";
    if (cle.length < 40) return Promise.reject(new Error("pas de clé Esri"));
    return fetch(SERVICE + "?language=" + encodeURIComponent(langue) +
                 "&token=" + encodeURIComponent(cle))
      .then(function (r) {
        /* L'adresse contient la clé : on ne l'écrit pas dans l'erreur. */
        if (!r.ok) throw new Error("Esri : " + r.status);
        return r.json();
      })
      .then(function (style) { return preparer(style, sansRoutes); });
  }

  /* « Powered by Esri », toujours visible, comme Esri le demande. Les sources
     des photos, bien plus longues, sont dans l'étiquette à côté, que MapLibre
     replie quand on bouge la carte (le bouton « i » la rouvre). Sur un petit
     écran, elle couvrirait le bas de la carte : elle démarre repliée. */
  function ajouterMention() {
    var zone = document.querySelector(".zone-carte");
    if (!zone || zone.querySelector(".mention-esri")) return;
    var mention = document.createElement("div");
    mention.className = "mention-esri";
    mention.innerHTML = 'Powered by <a href="https://www.esri.com/">Esri</a>';
    zone.appendChild(mention);
    if (window.matchMedia("(max-width: 860px)").matches) {
      var etiquette = zone.querySelector(".maplibregl-ctrl-attrib");
      if (etiquette) {
        etiquette.classList.remove("maplibregl-compact-show");
        etiquette.removeAttribute("open");
      }
    }
  }

  return { telecharger: telecharger, ajouterMention: ajouterMention };
})();
