/* ==========================================================================
   i18n.js — TOUS les textes du site, dans les treize langues.
   Si tu veux corriger une formulation, c'est ICI et nulle part ailleurs.
   ("i18n" est l'abréviation habituelle de "internationalisation".)

   Les NOMS DE PAYS ne sont pas ici : ils viennent du fond de carte, préparé
   par scripts/build_geojson.py. Natural Earth les fournit déjà dans les treize
   langues, il n'y a donc rien à traduire à la main de ce côté-là.

   Ne sont pas ici non plus, et pour la même raison, tout ce qui est ÉCRIT DANS
   LES PAGES plutôt qu'affiché par le JavaScript : les titres, les descriptions
   pour Google, les adresses, les libellés du menu des cartes et le nom des
   langues. Tout cela vit dans scripts/build_pages.py.

   Une remarque sur les pluriels : le français dit « 1 an » puis « 5 ans »,
   le polonais « 1 rok », « 2 lata », « 5 lat », l'arabe a six formes, le
   japonais une seule. On ne code aucune de ces règles : le navigateur les
   connaît toutes (Intl.PluralRules). Il suffit de remplir les formes que la
   langue utilise réellement, les autres retombent sur « _other ».
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

    /* Infobulle des cartes « année record ».
       Il y a plusieurs formes parce que les langues ne comptent pas pareil :
       le français dit « 1 an » puis « 5 ans », l'ukrainien dit « 1 рік »,
       « 3 роки » puis « 5 років ». Le navigateur choisit tout seul la bonne
       forme ; il suffit de remplir celles qui existent dans la langue.
       {n} sera remplacé par le nombre d'années.                            */
    ecart_zero: "record de l'année en cours",
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

    /* L'onglet « Records » du panneau : « en quelle année ce pays a-t-il été
       à son maximum ? ». {carte} sera remplacé par le titre de la carte
       ouverte, {annee} par l'année affichée. */
    onglet_records: "Records",
    record_titre: "Année record — {carte}",
    record_unite: "années écoulées depuis le record",
    record_valeur: "Record",
    record_annee: "Année du record",
    record_aujourdhui: "Écart au record en {annee}",
    record_invite: "Clique sur un pays pour voir son record.",

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

    onglet_records: "Records",
    record_titre: "Peak year — {carte}",
    record_unite: "years since the peak",
    record_valeur: "Peak",
    record_annee: "Peak year",
    record_aujourdhui: "Gap to the peak in {annee}",
    record_invite: "Click a country to see its peak.",
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

  },

  uk: {
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

    comparer_stop: "Повернутися до значень",
    ecart_titre: "Розрив",
    reference_pays: "країна порівняння",
    unite_points: "п.",
    unite_annees: "років",
    an_one: "{n} рік",
    an_few: "{n} роки",
    an_many: "{n} років",
    an_other: "{n} років",

    onglet_comparer: "Порівняти",

    onglet_records: "Рекорди",
    record_titre: "Рекордний рік — {carte}",
    record_unite: "років від рекорду",
    record_valeur: "Рекорд",
    record_annee: "Рік рекорду",
    record_aujourdhui: "Відставання від рекорду у {annee}",
    record_invite: "Натисніть на країну, щоб побачити її рекорд.",
    comparateur_choisir: "Обрати країну",
    comparateur_invite: "Оберіть дві країни, щоб побачити розрив між ними.",
    comparateur_sans_donnee: "Ці дві країни не мають спільних років даних.",
    comparateur_choix_a: "Країна порівняння",
    comparateur_choix_b: "Країна для порівняння",
    reference_court: "основа",
    ecart_en: "Розрив у {annee}",
    ecart_max: "Найбільший розрив",
    ecart_min: "Найменший розрив",
    croisement: "Останній перетин",

    source: "Джерело",
    deux_points: ": ",
    mis_a_jour: "оновлено",
    weo_avril: "квітень",
    weo_octobre: "жовтень",
    voir_classement: "Рейтинг",
    fermer: "Закрити",

  },

  /* --- Allemand --- */
  de: {
    /* Panneau de classement */
    classement: "Rangliste",
    recherche: "Land suchen…",
    aucun_resultat: "Kein Land gefunden.",
    pays_classes: "Länder gewertet",
    sans_donnee_compte: "ohne Daten",
    chargement: "Daten werden geladen…",
    erreur: "Die Daten konnten nicht geladen werden. Bitte gleich noch einmal versuchen.",

    /* Légende et années */
    legende: "Legende",
    non_disponible: "Keine Daten verfügbar",
    annee: "Jahr",
    projection: "IWF-Prognose",
    estimation: "IWF-Schätzung",
    donnee_reelle: "tatsächlicher Wert",

    /* Infobulle */
    rang: "Rang",
    sur: "von",
    pas_de_donnee: "Für dieses Jahr liegen keine Daten vor.",
    territoire: "Gebiet, nicht gewertet",

    /* Cartes « année record » */
    ecart_zero: "Höchststand im laufenden Jahr",
    ecart_one: "vor {n} Jahr",
    ecart_other: "vor {n} Jahren",

    /* Comparaison entre pays */
    comparer_stop: "Zurück zu den Werten",
    ecart_titre: "Unterschied",
    reference_pays: "Bezugsland",
    unite_points: "Pp",
    unite_annees: "Jahre",
    an_one: "{n} Jahr",
    an_other: "{n} Jahre",

    /* Onglet « Comparer » */
    onglet_comparer: "Vergleichen",

    onglet_records: "Rekorde",
    record_titre: "Höchststand — {carte}",
    record_unite: "Jahre seit dem Höchststand",
    record_valeur: "Höchstwert",
    record_annee: "Jahr des Höchststands",
    record_aujourdhui: "Abstand zum Höchststand {annee}",
    record_invite: "Klicke auf ein Land, um seinen Höchststand zu sehen.",
    comparateur_choisir: "Land auswählen",
    comparateur_invite: "Zwei Länder auswählen, um den Unterschied zu sehen.",
    comparateur_sans_donnee: "Für diese beiden Länder gibt es kein gemeinsames Jahr.",
    comparateur_choix_a: "Bezugsland",
    comparateur_choix_b: "Verglichenes Land",
    reference_court: "Bezug",
    ecart_en: "Unterschied {annee}",
    ecart_max: "Größter Unterschied",
    ecart_min: "Kleinster Unterschied",
    croisement: "Letzte Überschneidung",

    /* Divers */
    source: "Quelle",
    deux_points: ": ",
    mis_a_jour: "aktualisiert am",
    weo_avril: "April",
    weo_octobre: "Oktober",
    voir_classement: "Rangliste",
    fermer: "Schließen",
  },

  /* --- Espagnol --- */
  es: {
    /* Panneau de classement */
    classement: "Clasificación",
    recherche: "Buscar un país…",
    aucun_resultat: "No se ha encontrado ningún país.",
    pays_classes: "países clasificados",
    sans_donnee_compte: "sin datos",
    chargement: "Cargando los datos…",
    erreur: "No se han podido cargar los datos. Inténtalo de nuevo en un momento.",

    /* Légende et années */
    legende: "Leyenda",
    non_disponible: "Datos no disponibles",
    annee: "Año",
    projection: "proyección del FMI",
    estimation: "estimación del FMI",
    donnee_reelle: "dato observado",

    /* Infobulle */
    rang: "puesto",
    sur: "de",
    pas_de_donnee: "No hay datos disponibles para este año.",
    territoire: "territorio, sin clasificar",

    /* Cartes « année record » */
    ecart_zero: "récord en el año en curso",
    ecart_one: "hace {n} año",
    ecart_other: "hace {n} años",

    /* Comparaison entre pays */
    comparer_stop: "Volver a los valores",
    ecart_titre: "Diferencia",
    reference_pays: "país de referencia",
    unite_points: "pp",
    unite_annees: "años",
    an_one: "{n} año",
    an_other: "{n} años",

    /* Onglet « Comparer » */
    onglet_comparer: "Comparar",

    onglet_records: "Récords",
    record_titre: "Año récord — {carte}",
    record_unite: "años desde el récord",
    record_valeur: "Récord",
    record_annee: "Año del récord",
    record_aujourdhui: "Distancia al récord en {annee}",
    record_invite: "Haz clic en un país para ver su récord.",
    comparateur_choisir: "Elegir un país",
    comparateur_invite: "Elige dos países para ver la diferencia entre ellos.",
    comparateur_sans_donnee: "Estos dos países no comparten ningún año con datos.",
    comparateur_choix_a: "País de referencia",
    comparateur_choix_b: "País comparado",
    reference_court: "referencia",
    ecart_en: "Diferencia en {annee}",
    ecart_max: "Diferencia máxima",
    ecart_min: "Diferencia mínima",
    croisement: "Último cruce",

    /* Divers */
    source: "Fuente",
    deux_points: ": ",
    mis_a_jour: "actualizado el",
    weo_avril: "abril",
    weo_octobre: "octubre",
    voir_classement: "Clasificación",
    fermer: "Cerrar",
  },

  /* --- Italien --- */
  it: {
    /* Panneau de classement */
    classement: "Classifica",
    recherche: "Cerca un paese…",
    aucun_resultat: "Nessun paese trovato.",
    pays_classes: "paesi in classifica",
    sans_donnee_compte: "senza dati",
    chargement: "Caricamento dei dati…",
    erreur: "Impossibile caricare i dati. Riprova tra un istante.",

    /* Légende et années */
    legende: "Legenda",
    non_disponible: "Dati non disponibili",
    annee: "Anno",
    projection: "proiezione FMI",
    estimation: "stima FMI",
    donnee_reelle: "dato effettivo",

    /* Infobulle */
    rang: "posizione",
    sur: "su",
    pas_de_donnee: "Nessun dato disponibile per quest'anno.",
    territoire: "territorio, fuori classifica",

    /* Cartes « année record » */
    ecart_zero: "record nell'anno in corso",
    ecart_one: "{n} anno fa",
    ecart_other: "{n} anni fa",

    /* Comparaison entre pays */
    comparer_stop: "Torna ai valori",
    ecart_titre: "Scarto",
    reference_pays: "paese di riferimento",
    unite_points: "p.p.",
    unite_annees: "anni",
    an_one: "{n} anno",
    an_other: "{n} anni",

    /* Onglet « Comparer » */
    onglet_comparer: "Confronta",

    onglet_records: "Record",
    record_titre: "Anno record — {carte}",
    record_unite: "anni dal record",
    record_valeur: "Record",
    record_annee: "Anno del record",
    record_aujourdhui: "Distanza dal record nel {annee}",
    record_invite: "Clicca su un paese per vedere il suo record.",
    comparateur_choisir: "Scegli un paese",
    comparateur_invite: "Scegli due paesi per vedere lo scarto tra loro.",
    comparateur_sans_donnee: "Questi due paesi non hanno alcun anno in comune.",
    comparateur_choix_a: "Paese di riferimento",
    comparateur_choix_b: "Paese confrontato",
    reference_court: "riferimento",
    ecart_en: "Scarto nel {annee}",
    ecart_max: "Scarto massimo",
    ecart_min: "Scarto minimo",
    croisement: "Ultimo sorpasso",

    /* Divers */
    source: "Fonte",
    deux_points: ": ",
    mis_a_jour: "aggiornato il",
    weo_avril: "aprile",
    weo_octobre: "ottobre",
    voir_classement: "Classifica",
    fermer: "Chiudi",
  },

  /* --- Portugais --- */
  pt: {
    /* Panneau de classement */
    classement: "Classificação",
    recherche: "Procurar um país…",
    aucun_resultat: "Nenhum país encontrado.",
    pays_classes: "países classificados",
    sans_donnee_compte: "sem dados",
    chargement: "A carregar os dados…",
    erreur: "Não foi possível carregar os dados. Tenta novamente daqui a pouco.",

    /* Légende et années */
    legende: "Legenda",
    non_disponible: "Dados não disponíveis",
    annee: "Ano",
    projection: "projeção do FMI",
    estimation: "estimativa do FMI",
    donnee_reelle: "dado observado",

    /* Infobulle */
    rang: "posição",
    sur: "de",
    pas_de_donnee: "Não há dados disponíveis para este ano.",
    territoire: "território, fora da classificação",

    /* Cartes « année record » */
    ecart_zero: "recorde no ano em curso",
    ecart_one: "há {n} ano",
    ecart_other: "há {n} anos",

    /* Comparaison entre pays */
    comparer_stop: "Voltar aos valores",
    ecart_titre: "Diferença",
    reference_pays: "país de referência",
    unite_points: "p.p.",
    unite_annees: "anos",
    an_one: "{n} ano",
    an_other: "{n} anos",

    /* Onglet « Comparer » */
    onglet_comparer: "Comparar",

    onglet_records: "Recordes",
    record_titre: "Ano recorde — {carte}",
    record_unite: "anos desde o recorde",
    record_valeur: "Recorde",
    record_annee: "Ano do recorde",
    record_aujourdhui: "Distância do recorde em {annee}",
    record_invite: "Clica num país para ver o seu recorde.",
    comparateur_choisir: "Escolher um país",
    comparateur_invite: "Escolhe dois países para veres a diferença entre eles.",
    comparateur_sans_donnee: "Estes dois países não têm nenhum ano em comum.",
    comparateur_choix_a: "País de referência",
    comparateur_choix_b: "País comparado",
    reference_court: "referência",
    ecart_en: "Diferença em {annee}",
    ecart_max: "Diferença máxima",
    ecart_min: "Diferença mínima",
    croisement: "Último cruzamento",

    /* Divers */
    source: "Fonte",
    deux_points: ": ",
    mis_a_jour: "atualizado a",
    weo_avril: "abril",
    weo_octobre: "outubro",
    voir_classement: "Classificação",
    fermer: "Fechar",
  },

  /* --- Polonais — quatre formes de pluriel : 1 rok, 2-4 lata, 5+ lat --- */
  pl: {
    /* Panneau de classement */
    classement: "Ranking",
    recherche: "Szukaj kraju…",
    aucun_resultat: "Nie znaleziono kraju.",
    pays_classes: "krajów w rankingu",
    sans_donnee_compte: "bez danych",
    chargement: "Wczytywanie danych…",
    erreur: "Nie udało się wczytać danych. Spróbuj ponownie za chwilę.",

    /* Légende et années */
    legende: "Legenda",
    non_disponible: "Brak danych",
    annee: "Rok",
    projection: "prognoza MFW",
    estimation: "szacunek MFW",
    donnee_reelle: "dane rzeczywiste",

    /* Infobulle */
    rang: "miejsce",
    sur: "z",
    pas_de_donnee: "Brak danych za ten rok.",
    territoire: "terytorium, poza rankingiem",

    /* Cartes « année record » */
    ecart_zero: "rekord w bieżącym roku",
    ecart_one: "{n} rok temu",
    ecart_few: "{n} lata temu",
    ecart_many: "{n} lat temu",
    ecart_other: "{n} lat temu",

    /* Comparaison entre pays */
    comparer_stop: "Wróć do wartości",
    ecart_titre: "Różnica",
    reference_pays: "kraj odniesienia",
    unite_points: "pkt",
    unite_annees: "lat",
    an_one: "{n} rok",
    an_few: "{n} lata",
    an_many: "{n} lat",
    an_other: "{n} lat",

    /* Onglet « Comparer » */
    onglet_comparer: "Porównaj",

    onglet_records: "Rekordy",
    record_titre: "Rekordowy rok — {carte}",
    record_unite: "lat od rekordu",
    record_valeur: "Rekord",
    record_annee: "Rok rekordu",
    record_aujourdhui: "Odległość od rekordu w {annee}",
    record_invite: "Kliknij kraj, aby zobaczyć jego rekord.",
    comparateur_choisir: "Wybierz kraj",
    comparateur_invite: "Wybierz dwa kraje, aby zobaczyć różnicę między nimi.",
    comparateur_sans_donnee: "Te dwa kraje nie mają wspólnego roku z danymi.",
    comparateur_choix_a: "Kraj odniesienia",
    comparateur_choix_b: "Kraj porównywany",
    reference_court: "odniesienie",
    ecart_en: "Różnica w {annee}",
    ecart_max: "Największa różnica",
    ecart_min: "Najmniejsza różnica",
    croisement: "Ostatnie przecięcie",

    /* Divers */
    source: "Źródło",
    deux_points: ": ",
    mis_a_jour: "zaktualizowano",
    weo_avril: "kwiecień",
    weo_octobre: "październik",
    voir_classement: "Ranking",
    fermer: "Zamknij",
  },

  /* --- Japonais — une seule forme de pluriel --- */
  ja: {
    /* Panneau de classement */
    classement: "ランキング",
    recherche: "国を検索…",
    aucun_resultat: "該当する国がありません。",
    pays_classes: "か国",
    sans_donnee_compte: "データなし",
    chargement: "データを読み込み中…",
    erreur: "データを読み込めませんでした。しばらくしてからもう一度お試しください。",

    /* Légende et années */
    legende: "凡例",
    non_disponible: "データなし",
    annee: "年",
    projection: "IMF予測",
    estimation: "IMF推計",
    donnee_reelle: "実績値",

    /* Infobulle */
    rang: "順位",
    sur: "/",
    pas_de_donnee: "この年のデータはありません。",
    territoire: "地域、ランキング対象外",

    /* Cartes « année record » */
    ecart_zero: "今年が最高",
    ecart_other: "{n}年前",

    /* Comparaison entre pays */
    comparer_stop: "数値表示に戻る",
    ecart_titre: "差",
    reference_pays: "基準国",
    unite_points: "pt",
    unite_annees: "年",
    an_other: "{n}年",

    /* Onglet « Comparer » */
    onglet_comparer: "比較",

    onglet_records: "最高記録",
    record_titre: "最高年 — {carte}",
    record_unite: "最高年からの経過年数",
    record_valeur: "最高値",
    record_annee: "最高年",
    record_aujourdhui: "{annee}年の最高値との差",
    record_invite: "国をクリックすると、その最高記録が表示されます。",
    comparateur_choisir: "国を選ぶ",
    comparateur_invite: "2か国を選ぶと、その差が表示されます。",
    comparateur_sans_donnee: "この2か国に共通するデータの年がありません。",
    comparateur_choix_a: "基準国",
    comparateur_choix_b: "比較する国",
    reference_court: "基準",
    ecart_en: "{annee}年の差",
    ecart_max: "最大の差",
    ecart_min: "最小の差",
    croisement: "直近の逆転",

    /* Divers */
    source: "出典",
    deux_points: "：",
    mis_a_jour: "更新日",
    weo_avril: "4月",
    weo_octobre: "10月",
    voir_classement: "ランキング",
    fermer: "閉じる",
  },

  /* --- Coréen — une seule forme de pluriel --- */
  ko: {
    /* Panneau de classement */
    classement: "순위",
    recherche: "국가 검색…",
    aucun_resultat: "국가를 찾을 수 없습니다.",
    pays_classes: "개국",
    sans_donnee_compte: "자료 없음",
    chargement: "데이터를 불러오는 중…",
    erreur: "데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.",

    /* Légende et années */
    legende: "범례",
    non_disponible: "자료 없음",
    annee: "연도",
    projection: "IMF 전망",
    estimation: "IMF 추정",
    donnee_reelle: "실측치",

    /* Infobulle */
    rang: "순위",
    sur: "/",
    pas_de_donnee: "해당 연도의 자료가 없습니다.",
    territoire: "지역, 순위 제외",

    /* Cartes « année record » */
    ecart_zero: "올해가 최고치",
    ecart_other: "{n}년 전",

    /* Comparaison entre pays */
    comparer_stop: "값으로 돌아가기",
    ecart_titre: "격차",
    reference_pays: "기준 국가",
    unite_points: "%p",
    unite_annees: "년",
    an_other: "{n}년",

    /* Onglet « Comparer » */
    onglet_comparer: "비교",

    onglet_records: "최고 기록",
    record_titre: "최고 연도 — {carte}",
    record_unite: "최고 연도 이후 경과 연수",
    record_valeur: "최고치",
    record_annee: "최고 연도",
    record_aujourdhui: "{annee}년 최고치와의 격차",
    record_invite: "국가를 클릭하면 최고 기록이 표시됩니다.",
    comparateur_choisir: "나라 선택",
    comparateur_invite: "두 나라를 선택하면 격차가 표시됩니다.",
    comparateur_sans_donnee: "두 나라에 공통된 자료 연도가 없습니다.",
    comparateur_choix_a: "기준 국가",
    comparateur_choix_b: "비교 국가",
    reference_court: "기준",
    ecart_en: "{annee}년 격차",
    ecart_max: "최대 격차",
    ecart_min: "최소 격차",
    croisement: "최근 역전",

    /* Divers */
    source: "출처",
    deux_points: ": ",
    mis_a_jour: "업데이트",
    weo_avril: "4월",
    weo_octobre: "10월",
    voir_classement: "순위",
    fermer: "닫기",
  },

  /* --- Turc --- */
  tr: {
    /* Panneau de classement */
    classement: "Sıralama",
    recherche: "Ülke ara…",
    aucun_resultat: "Ülke bulunamadı.",
    pays_classes: "ülke sıralandı",
    sans_donnee_compte: "veri yok",
    chargement: "Veriler yükleniyor…",
    erreur: "Veriler yüklenemedi. Lütfen birazdan tekrar dene.",

    /* Légende et années */
    legende: "Gösterge",
    non_disponible: "Veri yok",
    annee: "Yıl",
    projection: "IMF öngörüsü",
    estimation: "IMF tahmini",
    donnee_reelle: "gerçekleşen veri",

    /* Infobulle */
    rang: "sıra",
    sur: "/",
    pas_de_donnee: "Bu yıl için veri yok.",
    territoire: "bölge, sıralama dışı",

    /* Cartes « année record » */
    ecart_zero: "zirve bu yıl",
    ecart_one: "{n} yıl önce",
    ecart_other: "{n} yıl önce",

    /* Comparaison entre pays */
    comparer_stop: "Değerlere dön",
    ecart_titre: "Fark",
    reference_pays: "referans ülke",
    unite_points: "puan",
    unite_annees: "yıl",
    an_one: "{n} yıl",
    an_other: "{n} yıl",

    /* Onglet « Comparer » */
    onglet_comparer: "Karşılaştır",

    onglet_records: "Rekorlar",
    record_titre: "Zirve yılı — {carte}",
    record_unite: "zirveden bu yana geçen yıl",
    record_valeur: "Zirve",
    record_annee: "Zirve yılı",
    record_aujourdhui: "{annee} yılında zirveye uzaklık",
    record_invite: "Zirvesini görmek için bir ülkeye tıkla.",
    comparateur_choisir: "Ülke seç",
    comparateur_invite: "Aradaki farkı görmek için iki ülke seç.",
    comparateur_sans_donnee: "Bu iki ülkenin ortak veri yılı yok.",
    comparateur_choix_a: "Referans ülke",
    comparateur_choix_b: "Karşılaştırılan ülke",
    reference_court: "referans",
    ecart_en: "{annee} yılındaki fark",
    ecart_max: "En büyük fark",
    ecart_min: "En küçük fark",
    croisement: "Son kesişme",

    /* Divers */
    source: "Kaynak",
    deux_points: ": ",
    mis_a_jour: "güncellendi",
    weo_avril: "Nisan",
    weo_octobre: "Ekim",
    voir_classement: "Sıralama",
    fermer: "Kapat",
  },

  /* --- Hindi --- */
  hi: {
    /* Panneau de classement */
    classement: "क्रम",
    recherche: "देश खोजें…",
    aucun_resultat: "कोई देश नहीं मिला।",
    pays_classes: "देश क्रम में",
    sans_donnee_compte: "बिना आँकड़ों के",
    chargement: "आँकड़े लोड हो रहे हैं…",
    erreur: "आँकड़े लोड नहीं हो सके। कृपया थोड़ी देर बाद फिर कोशिश करें।",

    /* Légende et années */
    legende: "संकेत",
    non_disponible: "आँकड़े उपलब्ध नहीं",
    annee: "वर्ष",
    projection: "IMF अनुमान",
    estimation: "IMF आकलन",
    donnee_reelle: "वास्तविक आँकड़ा",

    /* Infobulle */
    rang: "स्थान",
    sur: "में से",
    pas_de_donnee: "इस वर्ष के लिए आँकड़े उपलब्ध नहीं हैं।",
    territoire: "क्षेत्र, क्रम से बाहर",

    /* Cartes « année record » */
    ecart_zero: "शिखर इसी वर्ष",
    ecart_one: "{n} वर्ष पहले",
    ecart_other: "{n} वर्ष पहले",

    /* Comparaison entre pays */
    comparer_stop: "मानों पर लौटें",
    ecart_titre: "अंतर",
    reference_pays: "संदर्भ देश",
    unite_points: "अंक",
    unite_annees: "वर्ष",
    an_one: "{n} वर्ष",
    an_other: "{n} वर्ष",

    /* Onglet « Comparer » */
    onglet_comparer: "तुलना",

    onglet_records: "रिकॉर्ड",
    record_titre: "शिखर वर्ष — {carte}",
    record_unite: "शिखर वर्ष से बीते वर्ष",
    record_valeur: "शिखर",
    record_annee: "शिखर वर्ष",
    record_aujourdhui: "{annee} में शिखर से अंतर",
    record_invite: "किसी देश पर क्लिक करके उसका शिखर देखें।",
    comparateur_choisir: "देश चुनें",
    comparateur_invite: "अंतर देखने के लिए दो देश चुनें।",
    comparateur_sans_donnee: "इन दोनों देशों का कोई साझा वर्ष नहीं है।",
    comparateur_choix_a: "संदर्भ देश",
    comparateur_choix_b: "तुलना किया गया देश",
    reference_court: "संदर्भ",
    ecart_en: "{annee} में अंतर",
    ecart_max: "सबसे बड़ा अंतर",
    ecart_min: "सबसे छोटा अंतर",
    croisement: "अंतिम क्रॉसिंग",

    /* Divers */
    source: "स्रोत",
    deux_points: ": ",
    mis_a_jour: "अद्यतन",
    weo_avril: "अप्रैल",
    weo_octobre: "अक्तूबर",
    voir_classement: "क्रम",
    fermer: "बंद करें",
  },

  /* --- Arabe — six formes de pluriel, et la page s'écrit de droite à gauche --- */
  ar: {
    /* Panneau de classement */
    classement: "الترتيب",
    recherche: "ابحث عن بلد…",
    aucun_resultat: "لم يُعثر على أي بلد.",
    pays_classes: "بلدًا في الترتيب",
    sans_donnee_compte: "بلا بيانات",
    chargement: "جارٍ تحميل البيانات…",
    erreur: "تعذّر تحميل البيانات. حاول مرة أخرى بعد قليل.",

    /* Légende et années */
    legende: "المفتاح",
    non_disponible: "لا تتوفر بيانات",
    annee: "السنة",
    projection: "توقعات صندوق النقد الدولي",
    estimation: "تقدير صندوق النقد الدولي",
    donnee_reelle: "بيانات فعلية",

    /* Infobulle */
    rang: "المرتبة",
    sur: "من",
    pas_de_donnee: "لا تتوفر بيانات لهذه السنة.",
    territoire: "إقليم، خارج الترتيب",

    /* Cartes « année record » */
    ecart_zero: "الذروة في السنة الجارية",
    ecart_one: "قبل سنة",
    ecart_two: "قبل سنتين",
    ecart_few: "قبل {n} سنوات",
    ecart_many: "قبل {n} سنة",
    ecart_other: "قبل {n} سنة",

    /* Comparaison entre pays */
    comparer_stop: "العودة إلى القيم",
    ecart_titre: "الفارق",
    reference_pays: "بلد المقارنة",
    unite_points: "نقطة",
    unite_annees: "سنة",
    an_zero: "{n} سنة",
    an_one: "سنة",
    an_two: "سنتان",
    an_few: "{n} سنوات",
    an_many: "{n} سنة",
    an_other: "{n} سنة",

    /* Onglet « Comparer » */
    onglet_comparer: "قارن",

    onglet_records: "الأرقام القياسية",
    record_titre: "سنة الذروة — {carte}",
    record_unite: "سنوات منذ الذروة",
    record_valeur: "الذروة",
    record_annee: "سنة الذروة",
    record_aujourdhui: "الفارق عن الذروة في {annee}",
    record_invite: "انقر على بلد لعرض رقمه القياسي.",
    comparateur_choisir: "اختر بلدًا",
    comparateur_invite: "اختر بلدين لمعرفة الفارق بينهما.",
    comparateur_sans_donnee: "لا توجد سنة مشتركة بين هذين البلدين.",
    comparateur_choix_a: "بلد المقارنة",
    comparateur_choix_b: "البلد المقارَن",
    reference_court: "المرجع",
    ecart_en: "الفارق في {annee}",
    ecart_max: "أكبر فارق",
    ecart_min: "أصغر فارق",
    croisement: "آخر تقاطع",

    /* Divers */
    source: "المصدر",
    deux_points: ": ",
    mis_a_jour: "حُدِّث في",
    weo_avril: "أبريل",
    weo_octobre: "أكتوبر",
    voir_classement: "الترتيب",
    fermer: "إغلاق",
  },
};

/* Petit raccourci : t("recherche") renvoie le texte dans la langue de la page. */
window.StatsMapsT = function (langue) {
  var table = window.StatsMapsTextes[langue] || window.StatsMapsTextes.fr;
  return function (cle) {
    return table[cle] !== undefined ? table[cle] : cle;
  };
};
