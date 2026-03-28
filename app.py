import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px

# -------------------------
# LOGIN
# -------------------------
USER_CREDENTIALS = {"admin": "1234"}

def login():
    st.title("🔐 Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if USER_CREDENTIALS.get(u) == p:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid login")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# -------------------------
# PAGE
# -------------------------
st.set_page_config(layout="wide")
st.title("📊 Learner Dashboard")

# -------------------------
# GOOGLE SHEETS
# -------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

@st.cache_data
def load():
    wb = client.open_by_key("1bEZcEAxRAcrlo_Aa92a0u_hFCZsaBZ2DSCMIKNqyblM")
    return (
        pd.DataFrame(wb.worksheet("Learner Tracker").get_all_records()),
        pd.DataFrame(wb.worksheet("Registration Form").get_all_records())
    )

learner_df, reg_df = load()

# -------------------------
# CLEAN (IMPORTANT FIX)
# -------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

if "scan_date" in learner_df.columns:
    learner_df["scan_date"] = pd.to_datetime(learner_df["scan_date"], errors="coerce")

filtered_df = learner_df.copy()

# -------------------------
# FILTERS
# -------------------------
st.sidebar.header("Filters")

if "scan_date" in filtered_df.columns:
    dates = filtered_df["scan_date"].dropna().dt.date.unique()
    selected = st.sidebar.multiselect("Date", sorted(dates), default=dates)
    filtered_df = filtered_df[filtered_df["scan_date"].dt.date.isin(selected)]

if "gender" in filtered_df.columns:
    opts = filtered_df["gender"].dropna().unique()
    sel = st.sidebar.multiselect("Gender", opts, default=opts)
    filtered_df = filtered_df[filtered_df["gender"].isin(sel)]

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# -------------------------
# TABS (RESTORED ✅)
# -------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Trend Charts",
    "Learner Tracker",
    "Registration"
])

# =========================
# TAB 1: DASHBOARD
# =========================
with tab1:

    k1, k2, k3 = st.columns(3)

    with k1:
        st.metric("Total Registered", len(reg_df))

    with k2:
        if "learner name" in learner_df.columns:
            total = learner_df["learner name"].notna().sum()
        else:
            total = len(learner_df)
        st.metric("Total Attendance", total)

    with k3:
        st.metric("Absent", 0)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.subheader("Learners by Grade")
        if "grade" in filtered_df.columns:
            st.bar_chart(filtered_df["grade"].value_counts())

    with c2:
        st.subheader("Learners by Gender")
        if "gender" in filtered_df.columns:
            st.bar_chart(filtered_df["gender"].value_counts())

    with c3:
        st.subheader("Age Distribution")
        if "age" in reg_df.columns:
            st.bar_chart(reg_df["age"].value_counts())

    # 🔥 Attendance Trend FIXED
    st.subheader("Attendance Trend (Male vs Female)")

    if "scan_date" in filtered_df.columns and "gender" in filtered_df.columns:
        df = filtered_df.copy()
        df["gender"] = df["gender"].str.capitalize()

        trend = df.groupby(["scan_date", "gender"]).size().reset_index(name="count")

        fig = px.area(trend, x="scan_date", y="count", color="gender")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Date or Gender missing")

# =========================
# TAB 2: TREND CHARTS
# =========================
with tab2:

    if "scan_date" in filtered_df.columns and "gender" in filtered_df.columns:
        df = filtered_df.groupby(["scan_date", "gender"]).size().unstack(fill_value=0)
        st.line_chart(df)

# =========================
# TAB 3: LEARNER TABLE
# =========================
with tab3:
    st.dataframe(filtered_df)

# =========================
# TAB 4: REGISTRATION
# =========================
with tab4:
    st.dataframe(reg_df)
