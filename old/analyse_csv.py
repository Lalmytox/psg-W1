import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Analyse clubs de foot - CSV",
    page_icon="⚽",
    layout="wide"
)

ORDER_DAYS = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

# -----------------------------
# OUTILS
# -----------------------------
@st.cache_data
def load_csv(file):
    # Ton CSV contient une 1re ligne "report run at ..."
    df = pd.read_csv(file, skiprows=1, encoding="utf-8-sig")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def classify_theme(row):
    text = " ".join([
        str(row.get("Video_Title", "")),
        str(row.get("Topics", "")),
        str(row.get("Categories", "")),
        str(row.get("Sound Title", "")),
    ]).lower()

    if any(k in text for k in ["match", "goal", "but", "win", "victoire", "score", "premier league", "association football"]):
        return "Match / performance sportive"

    if any(k in text for k in ["player", "rodri", "ederson", "haaland", "de bruyne", "footballer"]):
        return "Joueur / star"

    if any(k in text for k in ["training", "warm up", "practice", "session"]):
        return "Entraînement"

    if any(k in text for k in ["behind the scenes", "inside", "backstage", "locker room", "tunnel", "coulisses"]):
        return "Coulisses"

    if any(k in text for k in ["fans", "supporters", "community", "stadium atmosphere"]):
        return "Fans / communauté"

    if any(k in text for k in ["commercial", "advertising", "partnership", "midea", "sponsor", "brand"]):
        return "Sponsor / partenariat"

    if any(k in text for k in ["fun", "challenge", "meme", "original sound", "😅", "😂"]):
        return "Fun / divertissement"

    return "Autre"


def prepare_data(df):
    df = df.copy()

    # Dates
    df["Published_Date"] = pd.to_datetime(df["Published_Date"], errors="coerce")
    df = df[df["Published_Date"].notna()].copy()

    df["year"] = df["Published_Date"].dt.year
    df["month"] = df["Published_Date"].dt.month
    df["month_name"] = df["Published_Date"].dt.month_name()
    df["day_name"] = df["Published_Date"].dt.day_name()
    df["hour"] = df["Published_Date"].dt.hour

    # Numériques
    numeric_cols = [
        "Views", "V1", "V2", "V3", "V7", "V30",
        "Total_Engagements",
        "ER1", "ER2", "ER3", "ER7", "ER30",
        "E1", "E2", "E3", "E7", "E30",
        "Likes", "Comments",
        "Twitter Favorites", "Tweets",
        "Facebook_Total_Engagements", "Facebook_Likes", "Facebook_Comments",
        "Facebook_Loves", "Facebook_Hahas", "Facebook_Wows",
        "Facebook_Sads", "Facebook_Angrys",
        "Creator_FollowerCount_or_YouTube_Subscribers",
        "Duration (seconds)"
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Variables utiles
    df["Theme"] = df.apply(classify_theme, axis=1)

    df["engagement_rate_calc"] = np.where(
        df["Creator_FollowerCount_or_YouTube_Subscribers"] > 0,
        (df["Total_Engagements"] / df["Creator_FollowerCount_or_YouTube_Subscribers"]) * 100,
        np.nan
    )

    df["duration_group"] = pd.cut(
        df["Duration (seconds)"],
        bins=[0, 15, 30, 60, 300, np.inf],
        labels=["0-15 sec", "16-30 sec", "31-60 sec", "1-5 min", "5+ min"],
        include_lowest=True
    )

    return df


# -----------------------------
# INTERFACE
# -----------------------------
st.title("⚽ Analyse des performances des contenus")
st.markdown("Analyse spécifique du fichier CSV des clubs de foot.")

uploaded_file = st.file_uploader("Importer le fichier CSV", type=["csv"])

if uploaded_file is None:
    st.info("Ajoute ton fichier `Group A_IUT.csv`.")
    st.stop()

df_raw = load_csv(uploaded_file)
df = prepare_data(df_raw)

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("Filtres")

creators = sorted(df["Creator"].dropna().unique().tolist())
platforms = sorted(df["Platform"].dropna().unique().tolist())
themes = sorted(df["Theme"].dropna().unique().tolist())

selected_creators = st.sidebar.multiselect("Clubs / créateurs", creators, default=creators)
selected_platforms = st.sidebar.multiselect("Plateformes", platforms, default=platforms)
selected_themes = st.sidebar.multiselect("Thématiques", themes, default=themes)

date_min = df["Published_Date"].min().date()
date_max = df["Published_Date"].max().date()

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
    (df["Creator"].isin(selected_creators)) &
    (df["Platform"].isin(selected_platforms)) &
    (df["Theme"].isin(selected_themes)) &
    (df["Published_Date"].dt.date >= start_date) &
    (df["Published_Date"].dt.date <= end_date)
].copy()

if df_filtered.empty:
    st.warning("Aucune donnée avec les filtres actuels.")
    st.stop()

# -----------------------------
# KPIS
# -----------------------------
st.subheader("Vue d’ensemble")

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Nb contenus", f"{len(df_filtered):,}".replace(",", " "))
c2.metric("Vues moyennes", f"{df_filtered['Views'].mean():,.0f}".replace(",", " "))
c3.metric("Engagement moyen", f"{df_filtered['Total_Engagements'].mean():,.0f}".replace(",", " "))
c4.metric("ER moyen recalculé", f"{df_filtered['engagement_rate_calc'].mean():.2f}%")
c5.metric("Durée moyenne", f"{df_filtered['Duration (seconds)'].mean():.1f} sec")

# -----------------------------
# ONGLETS
# -----------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Comparaison clubs",
    "Plateformes",
    "Thématiques",
    "Durée",
    "Temps",
    "Top contenus"
])

with tab1:
    st.subheader("Comparaison entre les clubs")

    club_perf = (
        df_filtered.groupby("Creator", as_index=False)
        .agg(
            nb_posts=("Creator", "size"),
            vues_moyennes=("Views", "mean"),
            engagement_moyen=("Total_Engagements", "mean"),
            likes_moyens=("Likes", "mean"),
            commentaires_moyens=("Comments", "mean"),
            er_calc_moyen=("engagement_rate_calc", "mean"),
            followers=("Creator_FollowerCount_or_YouTube_Subscribers", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(club_perf, use_container_width=True)

    fig = px.bar(
        club_perf,
        x="Creator",
        y="engagement_moyen",
        title="Engagement moyen par club",
        text_auto=".0f"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        club_perf.sort_values("er_calc_moyen", ascending=False),
        x="Creator",
        y="er_calc_moyen",
        title="Taux d’engagement recalculé moyen par club",
        text_auto=".2f"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        club_perf.sort_values("nb_posts", ascending=False),
        x="Creator",
        y="nb_posts",
        title="Nombre de contenus publiés par club",
        text_auto=True
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Analyse par plateforme")

    platform_perf = (
        df_filtered.groupby("Platform", as_index=False)
        .agg(
            nb_posts=("Platform", "size"),
            vues_moyennes=("Views", "mean"),
            engagement_moyen=("Total_Engagements", "mean"),
            er_calc_moyen=("engagement_rate_calc", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(platform_perf, use_container_width=True)

    fig = px.bar(
        platform_perf,
        x="Platform",
        y="engagement_moyen",
        title="Engagement moyen par plateforme",
        text_auto=".0f"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        platform_perf,
        x="Platform",
        y="vues_moyennes",
        title="Vues moyennes par plateforme",
        text_auto=".0f"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Analyse par thématique")

    theme_perf = (
        df_filtered.groupby("Theme", as_index=False)
        .agg(
            nb_posts=("Theme", "size"),
            vues_moyennes=("Views", "mean"),
            engagement_moyen=("Total_Engagements", "mean"),
            er_calc_moyen=("engagement_rate_calc", "mean")
        )
        .sort_values("engagement_moyen", ascending=False)
    )

    st.dataframe(theme_perf, use_container_width=True)

    fig = px.bar(
        theme_perf,
        x="Theme",
        y="engagement_moyen",
        title="Engagement moyen par thématique",
        text_auto=".0f"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        theme_perf,
        x="Theme",
        y="vues_moyennes",
        title="Vues moyennes par thématique",
        text_auto=".0f"
    )
    st.plotly_chart(fig, use_container_width=True)

    creator_theme_perf = (
        df_filtered.groupby(["Creator", "Theme"], as_index=False)
        .agg(engagement_moyen=("Total_Engagements", "mean"))
    )

    fig = px.bar(
        creator_theme_perf,
        x="Creator",
        y="engagement_moyen",
        color="Theme",
        barmode="group",
        title="Engagement moyen par club et par thématique"
    )
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Impact de la durée")

    duration_perf = (
        df_filtered.groupby("duration_group", as_index=False)
        .agg(
            nb_posts=("duration_group", "size"),
            vues_moyennes=("Views", "mean"),
            engagement_moyen=("Total_Engagements", "mean"),
            er_calc_moyen=("engagement_rate_calc", "mean")
        )
    )

    st.dataframe(duration_perf, use_container_width=True)

    fig = px.bar(
        duration_perf,
        x="duration_group",
        y="engagement_moyen",
        title="Engagement moyen selon la durée",
        text_auto=".0f"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(
        df_filtered,
        x="Duration (seconds)",
        y="Total_Engagements",
        color="Creator",
        title="Durée vs engagement",
        hover_data=["Video_Title", "Platform", "Views"]
    )
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Analyse temporelle")

    by_day = (
        df_filtered.groupby("day_name", as_index=False)
        .agg(engagement_moyen=("Total_Engagements", "mean"))
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

    by_hour = (
        df_filtered.groupby("hour", as_index=False)
        .agg(engagement_moyen=("Total_Engagements", "mean"))
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
        .agg(engagement_moyen=("Total_Engagements", "mean"))
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

with tab6:
    st.subheader("Top contenus")

    score_options = {
        "Vues": "Views",
        "Engagements": "Total_Engagements",
        "Likes": "Likes",
        "Commentaires": "Comments",
        "ER recalculé": "engagement_rate_calc"
    }

    selected_score = st.selectbox("Classer par", list(score_options.keys()))
    score_col = score_options[selected_score]

    top_n = st.slider("Nombre de contenus à afficher", 5, 30, 10)

    cols_to_show = [
        "Published_Date",
        "Creator",
        "Platform",
        "Video_Title",
        "Theme",
        "Views",
        "Total_Engagements",
        "Likes",
        "Comments",
        "Duration (seconds)",
        "Video_URL"
    ]

    top_contents = (
        df_filtered.sort_values(score_col, ascending=False)[cols_to_show]
        .head(top_n)
    )

    st.dataframe(top_contents, use_container_width=True)

# -----------------------------
# SYNTHESE AUTO
# -----------------------------
st.markdown("---")
st.subheader("Synthèse automatique")

club_perf_resume = (
    df_filtered.groupby("Creator", as_index=False)
    .agg(
        engagement_moyen=("Total_Engagements", "mean"),
        er_calc_moyen=("engagement_rate_calc", "mean"),
        nb_posts=("Creator", "size")
    )
)

theme_perf_resume = (
    df_filtered.groupby("Theme", as_index=False)
    .agg(engagement_moyen=("Total_Engagements", "mean"))
    .sort_values("engagement_moyen", ascending=False)
)

platform_perf_resume = (
    df_filtered.groupby("Platform", as_index=False)
    .agg(engagement_moyen=("Total_Engagements", "mean"))
    .sort_values("engagement_moyen", ascending=False)
)

if not club_perf_resume.empty and not theme_perf_resume.empty and not platform_perf_resume.empty:
    best_club = club_perf_resume.sort_values("engagement_moyen", ascending=False).iloc[0]["Creator"]
    best_ir_club = club_perf_resume.sort_values("er_calc_moyen", ascending=False).iloc[0]["Creator"]
    best_theme = theme_perf_resume.iloc[0]["Theme"]
    best_platform = platform_perf_resume.iloc[0]["Platform"]

    st.markdown(f"""
### Enseignements clés
- Le club avec le **meilleur engagement moyen** est **{best_club}**.
- Le club avec le **meilleur taux d’engagement recalculé** est **{best_ir_club}**.
- La **thématique** la plus performante est **{best_theme}**.
- La **plateforme** la plus performante est **{best_platform}**.

### Recommandations
- Reproduire davantage les contenus liés à **{best_theme}**.
- Comparer les clubs non seulement sur le volume de vues, mais surtout sur le **taux d’engagement**.
- Vérifier si certaines durées ou plateformes reviennent souvent dans les meilleurs contenus.
- Identifier les posts les plus performants par club pour en reproduire les codes.
""")