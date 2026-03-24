import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Learner Clocking Dashboard", layout="wide")
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

# Open workbook and worksheet
workbook = client.open("Leaner Clocking System")
worksheet = workbook.worksheet("Leaner tracker")

# Read data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# ----------------------------
# CLEAN DATA
# ----------------------------
# Standardize column names
df.columns = [col.strip() for col in df.columns]

# Convert dates
if "scan_date" in df.columns:
    df["scan_date"] = pd.to_datetime(df["scan_date"], errors="coerce")

# Convert age
if "Age" in df.columns:
    df["Age"] = pd.to_numeric(df["Age"], errors="coerce")

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("Filter Data")

# Date filter
if "scan_date" in df.columns and df["scan_date"].notna().any():
    min_date = df["scan_date"].min().date()
    max_date = df["scan_date"].max().date()

    date_range = st.sidebar.date_input(
        "Select Scan Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        df = df[
            (df["scan_date"].dt.date >= start_date) &
            (df["scan_date"].dt.date <= end_date)
        ]

# Direction filter
if "direction" in df.columns:
    direction_options = sorted(df["direction"].dropna().unique())
    selected_direction = st.sidebar.multiselect(
        "Select Direction",
        options=direction_options,
        default=direction_options
    )
    if selected_direction:
        df = df[df["direction"].isin(selected_direction)]

# Grade filter
if "Grade" in df.columns:
    grade_options = sorted(df["Grade"].dropna().unique())
    selected_grade = st.sidebar.multiselect(
        "Select Grade",
        options=grade_options,
        default=grade_options
    )
    if selected_grade:
        df = df[df["Grade"].isin(selected_grade)]

# Gender filter
if "Gender" in df.columns:
    gender_options = sorted(df["Gender"].dropna().unique())
    selected_gender = st.sidebar.multiselect(
        "Select Gender",
        options=gender_options,
        default=gender_options
    )
    if selected_gender:
        df = df[df["Gender"].isin(selected_gender)]

# Age filter
if "Age" in df.columns and df["Age"].notna().any():
    min_age = int(df["Age"].min())
    max_age = int(df["Age"].max())

    age_range = st.sidebar.slider(
        "Select Age Range",
        min_value=min_age,
        max_value=max_age,
        value=(min_age, max_age)
    )

    df = df[
        (df["Age"] >= age_range[0]) &
        (df["Age"] <= age_range[1])
    ]

# ----------------------------
# DASHBOARD METRICS
# ----------------------------
st.subheader("Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Records", len(df))

if "Grade" in df.columns:
    col2.metric("Grades", df["Grade"].nunique())
else:
    col2.metric("Grades", 0)

if "Gender" in df.columns:
    col3.metric("Gender Types", df["Gender"].nunique())
else:
    col3.metric("Gender Types", 0)

if "Age" in df.columns and df["Age"].notna().any():
    col4.metric("Average Age", round(df["Age"].mean(), 1))
else:
    col4.metric("Average Age", 0)

# ----------------------------
# CHARTS
# ----------------------------
st.subheader("Visuals")

chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    if "Grade" in df.columns:
        st.write("### Learners by Grade")
        grade_count = df["Grade"].value_counts().sort_index()
        st.bar_chart(grade_count)

with chart_col2:
    if "Gender" in df.columns:
        st.write("### Learners by Gender")
        gender_count = df["Gender"].value_counts()
        st.bar_chart(gender_count)

if "direction" in df.columns:
    st.write("### Movement by Direction")
    direction_count = df["direction"].value_counts()
    st.bar_chart(direction_count)

# ----------------------------
# DATA TABLE
# ----------------------------
st.subheader("Filtered Data")
st.dataframe(df, use_container_width=True)
