import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Analyse contenus clubs de foot",
    page_icon="⚽",
    layout="wide"
)

# =========================================================
# CONFIG
# =========================================================

ORDER_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data(file_path):

    if file_path.endswith(".xlsx"):

        df = pd.read_excel(file_path)

    else:

        df = pd.read_csv(
            file_path,
            decimal=","
        )

    return df

# =========================================================
# CLASSIFICATION THEMATIQUE
# =========================================================

def classify_theme(text):

    if pd.isna(text):
        return "Autre"

    text = str(text).lower()

    themes = {

        "Match / résultat": [
            "match",
            "goal",
            "but",
            "win",
            "score",
            "final",
            "victoire",
            "highlights"
        ],

        "Joueur / star": [
            "mbappe",
            "haaland",
            "rodri",
            "player",
            "star",
            "captain",
            "legend"
        ],

        "Fans / communauté": [
            "fans",
            "supporters",
            "community",
            "stadium"
        ],

        "Annonce / communication": [
            "official",
            "announcement",
            "contract",
            "signing",
            "partnership",
            "maillot",
            "kit"
        ],

        "Fun / divertissement": [
            "fun",
            "challenge",
            "quiz",
            "meme",
            "😂",
            "😅"
        ]
    }

    for theme, keywords in themes.items():

        for kw in keywords:

            if kw in text:
                return theme

    return "Autre"


# =========================================================
# CLASSIFICATION CONTEXTE
# =========================================================

def classify_context(text):

    if pd.isna(text):
        return "Autre"

    text = str(text).lower()

    if any(
        k in text
        for k in [
            "match",
            "goal",
            "but",
            "score",
            "highlights"
        ]
    ):
        return "Match"

    if any(
        k in text
        for k in [
            "transfer",
            "mercato",
            "signing",
            "contract"
        ]
    ):
        return "Transfert"

    if any(
        k in text
        for k in [
            "kit",
            "maillot",
            "jersey"
        ]
    ):
        return "Lancement maillot"

    return "Autre"


# =========================================================
# PREPARE DATA
# =========================================================

def prepare_data(df):

    df = df.copy()

    # -----------------------------------------------------
    # DATE
    # -----------------------------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce"
    )

    df = df[df["Date"].notna()].copy()

    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month
    df["month_name"] = df["Date"].dt.month_name()
    df["day_name"] = df["Date"].dt.day_name()
    df["hour"] = df["Date"].dt.hour

    # -----------------------------------------------------
    # NUMERIC
    # -----------------------------------------------------

    numeric_cols = [

        "Interactions_totales",
        "Commentaires",
        "Likes",
        "Partages",
        "createur_followers",

        "Interactions_totales_par_1k_followers",
        "Commentaires_par_1k_followers",
        "Likes_par_1k_followers",
        "Partages_par_1k_followers",

        "tiktok_views",
        "insta_collaborators_nb",
        "x_insta_nb_mentions",
        "tiktok_duree_secondes"
    ]

    for col in numeric_cols:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # -----------------------------------------------------
    # VIEWS
    # -----------------------------------------------------

    df["views"] = df["tiktok_views"].fillna(0)

    # -----------------------------------------------------
    # FORMAT
    # -----------------------------------------------------

    df["media_type"] = np.where(
        df["x_insta_media_type"].notna(),
        df["x_insta_media_type"],
        "tiktok_video"
    )

    # -----------------------------------------------------
    # TEXTE
    # -----------------------------------------------------

    df["text_for_theme"] = (
        df["Titre"]
        .fillna("")
        .astype(str)
    )

    # -----------------------------------------------------
    # THEME + CONTEXTE
    # -----------------------------------------------------

    df["Theme"] = df["text_for_theme"].apply(
        classify_theme
    )

    df["Context"] = df["text_for_theme"].apply(
        classify_context
    )

    # -----------------------------------------------------
    # SCORE
    # -----------------------------------------------------

    df["score"] = (

        df["Interactions_totales_par_1k_followers"]
        .fillna(0)
        * 0.5

        +

        df["Likes_par_1k_followers"]
        .fillna(0)
        * 0.3

        +

        df["Commentaires_par_1k_followers"]
        .fillna(0)
        * 0.2
    )

    return df


# =========================================================
# METRIC CARD
# =========================================================

def metric_card(label, value):

    st.metric(
        label,
        value
    )


# =========================================================
# INTERFACE
# =========================================================

st.title("⚽ Analyse des contenus football")

st.markdown(
    """
Analyse comparative des performances Instagram et TikTok.
"""
)

# =========================================================
# LOAD DATA LOCAL
# =========================================================

FILE_PATH = "data/fichiers_communs_publications.xlsx"

df_raw = load_data(FILE_PATH)

df = prepare_data(df_raw)

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filtres")

clubs = sorted(
    df["createur_nom"]
    .dropna()
    .unique()
    .tolist()
)

platforms = sorted(
    df["Platforme"]
    .dropna()
    .unique()
    .tolist()
)

media_types = sorted(
    df["media_type"]
    .dropna()
    .unique()
    .tolist()
)

themes = sorted(
    df["Theme"]
    .dropna()
    .unique()
    .tolist()
)

contexts = sorted(
    df["Context"]
    .dropna()
    .unique()
    .tolist()
)

selected_clubs = st.sidebar.multiselect(
    "Clubs",
    clubs,
    default=clubs
)

selected_platforms = st.sidebar.multiselect(
    "Plateformes",
    platforms,
    default=platforms
)

selected_media = st.sidebar.multiselect(
    "Formats",
    media_types,
    default=media_types
)

selected_themes = st.sidebar.multiselect(
    "Thématiques",
    themes,
    default=themes
)

selected_contexts = st.sidebar.multiselect(
    "Contextes",
    contexts,
    default=contexts
)

date_min = df["Date"].min().date()
date_max = df["Date"].max().date()

selected_dates = st.sidebar.date_input(
    "Période",
    value=(date_min, date_max)
)

if len(selected_dates) != 2:

    st.warning(
        "Sélectionne une période."
    )

    st.stop()

start_date, end_date = selected_dates

# =========================================================
# FONCTIONS DIVERSES
# =========================================================

def format_k(x):

    try:
        x = float(x)
    except:
        return x 

    if pd.isna(x):
        return ""

    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.1f}M"

    if abs(x) >= 1_000:
        return f"{x/1_000:.1f}k"

    return f"{x:.0f}"

# =========================================================
# FORMATAGE
# =========================================================

TABLE_FORMAT = {

    "interactions_moyennes": format_k,

    "Interactions_totales": format_k,
    "Likes": format_k,
    "Commentaires": format_k,
    "Partages": format_k,
    "tiktok_views": format_k,

    "score_moyen": "{:.2f}",
    "likes_1k": "{:.2f}",
    "commentaires_1k": "{:.2f}",

    "score": "{:.2f}",
    "Interactions_totales_par_1k_followers": "{:.2f}",
    "Commentaires_par_1k_followers": "{:.2f}",
    "Likes_par_1k_followers": "{:.2f}"

}


# =========================================================
# FILTER
# =========================================================

df_filtered = df[

    (df["createur_nom"].isin(selected_clubs))
    &

    (df["Platforme"].isin(selected_platforms))
    &

    (df["media_type"].isin(selected_media))
    &

    (df["Theme"].isin(selected_themes))
    &

    (df["Context"].isin(selected_contexts))
    &

    (df["Date"].dt.date >= start_date)
    &

    (df["Date"].dt.date <= end_date)

].copy()

if df_filtered.empty:

    st.warning(
        "Aucune donnée avec ces filtres."
    )

    st.stop()

# =========================================================
# KPI
# =========================================================

st.subheader("Vue d’ensemble")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:

    metric_card(
        "Nb contenus",
        f"{len(df_filtered):,}".replace(",", " ")
    )

with col2:

    metric_card(
        "Interactions moyennes",
        #f"{df_filtered['Interactions_totales'].mean():,.0f}".replace(",", " ")
        format_k(df_filtered["Interactions_totales"].mean())
    )

with col3:

    metric_card(
        "Likes / 1k followers",
        f"{df_filtered['Likes_par_1k_followers'].mean():.2f}"
    )

with col4:

    metric_card(
        "Commentaires / 1k",
        f"{df_filtered['Commentaires_par_1k_followers'].mean():.2f}"
    )

with col5:

    metric_card(
        "Score moyen",
        f"{df_filtered['score'].mean():.2f}"
    )

st.markdown("---")

# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Clubs",
    "Plateformes",
    "Formats",
    "Thématiques",
    "Temporalité",
    "Top contenus",
    "À propos"
])

# =========================================================
# TAB CLUBS
# =========================================================

with tab1:

    st.subheader("Comparaison des clubs")

    club_perf = (

        df_filtered
        .groupby("createur_nom", as_index=False)

        .agg(

            nb_posts=("createur_nom", "size"),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            ),

            commentaires_1k=(
                "Commentaires_par_1k_followers",
                "mean"
            ),

            score_moyen=(
                "score",
                "mean"
            )
        )

        .sort_values(
            "score_moyen",
            ascending=False
        )
    )

    
    st.dataframe(
        club_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )



    fig = px.bar(

        club_perf,

        x="createur_nom",
        y="score_moyen",

        title="Score moyen par club",

        text_auto=".2f"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# TAB PLATEFORMES
# =========================================================

with tab2:

    st.subheader("Analyse des plateformes")

    # =====================================================
    # PERFORMANCE PLATEFORMES
    # =====================================================

    platform_perf = (

        df_filtered
        .groupby("Platforme", as_index=False)

        .agg(

            nb_posts=("Platforme", "size"),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            ),

            score_moyen=(
                "score",
                "mean"
            )
        )
    )

    st.dataframe(
        platform_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # SCORE PAR PLATEFORME
    # =====================================================

    fig = px.bar(

        platform_perf,

        x="Platforme",
        y="score_moyen",

        color="Platforme",

        text_auto=".2f",

        title="Score moyen par plateforme"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # FOLLOWERS PAR CLUB / PLATEFORME
    # =====================================================

    st.markdown("---")

    st.subheader(
        "Followers par club et plateforme"
    )

    followers_perf = (

        df_filtered

        .groupby(
            ["createur_nom", "Platforme"],
            as_index=False
        )

        .agg(

            followers=(
                "createur_followers",
                "max"
            ),

            nb_posts=(
                "createur_nom",
                "size"
            ),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            ),

            score_moyen=(
                "score",
                "mean"
            )
        )

        .sort_values(
            "followers",
            ascending=False
        )
    )

    st.dataframe(
        followers_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # BARPLOT FOLLOWERS
    # =====================================================

    fig = px.bar(

        followers_perf,

        x="createur_nom",
        y="followers",

        color="Platforme",

        barmode="group",

        title="Nombre de followers par club et plateforme",

        text_auto=".2s"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # SCATTER FOLLOWERS VS SCORE
    # =====================================================

    st.subheader(
        "Relation followers / performance"
    )

    fig = px.scatter(

        followers_perf,

        x="followers",
        y="score_moyen",

        color="Platforme",

        size="nb_posts",

        hover_name="createur_nom",

        title="Followers vs score moyen",

        labels={
            "followers": "Followers",
            "score_moyen": "Score moyen"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # FOLLOWERS VS INTERACTIONS
    # =====================================================

    fig = px.scatter(

        followers_perf,

        x="followers",
        y="interactions_moyennes",

        color="Platforme",

        size="nb_posts",

        hover_name="createur_nom",

        title="Followers vs interactions moyennes",

        labels={
            "followers": "Followers",
            "interactions_moyennes": "Interactions moyennes"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # TOP CLUBS PAR PLATEFORME
    # =====================================================

    st.subheader(
        "Top clubs par plateforme"
    )

    top_platform_clubs = (

        followers_perf

        .sort_values(
            "followers",
            ascending=False
        )

        .groupby(
            "Platforme",
            group_keys=False
        )

        .head(10)
    )

    st.dataframe(
        top_platform_clubs.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # HEATMAP FOLLOWERS
    # =====================================================

    st.subheader(
        "Heatmap followers clubs / plateformes"
    )

    heatmap_data = followers_perf.pivot_table(
        index="createur_nom",
        columns="Platforme",
        values="followers",
        aggfunc="max"
    )

    fig = px.imshow(

        heatmap_data,

        aspect="auto",

        title="Heatmap des followers"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# TAB FORMATS
# =========================================================

with tab3:

    st.subheader("Analyse des formats")

    # =====================================================
    # PERFORMANCE GLOBALE DES FORMATS
    # =====================================================

    format_perf = (

        df_filtered
        .groupby("media_type", as_index=False)

        .agg(

            nb_posts=("media_type", "size"),

            score_moyen=("score", "mean"),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            ),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            )
        )
    )

    st.dataframe(
        format_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    fig = px.bar(

        format_perf,

        x="media_type",
        y="score_moyen",

        color="media_type",

        text_auto=".2f",

        title="Performance par format"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # FORMATS VS CLUBS
    # =====================================================

    st.markdown("---")

    st.subheader(
        "Formats selon les clubs"
    )

    format_club_perf = (

        df_filtered

        .groupby(
            ["createur_nom", "media_type"],
            as_index=False
        )

        .agg(

            nb_posts=(
                "media_type",
                "size"
            ),

            score_moyen=(
                "score",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            ),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            )
        )
    )

    st.dataframe(
        format_club_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # BARPLOT SCORE PAR CLUB / FORMAT
    # =====================================================

    fig = px.bar(

        format_club_perf,

        x="createur_nom",
        y="score_moyen",

        color="media_type",

        barmode="group",

        title="Score moyen par club et format",

        text_auto=".2f"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # NB POSTS PAR CLUB / FORMAT
    # =====================================================

    fig = px.bar(

        format_club_perf,

        x="createur_nom",
        y="nb_posts",

        color="media_type",

        barmode="stack",

        title="Répartition des formats par club"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # HEATMAP FORMAT / CLUB
    # =====================================================

    st.subheader(
        "Heatmap formats / clubs"
    )

    heatmap_club = format_club_perf.pivot_table(

        index="createur_nom",
        columns="media_type",
        values="score_moyen",
        aggfunc="mean"
    )

    fig = px.imshow(

        heatmap_club,

        aspect="auto",

        title="Heatmap score moyen format / club"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # FORMATS VS PLATEFORMES
    # =====================================================

    st.markdown("---")

    st.subheader(
        "Formats selon les plateformes"
    )

    format_platform_perf = (

        df_filtered

        .groupby(
            ["Platforme", "media_type"],
            as_index=False
        )

        .agg(

            nb_posts=(
                "media_type",
                "size"
            ),

            score_moyen=(
                "score",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            ),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            )
        )
    )

    st.dataframe(
        format_platform_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # SCORE FORMAT / PLATEFORME
    # =====================================================

    fig = px.bar(

        format_platform_perf,

        x="Platforme",
        y="score_moyen",

        color="media_type",

        barmode="group",

        title="Performance des formats selon la plateforme",

        text_auto=".2f"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # REPARTITION FORMATS / PLATEFORME
    # =====================================================

    fig = px.bar(

        format_platform_perf,

        x="Platforme",
        y="nb_posts",

        color="media_type",

        barmode="stack",

        title="Répartition des formats par plateforme"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # HEATMAP FORMAT / PLATEFORME
    # =====================================================

    st.subheader(
        "Heatmap formats / plateformes"
    )

    heatmap_platform = format_platform_perf.pivot_table(

        index="Platforme",
        columns="media_type",
        values="score_moyen",
        aggfunc="mean"
    )

    fig = px.imshow(

        heatmap_platform,

        aspect="auto",

        title="Heatmap score moyen format / plateforme"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# TAB THEMES
# =========================================================

with tab4:

    st.subheader("Analyse des thématiques")

    theme_perf = (

        df_filtered
        .groupby("Theme", as_index=False)

        .agg(

            nb_posts=("Theme", "size"),

            score_moyen=("score", "mean"),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            )
        )
    )

    st.dataframe(
        theme_perf.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    fig = px.bar(

        theme_perf,

        x="Theme",
        y="score_moyen",

        color="Theme",

        text_auto=".2f",

        title="Performance par thématique"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# TAB 5 - TEMPORALITE
# =========================================================

with tab5:

    st.subheader("Analyse temporelle")

    # =====================================================
    # POSTS PAR JOUR
    # =====================================================

    st.markdown("## Publications par jour")

    posts_by_day = (

        df_filtered

        .groupby(
            "day_name",
            as_index=False
        )

        .agg(

            nb_posts=("Titre", "size"),

            score_moyen=("score", "mean"),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            )
        )
    )

    posts_by_day["day_name"] = pd.Categorical(

        posts_by_day["day_name"],

        categories=ORDER_DAYS,

        ordered=True
    )

    posts_by_day = posts_by_day.sort_values(
        "day_name"
    )

    st.dataframe(
        posts_by_day.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:

        fig = px.bar(

            posts_by_day,

            x="day_name",
            y="nb_posts",

            text_auto=True,

            title="Nombre de publications par jour"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:

        fig = px.line(

            posts_by_day,

            x="day_name",
            y="score_moyen",

            markers=True,

            title="Score moyen par jour"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # ANALYSE HEURES
    # =====================================================

    st.markdown("---")

    st.markdown("## Analyse par heure")

    by_hour = (

        df_filtered

        .groupby(
            "hour",
            as_index=False
        )

        .agg(

            nb_posts=("Titre", "size"),

            score_moyen=("score", "mean"),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            )

        )

        .sort_values("hour")
    )

    st.dataframe(
        by_hour.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:

        fig = px.line(

            by_hour,

            x="hour",
            y="score_moyen",

            markers=True,

            title="Score moyen selon l'heure"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:

        fig = px.bar(

            by_hour,

            x="hour",
            y="nb_posts",

            text_auto=True,

            title="Nombre de publications par heure"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # EVOLUTION TEMPORELLE
    # =====================================================

    st.markdown("---")

    st.markdown("## Evolution temporelle")

    by_month = (

        df_filtered

        .groupby(
            ["year", "month", "month_name"],
            as_index=False
        )

        .agg(

            nb_posts=("Titre", "size"),

            score_moyen=("score", "mean"),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            )

        )

        .sort_values(
            ["year", "month"]
        )
    )

    by_month["label"] = (

        by_month["month_name"]
        + " "
        + by_month["year"].astype(str)
    )

    st.dataframe(
        by_month.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    fig = px.line(

        by_month,

        x="label",
        y="score_moyen",

        markers=True,

        title="Evolution mensuelle du score moyen"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # HEATMAP JOUR / HEURE
    # =====================================================

    st.markdown("---")

    st.markdown("## Heatmap jour / heure")

    heatmap_data = (

        df_filtered

        .groupby(
            ["day_name", "hour"],
            as_index=False
        )

        .agg(
            score_moyen=("score", "mean")
        )
    )

    heatmap_data["day_name"] = pd.Categorical(

        heatmap_data["day_name"],

        categories=ORDER_DAYS,

        ordered=True
    )

    heatmap_data = heatmap_data.sort_values(
        "day_name"
    )

    heatmap_pivot = heatmap_data.pivot_table(

        index="day_name",
        columns="hour",
        values="score_moyen"
    )

    fig = px.imshow(

        heatmap_pivot,

        aspect="auto",

        title="Heatmap score moyen jour / heure"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # ANALYSE CLUBS / HEURES
    # =====================================================

    st.markdown("---")

    st.markdown("## Clubs et horaires")

    club_hour_perf = (

        df_filtered

        .groupby(
            ["createur_nom", "hour"],
            as_index=False
        )

        .agg(

            nb_posts=("Titre", "size"),

            score_moyen=("score", "mean")
        )
    )

    fig = px.line(

        club_hour_perf,

        x="hour",
        y="score_moyen",

        color="createur_nom",

        markers=True,

        title="Performance des clubs selon l'heure"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # BEST TIME
    # =====================================================

    st.markdown("---")

    st.subheader("Meilleurs créneaux")

    best_hours = (

        by_hour

        .sort_values(
            "score_moyen",
            ascending=False
        )

        .head(10)
    )

    st.dataframe(
        best_hours.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # ANALYSE PAR DATE
    # =====================================================

    st.markdown("---")

    st.markdown("## Analyse par date")

    by_date = (

        df_filtered

        .groupby(
            df_filtered["Date"].dt.date,
            as_index=False
        )

        .agg(

            nb_posts=("Titre", "size"),

            score_moyen=("score", "mean"),

            interactions_moyennes=(
                "Interactions_totales",
                "mean"
            ),

            likes_1k=(
                "Likes_par_1k_followers",
                "mean"
            )
        )
    )

    by_date = (
        df_filtered
        .assign(date=df_filtered["Date"].dt.date)
        .groupby("date", as_index=False)
        .agg(
            nb_posts=("Titre", "size"),
            score_moyen=("score", "mean"),
            interactions_moyennes=("Interactions_totales", "mean"),
            likes_1k=("Likes_par_1k_followers", "mean")
        )
    )


    st.dataframe(
        by_date.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    c1, c2 = st.columns(2)

    with c1:

        fig = px.line(

            by_date,

            x="date",
            y="score_moyen",

            markers=True,

            title="Evolution quotidienne du score moyen"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with c2:

        fig = px.bar(

            by_date,

            x="date",
            y="nb_posts",

            text_auto=True,

            title="Nombre de publications par date"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # =====================================================
    # TOP DATES
    # =====================================================

    st.markdown("---")

    st.markdown("## Dates les plus performantes")

    top_dates = (

        by_date

        .sort_values(
            "score_moyen",
            ascending=False
        )

        .head(10)
    )

    st.dataframe(
        top_dates.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    fig = px.bar(

        top_dates,

        x="date",
        y="score_moyen",

        text_auto=".2f",

        title="Top dates selon le score moyen"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # =====================================================
    # ANALYSE CLUBS / DATES
    # =====================================================

    st.markdown("---")

    st.markdown("## Evolution des clubs dans le temps")

    df_filtered["date"] = df_filtered["Date"].dt.date

    club_date_perf = (
        df_filtered
        .groupby(["date", "createur_nom"], as_index=False)
        .agg(score_moyen=("score", "mean"))
    )

    # club_date_perf = (

    #     df_filtered

    #     .groupby(
    #         [
    #             df_filtered["Date"].dt.date,
    #             "createur_nom"
    #         ],
    #         as_index=False
    #     )

    #     .agg(
    #         score_moyen=("score", "mean")
    #     )
    # )

    # st.write("Colonnes détectées :", club_date_perf.columns)
    # st.write(club_date_perf.head())

    club_date_perf.columns = [
        "date",
        "createur_nom",
        "score_moyen"
    ]

    fig = px.line(

        club_date_perf,

        x="date",
        y="score_moyen",

        color="createur_nom",

        markers=True,

        title="Evolution temporelle des performances des clubs"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =========================================================
# TAB TOP CONTENTS
# =========================================================

with tab6:

    st.subheader("Top contenus")

    # =====================================================
    # CHOIX DU TRI
    # =====================================================

    score_options = {

        "Score global": "score",

        "Interactions totales": "Interactions_totales",

        "Likes": "Likes",

        "Commentaires": "Commentaires",

        "Partages": "Partages",

        "Likes par 1k followers": "Likes_par_1k_followers",

        "Commentaires par 1k followers": "Commentaires_par_1k_followers",

        "Interactions par 1k followers": "Interactions_totales_par_1k_followers",

        "TikTok views": "tiktok_views",

        "Nombre de collaborateurs": "insta_collaborators_nb",

        "Nombre de mentions": "x_insta_nb_mentions"
    }

    selected_metric = st.selectbox(
        "Classer les contenus par",
        list(score_options.keys())
    )

    sort_col = score_options[selected_metric]

    # =====================================================
    # NOMBRE DE POSTS
    # =====================================================

    top_n = st.slider(
        "Nombre de contenus",
        min_value=5,
        max_value=30,
        value=10
    )

    # =====================================================
    # TABLE TOP POSTS
    # =====================================================

    cols_to_show = [

        "Date",
        "createur_nom",
        "Platforme",
        "media_type",
        "Theme",
        "Context",

        "Titre",

        "Interactions_totales",
        "Likes",
        "Commentaires",
        "Partages",

        "Interactions_totales_par_1k_followers",
        "Likes_par_1k_followers",
        "Commentaires_par_1k_followers",

        "tiktok_views",
        "insta_collaborators_nb",
        "x_insta_nb_mentions",

        "score",

        "URL"
    ]

    existing_cols = [
        c
        for c in cols_to_show
        if c in df_filtered.columns
    ]

    top_contents = (

        df_filtered

        .sort_values(
            sort_col,
            ascending=False
        )

        [existing_cols]

        .head(top_n)
    )

    st.dataframe(
        top_contents.style.format(TABLE_FORMAT),
        use_container_width=True
    )

    # =====================================================
    # TOP 3 PAR CLUB
    # =====================================================

    st.subheader("Top 3 par club")

    top_by_club = (

        df_filtered

        .sort_values(
            sort_col,
            ascending=False
        )

        .groupby(
            "createur_nom",
            group_keys=False
        )

        .head(3)

        [existing_cols]
    )

    st.dataframe(
        top_by_club.style.format(TABLE_FORMAT),
        use_container_width=True
    )

# =========================================================
# TAB A PROPOS
# =========================================================

with tab7:

    st.subheader("À propos du projet")

    st.markdown(
        """
Nous sommes un groupe de **6 étudiants en 3e année de BUT Sciences des Données**
(promo 2025-2026).


### Objectifs de l’étude

Dans le cadre d’une SAE autour de l’analyse des contenus publiés par des clubs de football sur les réseaux sociaux, 
cette étude à pour objectif de :

- Comparer la performance des contenus
- Identifier les facteurs de performance
- Proposer des recommandations **data-driven**
  afin d’optimiser les publications sur les réseaux sociaux

### Présentation du projet

👉 [Voir la présentation Canva](<placeholder>)

---

### Auteurs

- William LEFEBVRE 
- Clara LAURENT 
- Diego CASAS BARCENAS 

Ainsi que
- Matteo CAI
- Terryl HASSEN
- Leo JEAN UNITE

"""
    )

# =========================================================
# SYNTHÈSE
# =========================================================

st.markdown("---")

st.subheader("Synthèse automatique")

best_club = (

    df_filtered
    .groupby("createur_nom")["score"]
    .mean()
    .sort_values(ascending=False)
    .index[0]
)

best_platform = (

    df_filtered
    .groupby("Platforme")["score"]
    .mean()
    .sort_values(ascending=False)
    .index[0]
)

best_theme = (

    df_filtered
    .groupby("Theme")["score"]
    .mean()
    .sort_values(ascending=False)
    .index[0]
)

st.markdown(
    f"""
### Enseignements clés

- Club le plus performant : **{best_club}**
- Plateforme la plus performante : **{best_platform}**
- Thématique la plus performante : **{best_theme}**

### Recommandations

- Prioriser les contenus avec fort score normalisé.
- Comparer les clubs via les métriques par 1k followers.
- Identifier les formats dominants par plateforme.
- Reproduire les meilleures thématiques.
"""
)