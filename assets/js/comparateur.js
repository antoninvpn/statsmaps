/* ==========================================================================
   comparateur.js — l'onglet « Comparer » du panneau de gauche.

   Il répond à une question que le classement ne sait pas poser :
   « De combien la France est-elle derrière l'Allemagne — et depuis quand ? »

   Deux pays côte à côte, l'écart entre eux pour l'année affichée, et surtout
   un petit graphique de cet écart de 1980 à 2031 : c'est là qu'on voit un
   pays rattraper l'autre, le dépasser, ou décrocher.

   CE FICHIER NE SAIT RIEN DU SITE. Il ne lit aucune donnée, ne connaît ni les
   langues ni les couleurs : carte.js lui passe tout au démarrage. C'est ce qui
   permet de le faire fonctionner à l'identique sur les cinq cartes, alors
   qu'un écart s'y mesure de trois façons différentes (en %, en points de
   croissance, ou en années).

   Il fabrique lui-même son HTML dans le panneau : les pages n'ont donc rien
   à contenir de particulier, juste à charger ce fichier.

   Déroulé du fichier :
     1. L'état et les réglages reçus de carte.js
     2. La fabrication du panneau (onglets compris)
     3. Le choix des deux pays
     4. Le calcul de l'écart et de son histoire
     5. Le graphique
     6. L'affichage
   ========================================================================== */

(function () {
  "use strict";

  /* --- 1. L'état ---------------------------------------------------------- */

  var reglages = null;   // tout ce que carte.js nous a passé
  var t = null;          // les textes de la langue de la page
  var paysA = null;      // le pays de référence : celui qui sert de base
  var paysB = null;      // le pays mesuré, dont on lit l'écart
  var fenteActive = "a"; // la fente que remplira le prochain pays choisi
  var anneeAffichee = null;
  var ongletOuvert = false;

  /* Les éléments fabriqués par ce fichier, retenus une fois pour toutes. */
  var boite = null;          // le contenu de l'onglet
  var ongletClassement = null;
  var ongletComparer = null;

  /* --- 2. La fabrication du panneau --------------------------------------- */

  /* Les deux onglets, glissés dans l'en-tête du panneau juste avant le champ
     de recherche du classement. */
  function fabriquerOnglets(entete, recherche) {
    var barre = document.createElement("div");
    barre.className = "onglets";
    barre.setAttribute("role", "tablist");

    ongletClassement = bouton(t("classement"), true);
    ongletComparer = bouton(t("onglet_comparer"), false);
    barre.appendChild(ongletClassement);
    barre.appendChild(ongletComparer);

    /* Avant le champ de recherche : celui-ci appartient au classement et
       disparaît avec lui. */
    entete.insertBefore(barre, recherche || null);

    ongletClassement.addEventListener("click", function () { ouvrir(false); });
    ongletComparer.addEventListener("click", function () { ouvrir(true); });

    function bouton(texte, choisi) {
      var element = document.createElement("button");
      element.type = "button";
      element.className = "onglet";
      element.setAttribute("role", "tab");
      element.setAttribute("aria-selected", choisi ? "true" : "false");
      element.textContent = texte;
      return element;
    }
  }

  /* Bascule entre le classement et le comparateur. */
  function ouvrir(comparer) {
    ongletOuvert = comparer;
    var liste = document.getElementById("classement");
    var recherche = document.getElementById("recherche");

    if (liste) liste.hidden = comparer;
    if (recherche) recherche.hidden = comparer;
    boite.hidden = !comparer;
    ongletClassement.setAttribute("aria-selected", comparer ? "false" : "true");
    ongletComparer.setAttribute("aria-selected", comparer ? "true" : "false");

    /* À l'ouverture, si un pays est déjà choisi sur la carte, il prend la
       première fente : on évite au visiteur de le désigner deux fois. */
    if (comparer) {
      if (!paysA && reglages.paysChoisi && reglages.paysChoisi()) {
        paysA = reglages.paysChoisi();
        fenteActive = "b";
      }
      dessiner();
    }
  }

  /* --- 3. Le choix des deux pays ------------------------------------------ */

  /* La liste des pays qui ont au moins un chiffre sur cette carte, rangée par
     ordre alphabétique de la langue affichée. */
  function paysDisponibles() {
    var liste = [];
    for (var iso in reglages.donnees.valeurs) {
      if (reglages.pays.noms[iso]) liste.push(iso);
    }
    liste.sort(function (a, b) {
      return reglages.pays.noms[a].localeCompare(reglages.pays.noms[b], reglages.locale);
    });
    return liste;
  }

  /* Pose un pays dans la fente active, puis passe la main à l'autre fente :
     deux clics de suite sur la carte remplissent A puis B, sans rien régler. */
  function choisirPays(iso) {
    if (!iso) return;
    if (fenteActive === "a") {
      if (iso === paysB) paysB = paysA;
      paysA = iso;
      fenteActive = "b";
    } else {
      if (iso === paysA) paysA = paysB;
      paysB = iso;
      fenteActive = "a";
    }
    if (ongletOuvert) dessiner();
  }

  /* --- 4. L'écart et son histoire ----------------------------------------- */

  /* L'écart entre les deux pays pour une année donnée, ou null si l'un des
     deux n'a pas de chiffre cette année-là. */
  function ecartDeLAnnee(annee) {
    var valeurs = reglages.donnees.valeurs;
    if (!paysA || !paysB) return null;
    var a = valeurs[paysA] && valeurs[paysA][String(annee)];
    var b = valeurs[paysB] && valeurs[paysB][String(annee)];
    if (typeof a !== "number" || typeof b !== "number") return null;
    /* B est mesuré, A sert de base : le signe se lit donc comme sur la carte
       en mode comparaison — positif = le second pays fait mieux que le
       premier, celui qu'on a désigné en premier. */
    return reglages.outils.calculerEcart(b, a);
  }

  /* Toute l'histoire de l'écart, année par année. C'est le cœur du fichier :
     le graphique et les repères en découlent. */
  function histoire() {
    var points = [];
    reglages.donnees.annees.forEach(function (annee) {
      var ecart = ecartDeLAnnee(annee);
      if (ecart !== null) points.push({ annee: annee, ecart: ecart });
    });
    return points;
  }

  /* Les années remarquables : l'écart le plus fort dans un sens, dans l'autre,
     et la dernière fois que les deux pays se sont croisés.
     C'est ce qui répond à « 24 % telle année, 10 % telle autre ». */
  function reperes(points) {
    if (!points.length) return null;

    var haut = points[0];
    var bas = points[0];
    var croisement = null;

    for (var i = 0; i < points.length; i++) {
      if (points[i].ecart > haut.ecart) haut = points[i];
      if (points[i].ecart < bas.ecart) bas = points[i];
      /* Un changement de signe entre deux années : les deux pays se sont
         rejoints quelque part entre les deux. On retient la plus récente. */
      if (i > 0) {
        var avant = points[i - 1].ecart;
        var apres = points[i].ecart;
        if ((avant < 0 && apres >= 0) || (avant > 0 && apres <= 0)) {
          croisement = points[i].annee;
        }
      }
    }
    return { haut: haut, bas: bas, croisement: croisement };
  }

  /* --- 5. Le graphique ---------------------------------------------------- */

  var LARGEUR = 300;
  var HAUTEUR = 104;
  var MARGE = 4;

  /* Un SVG dessiné à la main : une courbe, la ligne du zéro, et un repère sur
     l'année affichée. Pas de bibliothèque — quelques dizaines de lignes
     suffisent, et le site n'a rien de plus à télécharger. */
  function graphique(points) {
    if (points.length < 2) return "";

    var annees = points.map(function (p) { return p.annee; });
    var ecarts = points.map(function (p) { return p.ecart; });
    var anneeMin = annees[0];
    var anneeMax = annees[annees.length - 1];

    /* L'échelle verticale contient toujours le zéro : sans lui, on ne verrait
       pas de quel côté de l'autre pays on se trouve. */
    var hautMax = Math.max.apply(null, ecarts.concat([0]));
    var basMin = Math.min.apply(null, ecarts.concat([0]));
    if (hautMax === basMin) { hautMax += 1; basMin -= 1; }
    var marge = (hautMax - basMin) * 0.12;
    hautMax += marge;
    basMin -= marge;

    function x(annee) {
      return MARGE + ((annee - anneeMin) / (anneeMax - anneeMin)) * (LARGEUR - 2 * MARGE);
    }
    function y(ecart) {
      return MARGE + ((hautMax - ecart) / (hautMax - basMin)) * (HAUTEUR - 2 * MARGE);
    }

    var yZero = y(0);
    var courbe = points
      .map(function (p, i) { return (i ? "L" : "M") + x(p.annee).toFixed(1) + " " + y(p.ecart).toFixed(1); })
      .join(" ");
    /* La surface entre la courbe et la ligne du zéro. */
    var surface =
      courbe +
      " L" + x(anneeMax).toFixed(1) + " " + yZero.toFixed(1) +
      " L" + x(anneeMin).toFixed(1) + " " + yZero.toFixed(1) + " Z";

    var couleurs = reglages.outils.couleursExtremes();
    var id = "cmp" + Math.random().toString(36).slice(2, 8);

    /* La surface est peinte deux fois, découpée au ras de la ligne du zéro :
       en vert au-dessus (le pays du haut mène), en rouge en dessous. */
    var svg =
      '<svg class="cmp__graphe" viewBox="0 0 ' + LARGEUR + " " + HAUTEUR + '" ' +
      'preserveAspectRatio="none" role="img">' +
      "<defs>" +
      '<clipPath id="' + id + 'h"><rect x="0" y="0" width="' + LARGEUR + '" height="' + yZero.toFixed(1) + '"/></clipPath>' +
      '<clipPath id="' + id + 'b"><rect x="0" y="' + yZero.toFixed(1) + '" width="' + LARGEUR + '" height="' + (HAUTEUR - yZero).toFixed(1) + '"/></clipPath>' +
      "</defs>" +
      '<path d="' + surface + '" fill="' + couleurs.vert + '" opacity="0.28" clip-path="url(#' + id + 'h)"/>' +
      '<path d="' + surface + '" fill="' + couleurs.rouge + '" opacity="0.28" clip-path="url(#' + id + 'b)"/>' +
      '<line x1="0" y1="' + yZero.toFixed(1) + '" x2="' + LARGEUR + '" y2="' + yZero.toFixed(1) +
      '" stroke="' + reglages.outils.couleurCSS("--texte-tres-doux") + '" stroke-width="1" stroke-dasharray="3 3"/>' +
      '<path d="' + courbe + '" fill="none" stroke="' + reglages.outils.couleurCSS("--texte") +
      '" stroke-width="1.6" stroke-linejoin="round" vector-effect="non-scaling-stroke"/>';

    /* Le repère de l'année affichée, s'il y a un chiffre cette année-là. */
    var actuel = null;
    for (var i = 0; i < points.length; i++) {
      if (points[i].annee === anneeAffichee) actuel = points[i];
    }
    if (actuel) {
      var cx = x(actuel.annee);
      svg +=
        '<line x1="' + cx.toFixed(1) + '" y1="0" x2="' + cx.toFixed(1) + '" y2="' + HAUTEUR +
        '" stroke="' + reglages.outils.couleurCSS("--accent") + '" stroke-width="1" opacity="0.6"/>' +
        '<circle cx="' + cx.toFixed(1) + '" cy="' + y(actuel.ecart).toFixed(1) + '" r="3.5" ' +
        'fill="' + reglages.outils.couleurCSS("--accent") + '"/>';
    }
    svg += "</svg>";

    return (
      '<div class="cmp__graphe-boite" data-min="' + anneeMin + '" data-max="' + anneeMax + '">' +
      svg +
      '<div class="cmp__bornes"><span>' + anneeMin + "</span><span>" + anneeMax + "</span></div>" +
      "</div>"
    );
  }

  /* Cliquer ou glisser sur le graphique déplace le curseur des années. */
  function brancherGraphique() {
    var cadre = boite.querySelector(".cmp__graphe-boite");
    if (!cadre) return;

    var anneeMin = Number(cadre.getAttribute("data-min"));
    var anneeMax = Number(cadre.getAttribute("data-max"));
    var enCours = false;

    function viser(evenement) {
      var cadreEcran = cadre.getBoundingClientRect();
      var part = (evenement.clientX - cadreEcran.left) / cadreEcran.width;
      part = Math.max(0, Math.min(1, part));
      reglages.surAnneeChoisie(Math.round(anneeMin + part * (anneeMax - anneeMin)));
    }

    cadre.addEventListener("pointerdown", function (evenement) {
      enCours = true;
      cadre.setPointerCapture(evenement.pointerId);
      viser(evenement);
    });
    cadre.addEventListener("pointermove", function (evenement) {
      if (enCours) viser(evenement);
    });
    cadre.addEventListener("pointerup", function () { enCours = false; });
    cadre.addEventListener("pointercancel", function () { enCours = false; });
  }

  /* --- 6. L'affichage ----------------------------------------------------- */

  function fente(iso, lettre, estLaBase) {
    var e = reglages.outils.echapper;
    var valeur = null;
    if (iso) {
      var parAnnee = reglages.donnees.valeurs[iso];
      var brut = parAnnee && parAnnee[String(anneeAffichee)];
      if (typeof brut === "number") valeur = reglages.outils.valeurLisible(brut);
    }

    return (
      '<button type="button" class="cmp__fente' +
      (fenteActive === lettre ? " est-active" : "") +
      (iso ? "" : " est-vide") +
      '" data-fente="' + lettre + '">' +
      (iso
        ? '<span class="drapeau" aria-hidden="true">' + e(reglages.pays.drapeaux[iso] || "") + "</span>" +
          '<span class="cmp__nom">' + e(reglages.pays.noms[iso] || iso) + "</span>" +
          (estLaBase ? '<span class="cmp__base">' + e(t("reference_court")) + "</span>" : "") +
          '<span class="cmp__valeur nombre">' + e(valeur === null ? "—" : valeur) + "</span>"
        : '<span class="cmp__nom cmp__nom--vide">' + e(t("comparateur_choisir")) + "</span>") +
      "</button>"
    );
  }

  function dessiner() {
    var e = reglages.outils.echapper;
    var morceaux = [
      '<div class="cmp__fentes">' +
        fente(paysA, "a", true) +
        fente(paysB, "b", false) +
      "</div>",
    ];

    if (!paysA || !paysB) {
      morceaux.push('<p class="cmp__invite">' + e(t("comparateur_invite")) + "</p>");
      morceaux.push(listeDeChoix());
      boite.innerHTML = morceaux.join("");
      brancherContenu();
      return;
    }

    var points = histoire();
    var ecartActuel = ecartDeLAnnee(anneeAffichee);

    /* Le grand chiffre : l'écart de l'année affichée. */
    morceaux.push(
      '<div class="cmp__resultat">' +
        '<div class="cmp__ecart nombre">' +
        e(ecartActuel === null ? "—" : reglages.outils.ecartLisible(ecartActuel)) +
        "</div>" +
        '<div class="cmp__legende">' +
        e(t("ecart_en").replace("{annee}", anneeAffichee)) +
        "</div>" +
      "</div>"
    );

    if (points.length < 2) {
      morceaux.push('<p class="cmp__invite">' + e(t("comparateur_sans_donnee")) + "</p>");
    } else {
      morceaux.push(graphique(points));

      var r = reperes(points);
      var lignes = [
        ligneRepere(t("ecart_max"), r.haut),
        ligneRepere(t("ecart_min"), r.bas),
      ];
      if (r.croisement !== null) {
        lignes.push(
          '<div class="cmp__repere"><span class="cmp__repere-nom">' +
          e(t("croisement")) + '</span><span class="cmp__repere-valeur nombre">' +
          e(String(r.croisement)) + "</span></div>"
        );
      }
      morceaux.push('<div class="cmp__reperes">' + lignes.join("") + "</div>");
    }

    morceaux.push(listeDeChoix());
    boite.innerHTML = morceaux.join("");
    brancherContenu();
    brancherGraphique();

    function ligneRepere(nom, point) {
      return (
        '<div class="cmp__repere">' +
        '<span class="cmp__repere-nom">' + e(nom) + "</span>" +
        '<span class="cmp__repere-valeur nombre">' +
        e(reglages.outils.ecartLisible(point.ecart)) +
        '<i>' + e(String(point.annee)) + "</i></span>" +
        "</div>"
      );
    }
  }

  /* La liste déroulante pour choisir un pays sans passer par la carte. */
  function listeDeChoix() {
    var e = reglages.outils.echapper;
    var options = paysDisponibles()
      .map(function (iso) {
        var choisi = (fenteActive === "a" ? paysA : paysB) === iso;
        return (
          '<option value="' + e(iso) + '"' + (choisi ? " selected" : "") + ">" +
          e((reglages.pays.drapeaux[iso] ? reglages.pays.drapeaux[iso] + " " : "") +
            (reglages.pays.noms[iso] || iso)) +
          "</option>"
        );
      })
      .join("");

    return (
      '<label class="cmp__choix">' +
      '<span class="cmp__choix-titre">' +
      e(t(fenteActive === "a" ? "comparateur_choix_a" : "comparateur_choix_b")) +
      "</span>" +
      '<select class="cmp__select" id="cmp-select">' +
      '<option value="">' + e(t("comparateur_choisir")) + "</option>" +
      options +
      "</select></label>"
    );
  }

  function brancherContenu() {
    /* Cliquer sur une fente la rend active : le prochain pays choisi — sur la
       carte comme dans la liste — ira dedans. */
    var fentes = boite.querySelectorAll(".cmp__fente");
    for (var i = 0; i < fentes.length; i++) {
      fentes[i].addEventListener("click", function () {
        fenteActive = this.getAttribute("data-fente");
        dessiner();
      });
    }

    var select = boite.querySelector("#cmp-select");
    if (select) {
      select.addEventListener("change", function () {
        if (this.value) choisirPays(this.value);
      });
    }
  }

  /* --- Ce que carte.js appelle -------------------------------------------- */

  window.StatsMapsComparateur = {
    /* Appelé une fois, quand les données sont chargées. */
    demarrer: function (options) {
      reglages = options;
      t = options.outils.t;
      anneeAffichee = options.anneeAffichee;

      var panneau = document.getElementById("panneau");
      var entete = panneau && panneau.querySelector(".panneau__entete");
      if (!entete) return;

      boite = document.createElement("div");
      boite.className = "comparateur";
      boite.id = "comparateur";
      boite.hidden = true;

      var liste = document.getElementById("classement");
      panneau.insertBefore(boite, liste ? liste.nextSibling : null);

      fabriquerOnglets(entete, document.getElementById("recherche"));
    },

    /* Le curseur des années a bougé. */
    majAnnee: function (annee) {
      anneeAffichee = annee;
      if (ongletOuvert) dessiner();
    },

    /* Un pays vient d'être choisi sur la carte ou dans le classement. */
    choisirPays: function (iso) {
      choisirPays(iso);
    },

    /* Le thème a changé : les couleurs du graphique sont à refaire. */
    redessiner: function () {
      if (ongletOuvert) dessiner();
    },

    /* L'onglet « Comparer » est-il ouvert ? carte.js s'en sert pour savoir
       s'il doit lui envoyer les pays cliqués. */
    estOuvert: function () {
      return ongletOuvert;
    },
  };
})();
