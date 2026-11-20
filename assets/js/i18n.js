/* ==========================================================================
   i18n.js — TOUS les textes du site, en français et en anglais.
   Si tu veux corriger une formulation, c'est ICI et nulle part ailleurs.
   ("i18n" est l'abréviation habituelle de "internationalisation".)

   Les NOMS DE PAYS ne sont pas ici : ils viennent du fond de carte, préparé
   par scripts/build_geojson.py. Natural Earth les fournit déjà traduits, il
   n'y a donc rien à traduire à la main de ce côté-là.

   Ne sont pas ici non plus, et pour la même raison, tout ce qui est ÉCRIT DANS
   LES PAGES plutôt qu'affiché par le JavaScript : les titres, les descriptions
   pour Google, les adresses, les libellés du menu des cartes et le nom des
   langues. Tout cela vit dans scripts/build_pages.py.

   Une remarque sur les pluriels : « 1 an » puis « 5 ans ». On ne code pas
   cette règle : le navigateur la connaît (Intl.PluralRules). Il suffit de
   remplir les formes que la langue utilise, les autres retombent sur
   « _other ».
   ========================================================================== */

window.StatsMapsTextes = {
  fr: {
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

    /* Infobulle de l'onglet « Pic ».
       Il y a plusieurs formes parce que les langues ne comptent pas pareil :
       le français dit « 1 an » puis « 5 ans », l'ukrainien dit « 1 рік »,
       « 3 роки » puis « 5 років ». Le navigateur choisit tout seul la bonne
       forme ; il suffit de remplir celles qui existent dans la langue.
       {n} sera remplacé par le nombre d'années.                            */
    ecart_zero: "pic de l’année en cours",
    ecart_one: "il y a {n} an",
    ecart_other: "il y a {n} ans",

    /* Comparaison entre pays. Il n'y a pas de bouton « comparer » : cliquer
       sur un pays suffit à repeindre la carte en écarts avec lui. Ces textes
       sont donc ceux de la SORTIE (la croix du panneau), et de l'écart affiché
       dans la bulle et dans le classement. Les formulations évitent
       volontairement toute préposition devant un nom de pays — « par rapport à
       la France » — parce que la moitié des langues du site devraient alors le
       décliner. */
    comparer_stop: "Revenir aux valeurs",
    ecart_titre: "Écart",
    reference_pays: "pays de référence",
    unite_points: "pt",
    unite_annees: "ans",
    an_one: "{n} an",
    an_other: "{n} ans",

    /* L'onglet « Comparer » du panneau */
    onglet_comparer: "Comparer",

    /* L'onglet « Pic » du panneau : « en quelle année ce pays a-t-il été à son
       maximum ? ». {carte} sera remplacé par le titre de la carte ouverte,
       {annee} par l'année affichée.
       En anglais l'onglet s'appelle « Peaked », le mot employé par le FMI. */
    onglet_pic: "Pic",
    pic_titre: "Pic — {carte}",
    pic_unite: "années écoulées depuis le pic",
    pic_valeur: "Pic",
    pic_annee: "Année du pic",
    pic_aujourdhui: "Écart au pic en {annee}",
    pic_invite: "Clique sur un pays pour voir son pic.",

    /* L'onglet « Comparer » : deux pays face à face */
    comparateur_choisir: "Choisir un pays",
    comparateur_invite: "Choisis deux pays pour voir l'écart entre eux.",
    comparateur_sans_donnee: "Ces deux pays n'ont aucune année en commun.",
    comparateur_choix_a: "Pays de référence",
    comparateur_choix_b: "Pays comparé",
    reference_court: "référence",
    ecart_en: "Écart en {annee}",
    ecart_max: "Écart maximal",
    ecart_min: "Écart minimal",
    croisement: "Dernier croisement",

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

    /* --- La carte des métros ------------------------------------------------
       C'est la seule carte du site qui ne classe pas des valeurs mais des
       RÉSEAUX. Son panneau a donc son propre vocabulaire : cinq façons de
       classer les pays, puis la fiche d'une ville et la liste de ses lignes.
       Les cinq libellés des critères doivent rester TRÈS courts : ils
       partagent une seule rangée de 320 px. */
    metro_titre: "Métros",
    metro_recherche: "Rechercher un pays, une ville…",
    metro_rien_trouve: "Aucun pays ni aucune ville trouvés.",
    metro_pays_avec_metro: "pays",
    metro_villes: "villes",
    metro_retour: "← Tous les pays",

    /* Les cinq critères de classement */
    metro_par_reseaux: "Réseaux",
    metro_par_km: "Km",
    metro_par_stations: "Stations",
    metro_par_lignes: "Lignes",
    metro_par_chantiers: "Chantiers",

    /* La fiche d'une ville */
    metro_km: "de lignes",
    metro_stations: "stations",
    metro_lignes: "lignes",
    metro_chantier: "en construction",
    metro_depuis: "Premier métro ouvert en {annee}.",
    metro_voyageurs: "{n} millions de voyageurs par an.",
    metro_prevu: "ouverture prévue en {annee}",
    metro_en_construction: "en construction",
    metro_ses_lignes: "Ses lignes, dans leur couleur officielle",
    metro_ses_chantiers: "Des tronçons sont en construction (en pointillés sur la carte).",

    /* La légende */
    metro_leg_ville: "Ville avec un métro",
    metro_leg_chantier: "Premier métro en construction",
    metro_leg_pointilles: "Ligne en construction",
    metro_leg_couleurs: "Chaque ligne dans sa couleur officielle",
    metro_leg_zoom: "La taille de la pastille suit la longueur du réseau. Zoome pour voir les tracés au détail près, station par station.",
    metro_source: "Tracés, couleurs, stations : OpenStreetMap · Noms, ouverture, fréquentation : Wikidata",

    /* --- La carte des entreprises cotées ------------------------------------
       Des points sur les sièges, et un panneau de cases à cocher : les
       secteurs, puis les places boursières. */
    bourse_titre: "Entreprises cotées en bourse",
    bourse_recherche: "Rechercher une entreprise…",
    bourse_rien_trouve: "Aucune entreprise trouvée.",
    bourse_entreprises: "entreprises",
    bourse_affichees: "affichées",
    bourse_retour: "← Retour aux filtres",
    bourse_secteurs: "Secteurs",
    bourse_bourses: "Places boursières",
    bourse_tout: "Tout",
    bourse_rien: "Rien",
    bourse_voir_plus: "Voir les {n} autres places",
    bourse_voir_moins: "Voir moins",
    bourse_ici: "{n} entreprises à cet endroit",
    bourse_exact: "Siège à l’adresse exacte",
    bourse_ville: "Adresse exacte inconnue : placée au centre de {ville}",
    bourse_ville_seule: "Adresse exacte inconnue : placée au centre-ville",
    bourse_inconnu: "Siège inconnu : placée au centre du pays de sa bourse",
    bourse_gleif: "Fiche GLEIF",
    bourse_leg_inconnu: "Siège inconnu (placée au centre du pays)",
    bourse_cotee: "Cotée à",
    bourse_secteur: "Secteur",
    bourse_ca: "chiffre d’affaires",
    bourse_effectifs: "salariés",
    bourse_capi: "valeur en bourse",
    bourse_site: "Site officiel",
    bourse_wikidata: "Fiche Wikidata",
    bourse_leg_exact: "Siège à l’adresse exacte",
    bourse_leg_ville: "Siège connu à la ville près (placé au centre-ville)",
    bourse_leg_zoom: "Zoome pour voir les logos. Clique sur un point pour ouvrir la fiche de l’entreprise.",
    bourse_source: "Entreprises, sièges, secteurs, chiffres : Wikidata · Logos : Wikimedia Commons · Fond de carte : OpenStreetMap, via OpenFreeMap",
    bourse_milliards: "{n} Md",
    bourse_millions: "{n} M",

    /* Les grandes familles de secteurs (voir scripts/build_bourse.py). */
    bourse_sec_banque: "Banque & finance",
    bourse_sec_assurance: "Assurance",
    bourse_sec_immobilier: "Immobilier",
    bourse_sec_logiciel: "Logiciels & internet",
    bourse_sec_ia: "Intelligence artificielle",
    bourse_sec_electronique: "Électronique & semi-conducteurs",
    bourse_sec_telecom: "Télécoms",
    bourse_sec_medias: "Médias & divertissement",
    bourse_sec_jeux: "Jeux vidéo & jeux d’argent",
    bourse_sec_sante: "Santé & pharmacie",
    bourse_sec_energie: "Énergie",
    bourse_sec_mines: "Mines & métaux",
    bourse_sec_chimie: "Chimie & matériaux",
    bourse_sec_industrie: "Industrie & machines",
    bourse_sec_automobile: "Automobile",
    bourse_sec_aeronautique: "Aéronautique, spatial & défense",
    bourse_sec_transport: "Transport & logistique",
    bourse_sec_commerce: "Commerce & distribution",
    bourse_sec_alimentation: "Alimentation & boissons",
    bourse_sec_consommation: "Mode, beauté & biens de conso.",
    bourse_sec_tourisme: "Tourisme, hôtels & restaurants",
    bourse_sec_construction: "BTP & construction",
    bourse_sec_services: "Services aux entreprises",
    bourse_sec_conglomerat: "Conglomérats & holdings",
    bourse_sec_autre: "Autre ou non renseigné",
  },

  en: {
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

    comparer_stop: "Back to values",
    ecart_titre: "Gap",
    reference_pays: "reference country",
    unite_points: "pts",
    unite_annees: "years",
    an_one: "{n} year",
    an_other: "{n} years",

    onglet_comparer: "Compare",

    onglet_pic: "Peaked",
    pic_titre: "Peak year — {carte}",
    pic_unite: "years since the peak",
    pic_valeur: "Peak",
    pic_annee: "Peak year",
    pic_aujourdhui: "Gap to the peak in {annee}",
    pic_invite: "Click a country to see its peak.",
    comparateur_choisir: "Choose a country",
    comparateur_invite: "Pick two countries to see the gap between them.",
    comparateur_sans_donnee: "These two countries share no year of data.",
    comparateur_choix_a: "Reference country",
    comparateur_choix_b: "Compared country",
    reference_court: "reference",
    ecart_en: "Gap in {annee}",
    ecart_max: "Widest gap",
    ecart_min: "Narrowest gap",
    croisement: "Latest crossover",

    source: "Source",
    deux_points: ": ",
    mis_a_jour: "updated",
    weo_avril: "April",
    weo_octobre: "October",
    voir_classement: "Ranking",
    fermer: "Close",

    /* La carte des métros */
    metro_titre: "Metros",
    metro_recherche: "Search a country, a city…",
    metro_rien_trouve: "No country or city found.",
    metro_pays_avec_metro: "countries",
    metro_villes: "cities",
    metro_retour: "← All countries",
    metro_par_reseaux: "Systems",
    metro_par_km: "Km",
    metro_par_stations: "Stations",
    metro_par_lignes: "Lines",
    metro_par_chantiers: "Building",
    metro_km: "of lines",
    metro_stations: "stations",
    metro_lignes: "lines",
    metro_chantier: "under construction",
    metro_depuis: "First metro opened in {annee}.",
    metro_voyageurs: "{n} million passengers a year.",
    metro_prevu: "opening planned for {annee}",
    metro_en_construction: "under construction",
    metro_ses_lignes: "Its lines, in their official colours",
    metro_ses_chantiers: "Some sections are under construction (dotted on the map).",
    metro_leg_ville: "City with a metro",
    metro_leg_chantier: "First metro under construction",
    metro_leg_pointilles: "Line under construction",
    metro_leg_couleurs: "Each line in its official colour",
    metro_leg_zoom: "The size of the dot follows the length of the network. Zoom in to see the lines in detail, station by station.",
    metro_source: "Lines, colours, stations: OpenStreetMap · Names, opening, ridership: Wikidata",

    /* La carte des entreprises cotées */
    bourse_titre: "Listed companies",
    bourse_recherche: "Search a company…",
    bourse_rien_trouve: "No company found.",
    bourse_entreprises: "companies",
    bourse_affichees: "shown",
    bourse_retour: "← Back to filters",
    bourse_secteurs: "Sectors",
    bourse_bourses: "Stock exchanges",
    bourse_tout: "All",
    bourse_rien: "None",
    bourse_voir_plus: "Show the other {n} exchanges",
    bourse_voir_moins: "Show fewer",
    bourse_ici: "{n} companies at this spot",
    bourse_exact: "Headquarters at the exact address",
    bourse_ville: "Exact address unknown: placed in the centre of {ville}",
    bourse_ville_seule: "Exact address unknown: placed in the city centre",
    bourse_inconnu: "Headquarters unknown: placed in the centre of its exchange's country",
    bourse_gleif: "GLEIF record",
    bourse_leg_inconnu: "Headquarters unknown (placed in the centre of the country)",
    bourse_cotee: "Listed on",
    bourse_secteur: "Sector",
    bourse_ca: "revenue",
    bourse_effectifs: "employees",
    bourse_capi: "market value",
    bourse_site: "Official website",
    bourse_wikidata: "Wikidata entry",
    bourse_leg_exact: "Headquarters at the exact address",
    bourse_leg_ville: "Headquarters known to the city (placed in the centre)",
    bourse_leg_zoom: "Zoom in to see the logos. Click a dot to open the company’s card.",
    bourse_source: "Companies, headquarters, sectors, figures: Wikidata · Logos: Wikimedia Commons · Map: OpenStreetMap, via OpenFreeMap",
    bourse_milliards: "{n} bn",
    bourse_millions: "{n} m",
    bourse_sec_banque: "Banking & finance",
    bourse_sec_assurance: "Insurance",
    bourse_sec_immobilier: "Real estate",
    bourse_sec_logiciel: "Software & internet",
    bourse_sec_ia: "Artificial intelligence",
    bourse_sec_electronique: "Electronics & semiconductors",
    bourse_sec_telecom: "Telecoms",
    bourse_sec_medias: "Media & entertainment",
    bourse_sec_jeux: "Video games & gambling",
    bourse_sec_sante: "Health & pharma",
    bourse_sec_energie: "Energy",
    bourse_sec_mines: "Mining & metals",
    bourse_sec_chimie: "Chemicals & materials",
    bourse_sec_industrie: "Industry & machinery",
    bourse_sec_automobile: "Automotive",
    bourse_sec_aeronautique: "Aerospace & defence",
    bourse_sec_transport: "Transport & logistics",
    bourse_sec_commerce: "Retail & distribution",
    bourse_sec_alimentation: "Food & drink",
    bourse_sec_consommation: "Fashion, beauty & consumer goods",
    bourse_sec_tourisme: "Travel, hotels & restaurants",
    bourse_sec_construction: "Construction",
    bourse_sec_services: "Business services",
    bourse_sec_conglomerat: "Conglomerates & holdings",
    bourse_sec_autre: "Other or not specified",
  },
};

/* Petit raccourci : t("recherche") renvoie le texte dans la langue de la page. */
window.StatsMapsT = function (langue) {
  var table = window.StatsMapsTextes[langue] || window.StatsMapsTextes.fr;
  return function (cle) {
    return table[cle] !== undefined ? table[cle] : cle;
  };
};
