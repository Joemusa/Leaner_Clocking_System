import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

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

    learner_ws = workbook.worksheet("Leaner Tracker")
    reg_ws = workbook.worksheet("Registration Form")

    learner_data = learner_ws.get_all_records()
    reg_data = reg_ws.get_all_records()

    learner_df = pd.DataFrame(learner_data)
    reg_df = pd.DataFrame(reg_data)

    return learner_df, reg_df


learner_df, reg_df = load_data()

# ----------------------------
# CLEAN LEARNER DATA
# ----------------------------
learner_df.columns = [str(col).strip() for col in learner_df.columns]
reg_df.columns = [str(col).strip() for col in reg_df.columns]

# Standardize expected columns if present
if "scan_date" in learner_df.columns:
    learner_df["scan_date"] = pd.to_datetime(learner_df["scan_date"], errors="coerce")

if "time_stamp" in learner_df.columns:
    learner_df["time_stamp"] = pd.to_datetime(learner_df["time_stamp"], errors="coerce")

if "Age" in learner_df.columns:
    learner_df["Age"] = pd.to_numeric(learner_df["Age"], errors="coerce")

# Keep a filtered copy
filtered_df = learner_df.copy()

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filters")

# Date filter
if "scan_date" in filtered_df.columns and filtered_df["scan_date"].notna().any():
    min_date = filtered_df["scan_date"].min().date()
    max_date = filtered_df["scan_date"].max().date()

    date_range = st.sidebar.date_input(
        "Scan Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df["scan_date"].dt.date >= start_date) &
            (filtered_df["scan_date"].dt.date <= end_date)
        ]

# Direction filter
if "direction" in filtered_df.columns:
    direction_options = sorted([x for x in filtered_df["direction"].dropna().unique()])
    selected_direction = st.sidebar.multiselect(
        "Direction",
        options=direction_options,
        default=direction_options
    )
    if selected_direction:
        filtered_df = filtered_df[filtered_df["direction"].isin(selected_direction)]

# Grade filter
if "Grade" in filtered_df.columns:
    grade_options = sorted([x for x in filtered_df["Grade"].dropna().unique()])
    selected_grade = st.sidebar.multiselect(
        "Grade",
        options=grade_options,
        default=grade_options
    )
    if selected_grade:
        filtered_df = filtered_df[filtered_df["Grade"].isin(selected_grade)]

# Gender filter
if "Gender" in filtered_df.columns:
    gender_options = sorted([x for x in filtered_df["Gender"].dropna().unique()])
    selected_gender = st.sidebar.multiselect(
        "Gender",
        options=gender_options,
        default=gender_options
    )
    if selected_gender:
        filtered_df = filtered_df[filtered_df["Gender"].isin(selected_gender)]

# Age filter
if "Age" in filtered_df.columns and filtered_df["Age"].notna().any():
    min_age = int(filtered_df["Age"].min())
    max_age = int(filtered_df["Age"].max())

    selected_age = st.sidebar.slider(
        "Age Range",
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age)
    )

    filtered_df = filtered_df[
        (filtered_df["Age"] >= selected_age[0]) &
        (filtered_df["Age"] <= selected_age[1])
    ]

# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3 = st.tabs([
    "Dashboard",
    "Leaner Tracker Table",
    "Registration Form Table"
])

# ----------------------------
# DASHBOARD TAB
# ----------------------------
with tab1:
    st.markdown('<div class="section-title">Summary KPIs</div>', unsafe_allow_html=True)

    total_records = len(filtered_df)
    total_grades = filtered_df["Grade"].nunique() if "Grade" in filtered_df.columns else 0
    total_genders = filtered_df["Gender"].nunique() if "Gender" in filtered_df.columns else 0
    avg_age = round(filtered_df["Age"].mean(), 1) if "Age" in filtered_df.columns and filtered_df["Age"].notna().any() else 0

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Records</div>
            <div class="kpi-value">{total_records}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Grades</div>
            <div class="kpi-value">{total_grades}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Gender Types</div>
            <div class="kpi-value">{total_genders}</div>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Average Age</div>
            <div class="kpi-value">{avg_age}</div>
        </div>
        """, unsafe_allow_html=True)

    # ----------------------------
    # CHARTS ROW 1
    # ----------------------------
    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Grade")
        if "Grade" in filtered_df.columns and not filtered_df.empty:
            grade_count = filtered_df["Grade"].value_counts().sort_index()
            st.bar_chart(grade_count)
        else:
            st.info("No Grade data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Learners by Gender")
        if "Gender" in filtered_df.columns and not filtered_df.empty:
            gender_count = filtered_df["Gender"].value_counts()
            st.bar_chart(gender_count)
        else:
            st.info("No Gender data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # CHARTS ROW 2
    # ----------------------------
    c3, c4 = st.columns(2)

    with c3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Movement by Direction")
        if "direction" in filtered_df.columns and not filtered_df.empty:
            direction_count = filtered_df["direction"].value_counts()
            st.bar_chart(direction_count)
        else:
            st.info("No direction data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Age Distribution")
        if "Age" in filtered_df.columns and filtered_df["Age"].notna().any():
            age_count = filtered_df["Age"].value_counts().sort_index()
            st.bar_chart(age_count)
        else:
            st.info("No age data available.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # DIRECTION TREND BY DATE
    # ----------------------------
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.subheader("Direction Trend by Date")

    if (
        "scan_date" in filtered_df.columns and
        "direction" in filtered_df.columns and
        not filtered_df.empty
    ):
        trend_df = filtered_df.copy()
        trend_df["scan_date_only"] = trend_df["scan_date"].dt.date

        direction_trend = (
            trend_df.groupby(["scan_date_only", "direction"])
            .size()
            .unstack(fill_value=0)
            .sort_index()
        )

        st.line_chart(direction_trend)
        st.markdown("### Trend Data Table")
        st.dataframe(direction_trend, use_container_width=True)
    else:
        st.info("No scan date or direction data available for trend analysis.")

    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# LEANER TRACKER TABLE TAB
# ----------------------------
with tab2:
    st.subheader("Leaner Tracker Data")
    st.dataframe(filtered_df, use_container_width=True)

# ----------------------------
# REGISTRATION FORM TABLE TAB
# ----------------------------
with tab3:
    st.subheader("Registration Form Data")
    st.dataframe(reg_df, use_container_width=True)
