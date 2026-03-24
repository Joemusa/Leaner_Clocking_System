import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Learner Clocking Dashboard",
    layout="wide"
)

# ----------------------------
# STYLING
# ----------------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    .kpi-box {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 18px;
        background-color: #ffffff;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        text-align: center;
        margin-bottom: 10px;
    }

    .kpi-title {
        font-size: 14px;
        color: #666666;
        margin-bottom: 8px;
        font-weight: 600;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #111111;
    }

    .chart-box {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 16px;
        background-color: #ffffff;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        margin-bottom: 18px;
    }

    .section-title {
        font-size: 18px;
        font-weight: 700;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Learner Clocking Dashboard")

# ----------------------------
# GOOGLE SHEETS CONNECTION
# ----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)

# ----------------------------
# LOAD DATA
# ----------------------------
@st.cache_data(ttl=300)
def load_data():
    workbook = client.open_by_key("1bEZcEAxRAcrlo_Aa92a0u_hFCZsaBZ2DSCMIKNqyblM")

    learner_ws = workbook.worksheet("Learner Tracker")
    reg_ws = workbook.worksheet("Registration Form")

    learner_data = learner_ws.get_all_records()
    reg_data = reg_ws.get_all_records()

    learner_df = pd.DataFrame(learner_data)
    reg_df = pd.DataFrame(reg_data)

    return learner_df, reg_df


learner_df, reg_df = load_data()

# ----------------------------
# CLEAN DATA
# ----------------------------
learner_df.columns = [str(col).strip() for col in learner_df.columns]
reg_df.columns = [str(col).strip() for col in reg_df.columns]

if "scan_date" in learner_df.columns:
    learner_df["scan_date"] = pd.to_datetime(
        learner_df["scan_date"],
        errors="coerce",
        dayfirst=True
    )

if "time_stamp" in learner_df.columns:
    learner_df["time_stamp"] = learner_df["time_stamp"].astype(str).str.strip()

if "Age" in learner_df.columns:
    learner_df["Age"] = learner_df["Age"].astype(str).str.strip()
    learner_df.loc[learner_df["Age"].isin(["", "nan", "None"]), "Age"] = pd.NA

age_order = [
    "0 - 2 yrs",
    "3 - 4 yrs",
    "5 yrs",
    "6 yrs",
    "7 yrs",
    "8 yrs",
    "9 yrs",
    "10 yrs",
    "11 yrs",
    "12 yrs",
    "13 yrs",
    "14 yrs",
    "15 yrs",
    "16 yrs",
    "17 yrs",
    "18 yrs"
]

# ----------------------------
# CHART HELPERS
# ----------------------------
def style_axes(ax):
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

def plot_bar_with_labels(series, xlabel="", ylabel="Count", rotate_xticks=False):
    if series.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(series.index.astype(str), series.values)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    style_axes(ax)

    if rotate_xticks:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    max_val = max(series.values) if len(series.values) > 0 else 0
    offset = max(max_val * 0.01, 0.1)

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + offset,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=9
        )

    fig.tight_layout()
    st.pyplot(fig)

def plot_line_with_labels(df, xlabel="", ylabel="Count"):
    if df.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for col in df.columns:
        ax.plot(df.index, df[col].values, marker="o", label=str(col))
        for x, y in zip(df.index, df[col].values):
            ax.text(x, y, str(int(y)), fontsize=8, ha="center", va="bottom")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    style_axes(ax)
    ax.legend()

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b-%y"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    fig.tight_layout()
    st.pyplot(fig)

# ----------------------------
# FILTERED COPY
# ----------------------------
filtered_df = learner_df.copy()

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filters")

if "scan_date" in filtered_df.columns and filtered_df["scan_date"].notna().any():
    min_date = filtered_df["scan_date"].min().date()
    max_date = filtered_df["scan_date"].max().date()

    date_range = st.sidebar.date_input(
        "Scan Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["scan_date"].dt.date >= start_date) &
            (filtered_df["scan_date"].dt.date <= end_date)
        ]

if "direction" in filtered_df.columns:
    direction_options = sorted([x for x in filtered_df["direction"].dropna().unique()])
    selected_direction = st.sidebar.multiselect(
        "Direction",
        options=direction_options,
        default=direction_options
    )
    if selected_direction:
        filtered_df = filtered_df[filtered_df["direction"].isin(selected_direction)]

if "Grade" in filtered_df.columns:
    grade_options = sorted([x for x in filtered_df["Grade"].dropna().unique()])
    selected_grade = st.sidebar.multiselect(
        "Grade",
        options=grade_options,
        default=grade_options
    )
    if selected_grade:
        filtered_df = filtered_df[filtered_df["Grade"].isin(selected_grade)]

if "Gender" in filtered_df.columns:
    gender_options = sorted([x for x in filtered_df["Gender"].dropna().unique()])
    selected_gender = st.sidebar.multiselect(
        "Gender",
        options=gender_options,
        default=gender_options
    )
    if selected_gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(selected_gender)]

if "Age" in filtered_df.columns:
    available_ages = [x for x in age_order if x in filtered_df["Age"].dropna().unique()]
    if available_ages:
        selected_age_groups = st.sidebar.multiselect(
            "Age Group",
            options=available_ages,
            default=available_ages
        )
        if selected_age_groups:
            filtered_df = filtered_df[filtered_df["Age"].isin(selected_age_groups)]

# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "Dashboard",
    "Learner Tracker Table",
    "Registration Form Table"
])

# ----------------------------
# DASHBOARD TAB
# ----------------------------
with tab1:
    st.markdown('<div class="section-title">Summary KPIs</div>', unsafe_allow_html=True)

    total_records = len(filtered_df)
    total_registered = len(reg_df)

    if "Age" in filtered_df.columns and filtered_df["Age"].notna().any():
        most_common_age_group = filtered_df["Age"].mode().iloc[0]
    else:
        most_common_age_group = "N/A"

    k1, k2, k3 = st.columns(3)

    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Records</div>
            <div class="kpi-value">{total_records}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Registered</div>
            <div class="kpi-value">{total_registered}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Most Common Age Group</div>
            <div class="kpi-value">{most_common_age_group}</div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Grade")
        if "Grade" in filtered_df.columns and not filtered_df.empty:
            grade_count = filtered_df["Grade"].value_counts().sort_index()
            plot_bar_with_labels(grade_count, xlabel="Grade")
        else:
            st.info("No Grade data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Gender")
        if "Gender" in filtered_df.columns and not filtered_df.empty:
            gender_count = filtered_df["Gender"].value_counts()
            plot_bar_with_labels(gender_count, xlabel="Gender")
        else:
            st.info("No Gender data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Movement by Direction")
        if "direction" in filtered_df.columns and not filtered_df.empty:
            direction_count = filtered_df["direction"].value_counts()
            plot_bar_with_labels(direction_count, xlabel="Direction")
        else:
            st.info("No direction data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Age Distribution")
        if "Age" in filtered_df.columns and filtered_df["Age"].notna().any():
            age_count = filtered_df["Age"].value_counts()
            age_count = age_count.reindex(age_order)
            age_count = age_count.dropna()
            age_count = age_count[age_count > 0]
            plot_bar_with_labels(age_count, xlabel="Age Group", rotate_xticks=True)
        else:
            st.info("No age data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    t1, t2 = st.columns(2)

    with t1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Direction Trended by Date")
        if (
            "scan_date" in filtered_df.columns and
            "direction" in filtered_df.columns and
            not filtered_df.empty
        ):
            direction_trend = (
                filtered_df.groupby(["scan_date", "direction"])
                .size()
                .unstack(fill_value=0)
                .sort_index()
            )
            plot_line_with_labels(direction_trend, xlabel="Date")
        else:
            st.info("No scan date or direction data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Gender Trended by Date")
        if (
            "scan_date" in filtered_df.columns and
            "Gender" in filtered_df.columns and
            not filtered_df.empty
        ):
            gender_trend = (
                filtered_df.groupby(["scan_date", "Gender"])
                .size()
                .unstack(fill_value=0)
                .sort_index()
            )
            plot_line_with_labels(gender_trend, xlabel="Date")
        else:
            st.info("No scan date or gender data available.")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# LEARNER TRACKER TABLE TAB
# ----------------------------
with tab2:
    st.subheader("Learner Tracker Data")
    st.dataframe(filtered_df, use_container_width=True)

# ----------------------------
# REGISTRATION FORM TABLE TAB
# ----------------------------
with tab3:
    st.subheader("Registration Form Data")
    st.dataframe(reg_df, use_container_width=True)
