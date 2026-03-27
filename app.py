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
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    .kpi-box {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 18px;
        background-color: #ffffff;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        text-align: center;
        margin-bottom: 10px;
    }
    .kpi-title { font-size: 14px; color: #666666; margin-bottom: 8px; font-weight: 600; }
    .kpi-value { font-size: 28px; font-weight: 700; color: #111111; }
    .chart-box {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 16px;
        background-color: #ffffff;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
        margin-bottom: 18px;
    }
    .section-title { font-size: 18px; font-weight: 700; margin-bottom: 10px; }
    .scroll-chart { overflow-x: auto; width: 100%; padding-bottom: 8px; }
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

    learner_df = pd.DataFrame(learner_ws.get_all_records())
    reg_df = pd.DataFrame(reg_ws.get_all_records())

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

# ----------------------------
# CHART SETTINGS
# ----------------------------
FIG_SIZE = (8, 4.5)
BAR_COLOR = "#4e79a7"

def style_axes(ax):
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

def plot_bar_with_labels(series, xlabel=""):
    if series.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    bars = ax.bar(series.index.astype(str), series.values, color=BAR_COLOR)

    style_axes(ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Count")

    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            str(int(height)),
            ha='center',
            va='bottom'
        )

    fig.tight_layout()
    st.pyplot(fig)

# ----------------------------
# FILTERED COPY
# ----------------------------
filtered_df = learner_df.copy()

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

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Grade")
        if "Grade" in filtered_df.columns:
            plot_bar_with_labels(filtered_df["Grade"].value_counts().sort_index(), "Grade")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Gender")
        if "Gender" in filtered_df.columns:
            plot_bar_with_labels(filtered_df["Gender"].value_counts(), "Gender")
        st.markdown('</div>', unsafe_allow_html=True)

    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Movement by Direction")
        if "direction" in filtered_df.columns:
            plot_bar_with_labels(filtered_df["direction"].value_counts(), "Direction")
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Age Distribution")
        if "Age" in reg_df.columns:
            df = reg_df.copy()
            df["Age"] = df["Age"].astype(str).str.strip()
            plot_bar_with_labels(df["Age"].value_counts().sort_index(), "Age")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# TABLES
# ----------------------------
with tab3:
    st.dataframe(filtered_df, use_container_width=True)

with tab4:
    st.dataframe(reg_df, use_container_width=True)
