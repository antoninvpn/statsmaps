/* ==========================================================================
   barre.js — le petit menu des langues, en haut à droite de chaque page.

   Le menu lui-même est écrit en HTML tout simple, avec les balises <details>
   et <summary> : le navigateur sait déjà les ouvrir et les fermer tout seul.
   Autrement dit, le menu marche même si ce fichier ne se charge pas.

   Ce fichier n'ajoute que deux politesses :
     - le menu se referme quand on clique ailleurs sur la page ;
     - le menu se referme quand on appuie sur la touche Échap.
   ========================================================================== */

(function () {
  "use strict";

  /* Ferme tous les menus ouverts, sauf éventuellement celui qu'on vient de
     toucher (sinon un clic sur le bouton l'ouvrirait et le refermerait
     aussitôt). */
  function fermerLesMenus(sauf) {
    var ouverts = document.querySelectorAll("details.langues[open]");
    for (var i = 0; i < ouverts.length; i++) {
      if (ouverts[i] !== sauf) ouverts[i].removeAttribute("open");
    }
  }

  document.addEventListener("click", function (evenement) {
    var cible = evenement.target;
    /* "closest" remonte de proche en proche : est-on quelque part à
       l'intérieur d'un menu de langues, ou complètement ailleurs ? */
    var dansUnMenu = cible.closest ? cible.closest("details.langues") : null;
    fermerLesMenus(dansUnMenu);
  });

  document.addEventListener("keydown", function (evenement) {
    if (evenement.key === "Escape" || evenement.key === "Esc") {
      fermerLesMenus(null);
    }
  });
})();
