import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Google Play Store Analytics",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📱 Google Play Store Data Analytics")
st.caption(
    "Interactive analytics dashboard | Python • Pandas • Plotly • Streamlit"
)

# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
EXCEL_FILE = BASE_DIR / "googleplaystore.csv.xlsx"
CSV_FILE = BASE_DIR / "googleplaystore.csv"


@st.cache_data
def load_data(file_path, file_type):
    if file_type == "excel":
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)

    df.columns = df.columns.str.strip()
    return df


try:
    if CSV_FILE.exists():
        raw_df = load_data(str(CSV_FILE), "csv")
    elif EXCEL_FILE.exists():
        raw_df = load_data(str(EXCEL_FILE), "excel")
    else:
        st.error(
            "Dataset not found. Place googleplaystore.csv.xlsx "
            "or googleplaystore.csv in the project folder."
        )
        st.stop()

except Exception as error:
    st.error(f"Could not read the dataset: {error}")
    st.stop()


# --------------------------------------------------
# DATA CLEANING
# --------------------------------------------------

def parse_size(value):
    """Convert app size strings into MB."""
    if pd.isna(value):
        return np.nan

    value = str(value).strip().upper()

    if value in ("", "NAN", "VARIES WITH DEVICE"):
        return np.nan

    try:
        if value.endswith("M"):
            return float(value[:-1])

        if value.endswith("K"):
            return float(value[:-1]) / 1024

        return float(value)
    except ValueError:
        return np.nan


def parse_installs(value):
    """Convert installs such as 10,000+ into numbers."""
    if pd.isna(value):
        return np.nan

    value = re.sub(r"[,+\s]", "", str(value))

    try:
        return float(value)
    except ValueError:
        return np.nan


def parse_price(value):
    """Convert price strings into numeric values."""
    if pd.isna(value):
        return np.nan

    value = str(value).strip().replace("$", "").replace(",", "")

    try:
        return float(value)
    except ValueError:
        return np.nan


def parse_android_version(value):
    """Extract the first numeric Android version."""
    if pd.isna(value):
        return np.nan

    match = re.search(r"(\d+(?:\.\d+)*)", str(value))

    if not match:
        return np.nan

    try:
        return float(match.group(1))
    except ValueError:
        return np.nan


df = raw_df.copy()

required_columns = [
    "App", "Category", "Rating", "Reviews", "Size",
    "Installs", "Type", "Price", "Content Rating",
    "Genres", "Last Updated", "Current Ver", "Android Ver"
]

missing_columns = [col for col in required_columns if col not in df.columns]

if missing_columns:
    st.error(f"Missing required columns: {missing_columns}")
    st.stop()

df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce")
df["Size_MB"] = df["Size"].apply(parse_size)
df["Installs_Num"] = df["Installs"].apply(parse_installs)
df["Price_Num"] = df["Price"].apply(parse_price)
df["Android_Min"] = df["Android Ver"].apply(parse_android_version)

df["Last Updated"] = pd.to_datetime(
    df["Last Updated"],
    errors="coerce"
)

df["Type"] = df["Type"].fillna("Unknown").astype(str).str.strip()
df["Category"] = df["Category"].fillna("Unknown").astype(str).str.strip()
df["Content Rating"] = df["Content Rating"].fillna("Unknown").astype(str)
df["App"] = df["App"].fillna("Unknown").astype(str)

df["Price_Num"] = df["Price_Num"].fillna(0).clip(lower=0)
df["Reviews"] = df["Reviews"].fillna(0).clip(lower=0)
df["Installs_Num"] = df["Installs_Num"].fillna(0).clip(lower=0)

# Invalid ratings are removed from rating analysis.
df.loc[~df["Rating"].between(1, 5), "Rating"] = np.nan

# Duplicate app/category records are removed for cleaner summaries.
df = df.drop_duplicates(subset=["App", "Category"], keep="first").copy()

df["Revenue_Estimate"] = np.where(
    df["Type"].str.lower() == "paid",
    df["Installs_Num"] * df["Price_Num"],
    0
)

df["Engagement_Rate"] = np.where(
    df["Installs_Num"] > 0,
    df["Reviews"] / df["Installs_Num"] * 100,
    np.nan
)

df["Month"] = df["Last Updated"].dt.to_period("M").astype(str)
df.loc[df["Last Updated"].isna(), "Month"] = np.nan

df["Year"] = df["Last Updated"].dt.year
df["Month_Number"] = df["Last Updated"].dt.month
df["Rating_Band"] = pd.cut(
    df["Rating"],
    bins=[4.0, 4.2, 4.5, 4.7, 5.01],
    labels=["4.0–4.2", "4.2–4.5", "4.5–4.7", "4.7–5.0"],
    include_lowest=True,
    right=True,
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

st.sidebar.title("🎛️ Dashboard Controls")

st.sidebar.write("Adjust the shared filters below.")

valid_ratings = df["Rating"].dropna()

rating_min = st.sidebar.slider(
    "Minimum rating",
    min_value=1.0,
    max_value=5.0,
    value=3.5,
    step=0.1,
)

installs_min = st.sidebar.number_input(
    "Minimum installs",
    min_value=0,
    value=10000,
    step=10000,
)

reviews_min = st.sidebar.number_input(
    "Minimum reviews",
    min_value=0,
    value=500,
    step=500,
)

size_min = st.sidebar.number_input(
    "Minimum app size (MB)",
    min_value=0.0,
    value=0.0,
    step=5.0,
)

size_max = st.sidebar.number_input(
    "Maximum app size (MB)",
    min_value=1.0,
    value=100.0,
    step=5.0,
)

all_categories = sorted(df["Category"].dropna().unique().tolist())

selected_categories = st.sidebar.multiselect(
    "Categories",
    options=all_categories,
    default=all_categories,
)

filtered = df[
    (df["Rating"] >= rating_min)
    & (df["Installs_Num"] >= installs_min)
    & (df["Reviews"] >= reviews_min)
    & (df["Size_MB"].between(size_min, size_max))
    & (df["Category"].isin(selected_categories))
].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    "Monthly charts represent app update activity, not monthly installs."
)

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------

k1, k2, k3, k4 = st.columns(4)

k1.metric("Apps in dataset", f"{len(df):,}")
k2.metric("Apps after filters", f"{len(filtered):,}")
k3.metric(
    "Average rating",
    f"{filtered['Rating'].mean():.2f}" if filtered["Rating"].notna().any() else "N/A",
)
k4.metric("Categories selected", f"{filtered['Category'].nunique():,}")

st.markdown("---")

# --------------------------------------------------
# SIX TASKS
# --------------------------------------------------

tabs = st.tabs([
    "1. Density Analysis",
    "2. Sunburst",
    "3. Calendar Heatmap",
    "4. Monthly Trends",
    "5. Category Heatmap",
    "6. Free vs Paid",
])


# ==================================================
# TASK 1: DENSITY ANALYSIS
# ==================================================

with tabs[0]:
    st.header("Task 1 — App Size vs Rating Density")

    st.write(
        "Explore the relationship between application size and user ratings. "
        "The shared filters are applied to this analysis."
    )

    density_df = filtered.dropna(subset=["Size_MB", "Rating"]).copy()

    if len(density_df) > 1:
        left, right = st.columns(2)

        with left:
            fig = px.density_heatmap(
                density_df,
                x="Size_MB",
                y="Rating",
                nbinsx=30,
                nbinsy=20,
                color_continuous_scale="Viridis",
                title="Density: App Size vs Rating",
                labels={
                    "Size_MB": "App Size (MB)",
                    "Rating": "User Rating",
                    "count": "Number of Apps",
                },
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            fig = px.histogram(
                density_df,
                x="Size_MB",
                marginal="box",
                nbins=35,
                title="App Size Distribution",
                labels={"Size_MB": "App Size (MB)"},
            )
            st.plotly_chart(fig, use_container_width=True)

        fig = px.scatter(
            density_df.sample(min(3000, len(density_df)), random_state=42),
            x="Size_MB",
            y="Rating",
            color="Category",
            hover_name="App",
            opacity=0.55,
            title="App Size vs Rating — Sampled Scatter Plot",
        )
        st.plotly_chart(fig, use_container_width=True)

        q1 = density_df["Size_MB"].quantile(0.25)
        q3 = density_df["Size_MB"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = density_df[
            (density_df["Size_MB"] < lower)
            | (density_df["Size_MB"] > upper)
        ]

        c1, c2, c3 = st.columns(3)
        c1.metric("Apps analysed", f"{len(density_df):,}")
        c2.metric("Size outliers (IQR)", f"{len(outliers):,}")
        c3.metric("IQR upper bound", f"{upper:.2f} MB")

        st.caption(
            "IQR outliers are statistical flags, not necessarily incorrect records."
        )

        st.subheader("Largest app-size outliers")
        st.dataframe(
            outliers[["App", "Category", "Size_MB", "Rating"]]
            .sort_values("Size_MB", ascending=False)
            .head(20),
            use_container_width=True,
        )

        st.subheader("Category distribution")
        cat_counts = (
            density_df.groupby("Category")
            .size()
            .reset_index(name="App Count")
            .sort_values("App Count", ascending=False)
        )

        st.plotly_chart(
            px.bar(
                cat_counts.head(15),
                x="Category",
                y="App Count",
                title="Top Categories by App Count",
            ),
            use_container_width=True,
        )

    else:
        st.info("Not enough records match the current filters.")

    with st.expander("Category translation examples"):
        st.write(
            "Beauty — Hindi: सुंदरता | Business — Tamil: வணிகம் | "
            "Dating — German: Dating"
        )
        st.caption(
            "These are illustrative labels, not translations of app descriptions."
        )


# ==================================================
# TASK 2: SUNBURST
# ==================================================

with tabs[1]:
    st.header("Task 2 — Category Sunburst Analysis")

    sun_df = filtered.dropna(subset=["Rating"]).copy()
    sun_df["Rating_Band_Display"] = sun_df["Rating_Band"].astype(str)
    sun_df.loc[
        sun_df["Rating_Band"].isna(),
        "Rating_Band_Display"
    ] = "Other"

    if not sun_df.empty:
        sun_df["App Type"] = sun_df["Type"].fillna("Unknown")

        # Aggregate records to keep the sunburst readable.
        sun_summary = (
            sun_df.groupby(
                ["Category", "App Type", "Rating_Band_Display"],
                observed=True,
            )
            .agg(
                Total_Installs=("Installs_Num", "sum"),
                App_Count=("App", "nunique"),
                Reviews_Total=("Reviews", "sum"),
                Rating_Weighted_Sum=(
                    "Rating",
                    lambda s: 0,
                ),
            )
            .reset_index()
        )

        weighted = (
            sun_df.assign(
                Rating_Weighted_Value=sun_df["Rating"] * sun_df["Reviews"].clip(lower=1)
            )
            .groupby(
                ["Category", "App Type", "Rating_Band_Display"],
                observed=True,
            )
            .agg(
                Weighted_Sum=("Rating_Weighted_Value", "sum"),
                Weight_Total=("Reviews", lambda s: s.clip(lower=1).sum()),
            )
            .reset_index()
        )

        sun_summary = sun_summary.merge(
            weighted,
            on=["Category", "App Type", "Rating_Band_Display"],
            how="left",
        )

        sun_summary["Weighted_Rating"] = np.where(
            sun_summary["Weight_Total"] > 0,
            sun_summary["Weighted_Sum"] / sun_summary["Weight_Total"],
            np.nan,
        )

        sun_summary["Installs_Display"] = sun_summary["Total_Installs"].map(
            lambda x: f"{x:,.0f}"
        )

        fig = px.sunburst(
            sun_summary,
            path=["Category", "App Type", "Rating_Band_Display"],
            values="Total_Installs",
            color="Weighted_Rating",
            color_continuous_scale="RdYlGn",
            hover_data={
                "Total_Installs": ":,.0f",
                "App_Count": True,
                "Weighted_Rating": ":.2f",
            },
            title="Category → App Type → Rating Band",
        )
        st.plotly_chart(fig, use_container_width=True)

        top_categories = (
            sun_df.groupby("Category")
            .agg(Total_Installs=("Installs_Num", "sum"))
            .sort_values("Total_Installs", ascending=False)
            .head(5)
            .reset_index()
        )

        st.subheader("Top 5 categories by recorded install counts")
        st.plotly_chart(
            px.bar(
                top_categories,
                x="Category",
                y="Total_Installs",
                title="Top Categories by Total Installs",
            ),
            use_container_width=True,
        )

        high_install_apps = sun_df[sun_df["Installs_Num"] > 1_000_000]

        st.metric(
            "Apps with more than 1 million installs",
            f"{len(high_install_apps):,}",
        )

        st.dataframe(
            high_install_apps[
                ["App", "Category", "Type", "Rating", "Installs_Num"]
            ]
            .sort_values("Installs_Num", ascending=False)
            .head(20),
            use_container_width=True,
        )

    else:
        st.info("No rated apps match the selected filters.")

    st.warning(
        "Country-level analysis is unavailable because the source dataset "
        "does not contain a Country column. Installs are reported counts, "
        "not verified global totals."
    )


# ==================================================
# TASK 3: CALENDAR HEATMAP
# ==================================================

with tabs[2]:
    st.header("Task 3 — App Update Calendar Heatmap")

    st.info(
        "This heatmap measures the number of apps last updated on each date. "
        "It does not measure monthly installs."
    )

    calendar_df = filtered.dropna(subset=["Last Updated"]).copy()

    if not calendar_df.empty:
        years = sorted(calendar_df["Year"].dropna().astype(int).unique().tolist())

        if years:
            chosen_year = st.selectbox(
                "Choose update year",
                years,
                index=len(years) - 1,
                key="calendar_year",
            )

            year_df = calendar_df[calendar_df["Year"] == chosen_year].copy()

            if not year_df.empty:
                year_df["Date_Only"] = year_df["Last Updated"].dt.normalize()

                daily = (
                    year_df.groupby("Date_Only")
                    .size()
                    .rename("Updated Apps")
                    .reset_index()
                )

                full_dates = pd.date_range(
                    f"{chosen_year}-01-01",
                    f"{chosen_year}-12-31",
                    freq="D",
                )

                daily = (
                    daily.set_index("Date_Only")
                    .reindex(full_dates, fill_value=0)
                    .rename_axis("Date")
                    .reset_index()
                )

                daily["Week"] = daily["Date"].dt.isocalendar().week.astype(int)
                daily["Weekday"] = daily["Date"].dt.dayofweek
                daily["Weekday_Name"] = daily["Date"].dt.day_name()

                pivot = daily.pivot_table(
                    index="Weekday",
                    columns="Week",
                    values="Updated Apps",
                    aggfunc="sum",
                    fill_value=0,
                ).reindex(index=range(7), fill_value=0)

                pivot.index = [
                    "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
                ]

                fig = px.imshow(
                    pivot,
                    aspect="auto",
                    color_continuous_scale="YlGnBu",
                    labels={
                        "x": "ISO Week",
                        "y": "Day of Week",
                        "color": "Updated Apps",
                    },
                    title=f"Daily App Update Activity — {chosen_year}",
                )
                st.plotly_chart(fig, use_container_width=True)

                monthly = (
                    year_df.groupby("Month")
                    .size()
                    .rename("Updated Apps")
                    .reset_index()
                )
                monthly["Month_Date"] = pd.to_datetime(
                    monthly["Month"] + "-01",
                    errors="coerce",
                )
                monthly = monthly.sort_values("Month_Date")
                monthly["MoM Change %"] = (
                    monthly["Updated Apps"].pct_change() * 100
                )
                monthly["3-Month Moving Average"] = (
                    monthly["Updated Apps"].rolling(3, min_periods=1).mean()
                )

                st.subheader("Monthly update activity and moving average")

                fig = go.Figure()
                fig.add_trace(
                    go.Bar(
                        x=monthly["Month"],
                        y=monthly["Updated Apps"],
                        name="Updated Apps",
                    )
                )
                fig.add_trace(
                    go.Scatter(
                        x=monthly["Month"],
                        y=monthly["3-Month Moving Average"],
                        name="3-Month Moving Average",
                        mode="lines+markers",
                    )
                )
                fig.update_layout(
                    xaxis_title="Month",
                    yaxis_title="App Update Records",
                )
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(
                    monthly[
                        ["Month", "Updated Apps", "MoM Change %",
                         "3-Month Moving Average"]
                    ],
                    use_container_width=True,
                )

    else:
        st.info("No valid update dates match the current filters.")

    with st.expander("Category translation examples"):
        st.write(
            "Beauty — Hindi: सुंदरता | Business — Tamil: வணிகம் | "
            "Dating — German: Dating"
        )


# ==================================================
# TASK 4: MONTHLY STREAMGRAPH / TRENDS
# ==================================================

with tabs[3]:
    st.header("Task 4 — Monthly Update Activity Trends")

    st.info(
        "The dataset does not contain actual monthly install history. "
        "These trends use app Last Updated dates as an update-activity proxy."
    )

    trend_df = filtered.dropna(subset=["Last Updated"]).copy()

    if not trend_df.empty:
        monthly_category = (
            trend_df.groupby(["Month", "Category"])
            .size()
            .rename("Updated Apps")
            .reset_index()
        )

        monthly_category["Month_Date"] = pd.to_datetime(
            monthly_category["Month"] + "-01",
            errors="coerce",
        )
        monthly_category = monthly_category.dropna(subset=["Month_Date"])

        metric_choice = st.radio(
            "Trend metric",
            ["Monthly activity", "Cumulative activity", "Growth rate"],
            horizontal=True,
            key="trend_metric",
        )

        pivot = monthly_category.pivot_table(
            index="Month_Date",
            columns="Category",
            values="Updated Apps",
            aggfunc="sum",
            fill_value=0,
        ).sort_index()

        # Limit visual complexity to the top categories.
        top_names = (
            monthly_category.groupby("Category")["Updated Apps"]
            .sum()
            .nlargest(10)
            .index
        )
        pivot = pivot.reindex(columns=top_names, fill_value=0)

        if metric_choice == "Cumulative activity":
            plot_data = pivot.cumsum()
        elif metric_choice == "Growth rate":
            plot_data = pivot.pct_change().replace(
                [np.inf, -np.inf], np.nan
            ) * 100
            plot_data = plot_data.fillna(0)
        else:
            plot_data = pivot

        fig = go.Figure()

        for category in plot_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=plot_data.index,
                    y=plot_data[category],
                    mode="lines",
                    stackgroup="one" if metric_choice != "Growth rate" else None,
                    name=str(category),
                )
            )

        fig.update_layout(
            title=f"{metric_choice} by Category — Top 10 Categories",
            xaxis_title="Month",
            yaxis_title=metric_choice,
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        overall = (
            trend_df.groupby("Month")
            .size()
            .rename("Updated Apps")
            .reset_index()
        )

        overall["Month_Date"] = pd.to_datetime(
            overall["Month"] + "-01",
            errors="coerce",
        )
        overall = overall.dropna(subset=["Month_Date"]).sort_values("Month_Date")

        full_months = pd.date_range(
            overall["Month_Date"].min(),
            overall["Month_Date"].max(),
            freq="MS",
        )

        overall = (
            overall.set_index("Month_Date")
            .reindex(full_months)
            .rename_axis("Month_Date")
            .reset_index()
        )

        overall["Growth %"] = (
            overall["Updated Apps"].pct_change() * 100
        )

        rolling_mean = overall["Growth %"].rolling(6, min_periods=3).mean()
        rolling_std = overall["Growth %"].rolling(6, min_periods=3).std()

        overall["Rolling Z-Score"] = (
            (overall["Growth %"] - rolling_mean)
            / rolling_std.replace(0, np.nan)
        )

        overall["Anomaly"] = (
            (overall["Growth %"] > 25)
            | (overall["Rolling Z-Score"] > 2)
        )

        st.subheader("Monthly growth and anomaly flags")

        st.dataframe(
            overall[
                ["Month_Date", "Updated Apps", "Growth %",
                 "Rolling Z-Score", "Anomaly"]
            ],
            use_container_width=True,
        )

    else:
        st.info("No valid update dates match the current filters.")

    with st.expander("Category translation examples"):
        st.write(
            "Travel & Local — French: Voyages et infos locales | "
            "Productivity — Spanish: Productividad | "
            "Photography — Japanese: 写真"
        )


# ==================================================
# TASK 5: CATEGORY PERFORMANCE HEATMAP
# ==================================================

with tabs[4]:
    st.header("Task 5 — Category Performance Heatmap")

    st.write(
        "Compare category-level performance using ratings, reviews, installs, "
        "app size, engagement and update frequency."
    )

    heat_df = filtered.copy()

    if not heat_df.empty:
        heat_df["Update_Year"] = heat_df["Last Updated"].dt.year
        heat_df["Update_Month"] = heat_df["Last Updated"].dt.month

        january_only = st.checkbox(
            "Use apps last updated in January",
            value=False,
        )

        if january_only:
            heat_df = heat_df[heat_df["Update_Month"] == 1]

        numeric_apps = st.checkbox(
            "Exclude app names containing numbers",
            value=False,
        )

        if numeric_apps:
            heat_df = heat_df[
                ~heat_df["App"].str.contains(r"\d", regex=True, na=False)
            ]

        if not heat_df.empty:
            category_metrics = (
                heat_df.groupby("Category")
                .agg(
                    App_Count=("App", "nunique"),
                    Total_Reviews=("Reviews", "sum"),
                    Total_Installs=("Installs_Num", "sum"),
                    Average_Size_MB=("Size_MB", "mean"),
                    Average_Rating=("Rating", "mean"),
                    Rating_Weight=("Reviews", "sum"),
                    Update_Frequency=("Last Updated", "count"),
                    Total_Weighted_Rating=(
                        "Rating",
                        lambda s: np.nan,
                    ),
                )
                .reset_index()
            )

            weighted_source = heat_df.dropna(subset=["Rating"]).copy()
            weighted_source["Rating_x_Reviews"] = (
                weighted_source["Rating"]
                * weighted_source["Reviews"].clip(lower=1)
            )

            weighted = (
                weighted_source.groupby("Category")
                .agg(
                    Weighted_Sum=("Rating_x_Reviews", "sum"),
                    Weighted_Count=("Reviews", lambda s: s.clip(lower=1).sum()),
                )
                .reset_index()
            )

            category_metrics = category_metrics.merge(
                weighted,
                on="Category",
                how="left",
            )

            category_metrics["Weighted_Rating"] = (
                category_metrics["Weighted_Sum"]
                / category_metrics["Weighted_Count"].replace(0, np.nan)
            )

            category_metrics["Engagement_Rate"] = np.where(
                category_metrics["Total_Installs"] > 0,
                category_metrics["Total_Reviews"]
                / category_metrics["Total_Installs"] * 100,
                np.nan,
            )

            metric_columns = [
                "Weighted_Rating",
                "Total_Reviews",
                "Total_Installs",
                "Average_Size_MB",
                "Engagement_Rate",
                "Update_Frequency",
            ]

            category_metrics = category_metrics.replace(
                [np.inf, -np.inf], np.nan
            )

            category_metrics = category_metrics.dropna(
                subset=["Weighted_Rating"]
            )

            if not category_metrics.empty:
                normalized = category_metrics.copy()

                for col in metric_columns:
                    mean_value = normalized[col].mean()
                    std_value = normalized[col].std()

                    if pd.isna(std_value) or std_value == 0:
                        normalized[col] = 0.0
                    else:
                        normalized[col] = (
                            normalized[col] - mean_value
                        ) / std_value

                st.subheader("Category composite score weights")

                w1, w2, w3 = st.columns(3)

                with w1:
                    weight_rating = st.slider(
                        "Rating weight", 0.0, 1.0, 0.30, 0.05
                    )
                    weight_reviews = st.slider(
                        "Reviews weight", 0.0, 1.0, 0.20, 0.05
                    )

                with w2:
                    weight_installs = st.slider(
                        "Installs weight", 0.0, 1.0, 0.20, 0.05
                    )
                    weight_engagement = st.slider(
                        "Engagement weight", 0.0, 1.0, 0.10, 0.05
                    )

                with w3:
                    weight_size = st.slider(
                        "Size weight", 0.0, 1.0, 0.05, 0.05
                    )
                    weight_updates = st.slider(
                        "Update-frequency weight", 0.0, 1.0, 0.15, 0.05
                    )

                weights = np.array([
                    weight_rating,
                    weight_reviews,
                    weight_installs,
                    weight_size,
                    weight_engagement,
                    weight_updates,
                ])

                if weights.sum() == 0:
                    weights = np.ones(6) / 6
                else:
                    weights = weights / weights.sum()

                normalized["Composite_Score"] = (
                    normalized[metric_columns].fillna(0).to_numpy()
                    @ weights
                )

                category_metrics["Composite_Score"] = normalized[
                    "Composite_Score"
                ].values

                display_mode = st.radio(
                    "Heatmap values",
                    ["Z-score normalized", "Raw values"],
                    horizontal=True,
                    key="category_heatmap_mode",
                )

                matrix_source = normalized if display_mode == "Z-score normalized" else category_metrics

                # Keep the ten highest scoring categories.
                selected = (
                    category_metrics.nlargest(10, "Composite_Score")["Category"]
                )

                plot_matrix = matrix_source[
                    matrix_source["Category"].isin(selected)
                ].set_index("Category")[metric_columns]

                fig = px.imshow(
                    plot_matrix,
                    aspect="auto",
                    color_continuous_scale="RdYlGn",
                    text_auto=".2f",
                    title=f"Top 10 Categories — {display_mode}",
                )

                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Top and bottom category scores")

                ordered = category_metrics.sort_values(
                    "Composite_Score", ascending=False
                )

                st.write("Top 3 categories")
                st.dataframe(ordered.head(3), use_container_width=True)

                st.write("Bottom 3 categories")
                st.dataframe(ordered.tail(3), use_container_width=True)

            else:
                st.info("Not enough valid rating data for this comparison.")
        else:
            st.info("No records remain after applying the selected filters.")

    else:
        st.info("No records match the current filters.")


# ==================================================
# TASK 6: FREE VS PAID RADAR
# ==================================================

with tabs[5]:
    st.header("Task 6 — Free vs Paid App Comparison")

    st.write(
        "Compare Free and Paid apps across installs, weighted ratings, reviews, "
        "size, estimated paid revenue and engagement."
    )

    radar_df = filtered.copy()

    everyone_only = st.checkbox(
        "Only Content Rating: Everyone",
        value=False,
    )

    if everyone_only:
        radar_df = radar_df[
            radar_df["Content Rating"].str.lower() == "everyone"
        ]

    short_names_only = st.checkbox(
        "Only app names of 30 characters or fewer",
        value=False,
    )

    if short_names_only:
        radar_df = radar_df[radar_df["App"].str.len() <= 30]

    minimum_android = st.number_input(
        "Minimum Android version (0 = no extra restriction)",
        min_value=0.0,
        max_value=15.0,
        value=0.0,
        step=0.5,
    )

    if minimum_android > 0:
        radar_df = radar_df[
            radar_df["Android_Min"] > minimum_android
        ]

    if not radar_df.empty:
        top5_categories = (
            radar_df.groupby("Category")["Installs_Num"]
            .sum()
            .nlargest(5)
            .index.tolist()
        )

        category_options = ["Overall"] + top5_categories

        chosen_category = st.selectbox(
            "Select category",
            category_options,
            key="radar_category",
        )

        if chosen_category != "Overall":
            radar_df = radar_df[
                radar_df["Category"] == chosen_category
            ]

        # Keep the Free/Paid groups distinct.
        radar_df = radar_df[
            radar_df["Type"].str.lower().isin(["free", "paid"])
        ].copy()

        if not radar_df.empty:
            radar_metrics = (
                radar_df.groupby(radar_df["Type"].str.title())
                .agg(
                    Average_Installs=("Installs_Num", "mean"),
                    Total_Reviews=("Reviews", "sum"),
                    Average_Size_MB=("Size_MB", "mean"),
                    Revenue_Estimate=("Revenue_Estimate", "sum"),
                    Average_Engagement=("Engagement_Rate", "mean"),
                    App_Count=("App", "nunique"),
                )
                .reset_index()
                .rename(columns={"Type": "App_Type"})
            )

            rating_data = (
                radar_df.dropna(subset=["Rating"])
                .assign(
                    Rating_Weighted=(
                        radar_df.dropna(subset=["Rating"])["Rating"]
                        * radar_df.dropna(subset=["Rating"])["Reviews"].clip(lower=1)
                    )
                )
                .groupby(radar_df.dropna(subset=["Rating"])["Type"].str.title())
                .agg(
                    Rating_Weighted_Total=("Rating_Weighted", "sum"),
                    Rating_Weight=("Reviews", lambda s: s.clip(lower=1).sum()),
                )
                .reset_index()
                .rename(columns={"Type": "App_Type"})
            )

            radar_metrics = radar_metrics.merge(
                rating_data,
                on="App_Type",
                how="left",
            )

            radar_metrics["Weighted_Rating"] = (
                radar_metrics["Rating_Weighted_Total"]
                / radar_metrics["Rating_Weight"].replace(0, np.nan)
            )

            metric_map = {
                "Average Installs": "Average_Installs",
                "Weighted Rating": "Weighted_Rating",
                "Total Reviews": "Total_Reviews",
                "Average Size (MB)": "Average_Size_MB",
                "Estimated Revenue": "Revenue_Estimate",
                "Engagement (%)": "Average_Engagement",
            }

            # Percentile normalization allows different scales to be compared.
            for label, col in metric_map.items():
                values = radar_metrics[col].fillna(0)

                if len(values) > 1:
                    radar_metrics[label] = values.rank(pct=True) * 100
                elif len(values) == 1:
                    radar_metrics[label] = 100.0
                else:
                    radar_metrics[label] = 0.0

            radar_categories = list(metric_map.keys())

            fig = go.Figure()

            for _, row in radar_metrics.iterrows():
                fig.add_trace(
                    go.Scatterpolar(
                        r=[row[c] for c in radar_categories],
                        theta=radar_categories,
                        fill="toself",
                        name=row["App_Type"],
                        hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
                    )
                )

            fig.update_layout(
                title="Free vs Paid — Percentile-Normalized Metrics",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100],
                    )
                ),
                showlegend=True,
            )

            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Underlying metrics")
            st.dataframe(radar_metrics, use_container_width=True)

            if not radar_metrics.empty:
                radar_metrics["Composite_Score"] = radar_metrics[
                    radar_categories
                ].mean(axis=1)

                winner = radar_metrics.sort_values(
                    "Composite_Score", ascending=False
                ).iloc[0]

                st.success(
                    f"Highest average normalized score: {winner['App_Type']} "
                    f"({winner['Composite_Score']:.1f}/100)."
                )

            st.caption(
                "Revenue is estimated as installs × listed price for Paid apps. "
                "It is not verified revenue. Installs are reported install bands "
                "converted to their displayed numeric values."
            )

            minimum_revenue = st.number_input(
                "Minimum estimated paid-app revenue",
                min_value=0.0,
                value=10000.0,
                step=1000.0,
            )

            paid_revenue = radar_df[
                (radar_df["Type"].str.lower() == "paid")
                & (radar_df["Revenue_Estimate"] > minimum_revenue)
            ]

            st.write(
                f"Paid apps with estimated revenue above "
                f"{minimum_revenue:,.0f}: {len(paid_revenue):,}"
            )

            st.dataframe(
                paid_revenue[
                    ["App", "Category", "Price_Num", "Installs_Num",
                     "Revenue_Estimate", "Rating"]
                ]
                .sort_values("Revenue_Estimate", ascending=False)
                .head(20),
                use_container_width=True,
            )

        else:
            st.info("No Free or Paid records match the selected filters.")

    else:
        st.info("No records match the current filters.")


# --------------------------------------------------
# DATA QUALITY & FOOTER
# --------------------------------------------------

with st.expander("📋 Data quality and project limitations"):
    st.write(f"Original rows: {len(raw_df):,}")
    st.write(f"Rows after duplicate removal: {len(df):,}")
    st.write(f"Missing ratings: {df['Rating'].isna().sum():,}")
    st.write(f"Missing app sizes: {df['Size_MB'].isna().sum():,}")
    st.write(f"Missing update dates: {df['Last Updated'].isna().sum():,}")

    st.markdown(
        """
        **Important limitations**

        - The dataset does not contain a Country field.
        - It does not provide actual monthly install history.
        - Last Updated measures the app's recorded update date, not the date
          an install occurred.
        - Install counts are displayed as numeric approximations from labels
          such as `10,000+`.
        - Revenue is an estimate based on listed price and reported installs.
        - App ratings and reviews may be missing or unevenly distributed.
        - This dashboard describes the supplied dataset; it does not access
          live Google Play Store data.
        """
    )

st.markdown("---")
st.caption(
    "Google Play Store Analytics | Built with Python, Pandas, Plotly and Streamlit"
)
