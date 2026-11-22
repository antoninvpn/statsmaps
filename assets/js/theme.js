/* ==========================================================================
   theme.js — le site est toujours en clair.

   Jusqu'au 23 novembre 2026, ce fichier gérait le bouton soleil / lune et le
   thème sombre. Antonin a décidé de garder le site uniquement en clair (comme
   Our World in Data, le FMI ou l'Unesco) : le bouton a disparu des pages.

   Ce petit fichier reste chargé tôt, dans le <head> de chaque page, pour deux
   politesses :
     - effacer le choix « sombre » qu'un navigateur aurait gardé en mémoire
       d'une visite précédente ;
     - répondre « clair » aux cartes qui demandent le thème du moment
       (window.StatsMapsTheme.actuel()).
   ========================================================================== */

(function () {
  "use strict";

  try {
    localStorage.removeItem("statsmaps-theme");
  } catch (e) {
    /* navigation privée : rien à effacer */
  }

  document.documentElement.setAttribute("data-theme", "light");

  window.StatsMapsTheme = {
    actuel: function () {
      return "light";
    },
  };
})();
