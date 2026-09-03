/* ==========================================================================
   i18n.js — tous les textes du site, en français et en anglais.
   Si tu veux corriger une formulation, c'est ICI et nulle part ailleurs.
   ("i18n" est l'abréviation habituelle de "internationalisation".)
   ========================================================================== */

window.StatsMapsTextes = {
  fr: {
    /* Navigation */
    site: "StatsMaps",
    nav_pib: "PIB nominal",
    nav_pib_hab: "PIB par habitant",
    nav_croissance: "Croissance",
    autre_langue: "EN",
    autre_langue_titre: "Switch to English",

    /* Panneau de classement */
    classement: "Classement",
    recherche: "Rechercher un pays…",
    aucun_resultat: "Aucun pays trouvé.",
    pays_classes: "pays classés",
    chargement: "Chargement des données…",
    erreur: "Impossible de charger les données. Réessaie dans un instant.",

    /* Légende et années */
    legende: "Légende",
    non_disponible: "Données non disponibles",
    annee: "Année",
    projection: "projection FMI",
    estimation: "estimation FMI",
    donnee_reelle: "donnée constatée",

    /* Infobulle */
    rang: "rang",
    sur: "sur",
    pas_de_donnee: "Donnée non disponible pour cette année.",

    /* Divers */
    source: "Source",
    /* En français, un espace insécable précède les deux-points. Pas en anglais. */
    deux_points: "\u00a0: ",
    mis_a_jour: "mis à jour le",
    voir_classement: "Classement",
    fermer: "Fermer",

    /* Unités longues */
    milliards_dollars: "milliards de dollars",
    dollars_par_habitant: "dollars par habitant",
    pourcent_an: "% par an",
  },

  en: {
    site: "StatsMaps",
    nav_pib: "Nominal GDP",
    nav_pib_hab: "GDP per capita",
    nav_croissance: "Growth",
    autre_langue: "FR",
    autre_langue_titre: "Passer en français",

    classement: "Ranking",
    recherche: "Search a country…",
    aucun_resultat: "No country found.",
    pays_classes: "countries ranked",
    chargement: "Loading data…",
    erreur: "Could not load the data. Please try again shortly.",

    legende: "Legend",
    non_disponible: "No data available",
    annee: "Year",
    projection: "IMF projection",
    estimation: "IMF estimate",
    donnee_reelle: "actual figure",

    rang: "rank",
    sur: "of",
    pas_de_donnee: "No data available for this year.",

    source: "Source",
    deux_points: ": ",
    mis_a_jour: "updated",
    voir_classement: "Ranking",
    fermer: "Close",

    milliards_dollars: "billion US dollars",
    dollars_par_habitant: "US dollars per capita",
    pourcent_an: "% per year",
  },
};

/* Petit raccourci : t("recherche") renvoie le texte dans la langue de la page. */
window.StatsMapsT = function (langue) {
  var table = window.StatsMapsTextes[langue] || window.StatsMapsTextes.fr;
  return function (cle) {
    return table[cle] !== undefined ? table[cle] : cle;
  };
};
