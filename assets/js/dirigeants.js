/* ==========================================================================
   dirigeants.js — la carte de ceux qui dirigent chaque pays.

   Demandée par Antonin le 25 novembre 2026 : le visage de chaque dirigeant à
   l'intérieur de son pays, les pays coloriés selon que c'est une femme ou un
   homme, et à gauche la liste par ancienneté au pouvoir.

   Données : data/dirigeants.json (voir scripts/build_dirigeants.py) et
   data/centres.json (où poser le visage, voir scripts/build_centres.py).

   Déroulé : 1. Réglages — 2. Petits outils — 3. Les visages — 4. La carte —
             5. Le panneau — 6. La bulle — 7. La légende — 8. Démarrage
   ========================================================================== */

(function () {
  "use strict";

  /* --- 1. Réglages --------------------------------------------------------- */

  var CRITERES = {
    /* D'autres critères viendront (âge, origine, religion…) : il suffira d'en
       ajouter un ici, avec ses couleurs, et de le lire dans valeurDe(). */
    genre: {
      valeurs: ["h", "f"],
      clair: { h: "#5b8fd6", f: "#e0689f" },
      sombre: { h: "#3f6fb5", f: "#c94f88" },
    },
  };
  var critere = "genre";

  /* Les visages gagnent en finesse quand un pays devient plus grand qu'eux. */
  var TAILLES = [160, 320, 640, 1000];
  /* Un pays plus petit que ça à l'écran (en pixels) n'a pas encore de visage. */
  var PLUS_PETIT = 13;

  /* --- 2. Petits outils ---------------------------------------------------- */

  var corps = document.body;
  var langue = corps.getAttribute("data-langue") || "fr";
  var base = corps.getAttribute("data-base") || "./";
  var textes = (window.StatsMapsTextes || {})[langue] || (window.StatsMapsTextes || {}).fr || {};
  function t(clef) { return textes[clef] !== undefined ? textes[clef] : clef; }

  function echapper(texte) {
    return String(texte == null ? "" : texte).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function sansAccents(texte) {
    return String(texte || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  }
  function couleurCSS(nom) {
    return getComputedStyle(document.documentElement).getPropertyValue(nom).trim();
  }
  function themeSombre() {
    return !!(window.StatsMapsTheme && window.StatsMapsTheme.actuel() === "dark");
  }
  function charger(chemin) {
    return fetch(base + chemin).then(function (r) {
      if (!r.ok) throw new Error(chemin + " : " + r.status);
      return r.json();
    });
  }
  function dateEcrite(iso) {
    if (!iso) return t("dir_date_inconnue");
    var p = iso.split("-");
    return new Intl.DateTimeFormat(langue, { day: "numeric", month: "long", year: "numeric",
      timeZone: "UTC" }).format(new Date(Date.UTC(+p[0], +p[1] - 1, +p[2])));
  }
  /* Le temps passé depuis une date, en années, mois et jours pleins. */
  function ecart(iso, jour) {
    var p = iso.split("-").map(Number);
    var an = jour.getFullYear() - p[0], mois = jour.getMonth() + 1 - p[1], j = jour.getDate() - p[2];
    if (j < 0) {
      mois--;
      /* Le dernier « jour anniversaire » : le même quantième le mois d'avant,
         ou le dernier jour de ce mois s'il est plus court (31 -> 28 février). */
      var dernier = new Date(jour.getFullYear(), jour.getMonth(), 0).getDate();
      j = jour.getDate() + dernier - Math.min(p[2], dernier);
    }
    if (mois < 0) { mois += 12; an--; }
    return [an, mois, j];
  }

  /* « 1 an, 3 mois et 17 jours ». Ce qui vaut zéro n'est pas écrit. */
  function duree(iso) {
    if (!iso) return "";
    var e = ecart(iso, new Date());
    if (e[0] < 0) return "";
    var mots = ["an", "mois", "jour"].map(function (u, n) {
      if (!e[n]) return "";
      return e[n] + "\u00a0" + t("dir_" + u + (e[n] > 1 ? "s" : ""));
    }).filter(Boolean);
    if (!mots.length) return t("dir_aujourdhui");
    var fin = mots.pop();
    return mots.length ? mots.join(", ") + " " + t("dir_et") + " " + fin : fin;
  }

  var carte = null, dirigeants = {}, paysParIso = {}, formes = {}, centres = {};
  var bulle = null, choisi = null, prete = false;  /* prete : la carte est dessinée */

  function valeurDe(d) { return critere === "genre" ? d.g : null; }
  function couleurDe(d) {
    var c = CRITERES[critere][themeSombre() ? "sombre" : "clair"];
    return (d && c[valeurDe(d)]) || couleurCSS("--pays-sans-donnee");
  }
  function nomDuPays(iso) { return (paysParIso[iso] || {})[langue] || iso; }
  function nom(d) { return d[langue] || d.en; }
  function fichierPhoto(d, grande) {
    return base + "data/dirigeants/" + (grande ? "g-" : "") + d.q + ".jpg";
  }

  /* --- 3. Les visages ------------------------------------------------------ */

  /* Chaque visage est dessiné sur une petite toile de la forme du pays, puis
     la toile est posée sur la carte. Le fond de la toile est la couleur du
     pays ; la photo s'y fond en douceur, pour qu'un pays tout en longueur
     (le Chili) montre un vrai visage et pas une tranche de joue. */

  function monde(x, y) {          /* Mercator 0..1 -> longitude, latitude */
    return [x * 360 - 180,
            Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180 / Math.PI];
  }
  function mercator(p) {
    var lat = Math.max(-85, Math.min(85, p[1])) * Math.PI / 180;
    return [(p[0] + 180) / 360,
            0.5 - Math.log(Math.tan(Math.PI / 4 + lat / 2)) / (2 * Math.PI)];
  }

  var visages = {};   /* iso -> { toile, taille, image, charge } */

  function chargerImage(adresse) {
    return new Promise(function (oui, non) {
      var i = new Image();
      i.onload = function () { oui(i); };
      i.onerror = non;
      i.src = adresse;
    });
  }

  function dessinerVisage(iso, taille, image) {
    var d = dirigeants[iso.slice(0, 3)], c = centres[iso], anneaux = formes[iso];
    var large = c.b[2] - c.b[0], haut = c.b[3] - c.b[1];
    var ech = taille / Math.max(large, haut);
    var v = visages[iso];
    var toile = v && v.toile || document.createElement("canvas");
    toile.width = Math.max(8, Math.round(large * ech));
    toile.height = Math.max(8, Math.round(haut * ech));
    var x = toile.getContext("2d");

    /* La forme du pays : tout ce qui suit est dessiné dedans. */
    x.beginPath();
    anneaux.forEach(function (a) {
      a.forEach(function (p, n) {
        var px = (p[0] - c.b[0]) * ech, py = (p[1] - c.b[1]) * ech;
        if (n) x.lineTo(px, py); else x.moveTo(px, py);
      });
      x.closePath();
    });
    x.clip("evenodd");
    x.fillStyle = couleurDe(d);
    x.fillRect(0, 0, toile.width, toile.height);

    var cx = (c.c[0] - c.b[0]) * ech, cy = (c.c[1] - c.b[1]) * ech, r = c.r * ech;
    /* Pas de photo libre : la calligraphie de son nom, sur fond blanc. Le nom
       occupe les six dixièmes de l'image, et doit tenir dans le cercle. */
    if (d.photo.calligraphie) {
      x.fillStyle = "#ffffff";
      x.fillRect(0, 0, toile.width, toile.height);
      var cote = r * 1.9 / 0.62;
      x.drawImage(image, cx - cote / 2, cy - cote / 2, cote, cote);
      return toile;
    }
    var f = (d.photo && d.photo.visage) || [0.5, 0.36, 0.42, 0.34];
    /* Le visage (du menton au front) occupe presque tout le cercle. */
    var zoom = (r * 1.5) / (f[3] * image.height);
    /* Si le pays est assez trapu, on agrandit jusqu'à ce que la photo le
       couvre en entier, sans dépasser un visage un peu plus grand que le cercle. */
    var gauche = cx / (f[0] * image.width), droite = (toile.width - cx) / ((1 - f[0]) * image.width);
    var dessus = cy / (f[1] * image.height), dessous = (toile.height - cy) / ((1 - f[1]) * image.height);
    var couvre = Math.max(gauche, droite, dessus, dessous);
    zoom = Math.max(zoom, Math.min(couvre, zoom * 1.35));
    var l = image.width * zoom, h = image.height * zoom;
    var ox = cx - f[0] * l, oy = cy - f[1] * h;

    /* La photo, bords fondus. */
    var calque = document.createElement("canvas");
    calque.width = toile.width; calque.height = toile.height;
    var y = calque.getContext("2d");
    y.drawImage(image, ox, oy, l, h);
    if (couvre > zoom * 1.02) {
      y.globalCompositeOperation = "destination-in";
      var fondu = Math.max(l, h) * 0.12;
      [[ox, 0, ox + fondu, 0], [ox + l, 0, ox + l - fondu, 0],
       [0, oy, 0, oy + fondu], [0, oy + h, 0, oy + h - fondu]].forEach(function (g) {
        var d2 = y.createLinearGradient(g[0], g[1], g[2], g[3]);
        d2.addColorStop(0, "rgba(0,0,0,0)");
        d2.addColorStop(1, "rgba(0,0,0,1)");
        y.fillStyle = d2;
        y.fillRect(0, 0, toile.width, toile.height);
      });
    }
    x.drawImage(calque, 0, 0);
    return toile;
  }

  function coins(iso) {
    var b = centres[iso].b;
    return [monde(b[0], b[1]), monde(b[2], b[1]), monde(b[2], b[3]), monde(b[0], b[3])];
  }

  function pixelsDuPays(iso) {
    var b = centres[iso].b;
    return Math.max(b[2] - b[0], b[3] - b[1]) * 512 * Math.pow(2, carte.getZoom());
  }

  function estVisible(iso) {
    var v = carte.getBounds(), b = centres[iso].b;
    var a = monde(b[0], b[3]), c = monde(b[2], b[1]);
    /* La carte se répète : on regarde aussi la copie de gauche et de droite. */
    return [-360, 0, 360].some(function (tour) {
      return a[0] + tour < v.getEast() && c[0] + tour > v.getWest() &&
             a[1] < v.getNorth() && c[1] > v.getSouth();
    });
  }

  /* Pose les visages qui manquent, et affine ceux qui sont devenus trop gros
     pour leur toile. Appelée à chaque fin de mouvement. */
  function mettreLesVisages() {
    var densite = Math.min(2, window.devicePixelRatio || 1);
    Object.keys(formes).forEach(function (iso) {
      /* « DNK+ » : un second visage pour le Danemark, au Groenland. */
      var d = dirigeants[iso.slice(0, 3)], v = visages[iso];
      if (!d || !d.photo || !formes[iso] || !centres[iso]) return;
      var px = pixelsDuPays(iso);
      if (px < PLUS_PETIT || !estVisible(iso)) return;
      var taille = TAILLES[TAILLES.length - 1];
      for (var n = TAILLES.length - 1; n >= 0; n--) {
        if (TAILLES[n] >= px * densite * 0.8) taille = TAILLES[n];
      }
      if (v && (v.enCours || v.taille >= taille)) return;
      var grande = taille > 320;
      if (!v) v = visages[iso] = { taille: 0 };
      v.enCours = true;
      chargerImage(fichierPhoto(d, grande)).then(function (image) {
        v.image = image;
        poserVisage(iso, taille);
      }).catch(function () { /* photo absente : le pays garde sa couleur */ })
        .then(function () { v.enCours = false; });
    });
  }

  function poserVisage(iso, taille) {
    var v = visages[iso];
    v.toile = dessinerVisage(iso, taille, v.image);
    v.taille = taille;
    var id = "visage-" + iso;
    if (carte.getLayer(id)) carte.removeLayer(id);
    if (carte.getSource(id)) carte.removeSource(id);
    carte.addSource(id, { type: "canvas", canvas: v.toile, animate: false, coordinates: coins(iso) });
    carte.addLayer({ id: id, type: "raster", source: id,
      paint: { "raster-fade-duration": 0, "raster-resampling": "linear" } }, "pays-contour");
  }

  /* --- 4. La carte --------------------------------------------------------- */

  var CADRAGE_MONDE = [[-179, -56], [179, 81]];

  function marges() {
    var large = window.innerWidth > 860;
    return { top: 24, right: 24, bottom: large ? 60 : 90, left: large ? 350 : 24 };
  }

  function regleCouleur() {
    var regle = ["match", ["get", "iso"]];
    Object.keys(dirigeants).forEach(function (iso) { regle.push(iso, couleurDe(dirigeants[iso])); });
    regle.push(couleurCSS("--pays-sans-donnee"));
    return regle;
  }

  function construireCarte(geo) {
    carte = new maplibregl.Map({
      container: "carte",
      style: {
        version: 8,
        sources: { pays: { type: "geojson", data: geo, promoteId: "iso" } },
        layers: [
          { id: "pays-fond", type: "fill", source: "pays",
            paint: { "fill-color": regleCouleur() } },
          { id: "pays-contour", type: "line", source: "pays",
            paint: {
              "line-color": ["case",
                ["boolean", ["feature-state", "choisi"], false], couleurCSS("--texte"),
                ["boolean", ["feature-state", "survol"], false], couleurCSS("--texte"),
                couleurCSS("--contour-pays")],
              "line-width": ["case",
                ["boolean", ["feature-state", "choisi"], false], 2.4,
                ["boolean", ["feature-state", "survol"], false], 1.6, 0.6],
            } },
        ],
      },
      bounds: CADRAGE_MONDE,
      fitBoundsOptions: { padding: marges() },
      minZoom: 0.5, maxZoom: 9,
      attributionControl: false, dragRotate: false, pitchWithRotate: false,
    });
    carte.touchZoomRotate.disableRotation();
    carte.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    carte.addControl(new maplibregl.AttributionControl({
      compact: true,
      customAttribution: '<a href="https://www.naturalearthdata.com/">Natural Earth</a> · ' +
        '<a href="https://en.wikipedia.org/wiki/List_of_current_heads_of_state_and_government">Wikipedia</a> · ' +
        '<a href="https://commons.wikimedia.org/">Wikimedia Commons</a>',
    }), "bottom-right");
    carte.on("error", function (e) {
      console.error("[StatsMaps] carte :", (e && e.error && e.error.message) || e);
    });
    carte.on("load", function () {
      prete = true;
      mettreLesVisages();
      brancher();
      document.getElementById("chargement").classList.add("est-fini");
    });
    carte.on("moveend", function () { if (prete) mettreLesVisages(); });
  }

  function brancher() {
    var survole = null;
    function survol(iso) {
      if (survole === iso) return;
      if (survole) carte.setFeatureState({ source: "pays", id: survole }, { survol: false });
      survole = iso;
      if (iso) carte.setFeatureState({ source: "pays", id: iso }, { survol: true });
    }
    carte.on("mousemove", "pays-fond", function (e) {
      var iso = e.features[0].properties.iso;
      carte.getCanvas().style.cursor = dirigeants[iso] ? "pointer" : "";
      survol(dirigeants[iso] ? iso : null);
    });
    carte.on("mouseleave", "pays-fond", function () {
      carte.getCanvas().style.cursor = "";
      survol(null);
    });
    carte.on("click", function (e) {
      var f = carte.queryRenderedFeatures(e.point, { layers: ["pays-fond"] })[0];
      if (f && dirigeants[f.properties.iso]) choisir(f.properties.iso, e.lngLat, false);
      else fermer();
    });
  }

  function fermer() {
    if (bulle) { var b = bulle; bulle = null; b.remove(); }
    if (choisi) carte.setFeatureState({ source: "pays", id: choisi }, { choisi: false });
    choisi = null;
    marquer();
  }

  function choisir(iso, ou, voler) {
    if (!prete) return;
    fermer();
    choisi = iso;
    carte.setFeatureState({ source: "pays", id: iso }, { choisi: true });
    var c = centres[iso];
    /* Depuis la liste : la bulle au-dessus du pays, pour ne pas cacher le visage. */
    var place = ou || (c && monde(c.c[0], c.b[1]));
    if (voler && c) {
      var a = monde(c.b[0], c.b[3]), z = monde(c.b[2], c.b[1]);
      carte.fitBounds([a, z], { padding: Object.assign(marges(), { top: 190 }), maxZoom: 6, duration: 900 });
    }
    if (place) ouvrirBulle(iso, place);
    marquer();
    var boite = document.getElementById("panneau");
    if (voler && window.innerWidth <= 860) basculerTiroir(false);
    else if (boite) {
      var li = document.querySelector('[data-iso="' + iso + '"]');
      /* On fait défiler la LISTE seule : scrollIntoView() peut faire glisser
         toute la page avec elle. */
      if (li && !voler) {
        var haut = li.getBoundingClientRect().top - liste.getBoundingClientRect().top;
        liste.scrollTo({ top: liste.scrollTop + haut - liste.clientHeight / 2 + 30, behavior: "smooth" });
      }
    }
  }

  /* --- 5. Le panneau ------------------------------------------------------- */

  var liste = document.getElementById("classement");
  var recherche = document.getElementById("recherche");

  function dessinerListe() {
    var q = sansAccents(recherche.value.trim());
    var isos = Object.keys(dirigeants).sort(function (a, b) {
      var x = dirigeants[a].depuis || "9999", y = dirigeants[b].depuis || "9999";
      return x < y ? -1 : x > y ? 1 : nomDuPays(a).localeCompare(nomDuPays(b), langue);
    });
    var html = "";
    isos.forEach(function (iso, n) {
      var d = dirigeants[iso];
      if (q && sansAccents(nomDuPays(iso) + " " + d.fr + " " + d.en).indexOf(q) < 0) return;
      html += '<li class="dirigeant" data-iso="' + iso + '" style="--couleur-pays:' + couleurDe(d) + '">' +
        '<span class="rang">' + (d.depuis ? n + 1 : "–") + "</span>" +
        '<span class="drapeau" aria-hidden="true">' +
          window.StatsMapsDrapeau((paysParIso[iso] || {}).d) + "</span>" +
        '<span class="nom"><b>' + echapper(nom(d)) + "</b><i>" + echapper(nomDuPays(iso)) + "</i><i>" + echapper(duree(d.depuis)) + "</i></span>" +
        '<span class="valeur">' + echapper(dateEcrite(d.depuis)) + "</span></li>";
    });
    liste.innerHTML = html || '<li class="vide">' + echapper(t("aucun_resultat")) + "</li>";
    marquer();
  }

  function marquer() {
    Array.prototype.forEach.call(liste.querySelectorAll("[data-iso]"), function (li) {
      li.classList.toggle("est-choisi", li.getAttribute("data-iso") === choisi);
    });
  }

  function basculerTiroir(ouvert) {
    var boite = document.getElementById("panneau"), b = document.getElementById("bouton-panneau");
    boite.classList.toggle("est-ouvert", ouvert);
    b.setAttribute("aria-expanded", ouvert ? "true" : "false");
    b.textContent = ouvert ? "✕" : "☰ " + t("dir_titre");
  }

  function preparerPanneau() {
    var n = Object.keys(dirigeants);
    document.getElementById("compteur-pays").textContent =
      t("dir_compteur").replace("{n}", n.length);
    recherche.placeholder = t("dir_recherche");
    recherche.addEventListener("input", dessinerListe);
    liste.addEventListener("click", function (e) {
      var li = e.target.closest("[data-iso]");
      if (li) choisir(li.getAttribute("data-iso"), null, true);
    });
    document.getElementById("source").innerHTML = t("dir_source");
    document.getElementById("criteres").hidden = true;
    document.getElementById("bouton-panneau").addEventListener("click", function () {
      basculerTiroir(!document.getElementById("panneau").classList.contains("est-ouvert"));
    });
    basculerTiroir(false);
    dessinerListe();
  }

  /* --- 6. La bulle --------------------------------------------------------- */

  function ouvrirBulle(iso, place) {
    var d = dirigeants[iso];
    var sansPhoto = d.photo && d.photo.calligraphie;
    var wiki = d.wiki && (d.wiki[langue] || d.wiki.en);
    var credit = d.photo
      ? '<div class="dirigeant__credit">' +
          (sansPhoto ? echapper(t("dir_sans_photo")) +
            (wiki ? ' <a href="' + echapper(wiki) + '" target="_blank" rel="noopener">' +
              echapper(t("dir_voir_wiki")) + "</a>" : "") + "<br>" : "") +
          echapper(t(sansPhoto ? "dir_calligraphie" : "dir_photo")) + " " +
          echapper(d.photo.auteur || "Wikimedia Commons") + ' · <a href="' + echapper(d.photo.page) +
          '" target="_blank" rel="noopener">' + echapper(d.photo.licence || "Commons") + "</a></div>"
      : "";
    bulle = new maplibregl.Popup({ closeButton: true, offset: 8, maxWidth: "300px" })
      .setLngLat(place)
      .setHTML('<div class="dirigeant__bulle">' +
        (d.photo ? '<img src="' + echapper(fichierPhoto(d, true)) + '" alt="" width="84" height="104"' +
          (sansPhoto ? ' class="est-calligraphie"' : "") +
          (d.photo.visage ? ' style="object-position:' + Math.round(d.photo.visage[0] * 100) + "% " +
            Math.round(d.photo.visage[1] * 80) + '%"' : "") + ">" : "") +
        '<div><div class="popup__nom">' + echapper(nom(d)) + "</div>" +
        '<div class="dirigeant__titre">' + echapper(d.titre[langue] || d.titre.en) + "</div>" +
        '<div class="dirigeant__pays"><span class="drapeau">' +
          window.StatsMapsDrapeau((paysParIso[iso] || {}).d) + "</span> " + echapper(nomDuPays(iso)) + "</div>" +
        '<div class="popup__detail">' + (d.depuis
          ? echapper(t("dir_depuis").replace("{d}", dateEcrite(d.depuis))) + "<br>" + echapper(duree(d.depuis))
          : echapper(t("dir_date_inconnue"))) + "</div></div></div>" + credit)
      .addTo(carte);
    bulle.on("close", function () { if (bulle) fermer(); });
  }

  /* --- 7. La légende ------------------------------------------------------- */

  function dessinerLegende() {
    var compte = { h: 0, f: 0 };
    Object.keys(dirigeants).forEach(function (iso) { compte[dirigeants[iso].g] = (compte[dirigeants[iso].g] || 0) + 1; });
    var c = CRITERES[critere][themeSombre() ? "sombre" : "clair"];
    document.getElementById("legende").innerHTML =
      '<div class="legende__titre">' + echapper(t("dir_leg_titre")) + "</div>" +
      CRITERES[critere].valeurs.map(function (v) {
        return '<div class="legende__ligne"><span class="legende__pastille" style="background:' + c[v] +
          '"></span>' + echapper(t("dir_leg_" + v)) + " <b>" + (compte[v] || 0) + "</b></div>";
      }).join("") +
      '<div class="legende__nd"><i></i>' + echapper(t("dir_leg_nd")) + "</div>" +
      '<div class="legende__note">' + echapper(t("dir_leg_note")) + "</div>";
  }

  /* --- 8. Démarrage -------------------------------------------------------- */

  function demarrer() {
    var chargement = document.getElementById("chargement");
    chargement.textContent = t("chargement");
    Promise.all([charger("data/dirigeants.json"), charger("data/pays.json"),
                 charger("data/centres.json")]).then(function (r) {
      dirigeants = r[0].pays;
      centres = r[2];
      r[1].features.forEach(function (f) {
        var iso = f.properties.iso;
        paysParIso[iso] = f.properties;
        var g = f.geometry;
        [iso, iso + "+"].forEach(function (cle) {
          if (!centres[cle]) return;
          var morceau = g.type === "Polygon" ? g.coordinates : g.coordinates[centres[cle].m];
          formes[cle] = morceau.map(function (a) { return a.map(mercator); });
        });
      });
      preparerPanneau();
      dessinerLegende();
      construireCarte(r[1]);
    }).catch(function (e) {
      console.error("[StatsMaps] dirigeants :", e);
      chargement.textContent = t("erreur");
    });
  }

  window.addEventListener("statsmaps:theme", function () {
    if (!prete) return;
    carte.setPaintProperty("pays-fond", "fill-color", regleCouleur());
    var normal = couleurCSS("--contour-pays"), fort = couleurCSS("--texte");
    carte.setPaintProperty("pays-contour", "line-color", ["case",
      ["boolean", ["feature-state", "choisi"], false], fort,
      ["boolean", ["feature-state", "survol"], false], fort, normal]);
    Object.keys(visages).forEach(function (iso) {
      if (visages[iso].image) poserVisage(iso, visages[iso].taille);
    });
    dessinerLegende();
    dessinerListe();
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", demarrer);
  else demarrer();
})();
