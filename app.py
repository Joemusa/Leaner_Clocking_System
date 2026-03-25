import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Learner Clocking Dashboard", layout="wide")

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
# LOAD DATA (SAFE VERSION)
# ----------------------------
@st.cache_data(ttl=300)
def load_data():
    workbook = client.open_by_key("1bEZcEAxRAcrlo_Aa92a0u_hFCZsaBZ2DSCMIKNqyblM")

    learner_ws = workbook.worksheet("Learner Tracker")
    reg_ws = workbook.worksheet("Registration Form")

    # SAFE LOAD
    learner_raw = learner_ws.get_all_values()
    reg_raw = reg_ws.get_all_values()

    learner_df = pd.DataFrame(learner_raw[1:], columns=[c.strip() for c in learner_raw[0]])
    reg_df = pd.DataFrame(reg_raw[1:], columns=[c.strip() for c in reg_raw[0]])

    return learner_df, reg_df


learner_df, reg_df = load_data()

# ----------------------------
# CLEAN DATA
# ----------------------------
learner_df.columns = [c.strip() for c in learner_df.columns]
reg_df.columns = [c.strip() for c in reg_df.columns]

# Ensure student_id exists
if "student_id" not in reg_df.columns or "student_id" not in learner_df.columns:
    st.error("❌ 'student_id' column is required in BOTH sheets.")
    st.stop()

# Remove blanks
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

absent_count = len(absent_ids)

# ----------------------------
# KPI DISPLAY
# ----------------------------
k1, k2, k3 = st.columns(3)

with k1:
    st.metric("Registered", registered)

with k2:
    st.metric("Attendance", attendance)

with k3:
    st.metric("Absent Learners", absent_count)

# ----------------------------
# CHARTS
# ----------------------------
col1, col2 = st.columns(2)

# ----------------------------
# ABSENT PIE CHART (Gender)
# ----------------------------
with col1:
    st.subheader("Absent Learners by Gender")

    if "Gender" in absent_df.columns:
        gender_counts = absent_df["Gender"].value_counts()

        fig, ax = plt.subplots()
        ax.pie(gender_counts, labels=gender_counts.index, autopct='%1.0f%%')
        ax.axis("equal")

        st.pyplot(fig)
    else:
        st.info("Gender column missing in Registration Form")

# ----------------------------
# PRESENT BAR CHART (Gender)
# ----------------------------
with col2:
    st.subheader("Present Learners by Gender")

    present_df = reg_df[reg_df["student_id"].isin(present_ids)]

    if "Gender" in present_df.columns:
        gender_counts = present_df["Gender"].value_counts()

        fig, ax = plt.subplots()
        ax.bar(gender_counts.index, gender_counts.values)

        for i, v in enumerate(gender_counts.values):
            ax.text(i, v, str(v), ha="center")

        st.pyplot(fig)
    else:
        st.info("Gender column missing")

# ----------------------------
# ABSENT TABLE
# ----------------------------
st.subheader("Absent Learners List")

if not absent_df.empty:
    st.dataframe(absent_df, use_container_width=True)
else:
    st.success("🎉 No absent learners today!")

# ----------------------------
# TABS
# ----------------------------
tab1, tab2 = st.tabs(["Learner Tracker", "Registration"])

with tab1:
    st.dataframe(learner_df, use_container_width=True)

with tab2:
    st.dataframe(reg_df, use_container_width=True)
