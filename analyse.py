import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re

st.set_page_config(
    page_title="Analyse contenus clubs de foot",
    page_icon="⚽",
    layout="wide"
)

# -----------------------------
# CONFIG
# -----------------------------
FILE_PATH = "fichiers_communs_publications.xlsx.xlsx"

CLUB_RENAME = {
    "OM | Olympique de Marseille": "Olympique de Marseille"
}

ORDER_DAYS = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

# -----------------------------
# FONCTIONS
# -----------------------------
@st.cache_data
def load_data(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
    else:
        # utile si tu veux tester aussi avec un csv
        df = pd.read_csv(file, skiprows=1)
    return df


def classify_theme(text):
    """Classification simple par mots-clés."""
    if pd.isna(text):
        return "Autre"

    text = str(text).lower()

    themes = {
        "Match / résultat": [
            "match", "win", "goal", "but", "victoire", "defeat", "résumé",
            "highlights", "full time", "score", "final", "comeback"
        ],
        "Joueur / star": [
            "player", "joueur", "mbappé", "dembele", "haaland", "rodri",
            "ederson", "star", "legend", "captain"
        ],
        "Entraînement / préparation": [
            "training", "entrainement", "warm up", "session", "practice", "drill"
        ],
        "Coulisses / backstage": [
            "behind the scenes", "inside", "backstage", "locker room",
            "vestiaire", "coulisses", "tunnel"
        ],
        "Fans / communauté": [
            "fans", "supporters", "community", "crowd", "stadium atmosphere"
        ],
        "Annonce / communication": [
            "announcement", "official", "signing", "contract", "new kit",
            "maillot", "launch", "partnership"
        ],
        "Fun / divertissement": [
            "fun", "challenge", "quiz", "prank", "😂", "😅", "meme"
        ]
    }

    for theme, keywords in themes.items():
        for kw in keywords:
            if kw in text:
                return theme

    return "Autre"

def classify_context(text):
    if pd.isna(text):
        return "Autre"

    text = str(text).lower()

    if any(k in text for k in ["match", "goal", "but", "win", "score", "final", "highlights"]):
        return "Match"

    if any(k in text for k in ["transfer", "mercato", "signing", "contract"]):
        return "Transfert"

    if any(k in text for k in ["kit", "maillot", "new jersey", "third kit", "home kit", "away kit"]):
        return "Lancement maillot"

    return "Autre"

def prepare_data(df):
    df = df.copy()

    # Harmonisation noms clubs
    df["Profile name"] = df["Profile name"].replace(CLUB_RENAME)

    # Dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()].copy()

    df["year"] = df["Date"].dt.year
    df["month"] = df["Date"].dt.month
    df["month_name"] = df["Date"].dt.month_name()
    df["day_name"] = df["Date"].dt.day_name()
    df["hour"] = df["Date"].dt.hour

    # Vue principale : on prend Video view count sinon Media views
    df["views"] = df["Video view count"].fillna(df["Media views"])

    # Colonnes numériques utiles
    numeric_cols = [
        "Engagements",
        "Interaction Rate",
        "Virality Rate",
        "Total interactions",
        "Total shares",
        "Total comments",
        "Profile followers",
        "views"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Taux recalculé
    df["engagement_rate_calc"] = np.where(
        df["Profile followers"] > 0,
        (df["Engagements"] / df["Profile followers"]) * 100,
        np.nan
    )

    # Texte combiné pour la thématique
    df["text_for_theme"] = (
        df["Title"].fillna("").astype(str) + " " +
        df["Description"].fillna("").astype(str) + " " +
        df["Content"].fillna("").astype(str)
    )

    df["Theme"] = df["text_for_theme"].apply(classify_theme)
    df["Context"] = df["text_for_theme"].apply(classify_context)

    df["score"] = (
        df["views"].fillna(0) * 0.4 +
        df["Engagements"].fillna(0) * 0.4 +
        df["Total interactions"].fillna(0) * 0.2
    )
    return df


def metric_card(label, value):
    st.metric(label, value)


# -----------------------------
# INTERFACE
# -----------------------------
st.title("⚽ Analyse des performances des contenus des clubs")
st.markdown("Comparaison des clubs, formats, thématiques et performances des contenus.")

uploaded_file = st.file_uploader(
    "Importe ton fichier Excel ou CSV",
    type=["xlsx", "csv"]
)

if uploaded_file is None:
    st.info("Ajoute ton fichier `Groupe A_IUT.xlsx` pour lancer l’analyse.")
    st.stop()

# Chargement
df_raw = load_data(uploaded_file)
df = prepare_data(df_raw)

# -----------------------------
# SIDEBAR FILTRES
# -----------------------------
st.sidebar.header("Filtres")

clubs = sorted(df["Profile name"].dropna().unique().tolist())
platforms = sorted(df["Platform"].dropna().unique().tolist())
media_types = sorted(df["Media type"].dropna().unique().tolist())
themes = sorted(df["Theme"].dropna().unique().tolist())
contexts = sorted(df["Context"].dropna().unique().tolist())

selected_clubs = st.sidebar.multiselect("Clubs", clubs, default=clubs)
selected_platforms = st.sidebar.multiselect("Plateformes", platforms, default=platforms)
selected_media = st.sidebar.multiselect("Formats média", media_types, default=media_types)
selected_themes = st.sidebar.multiselect("Thématiques", themes, default=themes)
selected_contexts = st.sidebar.multiselect("Contextes", contexts, default=contexts)

date_min = df["Date"].min().date()
date_max = df["Date"].max().date()
selected_dates = st.sidebar.date_input(
    "Période",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max
)

if len(selected_dates) != 2:
    st.warning("Sélectionne une date de début et une date de fin.")
    st.stop()

start_date, end_date = selected_dates

df_filtered = df[
    (df["Profile name"].isin(selected_clubs)) &
    (df["Platform"].isin(selected_platforms)) &
    (df["Media type"].isin(selected_media)) &
    (df["Context"].isin(selected_contexts)) &
    (df["Theme"].isin(selected_themes)) &
    (df["Date"].dt.date >= start_date) &
    (df["Date"].dt.date <= end_date)
].copy()

if df_filtered.empty:
    st.warning("Aucune donnée avec les filtres actuels.")
    st.stop()

# -----------------------------
# KPIS
# -----------------------------
st.subheader("Vue d’ensemble")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    metric_card("Vues moyennes", f"{df_filtered['views'].mean():,.0f}".replace(",", " "))

with col2:
    likes_col = "Likes" if "Likes" in df_filtered.columns else None
    likes_value = df_filtered[likes_col].mean() if likes_col else np.nan
    metric_card("Likes moyens", f"{likes_value:,.0f}".replace(",", " ") if pd.notna(likes_value) else "N/A")

with col3:
    metric_card("Commentaires moyens", f"{df_filtered['Total comments'].mean():,.0f}".replace(",", " "))

with col4:
    metric_card("Partages moyens", f"{df_filtered['Total shares'].mean():,.0f}".replace(",", " "))

with col5:
    metric_card("Engagement moyen", f"{df_filtered['Engagements'].mean():,.0f}".replace(",", " "))

with col6:
    metric_card("Score moyen", f"{df_filtered['score'].mean():,.0f}".replace(",", " "))
st.markdown("---")

# -----------------------------
# ONGLET 1 : COMPARAISON CLUBS
# -----------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Comparaison clubs",
    "Plateformes",
    "Formats",
    "Thématiques",
    "Contexte",
    "Temps",
    "Top contenus"
])

with tab1:
    st.subheader("Comparaison entre les clubs")

    club_perf = (
        df_filtered.groupby("Profile name", as_index=False)
        .agg(
            nb_posts=("Profile name", "size"),
            engagement_moyen=("Engagements", "mean"),
            interaction_rate_moyen=("Interaction Rate", "mean"),
            virality_rate_moyen=("Virality Rate", "mean"),
            vues_moyennes=("views", "mean"),
            interactions_moyennes=("Total interactions", "mean"),
            shares_moyennes=("Total shares", "mean"),
            commentaires_moyens=("Total comments", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(club_perf, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            club_perf.sort_values("engagement_moyen", ascending=False),
            x="Profile name",
            y="engagement_moyen",
            title="Engagement moyen par club",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            club_perf.sort_values("interaction_rate_moyen", ascending=False),
            x="Profile name",
            y="interaction_rate_moyen",
            title="Interaction rate moyen par club",
            text_auto=".2f"
        )
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        fig = px.bar(
            club_perf.sort_values("vues_moyennes", ascending=False),
            x="Profile name",
            y="vues_moyennes",
            title="Vues moyennes par club",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        fig = px.bar(
            club_perf.sort_values("nb_posts", ascending=False),
            x="Profile name",
            y="nb_posts",
            title="Nombre de contenus publiés par club",
            text_auto=True
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Lecture rapide")
    if not club_perf.empty:
        best_engagement = club_perf.sort_values("engagement_moyen", ascending=False).iloc[0]
        best_ir = club_perf.sort_values("interaction_rate_moyen", ascending=False).iloc[0]
        most_active = club_perf.sort_values("nb_posts", ascending=False).iloc[0]

        st.markdown(
            f"""
- **Club le plus performant en engagement moyen** : **{best_engagement['Profile name']}**
- **Club avec le meilleur interaction rate** : **{best_ir['Profile name']}**
- **Club le plus actif** : **{most_active['Profile name']}**
"""
        )

with tab2:
    st.subheader("Analyse par plateforme")

    platform_perf = (
        df_filtered.groupby("Platform", as_index=False)
        .agg(
            nb_posts=("Platform", "size"),
            engagement_moyen=("Engagements", "mean"),
            interaction_rate_moyen=("Interaction Rate", "mean"),
            vues_moyennes=("views", "mean"),
            commentaires_moyens=("Total comments", "mean"),
            partages_moyens=("Total shares", "mean"),
            score_moyen=("score", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(platform_perf, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            platform_perf,
            x="Platform",
            y="engagement_moyen",
            title="Engagement moyen par plateforme",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            platform_perf,
            x="Platform",
            y="vues_moyennes",
            title="Vues moyennes par plateforme",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    fig = px.box(
        df_filtered,
        x="Platform",
        y="Engagements",
        title="Distribution de l’engagement par plateforme"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Analyse par format")

    format_perf = (
        df_filtered.groupby("Media type", as_index=False)
        .agg(
            nb_posts=("Media type", "size"),
            engagement_moyen=("Engagements", "mean"),
            interaction_rate_moyen=("Interaction Rate", "mean"),
            vues_moyennes=("views", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(format_perf, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            format_perf,
            x="Media type",
            y="engagement_moyen",
            title="Engagement moyen par format",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            format_perf,
            x="Media type",
            y="interaction_rate_moyen",
            title="Interaction rate moyen par format",
            text_auto=".2f"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Formats selon les clubs")
    format_club_perf = (
        df_filtered.groupby(["Profile name", "Media type"], as_index=False)
        .agg(engagement_moyen=("Engagements", "mean"))
    )

    fig = px.bar(
        format_club_perf,
        x="Profile name",
        y="engagement_moyen",
        color="Media type",
        barmode="group",
        title="Engagement moyen par club et par format"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Analyse par thématique")

    theme_perf = (
        df_filtered.groupby("Theme", as_index=False)
        .agg(
            nb_posts=("Theme", "size"),
            engagement_moyen=("Engagements", "mean"),
            interaction_rate_moyen=("Interaction Rate", "mean"),
            vues_moyennes=("views", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(theme_perf, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            theme_perf,
            x="Theme",
            y="engagement_moyen",
            title="Engagement moyen par thématique",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            theme_perf,
            x="Theme",
            y="interaction_rate_moyen",
            title="Interaction rate moyen par thématique",
            text_auto=".2f"
        )
        st.plotly_chart(fig, use_container_width=True)

    theme_club_perf = (
        df_filtered.groupby(["Profile name", "Theme"], as_index=False)
        .agg(engagement_moyen=("Engagements", "mean"))
    )

    fig = px.bar(
        theme_club_perf,
        x="Profile name",
        y="engagement_moyen",
        color="Theme",
        barmode="group",
        title="Engagement moyen par club et par thématique"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Analyse du contexte")

    context_perf = (
        df_filtered.groupby("Context", as_index=False)
        .agg(
            nb_posts=("Context", "size"),
            engagement_moyen=("Engagements", "mean"),
            interaction_rate_moyen=("Interaction Rate", "mean"),
            vues_moyennes=("views", "mean"),
            score_moyen=("score", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(context_perf, use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(
            context_perf,
            x="Context",
            y="engagement_moyen",
            title="Engagement moyen par contexte",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = px.bar(
            context_perf,
            x="Context",
            y="vues_moyennes",
            title="Vues moyennes par contexte",
            text_auto=".0f"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab6:
    st.subheader("Analyse temporelle")

    c1, c2 = st.columns(2)

    with c1:
        by_day = (
            df_filtered.groupby("day_name", as_index=False)
            .agg(engagement_moyen=("Engagements", "mean"))
        )
        by_day["day_name"] = pd.Categorical(by_day["day_name"], categories=ORDER_DAYS, ordered=True)
        by_day = by_day.sort_values("day_name")

        fig = px.bar(
            by_day,
            x="day_name",
            y="engagement_moyen",
            title="Engagement moyen par jour"
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        by_hour = (
            df_filtered.groupby("hour", as_index=False)
            .agg(engagement_moyen=("Engagements", "mean"))
            .sort_values("hour")
        )

        fig = px.line(
            by_hour,
            x="hour",
            y="engagement_moyen",
            markers=True,
            title="Engagement moyen par heure"
        )
        st.plotly_chart(fig, use_container_width=True)

    by_month = (
        df_filtered.groupby(["year", "month", "month_name"], as_index=False)
        .agg(engagement_moyen=("Engagements", "mean"))
        .sort_values(["year", "month"])
    )

    by_month["label"] = by_month["month_name"] + " " + by_month["year"].astype(str)

    fig = px.line(
        by_month,
        x="label",
        y="engagement_moyen",
        markers=True,
        title="Évolution mensuelle de l’engagement moyen"
    )
    st.plotly_chart(fig, use_container_width=True)

    by_context_day = (
        df_filtered.groupby(["day_name", "Context"], as_index=False)
        .agg(vues_moyennes=("views", "mean"))
    )
    by_context_day["day_name"] = pd.Categorical(
        by_context_day["day_name"],
        categories=ORDER_DAYS,
        ordered=True
    )
    by_context_day = by_context_day.sort_values("day_name")

    fig = px.line(
        by_context_day,
        x="day_name",
        y="vues_moyennes",
        color="Context",
        markers=True,
        title="Vues moyennes selon le jour et le contexte"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab7:
    st.subheader("Top contenus")

    score_options = {
        "Engagements": "Engagements",
        "Interaction Rate": "Interaction Rate",
        "Virality Rate": "Virality Rate",
        "Views": "views",
        "Total interactions": "Total interactions",
        "Score": "score"
    }

    selected_score = st.selectbox("Classer les contenus par", list(score_options.keys()))
    score_col = score_options[selected_score]

    top_n = st.slider("Nombre de contenus à afficher", min_value=5, max_value=30, value=10)

    cols_to_show = [
        "Date", "Profile name", "Platform", "Media type", "Theme",
        "Title", "Description", "Engagements", "Interaction Rate",
        "Virality Rate", "views", "Total interactions", "Total comments",
        "Total shares", "View on platform", "Collaborators", "Content"
    ]

    existing_cols = [c for c in cols_to_show if c in df_filtered.columns]

    top_contents = (
        df_filtered.sort_values(score_col, ascending=False)[existing_cols]
        .head(top_n)
    )

    st.dataframe(top_contents, use_container_width=True)

    st.subheader("Top 3 par club")
    top_by_club = (
        df_filtered.sort_values(score_col, ascending=False)
        .groupby("Profile name", group_keys=False)
        .head(3)[existing_cols]
    )
    st.dataframe(top_by_club, use_container_width=True)

# -----------------------------
# CONCLUSION AUTO
# -----------------------------
st.markdown("---")
st.subheader("Synthèse automatique")

club_perf_resume = (
    df_filtered.groupby("Profile name", as_index=False)
    .agg(
        engagement_moyen=("Engagements", "mean"),
        interaction_rate_moyen=("Interaction Rate", "mean"),
        nb_posts=("Profile name", "size")
    )
)

format_perf_resume = (
    df_filtered.groupby("Media type", as_index=False)
    .agg(engagement_moyen=("Engagements", "mean"))
    .sort_values("engagement_moyen", ascending=False)
)

theme_perf_resume = (
    df_filtered.groupby("Theme", as_index=False)
    .agg(engagement_moyen=("Engagements", "mean"))
    .sort_values("engagement_moyen", ascending=False)
)

if not club_perf_resume.empty and not format_perf_resume.empty and not theme_perf_resume.empty:
    best_club = club_perf_resume.sort_values("engagement_moyen", ascending=False).iloc[0]["Profile name"]
    best_ir_club = club_perf_resume.sort_values("interaction_rate_moyen", ascending=False).iloc[0]["Profile name"]
    best_format = format_perf_resume.iloc[0]["Media type"]
    best_theme = theme_perf_resume.iloc[0]["Theme"]

    st.markdown(
        f"""
### Enseignements clés
- Le club avec le **meilleur engagement moyen** est **{best_club}**.
- Le club avec le **meilleur interaction rate moyen** est **{best_ir_club}**.
- Le **format** le plus performant est **{best_format}**.
- La **thématique** la plus performante est **{best_theme}**.

### Recommandations
- Répliquer davantage les contenus du type **{best_format}**.
- Approfondir la thématique **{best_theme}**.
- Comparer les clubs non seulement sur l’engagement brut, mais aussi sur le **taux d’interaction**.
- Identifier les contenus les plus performants club par club pour reproduire leurs codes.
"""
    )