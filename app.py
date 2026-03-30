import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(
    page_title="Learner Clocking Dashboard",
    layout="wide"
)

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

# ----------------------------
# CLEAN DATA
# ----------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

# ----------------------------
# GLOBAL STYLE FUNCTION
# ----------------------------
def style_plotly(fig):
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=11),

        title=dict(x=0.01, font=dict(size=14)),

        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)"),

        legend=dict(font=dict(size=10)),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    return fig

# ----------------------------
# TABS
# ----------------------------
tab1, tab2 = st.tabs(["Dashboard", "Attendance"])

# =========================================================
# DASHBOARD TAB
# =========================================================
with tab1:

    col1, col2, col3 = st.columns(3)

    # ----------------------------
    # GRADE
    # ----------------------------
    with col1:
        st.subheader("Learners by Grade")

        grade_counts = reg_df["grade"].value_counts().reset_index()
        grade_counts.columns = ["Grade", "Count"]

        fig = px.bar(grade_counts, x="Grade", y="Count", text="Count")

        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
        )

        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # GENDER
    # ----------------------------
    with col2:
        st.subheader("Learners by Gender")

        gender_counts = reg_df["gender"].value_counts().reset_index()
        gender_counts.columns = ["Gender", "Count"]

        fig = px.bar(
            gender_counts,
            x="Gender",
            y="Count",
            text="Count",
            color="Gender",
            color_discrete_map={
                "Male": "#4e79a7",
                "Female": "#f28e2b"
            }
        )

        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
        )

        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # AGE
    # ----------------------------
    with col3:
        st.subheader("Age Distribution")

        reg_df["age"] = pd.to_numeric(reg_df["age"], errors="coerce")

        age_counts = reg_df["age"].value_counts().sort_index().reset_index()
        age_counts.columns = ["Age", "Count"]

        fig = px.bar(age_counts, x="Age", y="Count", text="Count")

        fig.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
        )

        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    col4, col5 = st.columns(2)

    # ----------------------------
    # YEARLY ATTENDANCE
    # ----------------------------
    with col4:
        st.subheader("Yearly Attendance")

        df = reg_df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["year"] = df["timestamp"].dt.year

        pivot = df.groupby(["year", "gender"]).size().reset_index(name="Count")

        fig = px.bar(
            pivot,
            x="year",
            y="Count",
            color="gender",
            text="Count",
            barmode="stack",
            color_discrete_map={
                "Male": "#4e79a7",
                "Female": "#f28e2b"
            }
        )

        fig.update_traces(
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>%{legendgroup}: %{y}<extra></extra>"
        )

        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

    # ----------------------------
    # RACE
    # ----------------------------
    with col5:
        st.subheader("Registered by Race")

        df = reg_df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df["year"] = df["timestamp"].dt.year

        pivot = df.groupby(["year", "race"]).size().reset_index(name="Count")

        fig = px.bar(
            pivot,
            x="year",
            y="Count",
            color="race",
            text="Count",
            barmode="stack",
            color_discrete_map={
                "Black": "#4e79a7",
                "Coloured": "#f28e2b",
                "Indian": "#59a14f",
                "White": "#e15759"
            }
        )

        fig.update_traces(
            textposition="inside",
            hovertemplate="<b>%{x}</b><br>%{legendgroup}: %{y}<extra></extra>"
        )

        fig = style_plotly(fig)
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# ATTENDANCE TAB
# =========================================================
with tab2:

    st.subheader("Daily Attendance by Gender")

    df = learner_df.copy()
    df["scan_date"] = pd.to_datetime(df["scan_date"], errors="coerce")
    df["gender"] = df["gender"].astype(str).str.capitalize()

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
        barmode="group",
        color_discrete_map={
            "Male": "#4e79a7",
            "Female": "#f28e2b"
        }
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{legendgroup}: %{y}<extra></extra>"
    )

    fig = style_plotly(fig)

    st.plotly_chart(fig, use_container_width=True)
