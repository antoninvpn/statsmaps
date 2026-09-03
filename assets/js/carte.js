/* ==========================================================================
   carte.js — le moteur des cartes de StatsMaps.

   Ce SEUL fichier fait fonctionner les 6 pages de carte (3 cartes × 2 langues).
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
     8. Démarrage
   ========================================================================== */

(function () {
  "use strict";

  /* --- 1. Réglages des cartes -------------------------------------------

     Pour chaque carte : les "tranches" (les seuils qui séparent les couleurs)
     et les couleurs, en thème clair et en thème sombre.
     Il y a toujours 1 couleur de plus que de tranches.

     Ces tranches sont FIXES : elles ne changent pas d'une année à l'autre.
     C'est volontaire : ainsi, quand on fait défiler les années, on voit
     vraiment les pays changer de couleur en s'enrichissant.                */

  var CARTES = {
    "pib-nominal": {
      tranches: [10, 50, 200, 1000, 3000, 10000],
      clair: ["#dceaf7", "#c0d9ed", "#9bc2e0", "#6ba3cf", "#4181b8", "#22609a", "#0d3f75"],
      sombre: ["#10243c", "#17395e", "#1f5285", "#2b71aa", "#4093ca", "#67b6e2", "#9ad8f5"],
    },
    "pib-par-habitant": {
      tranches: [1500, 5000, 15000, 30000, 50000, 70000],
      clair: ["#eadff5", "#d5c0e5", "#c0a2d6", "#a37cc2", "#8459a8", "#653c88", "#452363"],
      sombre: ["#241536", "#3a2154", "#523175", "#6d4796", "#8d64b5", "#b089d2", "#d3b5ea"],
    },
    croissance: {
      /* Échelle "divergente" : rouge quand l'économie recule, bleu quand elle
         avance. Le rouge/bleu est le duo le plus lisible pour les daltoniens.

         Point important : le ZÉRO est une frontière entre le rouge et le bleu,
         et non le milieu d'une tranche. Ainsi un pays à +0,5 % est forcément
         bleu (il a grandi) et un pays à -0,5 % forcément rouge (il a reculé).

         L'intensité augmente en s'éloignant de zéro : plus c'est vif, plus le
         mouvement est fort, dans un sens comme dans l'autre.                */
      tranches: [-4, -1.5, 0, 1.5, 4, 7],
      clair: ["#8f1220", "#cc4436", "#f0a08e", "#c3ddf0", "#7fb4da", "#3d81bd", "#0f4c86"],
      sombre: ["#e05a4a", "#b83a30", "#7d2822", "#1f4a6b", "#2f77a8", "#4aa3d4", "#7fd4f7"],
    },
  };

  /* --- 2. Petits outils --------------------------------------------------- */

  var corps = document.body;
  var idCarte = corps.getAttribute("data-indicateur");
  var langue = corps.getAttribute("data-langue") || "fr";
  var base = corps.getAttribute("data-base") || "./";
  var t = window.StatsMapsT(langue);
  var locale = langue === "fr" ? "fr-FR" : "en-US";
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

  /* Enlève les accents d'un texte : "Viêt Nam" devient "viet nam".
     Sans ça, chercher "vietnam" ou "coree" ne trouverait rien.            */
  function sansAccents(texte) {
    return String(texte)
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();
  }

  /* La valeur affichée partout (classement, infobulle) avec son unité. */
  function valeurLisible(valeur, donnees) {
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

  /* La couleur d'un pays, utilisée pour la petite pastille du classement. */
  function couleurDeLaValeur(valeur) {
    var couleurs = couleursActuelles();
    var index = 0;
    for (var i = 0; i < reglages.tranches.length; i++) {
      if (valeur >= reglages.tranches[i]) index = i + 1;
    }
    return couleurs[index];
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
  var classementActuel = []; // [{iso, nom, valeur, rang}, ...]
  var nomsParIso = {};
  var nomsCherchablesParIso = {}; // les mêmes noms, sans accents
  var isoSurvole = null;
  var infobulle = null;

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
    var etapes = ["step", ["to-number", ["feature-state", "valeur"], 0], couleurs[0]];
    for (var i = 0; i < reglages.tranches.length; i++) {
      etapes.push(reglages.tranches[i], couleurs[i + 1]);
    }
    return [
      "case",
      ["==", ["feature-state", "aDonnee"], 1],
      etapes,
      couleurCSS("--pays-sans-donnee"),
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
    return {
      top: 24,
      right: 24,
      bottom: large ? 130 : 150,
      left: large ? 340 : 24,
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
          "line-color": [
            "case",
            ["boolean", ["feature-state", "survol"], false],
            couleurCSS("--texte"),
            couleurCSS("--contour-pays"),
          ],
          "line-width": [
            "case",
            ["boolean", ["feature-state", "survol"], false],
            1.6,
            0.4,
          ],
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

  function ouvrirInfobulle(iso, position) {
    var ligne = null;
    for (var i = 0; i < classementActuel.length; i++) {
      if (classementActuel[i].iso === iso) { ligne = classementActuel[i]; break; }
    }
    var nom = nomsParIso[iso] || iso;
    var contenu = '<div class="popup__nom">' + echapper(nom) + "</div>";

    if (ligne) {
      contenu +=
        '<div class="popup__valeur nombre">' +
        echapper(valeurLisible(ligne.valeur, donnees)) +
        "</div>" +
        '<div class="popup__detail">' +
        anneeAffichee +
        " · " +
        t("rang") +
        " " +
        ligne.rang +
        " " +
        t("sur") +
        " " +
        classementActuel.length +
        "</div>";
    } else {
      contenu += '<div class="popup__detail">' + t("pas_de_donnee") + "</div>";
    }

    if (infobulle) infobulle.remove();
    infobulle = new maplibregl.Popup({ closeButton: true, maxWidth: "240px" })
      .setLngLat(position)
      .setHTML(contenu)
      .addTo(carte);
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

    var avecDonnee = {};
    classementActuel.forEach(function (element) {
      avecDonnee[element.iso] = true;
      carte.setFeatureState(
        { source: "pays", id: element.iso },
        { valeur: element.valeur, aDonnee: 1 }
      );
    });
    geo.features.forEach(function (pays) {
      var iso = pays.properties.iso;
      if (!avecDonnee[iso]) {
        carte.setFeatureState({ source: "pays", id: iso }, { valeur: 0, aDonnee: 0 });
      }
    });
  }

  function appliquerAnnee(annee) {
    anneeAffichee = annee;
    var clef = String(annee);
    var valeurs = donnees.valeurs;

    /* On prépare le classement des pays qui existent sur la carte. */
    var liste = [];
    geo.features.forEach(function (pays) {
      var iso = pays.properties.iso;
      var parAnnee = valeurs[iso];
      if (parAnnee && typeof parAnnee[clef] === "number") {
        liste.push({ iso: iso, nom: nomsParIso[iso], valeur: parAnnee[clef] });
      }
    });
    liste.sort(function (a, b) { return b.valeur - a.valeur; });
    liste.forEach(function (element, index) { element.rang = index + 1; });
    classementActuel = liste;

    /* On envoie sa valeur à chaque pays de la carte (si elle est prête). */
    appliquerEtatsCarte();

    dessinerClassement();
    majEtiquetteAnnee();
    if (infobulle) { infobulle.remove(); infobulle = null; }
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

    var morceaux = affiches.map(function (element) {
      return (
        '<li data-iso="' + element.iso + '">' +
        '<span class="rang">' + element.rang + "</span>" +
        '<span class="puce" style="background:' + couleurDeLaValeur(element.valeur) + '"></span>' +
        '<span class="nom">' + echapper(element.nom) + "</span>" +
        '<span class="valeur">' + echapper(valeurLisible(element.valeur, donnees)) + "</span>" +
        "</li>"
      );
    });
    liste.innerHTML = morceaux.join("");

    var compteur = document.getElementById("compteur-pays");
    if (compteur) {
      compteur.textContent = classementActuel.length + " " + t("pays_classes");
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

  /* Zoome sur un pays et ouvre son infobulle. */
  function volerVers(iso) {
    var pays = null;
    for (var i = 0; i < geo.features.length; i++) {
      if (geo.features[i].properties.iso === iso) { pays = geo.features[i]; break; }
    }
    if (!pays || !carte) return;

    var limites = new maplibregl.LngLatBounds();
    (function parcourir(coordonnees) {
      if (typeof coordonnees[0] === "number") limites.extend(coordonnees);
      else coordonnees.forEach(parcourir);
    })(pays.geometry.coordinates);

    /* maxZoom assez élevé pour que les tout petits pays (Singapour, Malte,
       Nauru...) remplissent quand même l'écran quand on clique dessus. */
    carte.fitBounds(limites, { padding: 60, maxZoom: 6.5, duration: 700 });
    ouvrirInfobulle(iso, limites.getCenter());
  }

  /* --- 6. La légende ------------------------------------------------------ */

  function dessinerLegende() {
    var boite = document.getElementById("legende");
    if (!boite) return;

    var couleurs = couleursActuelles();
    var unite = donnees.unite[langue] || donnees.unite.fr;

    var cases = couleurs
      .map(function (couleur) {
        return '<span class="legende__case" style="background:' + couleur + '"></span>';
      })
      .join("");

    /* Les repères chiffrés sous la barre. On les affiche tous s'ils sont
       courts ; sinon un sur deux, pour éviter qu'ils se chevauchent.
       Pour la croissance, le repère « 0 » est essentiel : c'est lui qui
       sépare les pays qui reculent de ceux qui avancent.                   */
    var etiquettes = reglages.tranches.map(formaterCourt);
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
      '<div class="legende__titre">' + echapper(donnees.titre[langue] || donnees.titre.fr) +
      " (" + echapper(unite) + ")</div>" +
      '<div class="legende__barre">' + cases + "</div>" +
      '<div class="legende__valeurs nombre"><span></span>' + reperes + "<span></span></div>" +
      '<div class="legende__nd"><i></i>' + t("non_disponible") + "</div>";
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
    carte.setPaintProperty("pays-contour", "line-color", [
      "case",
      ["boolean", ["feature-state", "survol"], false],
      couleurCSS("--texte"),
      couleurCSS("--contour-pays"),
    ]);
    dessinerLegende();
    dessinerClassement();
  });

  /* --- 8. Démarrage -------------------------------------------------------- */

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
          /* On garde aussi le nom dans l'autre langue : ainsi un visiteur
             francophone retrouve "Germany" et l'inverse.                  */
          nomsCherchablesParIso[iso] =
            sansAccents(nom) + " " + sansAccents(pays.properties.en || "") + " " + iso.toLowerCase();
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
          var date = new Date(meta.mis_a_jour_le).toLocaleDateString(locale, {
            day: "numeric", month: "long", year: "numeric",
          });
          source.innerHTML =
            t("source") + t("deux_points") +
            '<a href="' + meta.source_url + '" target="_blank" rel="noopener">' +
            echapper(nomSource) + "</a> — " + t("mis_a_jour") + " " + date;
        }

        brancherClassement();
        brancherAnnees();
        dessinerLegende();
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
