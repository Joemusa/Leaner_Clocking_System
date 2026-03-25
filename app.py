import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Learner Attendance Dashboard", layout="wide")
st.title("📊 Learner Attendance Dashboard")

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
# LOAD DATA (SAFE)
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
# CLEAN COLUMN NAMES (🔥 FIX)
# ----------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

# ----------------------------
# VALIDATION
# ----------------------------
if "student_id" not in learner_df.columns:
    st.error("❌ 'student_id' missing in Learner Tracker")
    st.write("Columns found:", learner_df.columns.tolist())
    st.stop()

if "student_id" not in reg_df.columns:
    st.error("❌ 'student_id' missing in Registration Form")
    st.write("Columns found:", reg_df.columns.tolist())
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
k1, k2, k3 = st.columns(3)

k1.metric("Registered", registered)
k2.metric("Attendance", attendance)
k3.metric("Absent Learners", len(absent_ids))

# ----------------------------
# CHARTS
# ----------------------------
col1, col2 = st.columns(2)

# ABSENT PIE CHART
with col1:
    st.subheader("Absent Learners by Gender")

    if "gender" in absent_df.columns:
        counts = absent_df["gender"].value_counts()

        fig, ax = plt.subplots()
        ax.pie(counts, labels=counts.index, autopct='%1.0f%%')
        ax.axis("equal")

        st.pyplot(fig)
    else:
        st.warning("⚠️ 'gender' column missing in Registration Form")

# PRESENT BAR CHART
with col2:
    st.subheader("Present Learners by Gender")

    present_df = reg_df[reg_df["student_id"].isin(present_ids)]

    if "gender" in present_df.columns:
        counts = present_df["gender"].value_counts()

        fig, ax = plt.subplots()
        bars = ax.bar(counts.index, counts.values)

        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2,
                height,
                str(int(height)),
                ha="center",
                va="bottom"
            )

        st.pyplot(fig)
    else:
        st.warning("⚠️ 'gender' column missing")

# ----------------------------
# ABSENT TABLE
# ----------------------------
st.subheader("📋 Absent Learners")

if not absent_df.empty:
    st.dataframe(absent_df, use_container_width=True)
else:
    st.success("🎉 No absent learners today!")

# ----------------------------
# RAW DATA TABS
# ----------------------------
tab1, tab2 = st.tabs(["Learner Tracker", "Registration"])

with tab1:
    st.dataframe(learner_df, use_container_width=True)

with tab2:
    st.dataframe(reg_df, use_container_width=True)
