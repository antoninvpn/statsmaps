/* ==========================================================================
   drapeaux.js — les drapeaux des pays, en images.

   Le fond de carte (data/pays.json) donne pour chaque pays son drapeau sous
   forme d'émoji (🇫🇷). Antonin préfère de vrais drapeaux dessinés, plus
   professionnels (demande du 23 novembre 2026) : ce petit fichier transforme
   l'émoji en image, prise dans assets/drapeaux/.

   Comment : un émoji de drapeau est fait de deux « lettres régionales »
   (🇫 + 🇷), qui donnent le code du pays à deux lettres (« fr »). On en déduit
   le nom du fichier : assets/drapeaux/fr.png. Les territoires en ont deux à
   la suite (🇨🇳🇭🇰 pour Hong Kong) : on dessine alors les deux drapeaux.

   Les dessins viennent de « flag-icons » (licence MIT, gratuite et libre :
   voir assets/drapeaux/LICENCE.txt), recopiés sur le site : rien n'est
   demandé à un autre serveur.
   ========================================================================== */

/* À augmenter de 1 chaque fois qu'on retouche les fichiers de drapeaux : les
   navigateurs vont alors chercher les nouveaux au lieu de garder les anciens.
   2 = dessins agrandis de 5 % pour supprimer le liseré clair de Safari.
   3 = nouveaux drapeaux de la Syrie et du Kirghizistan, et sept retouches.
   4 = le drapeau français aux bandes exactes de flag-icons 7.6.0.
   5 = le même, sans le liseré clair que la 4 avait ramené dans Safari.
   6 = des images PNG à la place des SVG (voir scripts/build_drapeaux.py) :
       plus de liseré au bord, dans aucun navigateur, à aucun zoom. */
var VERSION_DRAPEAUX = 6;

window.StatsMapsDrapeau = function (emoji) {
  if (!emoji) return "";
  var base = (document.body && document.body.getAttribute("data-base")) || "./";
  var lettres = Array.from(emoji);
  var html = "";
  for (var i = 0; i + 1 < lettres.length; i += 2) {
    var a = lettres[i].codePointAt(0) - 0x1f1e6;
    var b = lettres[i + 1].codePointAt(0) - 0x1f1e6;
    if (a < 0 || a > 25 || b < 0 || b > 25) continue;
    var code = String.fromCharCode(97 + a, 97 + b);
    html += '<img class="drapeau-img" src="' + base + "assets/drapeaux/" + code +
      ".png?v=" + VERSION_DRAPEAUX + '" alt="" width="20" height="15" loading="lazy" decoding="async">';
  }
  return html;
};
