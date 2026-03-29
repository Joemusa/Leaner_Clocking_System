import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px


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
    # Clean Age column
    filtered_df['Age'] = pd.to_numeric(filtered_df['Age'], errors='coerce')

    options = sorted(filtered_df['Age'].dropna().unique())

    selected = st.sidebar.multiselect("Age", options, default=options)

    filtered_df = filtered_df[filtered_df['Age'].isin(selected)]
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Grade")
        if "Grade" in reg_df.columns:
            df = reg_df.copy()
            df["Grade"] = df["Grade"].astype(str).str.strip()
            plot_bar(df["Grade"].value_counts().sort_index(), "Grade")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Gender")
        if "Gender" in reg_df.columns:
            df = reg_df.copy()
            df["Gender"] = df["Gender"].astype(str).str.strip()
            plot_bar(reg_df["Gender"].value_counts(), "Gender")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Age Distribution")
        if "Age" in reg_df.columns:
            df = reg_df.copy()
            df["Age"] = df["Age"].astype(str).str.strip()
            plot_bar(df["Age"].value_counts().sort_index(), "Age")
        st.markdown('</div>', unsafe_allow_html=True)

    col4, col5 = st.columns(2)
    
    with col4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Yearly Attendance (Male vs Female)")
    
        # Clean column names
        reg_df.columns = reg_df.columns.str.strip().str.lower()
    
        if "timestamp" in reg_df.columns and "gender" in reg_df.columns:
    
            df = reg_df.copy()
    
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["year"] = df["timestamp"].dt.year
            df["gender"] = df["gender"].astype(str).str.strip().str.capitalize()
    
            df = df.dropna(subset=["year", "gender"])
    
            pivot = df.groupby(["year", "gender"]).size().unstack(fill_value=0).sort_index()

            # ✅ FIX YEAR FORMAT HERE
            pivot.index = pivot.index.astype(int).astype(str)
            
            import matplotlib.pyplot as plt
            
            plt.rcParams.update({
                "font.size": 8
            })
            
            fig, ax = plt.subplots(figsize=(12,4))    
            
            pivot.plot(kind="bar", stacked=True, ax=ax)
            
            # ✅ FORCE CLEAN X-AXIS LABELS
            ax.set_xticklabels(pivot.index, rotation=0)
    
            # ✅ REMOVE BORDER (spines)
            for spine in ax.spines.values():
                spine.set_visible(False)
    
            # ✅ LABELS INSIDE BARS
            for container in ax.containers:
                ax.bar_label(container, label_type='center', fontsize=7)
    
            # ✅ TOTAL LABELS ON TOP
            for i, year in enumerate(pivot.index):
                total = pivot.loc[year].sum()
                ax.text(i, total, str(int(total)), ha='center', va='bottom', fontsize=8)
    
            # Clean axes
            ax.set_title("")
            ax.set_xlabel("")
            ax.set_ylabel("")
    
            # White background
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
    
            st.pyplot(fig)
    
        else:
            st.warning("Timestamp or Gender column not found.")

    st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Total Registered by Race")
    
        # Clean column names
        reg_df.columns = reg_df.columns.str.strip().str.lower()
    
        if "timestamp" in reg_df.columns and "race" in reg_df.columns:
            df = reg_df.copy()
    
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["year"] = df["timestamp"].dt.year
            df["race"] = df["race"].astype(str).str.strip().str.capitalize()
    
            df = df.dropna(subset=["year", "race"])
    
            pivot = (
                df.groupby(["year", "race"])
                .size()
                .unstack(fill_value=0)
                .sort_index()
            )
    
            # ✅ FIX YEAR FORMAT
            pivot.index = pivot.index.astype(int).astype(str)
    
            import matplotlib.pyplot as plt
    
            plt.rcParams.update({
                "font.size": 8
            })
    
            fig, ax = plt.subplots(figsize=(12, 4))
    
            pivot.plot(kind="bar", stacked=True, ax=ax)
    
            # ✅ CLEAN X-AXIS
            ax.set_xticklabels(pivot.index, rotation=0)
    
            # ✅ REMOVE BORDER
            for spine in ax.spines.values():
                spine.set_visible(False)
    
            # ✅ LABELS INSIDE BARS
            for container in ax.containers:
                ax.bar_label(container, label_type='center', fontsize=7)
    
            # ✅ TOTAL LABELS ON TOP
            for i, year in enumerate(pivot.index):
                total = pivot.loc[year].sum()
                ax.text(i, total, str(int(total)), ha='center', va='bottom', fontsize=8)
    
            # ✅ CLEAN AXES
            ax.set_title("")
            ax.set_xlabel("")
            ax.set_ylabel("")
    
            # ✅ WHITE BACKGROUND
            fig.patch.set_facecolor("white")
            ax.set_facecolor("white")
    
            # ✅ SHOW ONLY ONCE
            st.pyplot(fig)
    
        else:
            st.warning("Timestamp or Race column not found.")
    
        st.markdown('</div>', unsafe_allow_html=True)
# ----------------------------
# TREND TAB (UNCHANGED)
# ----------------------------
with tab2:

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    df = learner_df.copy()
    
    df.columns = df.columns.str.strip().str.lower()
    
    # ✅ FIX COLUMN NAME HERE
    if "time_stamp" in df.columns and "gender" in df.columns:
    
        # ✅ USE CORRECT COLUMN
        df["scan_date"] = pd.to_datetime(df["scan_date"], errors="coerce")
        df["date"] = df["scan_date"].dt.date
        df["gender"] = df["gender"].astype(str).str.strip().str.capitalize()
    
        df = df.dropna(subset=["date", "gender"])
    
        # -----------------------------
        # AGGREGATE
        # -----------------------------
        attendance = (
            df.groupby(["date", "gender"])
            .size()
            .reset_index(name="count")
        )
    
        # ✅ CRITICAL FIX FOR PLOTLY
        attendance["date"] = pd.to_datetime(attendance["date"])
    
        # -----------------------------
        # SESSION STATE
        # -----------------------------
        if "selected_date" not in st.session_state:
            st.session_state.selected_date = None
    
        # -----------------------------
        # REFRESH BUTTON
        # -----------------------------
        colA, colB = st.columns([1, 5])
    
        with colA:
            if st.button("🔄 Refresh"):
                st.session_state.selected_date = None
    
        # -----------------------------
        # BAR CHART
        # -----------------------------
        if not attendance.empty:
    
            fig = px.bar(
                attendance,
                x="date",
                y="count",
                color="gender",
                barmode="group",
                text="count",
                title="Daily Attendance by Gender"
            )
    
            fig.update_traces(textposition="outside")
    
            selected = st.plotly_chart(
                fig,
                use_container_width=True,
                key="attendance_chart",
                on_select="rerun"
            )
    
            # -----------------------------
            # HANDLE CLICK
            # -----------------------------
            if selected and selected.get("selection"):

                points = selected["selection"]["points"]

                if len(points) > 0:
                clicked_date = points[0]["x"]

                # ✅ FORCE SAME FORMAT AS scan_date
                clicked_date = pd.to_datetime(clicked_date).normalize()

                st.session_state.selected_date = clicked_date
    
        # -----------------------------
        # TABLE
        # -----------------------------
        st.subheader("Learner Tracker Data")
    
        if st.session_state.selected_date:
            filtered_df = df[
                df["date"] == pd.to_datetime(st.session_state.selected_date).date()
            ]
            st.info(f"Filtered for date: {st.session_state.selected_date}")
        else:
            filtered_df = df
    
        st.dataframe(filtered_df, use_container_width=True)
    
    else:
        st.warning("time_stamp or gender column not found.")

    

   
    

# ----------------------------
# TABLES (UNCHANGED)
# ----------------------------
with tab3:
    st.dataframe(filtered_df, use_container_width=True)

with tab4:
    st.dataframe(reg_df, use_container_width=True)
