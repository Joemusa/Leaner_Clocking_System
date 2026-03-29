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

```
if st.button("Login"):
    if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
        st.session_state["logged_in"] = True
        st.success("Login successful ✅")
        st.rerun()
    else:
        st.error("Invalid username or password ❌")
```

if "logged_in" not in st.session_state:
st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
login()
st.stop()

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

learner_df["scan_date"] = pd.to_datetime(learner_df["scan_date"], errors="coerce", dayfirst=True)

# ----------------------------

# 🔥 NEW: HIERARCHY DATE FILTER

# ----------------------------

st.sidebar.header("Date Filter")

df_dates = learner_df.copy()
df_dates["year"] = df_dates["scan_date"].dt.year
df_dates["month"] = df_dates["scan_date"].dt.month
df_dates["day"] = df_dates["scan_date"].dt.day

years = sorted(df_dates["year"].dropna().unique())
selected_year = st.sidebar.selectbox("Year", years)

months = sorted(df_dates[df_dates["year"] == selected_year]["month"].dropna().unique())
selected_month = st.sidebar.selectbox("Month", months)

days = sorted(
df_dates[
(df_dates["year"] == selected_year) &
(df_dates["month"] == selected_month)
]["day"].dropna().unique()
)

selected_day = st.sidebar.selectbox("Day", days)

selected_date = pd.to_datetime(
f"{selected_year}-{selected_month}-{selected_day}"
).normalize()

# ----------------------------

# APPLY GLOBAL FILTER

# ----------------------------

filtered_df = learner_df[
learner_df["scan_date"].dt.normalize() == selected_date
]

# ----------------------------

# TABS

# ----------------------------

tab1, tab2, tab3, tab4 = st.tabs([
"School Demographics",
"Attendance",
"Registered Learners",
"Absent Learners"
])

# ----------------------------

# TAB 2 (ATTENDANCE) FIXED

# ----------------------------

with tab2:

```
df = learner_df.copy()
df["scan_date"] = pd.to_datetime(df["scan_date"], errors="coerce")
df["gender"] = df["gender"].astype(str).str.strip().str.capitalize()

df = df[df["scan_date"].dt.normalize() == selected_date]

attendance = (
    df.groupby([df["scan_date"].dt.normalize(), "gender"])
    .size()
    .reset_index(name="count")
)

attendance.rename(columns={"scan_date": "date"}, inplace=True)

fig = px.bar(
    attendance,
    x="date",
    y="count",
    color="gender",
    barmode="group",
    text="count"
)

st.plotly_chart(fig, use_container_width=True)

st.dataframe(df, use_container_width=True)
```

# ----------------------------

# TAB 4 (ABSENT) FIXED

# ----------------------------

with tab4:

```
st.subheader("Absent Learners")

reg_df["student_id"] = reg_df["student_id"].astype(str).str.strip()
learner_df["student_id"] = learner_df["student_id"].astype(str).str.strip()

learner_df["direction"] = learner_df["direction"].astype(str).str.strip().str.upper()

present_df = learner_df[
    (learner_df["scan_date"].dt.normalize() == selected_date) &
    (learner_df["direction"] == "IN")
]

present_ids = present_df["student_id"].drop_duplicates()

absent_df = reg_df[
    ~reg_df["student_id"].isin(present_ids)
].copy()

attendance_all = learner_df[learner_df["direction"] == "IN"]

present_counts = (
    attendance_all.groupby("student_id")["scan_date"]
    .nunique()
    .reset_index(name="days_present")
)

total_days = learner_df["scan_date"].dt.normalize().nunique()

summary = reg_df.merge(present_counts, on="student_id", how="left")
summary["days_present"] = summary["days_present"].fillna(0)
summary["times_absent"] = total_days - summary["days_present"]

absent_df = absent_df.merge(
    summary[["student_id", "times_absent"]],
    on="student_id",
    how="left"
)

st.dataframe(absent_df, use_container_width=True)
```
