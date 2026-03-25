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
.kpi-box {
    border: 1px solid #d9d9d9;
    border-radius: 12px;
    padding: 18px;
    background-color: #ffffff;
    text-align: center;
}
.kpi-title {
    font-size: 14px;
    color: #666;
}
.kpi-value {
    font-size: 28px;
    font-weight: bold;
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

    learner_raw = learner_ws.get_all_values()
    reg_raw = reg_ws.get_all_values()

    learner_df = pd.DataFrame(learner_raw[1:], columns=learner_raw[0])
    reg_df = pd.DataFrame(reg_raw[1:], columns=reg_raw[0])

    return learner_df, reg_df


learner_df, reg_df = load_data()

# ----------------------------
# CLEAN COLUMNS (FIX)
# ----------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

# ----------------------------
# VALIDATION
# ----------------------------
if "student_id" not in learner_df.columns:
    st.error("student_id missing in Learner Tracker")
    st.stop()

if "student_id" not in reg_df.columns:
    st.error("student_id missing in Registration Form")
    st.stop()

# ----------------------------
# CLEAN DATA
# ----------------------------
learner_df = learner_df[learner_df["student_id"].astype(str).str.strip() != ""]
reg_df = reg_df[reg_df["student_id"].astype(str).str.strip() != ""]

# ----------------------------
# KPI CALCULATIONS
# ----------------------------
registered = reg_df["student_id"].nunique()
attendance = learner_df["student_id"].nunique()

present_ids = set(learner_df["student_id"])
all_ids = set(reg_df["student_id"])

absent_ids = all_ids - present_ids
absent_df = reg_df[reg_df["student_id"].isin(absent_ids)]

# ----------------------------
# KPI DISPLAY
# ----------------------------
st.markdown("### KPIs")

k1, k2, k3 = st.columns(3)

k1.markdown(f"<div class='kpi-box'><div class='kpi-title'>Registered</div><div class='kpi-value'>{registered}</div></div>", unsafe_allow_html=True)
k2.markdown(f"<div class='kpi-box'><div class='kpi-title'>Attendance</div><div class='kpi-value'>{attendance}</div></div>", unsafe_allow_html=True)
k3.markdown(f"<div class='kpi-box'><div class='kpi-title'>Absent Learners</div><div class='kpi-value'>{len(absent_ids)}</div></div>", unsafe_allow_html=True)

# ----------------------------
# CHARTS
# ----------------------------
c1, c2 = st.columns(2)

# ABSENT PIE
with c1:
    st.subheader("Absent Learners by Gender")

    if "gender" in absent_df.columns:
        counts = absent_df["gender"].value_counts()

        fig, ax = plt.subplots()
        ax.pie(counts, labels=counts.index, autopct='%1.0f%%')
        ax.axis("equal")

        st.pyplot(fig)

# PRESENT BAR
with c2:
    st.subheader("Present Learners by Gender")

    present_df = reg_df[reg_df["student_id"].isin(present_ids)]

    if "gender" in present_df.columns:
        counts = present_df["gender"].value_counts()

        fig, ax = plt.subplots()
        bars = ax.bar(counts.index, counts.values)

        for bar in bars:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(int(bar.get_height())), ha="center")

        st.pyplot(fig)

# ----------------------------
# ABSENT TABLE
# ----------------------------
st.subheader("Absent Learners List")

if not absent_df.empty:
    st.dataframe(absent_df, use_container_width=True)
else:
    st.success("No absent learners 🎉")

# ----------------------------
# TABS (UNCHANGED)
# ----------------------------
tab1, tab2 = st.tabs(["Learner Tracker", "Registration"])

with tab1:
    st.dataframe(learner_df, use_container_width=True)

with tab2:
    st.dataframe(reg_df, use_container_width=True)
