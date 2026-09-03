/* ==========================================================================
   theme.js — le bouton soleil / lune
   Ce fichier est chargé TÔT (dans le <head>, sans "defer") pour que la bonne
   couleur soit appliquée avant l'affichage : sinon on verrait un éclair blanc.
   ========================================================================== */

(function () {
  "use strict";

  var CLE = "statsmaps-theme"; // nom du souvenir gardé dans le navigateur

  /* Lit le choix mémorisé. Peut échouer (navigation privée) : on ne casse rien. */
  function lireChoix() {
    try {
      var valeur = localStorage.getItem(CLE);
      return valeur === "dark" || valeur === "light" ? valeur : null;
    } catch (e) {
      return null;
    }
  }

  function memoriser(theme) {
    try {
      localStorage.setItem(CLE, theme);
    } catch (e) {
      /* pas grave : le thème marchera quand même pour cette visite */
    }
  }

  /* Le thème réellement affiché : le choix de l'utilisateur, sinon celui du système. */
  function themeActuel() {
    var choix = lireChoix();
    if (choix) return choix;
    return window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function appliquer(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", theme === "dark" ? "#0e1116" : "#ffffff");
  }

  /* On applique immédiatement, avant que la page ne s'affiche. */
  if (lireChoix()) appliquer(lireChoix());

  /* Une fois la page prête, on branche le bouton. */
  function brancherBouton() {
    var bouton = document.getElementById("bouton-theme");
    if (!bouton) return;

    /* Le texte du bouton change avec la langue de la page. Comme ce fichier
       est chargé avant les traductions, chaque page écrit elle-même les deux
       phrases dans les attributs data-vers-clair et data-vers-sombre du
       bouton. Si elles manquent, on retombe sur le français.              */
    function rafraichirBouton() {
      var sombre = themeActuel() === "dark";
      bouton.textContent = sombre ? "☀︎" : "☾";
      var etiquette = sombre
        ? bouton.getAttribute("data-vers-clair") || "Passer en thème clair"
        : bouton.getAttribute("data-vers-sombre") || "Passer en thème sombre";
      bouton.setAttribute("aria-label", etiquette);
      bouton.setAttribute("title", etiquette);
    }

    bouton.addEventListener("click", function () {
      var nouveau = themeActuel() === "dark" ? "light" : "dark";
      appliquer(nouveau);
      memoriser(nouveau);
      rafraichirBouton();
      /* Prévient la carte pour qu'elle recolorie la mer et les contours. */
      window.dispatchEvent(new CustomEvent("statsmaps:theme", { detail: nouveau }));
    });

    rafraichirBouton();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", brancherBouton);
  } else {
    brancherBouton();
  }

  /* Si l'utilisateur n'a jamais cliqué sur le bouton, on suit son téléphone. */
  if (window.matchMedia) {
    var media = window.matchMedia("(prefers-color-scheme: dark)");
    var surChangement = function () {
      if (lireChoix()) return; // il a choisi : on ne le contrarie pas
      window.dispatchEvent(
        new CustomEvent("statsmaps:theme", { detail: themeActuel() })
      );
    };
    if (media.addEventListener) media.addEventListener("change", surChangement);
    else if (media.addListener) media.addListener(surChangement);
  }

  /* On expose une petite fonction pour que carte.js sache quel thème est actif. */
  window.StatsMapsTheme = { actuel: themeActuel };
})();
