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

    .scroll-chart {
        overflow-x: auto;
        overflow-y: hidden;
        width: 100%;
        padding-bottom: 8px;
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
    "0 - 2 yrs","3 - 4 yrs","5 yrs","6 yrs","7 yrs","8 yrs","9 yrs",
    "10 yrs","11 yrs","12 yrs","13 yrs","14 yrs","15 yrs",
    "16 yrs","17 yrs","18 yrs"
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
    else:
        plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height, f"{int(height)}", ha="center")

    fig.tight_layout()
    st.pyplot(fig)

def plot_line_with_labels(df, xlabel="", ylabel="Count", scroll_key="chart"):
    if df.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))

    for col in df.columns:
        ax.plot(df.index, df[col].values, marker="o", label=str(col))

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    style_axes(ax)
    ax.legend()

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b-%y"))
    plt.setp(ax.get_xticklabels(), rotation=45)

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

# ✅ ONLY CHANGE → DATE DROPDOWN
if "scan_date" in filtered_df.columns and filtered_df["scan_date"].notna().any():
    unique_dates = sorted(filtered_df["scan_date"].dropna().dt.date.unique())
    date_options = ["All"] + [d.strftime("%d-%b-%Y") for d in unique_dates]

    selected_date = st.sidebar.selectbox("Select Date", options=date_options)

    if selected_date != "All":
        selected_date = pd.to_datetime(selected_date).date()
        filtered_df = filtered_df[
            filtered_df["scan_date"].dt.date == selected_date
        ]

# KEEP ALL OTHER FILTERS SAME
if "direction" in filtered_df.columns:
    direction_options = sorted(filtered_df["direction"].dropna().unique())
    selected_direction = st.sidebar.multiselect(
        "Direction", direction_options, default=direction_options
    )
    filtered_df = filtered_df[filtered_df["direction"].isin(selected_direction)]

if "Grade" in filtered_df.columns:
    grade_options = sorted(filtered_df["Grade"].dropna().unique())
    selected_grade = st.sidebar.multiselect(
        "Grade", grade_options, default=grade_options
    )
    filtered_df = filtered_df[filtered_df["Grade"].isin(selected_grade)]

if "Gender" in filtered_df.columns:
    gender_options = sorted(filtered_df["Gender"].dropna().unique())
    selected_gender = st.sidebar.multiselect(
        "Gender", gender_options, default=gender_options
    )
    filtered_df = filtered_df[filtered_df["Gender"].isin(selected_gender)]

if "Age" in filtered_df.columns:
    available_ages = [x for x in age_order if x in filtered_df["Age"].dropna().unique()]
    selected_age_groups = st.sidebar.multiselect(
        "Age Group", available_ages, default=available_ages
    )
    filtered_df = filtered_df[filtered_df["Age"].isin(selected_age_groups)]

# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Trend Charts",
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

    most_common_age_group = (
        filtered_df["Age"].mode().iloc[0]
        if "Age" in filtered_df.columns and filtered_df["Age"].notna().any()
        else "N/A"
    )

    k1, k2, k3 = st.columns(3)

    k1.markdown(f"<div class='kpi-box'><div class='kpi-title'>Total Records</div><div class='kpi-value'>{total_records}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi-box'><div class='kpi-title'>Total Registered</div><div class='kpi-value'>{total_registered}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi-box'><div class='kpi-title'>Most Common Age Group</div><div class='kpi-value'>{most_common_age_group}</div></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Learners by Grade")
        if "Grade" in filtered_df.columns:
            plot_bar_with_labels(filtered_df["Grade"].value_counts())

    with c2:
        st.subheader("Learners by Gender")
        if "Gender" in filtered_df.columns:
            plot_bar_with_labels(filtered_df["Gender"].value_counts())

# ----------------------------
# TREND TAB
# ----------------------------
with tab2:
    st.subheader("Direction Trend by Date")

    if "scan_date" in filtered_df.columns and "direction" in filtered_df.columns:
        trend = filtered_df.groupby(["scan_date", "direction"]).size().unstack(fill_value=0)
        plot_line_with_labels(trend)

# ----------------------------
# TABLES
# ----------------------------
with tab3:
    st.dataframe(filtered_df, use_container_width=True)

with tab4:
    st.dataframe(reg_df, use_container_width=True)
