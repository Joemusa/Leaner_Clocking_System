import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px

# -------------------------
# LOGIN CONFIGURATION
# -------------------------
USER_CREDENTIALS = {
    "admin": "1234",
    "school": "abcd"
}

def login():
    st.title("🔐 Scholar System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Invalid username or password")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Learner Clocking Dashboard", layout="wide")

# ----------------------------
# STYLING
# ----------------------------
st.markdown("""
<style>
.kpi-box {
    border: 1px solid #333;
    border-radius: 12px;
    padding: 18px;
    background-color: #1e1e1e;
    text-align: center;
    margin-bottom: 10px;
}
.kpi-title { font-size: 14px; color: #bbb; }
.kpi-value { font-size: 28px; color: #fff; font-weight: bold; }
.chart-box {
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px;
    background-color: #1e1e1e;
    margin-bottom: 18px;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 Learner Clocking Dashboard")

# ----------------------------
# GOOGLE SHEETS
# ----------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

client = gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data():
    workbook = client.open_by_key("1bEZcEAxRAcrlo_Aa92a0u_hFCZsaBZ2DSCMIKNqyblM")
    learner_df = pd.DataFrame(workbook.worksheet("Learner Tracker").get_all_records())
    reg_df = pd.DataFrame(workbook.worksheet("Registration Form").get_all_records())
    return learner_df, reg_df

learner_df, reg_df = load_data()

# ----------------------------
# CLEAN DATA (FIXED)
# ----------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

if "scan_date" in learner_df.columns:
    learner_df["scan_date"] = pd.to_datetime(learner_df["scan_date"], errors="coerce")

filtered_df = learner_df.copy()

# ----------------------------
# SIDEBAR FILTERS (FIXED)
# ----------------------------
st.sidebar.header("Filters")

if "scan_date" in filtered_df.columns:
    dates = filtered_df["scan_date"].dropna().dt.date.unique()
    selected = st.sidebar.multiselect("Date", sorted(dates), default=dates)
    filtered_df = filtered_df[filtered_df["scan_date"].dt.date.isin(selected)]

if "direction" in filtered_df.columns:
    opts = filtered_df["direction"].dropna().unique()
    selected = st.sidebar.multiselect("Direction", opts, default=opts)
    filtered_df = filtered_df[filtered_df["direction"].isin(selected)]

if "grade" in filtered_df.columns:
    opts = filtered_df["grade"].dropna().unique()
    selected = st.sidebar.multiselect("Grade", opts, default=opts)
    filtered_df = filtered_df[filtered_df["grade"].isin(selected)]

if "gender" in filtered_df.columns:
    opts = filtered_df["gender"].dropna().unique()
    selected = st.sidebar.multiselect("Gender", opts, default=opts)
    filtered_df = filtered_df[filtered_df["gender"].isin(selected)]

if "age" in filtered_df.columns:
    filtered_df["age"] = pd.to_numeric(filtered_df["age"], errors="coerce")
    opts = sorted(filtered_df["age"].dropna().unique())
    selected = st.sidebar.multiselect("Age", opts, default=opts)
    filtered_df = filtered_df[filtered_df["age"].isin(selected)]

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# ----------------------------
# KPI SECTION (FIXED)
# ----------------------------
k1, k2, k3 = st.columns(3)

with k1:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-title">Total Registered Learners</div>
        <div class="kpi-value">{len(reg_df)}</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    if "learner name" in learner_df.columns:
        total = learner_df["learner name"].notna().sum()
    else:
        total = len(learner_df)

    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-title">Total Attendance</div>
        <div class="kpi-value">{total}</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-box">
        <div class="kpi-title">Absent Learners</div>
        <div class="kpi-value">0</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------------------
# CHARTS (FIXED)
# ----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    if "grade" in filtered_df.columns:
        st.bar_chart(filtered_df["grade"].value_counts())
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    if "gender" in filtered_df.columns:
        st.bar_chart(filtered_df["gender"].value_counts())
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    if "age" in reg_df.columns:
        st.bar_chart(reg_df["age"].value_counts())
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# ATTENDANCE TREND (FIXED)
# ----------------------------
st.markdown('<div class="chart-box">', unsafe_allow_html=True)
st.subheader("Attendance Trend (Male vs Female)")

if "scan_date" in filtered_df.columns and "gender" in filtered_df.columns:

    df = filtered_df.copy()
    df["gender"] = df["gender"].str.capitalize()
    df = df.dropna(subset=["scan_date", "gender"])

    trend = df.groupby(["scan_date", "gender"]).size().reset_index(name="count")

    fig = px.area(trend, x="scan_date", y="count", color="gender")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Date or Gender column not found.")

st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# TABLE
# ----------------------------
st.dataframe(filtered_df)
