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

    .kpi-title { font-size: 14px; color: #666; font-weight: 600; }
    .kpi-value { font-size: 28px; font-weight: 700; }

    .chart-box {
        border: 1px solid #d9d9d9;
        border-radius: 12px;
        padding: 16px;
        background-color: #ffffff;
        margin-bottom: 18px;
    }

    .section-title { font-size: 18px; font-weight: 700; margin-bottom: 10px; }
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
# CLEAN COLUMN NAMES (FIX)
# ----------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

# ----------------------------
# VALIDATION
# ----------------------------
if "student_id" not in learner_df.columns:
    st.error("❌ student_id missing in Learner Tracker")
    st.stop()

if "student_id" not in reg_df.columns:
    st.error("❌ student_id missing in Registration Form")
    st.stop()

# ----------------------------
# CLEAN DATA
# ----------------------------
learner_df = learner_df[learner_df["student_id"].astype(str).str.strip() != ""]
reg_df = reg_df[reg_df["student_id"].astype(str).str.strip() != ""]

# ----------------------------
# FILTER COPY
# ----------------------------
filtered_df = learner_df.copy()

# ----------------------------
# SIDEBAR FILTERS (UNCHANGED)
# ----------------------------
st.sidebar.header("Filters")

if "direction" in filtered_df.columns:
    options = filtered_df["direction"].dropna().unique()
    selected = st.sidebar.multiselect("Direction", options, default=options)
    filtered_df = filtered_df[filtered_df["direction"].isin(selected)]

# ----------------------------
# KPI CALCULATIONS
# ----------------------------
registered = reg_df["student_id"].nunique()
attendance = filtered_df["student_id"].nunique()

present_ids = set(filtered_df["student_id"])
all_ids = set(reg_df["student_id"])

absent_ids = all_ids - present_ids
absent_df = reg_df[reg_df["student_id"].isin(absent_ids)]

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

    k1, k2, k3 = st.columns(3)

    k1.markdown(f"<div class='kpi-box'><div class='kpi-title'>Registered</div><div class='kpi-value'>{registered}</div></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='kpi-box'><div class='kpi-title'>Attendance</div><div class='kpi-value'>{attendance}</div></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='kpi-box'><div class='kpi-title'>Absent Learners</div><div class='kpi-value'>{len(absent_ids)}</div></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    # ABSENT PIE
    with c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Absent Learners by Gender")

        if "gender" in absent_df.columns:
            counts = absent_df["gender"].value_counts()
            fig, ax = plt.subplots()
            ax.pie(counts, labels=counts.index, autopct='%1.0f%%')
            ax.axis("equal")
            st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # PRESENT BAR
    with c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Present Learners by Gender")

        present_df = reg_df[reg_df["student_id"].isin(present_ids)]

        if "gender" in present_df.columns:
            counts = present_df["gender"].value_counts()
            fig, ax = plt.subplots()
            bars = ax.bar(counts.index, counts.values)

            for bar in bars:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(int(bar.get_height())), ha="center")

            st.pyplot(fig)
        st.markdown('</div>', unsafe_allow_html=True)

    # ABSENT TABLE
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.subheader("Absent Learners")

    if not absent_df.empty:
        st.dataframe(absent_df, use_container_width=True)
    else:
        st.success("No absent learners 🎉")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# KEEP YOUR EXISTING TABS
# ----------------------------
with tab3:
    st.dataframe(filtered_df, use_container_width=True)

with tab4:
    st.dataframe(reg_df, use_container_width=True)
