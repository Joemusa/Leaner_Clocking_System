import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


import streamlit as st

# -------------------------
# LOGIN CONFIGURATION
# -------------------------
USER_CREDENTIALS = {
    "admin": "1234",   # change this!
    "school": "abcd"   # change this!
}

# -------------------------
# LOGIN FUNCTION
# -------------------------
def login():
    st.title("🔐 Scholar System Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            st.session_state["logged_in"] = True
            st.success("Login successful ✅")
            st.rerun()
        else:
            st.error("Invalid username or password ❌")

# Initialize login state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# If NOT logged in → show login screen
if not st.session_state["logged_in"]:
    login()
    st.stop()

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Learner Clocking Dashboard",
    layout="wide"
)

# ----------------------------
# STYLING (FIXED ONLY THIS PART)
# ----------------------------
st.markdown("""
<style>
.block-container { padding-top: 1rem; padding-bottom: 1rem; }

.kpi-box {
    border: 1px solid #333;
    border-radius: 12px;
    padding: 18px;
    background-color: #1e1e1e;
    box-shadow: 0 1px 6px rgba(0,0,0,0.3);
    text-align: center;
    margin-bottom: 10px;
}

.kpi-title {
    font-size: 14px;
    color: #bbbbbb;
    margin-bottom: 8px;
    font-weight: 600;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
}

.chart-box {
    border: 1px solid #333;
    border-radius: 12px;
    padding: 16px;
    background-color: #1e1e1e;
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

    learner_df = pd.DataFrame(workbook.worksheet("Learner Tracker").get_all_records())
    reg_df = pd.DataFrame(workbook.worksheet("Registration Form").get_all_records())

    return learner_df, reg_df

learner_df, reg_df = load_data()

# ----------------------------
# CLEAN DATA
# ----------------------------
learner_df.columns = [str(col).strip() for col in learner_df.columns]
reg_df.columns = [str(col).strip() for col in reg_df.columns]

if "scan_date" in learner_df.columns:
    learner_df["scan_date"] = pd.to_datetime(
        learner_df["scan_date"], errors="coerce", dayfirst=True
    )

# ----------------------------
# FILTERS (UNCHANGED)
# ----------------------------
filtered_df = learner_df.copy()

st.sidebar.header("Filters")

if "scan_date" in filtered_df.columns and filtered_df["scan_date"].notna().any():
    unique_dates = sorted(filtered_df["scan_date"].dropna().dt.date.unique())
    date_options = [d.strftime("%d-%b-%Y") for d in unique_dates]

    selected_dates = st.sidebar.multiselect(
        "Select Date",
        options=date_options,
        default=[date_options[-1]] if date_options else []
    )

    if selected_dates:
        selected_dates = [pd.to_datetime(d).date() for d in selected_dates]
        filtered_df = filtered_df[
            filtered_df["scan_date"].dt.date.isin(selected_dates)
        ]

if "direction" in filtered_df.columns:
    options = sorted(filtered_df["direction"].dropna().unique())
    selected = st.sidebar.multiselect("Direction", options, default=options)
    filtered_df = filtered_df[filtered_df["direction"].isin(selected)]

if "Grade" in filtered_df.columns:
    options = sorted(filtered_df["Grade"].dropna().unique())
    selected = st.sidebar.multiselect("Grade", options, default=options)
    filtered_df = filtered_df[filtered_df["Grade"].isin(selected)]

if "Gender" in filtered_df.columns:
    options = sorted(filtered_df["Gender"].dropna().unique())
    selected = st.sidebar.multiselect("Gender", options, default=options)
    filtered_df = filtered_df[filtered_df["Gender"].isin(selected)]

if "Age" in filtered_df.columns:
    options = sorted(filtered_df["Age"].dropna().unique())
    selected = st.sidebar.multiselect("Age", options, default=options)
    filtered_df = filtered_df[filtered_df["Age"].isin(selected)]

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# ----------------------------
# CHART SETTINGS (UNCHANGED)
# ----------------------------
FIG_SIZE = (8, 4.5)
BAR_COLOR = "#4e79a7"

def style_axes(ax):
    ax.grid(axis="y", linestyle="--", alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

def plot_bar(series, label):
    if series.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=FIG_SIZE)
    bars = ax.bar(series.index.astype(str), series.values, color=BAR_COLOR)

    style_axes(ax)
    ax.set_xlabel(label)
    ax.set_ylabel("Count")

    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            str(int(bar.get_height())),
            ha='center', va='bottom'
        )

    st.pyplot(fig)

def plot_line(df):
    if df.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=(10,4.5))

    for col in df.columns:
        ax.plot(df.index, df[col], marker="o", label=col)

    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b-%y"))
    plt.xticks(rotation=45)
    style_axes(ax)

    st.pyplot(fig)

# ----------------------------
# TABS (UNCHANGED)
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Trend Charts",
    "Learner Tracker Table",
    "Registration Form Table"
])

# ----------------------------
# DASHBOARD TAB (UNCHANGED)
# ----------------------------
with tab1:

    st.markdown('<div class="section-title">Summary KPIs</div>', unsafe_allow_html=True)

    total_records = len(filtered_df)
    total_registered = len(reg_df)

    if "student_id" in learner_df.columns and "student_id" in reg_df.columns:
        learner_ids = set(learner_df["student_id"].astype(str).str.strip())
        reg_ids = set(reg_df["student_id"].astype(str).str.strip())
        absent_ids = reg_ids - learner_ids
        absent_count = len(absent_ids)
    else:
        absent_count = 0

    k1, k2, k3 = st.columns(3)

    
    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Registered Leaners</div>
            <div class="kpi-value">{total_registered}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Absent Learners</div>
            <div class="kpi-value">{absent_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        total_records = learner_df['leaner name'].notna().sum()

        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Attendance</div>
            <div class="kpi-value">{total_records}</div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(4)

    with col1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Grade")
        if "Grade" in filtered_df.columns:
            plot_bar(filtered_df["Grade"].value_counts().sort_index(), "Grade")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Gender")
        if "Gender" in filtered_df.columns:
            plot_bar(filtered_df["Gender"].value_counts(), "Gender")
        st.markdown('</div>', unsafe_allow_html=True)

   

    with col3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Age Distribution")
        if "Age" in reg_df.columns:
            df = reg_df.copy()
            df["Age"] = df["Age"].astype(str).str.strip()
            plot_bar(df["Age"].value_counts().sort_index(), "Age")
        st.markdown('</div>', unsafe_allow_html=True)

    col5 = st.column(1)
    
     with col3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Movement by Direction")
        if "direction" in filtered_df.columns:
            plot_bar(filtered_df["direction"].value_counts(), "Direction")
        st.markdown('</div>', unsafe_allow_html=True)
    

# ----------------------------
# TREND TAB (UNCHANGED)
# ----------------------------
with tab2:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Direction Trend")
        if "scan_date" in filtered_df.columns and "direction" in filtered_df.columns:
            df = filtered_df.groupby(["scan_date","direction"]).size().unstack(fill_value=0)
            plot_line(df)

    with col2:
        st.subheader("Gender Trend")
        if "scan_date" in filtered_df.columns and "Gender" in filtered_df.columns:
            df = filtered_df.groupby(["scan_date","Gender"]).size().unstack(fill_value=0)
            plot_line(df)

# ----------------------------
# TABLES (UNCHANGED)
# ----------------------------
with tab3:
    st.dataframe(filtered_df, use_container_width=True)

with tab4:
    st.dataframe(reg_df, use_container_width=True)
