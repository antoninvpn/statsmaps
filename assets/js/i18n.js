/* ==========================================================================
   i18n.js — tous les textes du site, en français, en anglais et en ukrainien.
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
    nav_record_pib: "Année record du PIB",
    nav_record_pib_hab: "Année record du PIB par hab.",

    /* Choix de la langue */
    langue_nom: "Français",
    langue_drapeau: "🇫🇷",
    changer_langue: "Langue",

    /* Panneau de classement */
    classement: "Classement",
    recherche: "Rechercher un pays…",
    aucun_resultat: "Aucun pays trouvé.",
    pays_classes: "pays classés",
    sans_donnee_compte: "sans donnée",
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
    territoire: "territoire, hors classement",

    /* Infobulle des cartes « année record ».
       Il y a plusieurs formes parce que les langues ne comptent pas pareil :
       le français dit « 1 an » puis « 5 ans », l'ukrainien dit « 1 рік »,
       « 3 роки » puis « 5 років ». Le navigateur choisit tout seul la bonne
       forme ; il suffit de remplir celles qui existent dans la langue.
       {n} sera remplacé par le nombre d'années.                            */
    ecart_zero: "record de l'année en cours",
    ecart_one: "il y a {n} an",
    ecart_other: "il y a {n} ans",

    /* Divers */
    source: "Source",
    /* En français, un espace insécable précède les deux-points. Pas en anglais. */
    deux_points: " : ",
    mis_a_jour: "mis à jour le",
    /* Le FMI publie son rapport en avril et en octobre. */
    weo_avril: "avril",
    weo_octobre: "octobre",
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
    nav_record_pib: "When GDP peaked",
    nav_record_pib_hab: "When GDP per capita peaked",

    langue_nom: "English",
    langue_drapeau: "🇬🇧",
    changer_langue: "Language",

    classement: "Ranking",
    recherche: "Search a country…",
    aucun_resultat: "No country found.",
    pays_classes: "countries ranked",
    sans_donnee_compte: "without data",
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
    territoire: "territory, not ranked",

    ecart_zero: "peak is the current year",
    ecart_one: "{n} year ago",
    ecart_other: "{n} years ago",

    source: "Source",
    deux_points: ": ",
    mis_a_jour: "updated",
    weo_avril: "April",
    weo_octobre: "October",
    voir_classement: "Ranking",
    fermer: "Close",

    milliards_dollars: "billion US dollars",
    dollars_par_habitant: "US dollars per capita",
    pourcent_an: "% per year",
  },

  uk: {
    site: "StatsMaps",
    nav_pib: "Номінальний ВВП",
    nav_pib_hab: "ВВП на душу населення",
    nav_croissance: "Зростання",
    nav_record_pib: "Рекордний рік ВВП",
    nav_record_pib_hab: "Рекордний рік ВВП на особу",

    langue_nom: "Українська",
    langue_drapeau: "🇺🇦",
    changer_langue: "Мова",

    classement: "Рейтинг",
    recherche: "Пошук країни…",
    aucun_resultat: "Країну не знайдено.",
    pays_classes: "країн у рейтингу",
    sans_donnee_compte: "без даних",
    chargement: "Завантаження даних…",
    erreur: "Не вдалося завантажити дані. Спробуйте ще раз за мить.",

    legende: "Легенда",
    non_disponible: "Немає даних",
    annee: "Рік",
    projection: "прогноз МВФ",
    estimation: "оцінка МВФ",
    donnee_reelle: "фактичні дані",

    rang: "місце",
    sur: "з",
    pas_de_donnee: "Немає даних за цей рік.",
    territoire: "територія, поза рейтингом",

    /* L'ukrainien a trois formes de pluriel : 1 рік, 2-4 роки, 5+ років. */
    ecart_zero: "рекорд цього року",
    ecart_one: "{n} рік тому",
    ecart_few: "{n} роки тому",
    ecart_many: "{n} років тому",
    ecart_other: "{n} років тому",

    source: "Джерело",
    deux_points: ": ",
    mis_a_jour: "оновлено",
    weo_avril: "квітень",
    weo_octobre: "жовтень",
    voir_classement: "Рейтинг",
    fermer: "Закрити",

    milliards_dollars: "мільярдів доларів",
    dollars_par_habitant: "доларів на душу населення",
    pourcent_an: "% на рік",
  },
};

/* Petit raccourci : t("recherche") renvoie le texte dans la langue de la page. */
window.StatsMapsT = function (langue) {
  var table = window.StatsMapsTextes[langue] || window.StatsMapsTextes.fr;
  return function (cle) {
    return table[cle] !== undefined ? table[cle] : cle;
  };
};
