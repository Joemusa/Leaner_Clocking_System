import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
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
            st.error("Invalid username")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
    st.stop()

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="Learner Dashboard", layout="wide")

st.title("📊 School Attendance Dashboard")

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

learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

# ----------------------------
# SIDEBAR FILTERS (RESTORED)
# ----------------------------
st.sidebar.header("Filters")

filtered_df = learner_df.copy()

if "scan_date" in filtered_df.columns:
    filtered_df["scan_date"] = pd.to_datetime(filtered_df["scan_date"], errors="coerce")

    dates = sorted(filtered_df["scan_date"].dropna().dt.date.unique())
    selected_dates = st.sidebar.multiselect("Select Date", dates, default=dates)

    if selected_dates:
        filtered_df = filtered_df[
            filtered_df["scan_date"].dt.date.isin(selected_dates)
        ]

if "gender" in filtered_df.columns:
    options = filtered_df["gender"].dropna().unique()
    selected = st.sidebar.multiselect("Gender", options, default=options)
    filtered_df = filtered_df[filtered_df["gender"].isin(selected)]

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()

# ----------------------------
# GLOBAL STYLE
# ----------------------------
def style_plotly(fig):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=11),
        title=dict(x=0.01),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)")
    )
    return fig

# ----------------------------
# TABS (RESTORED)
# ----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "School Demographics",
    "Attendance",
    "Registered Learners",
    "Absent Learners"
])

# =========================================================
# TAB 1 - DEMOGRAPHICS
# =========================================================
with tab1:

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Learners by Grade")
        grade = reg_df["grade"].value_counts().reset_index()
        grade.columns = ["Grade", "Count"]

        fig = px.bar(grade, x="Grade", y="Count", text="Count")
        fig.update_traces(textposition="outside")
        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Learners by Gender")
        gender = reg_df["gender"].value_counts().reset_index()
        gender.columns = ["Gender", "Count"]

        fig = px.bar(gender, x="Gender", y="Count", text="Count", color="Gender")
        fig.update_traces(textposition="outside")
        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        st.subheader("Age Distribution")
        reg_df["age"] = pd.to_numeric(reg_df["age"], errors="coerce")

        age = reg_df["age"].value_counts().sort_index().reset_index()
        age.columns = ["Age", "Count"]

        fig = px.bar(age, x="Age", y="Count", text="Count")
        fig.update_traces(textposition="outside")
        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 2 - ATTENDANCE
# =========================================================
with tab2:

    st.subheader("Daily Attendance")

    df = filtered_df.copy()

    attendance = (
        df.groupby([df["scan_date"].dt.date, "gender"])
        .size()
        .reset_index(name="count")
    )

    fig = px.bar(
        attendance,
        x="scan_date",
        y="count",
        color="gender",
        text="count",
        barmode="group"
    )

    fig.update_traces(textposition="outside")
    fig = style_plotly(fig)

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
# TAB 3 - TABLE
# =========================================================
with tab3:
    st.dataframe(reg_df, use_container_width=True)

# =========================================================
# TAB 4 - ABSENT (RESTORED)
# =========================================================
with tab4:

    st.subheader("Absent Learners")

    reg_ids = set(reg_df["student_id"].astype(str))
    att_ids = set(learner_df["student_id"].astype(str))

    absent = reg_ids - att_ids

    absent_df = reg_df[reg_df["student_id"].isin(absent)]

    st.dataframe(absent_df, use_container_width=True)

    csv = absent_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download CSV",
        csv,
        "absent_learners.csv",
        "text/csv"
    )
```
