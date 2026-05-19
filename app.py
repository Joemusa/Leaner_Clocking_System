import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import plotly.express as px
import streamlit as st
import sqlite3
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
st.markdown("""
<style>
div[data-testid="stPlotlyChart"] {
    border-radius: 12px;
    overflow: hidden;
    background-color: white;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.kpi-box {
    border: 1px solid #333;
    border-radius: 12px;
    padding: 18px;
    background-color: #1e1e1e;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    text-align: center;
    margin-bottom: 10px;
}

.kpi-title {
    font-size: 14px;
    color: #bbbbbb;
    margin-bottom: 6px;
    font-weight: 500;
}

.kpi-value {
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)
# ----------------------------
# GLOBAL CHART STYLE (NEW 🔥)
# ----------------------------
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10
})

BAR_COLOR = "#4e79a7"
FIG_SIZE = (8, 4.5)

def plot_stacked_bar(pivot_df):
    fig, ax = plt.subplots(figsize=(12, 4.5))

    pivot_df.plot(kind="bar", stacked=True, ax=ax)

    style_axes(ax)

    ax.set_xticklabels(pivot_df.index.astype(str), rotation=0)

    for container in ax.containers:
        ax.bar_label(container, label_type="center", fontsize=10, color="white")

    for i, idx in enumerate(pivot_df.index):
        total = pivot_df.loc[idx].sum()
        ax.text(i, total, f"{int(total)}", ha="center", va="bottom")

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    return fig   # ✅ IMPORTANT

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
    ax.set_axisbelow(True)

    # Remove borders
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Clean labels
    ax.set_xlabel("")
    ax.set_ylabel("")

def plot_bar(series, label):
    if series.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=FIG_SIZE)

    bars = ax.bar(
        series.index.astype(str),
        series.values,
        color=BAR_COLOR
    )

    style_axes(ax)

    # Axis labels
    ax.set_xlabel(label)
    ax.set_ylabel("Count")

    # Data labels (STANDARD FORMAT)
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height,
            f"{int(height)}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold"
        )

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    st.pyplot(fig)
def plot_line(df):
    if df.empty:
        st.info("No data available.")
        return

    fig, ax = plt.subplots(figsize=(12,4.5))

    for col in df.columns:
        ax.plot(df.index, df[col], marker="o", label=col)

    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%b-%y"))
    plt.xticks(rotation=45)
    style_axes(ax)

    st.pyplot(fig)
# -----------------------------
# SIDEBAR DATE FILTER
# -----------------------------
selected_date = st.sidebar.date_input("Select Date")

# Ensure datetime format
selected_date = pd.to_datetime(selected_date).normalize()
# ----------------------------
# TABS
# ----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "School Demographics",
    "Attendance",
    "Registered Learners",
    "Absent Learners",
    "Time Table Generator"
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
            <div class="kpi-title">Total Registered Learners</div>
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
        #total_records = learner_df['learner name'].notna().sum()

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
        
            # ✅ DEFINE CORRECT ORDER
            grade_order = ["Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
        
            # Count values
            grade_counts = df["Grade"].value_counts()
        
            # Reindex to enforce order
            grade_counts = grade_counts.reindex(grade_order, fill_value=0)
        
            # Plot
            plot_bar(grade_counts, "Grade")

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
            pivot.index = pivot.index.astype(int).astype(str)
                                   
            fig = plot_stacked_bar(pivot)
            st.pyplot(fig)
            
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
                "font.size": 12
            })
    
            fig = plot_stacked_bar(pivot)
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

    # -----------------------------
    # VALIDATION
    # -----------------------------
    if "scan_date" in df.columns and "gender" in df.columns:

        # Clean data
        df["scan_date"] = pd.to_datetime(df["scan_date"], errors="coerce")
        df["gender"] = df["gender"].astype(str).str.strip().str.capitalize()

        df = df.dropna(subset=["scan_date", "gender"])

        # -----------------------------
        # SESSION STATE
        # -----------------------------
        if "selected_date" not in st.session_state:
            st.session_state.selected_date = None

        if "selected_gender" not in st.session_state:
            st.session_state.selected_gender = None

        # -----------------------------
        # GENDER FILTER (DROPDOWN)
        # -----------------------------
        genders = ["All"] + sorted(df["gender"].dropna().unique().tolist())

        selected_gender_filter = st.selectbox(
            "Filter by Gender",
            genders
        )

        # Apply dropdown filter
        df_filtered = df.copy()

        if selected_gender_filter != "All":
            df_filtered = df_filtered[
                df_filtered["gender"] == selected_gender_filter
            ]

        # -----------------------------
        # AGGREGATE (FOR CHART)
        # -----------------------------
        attendance = (
            df_filtered.groupby([df_filtered["scan_date"].dt.normalize(), "gender"])
            .size()
            .reset_index(name="count")
        )

        attendance.rename(columns={"scan_date": "date"}, inplace=True)
        attendance["date"] = pd.to_datetime(attendance["date"])

        # -----------------------------
        # REFRESH BUTTON
        # -----------------------------
        colA, colB = st.columns([1, 5])

        #with colA:
            #if s#t.button("🔄 Refresh"):
                #st.session_state.selected_date = None
                #st.session_state.selected_gender = None

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
                title="Daily Attendance by Gender",
                color_discrete_map={
                    "Male": "#4e79a7",
                    "Female": "#f28e2b"
                }
            )
            
            # 🔥 DATA LABELS (CLEAN + CONSISTENT)
            fig.update_traces(
                textposition="outside",
                textfont=dict(
                    size=12,
                    color="black"
                ),
                cliponaxis=False
            )
            
            # 🔥 LAYOUT (THIS IS THE MAGIC)
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
            
                # ✅ remove axis titles
                xaxis_title=None,
                yaxis_title=None,
            
                # ✅ SHOW X-AXIS LINE
                xaxis=dict(
                    showline=False,
                    linecolor="black",
                    linewidth=1,
                    showgrid=False,
                    zeroline = False,
                    showticklabels = True,
                    tickfont=dict(size=16, color = "black")
                ),
            
                # ✅ CLEAN Y-AXIS
                yaxis=dict(
                    showline=False,
                    gridcolor="rgba(0,0,0,0.1)",
                    tickfont=dict(size=16, color = "black")
                ),
            
                # ✅ FIX LEGEND
                legend=dict(
                    title=None,   # 🔥 removes "Gender"
                    font=dict(size=11, color="black"),
                    bgcolor="rgba(255,255,255,0.7)",
                    bordercolor="rgba(0,0,0,0.1)",
                    borderwidth=1
                ),
            
                margin=dict(l=10, r=10, t=40, b=10)
            )
            
            # 🔥 FORMAT DATE PROPERLY
            fig.update_xaxes(
                tickformat="%d-%b",
            )
            
            # 🔥 MAKE IT FULL WIDTH CLEAN
            fig.update_traces(
                textposition="inside",
                textfont=dict(size=18)   # ✅ numbers on bars
            )

            fig.update_layout(
                xaxis=dict(
                    tickfont=dict(size=12),     # ✅ date font size
                    title_font=dict(size=14),
                ),

                xaxis_title = None,
                yaxis_title = None,
                
                yaxis=dict(
                    tickfont=dict(size=12),
                    title_font=dict(size=14)
                ),
                title=dict(
                    font=dict(size=16)
                )
            )
                
            

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

                    clicked_date = pd.to_datetime(points[0]["x"]).normalize()

                    clicked_gender = points[0].get("legendgroup")
                    if not clicked_gender:
                        clicked_gender = points[0].get("label")

                    st.session_state.selected_date = clicked_date
                    st.session_state.selected_gender = clicked_gender

        else:
            st.warning("No attendance data available.")

        # -----------------------------
        # TABLE
        # -----------------------------
        st.subheader("Learner Tracker Data")

        filtered_df = df.copy()

        # Apply dropdown filter
        if selected_gender_filter != "All":
            filtered_df = filtered_df[
                filtered_df["gender"] == selected_gender_filter
            ]

        # Apply click filter
        if st.session_state.get("selected_date"):

            selected_date = pd.to_datetime(st.session_state.selected_date).normalize()

            filtered_df = filtered_df[
                filtered_df["scan_date"].dt.normalize() == selected_date
            ]

            # Apply clicked gender (override dropdown)
            if st.session_state.get("selected_gender"):
                filtered_df = filtered_df[
                    filtered_df["gender"] == st.session_state.selected_gender
                ]

            st.info(
                f"Filtered for: {selected_date.date()} | Gender: {st.session_state.get('selected_gender', selected_gender_filter)}"
            )

        st.dataframe(
            filtered_df[
                ["student_id", "scan_date", "time", "direction", "grade", "gender"]
            ],
            use_container_width=True
        )

    else:
        st.warning("scan_date or gender column not found.")


# ----------------------------
# TABLES (UNCHANGED)
# ----------------------------

with tab3:

    k1, k2, k3 = st.columns(3)

    
    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Registered Learners</div>
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
     

        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Attendance</div>
            <div class="kpi-value">{total_records}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.dataframe(reg_df, use_container_width=True)
    
    
with tab4:
    st.subheader("Absent Learners")
    k1, k2, k3 = st.columns(3)

    
    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Registered Learners</div>
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
     

        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Total Attendance</div>
            <div class="kpi-value">{total_records}</div>
        </div>
        """, unsafe_allow_html=True)

    
    # -----------------------------
    # LOAD DATA
    # -----------------------------
    reg_df = reg_df.copy()
    att_df = learner_df.copy()
    
    # Clean columns
    reg_df.columns = reg_df.columns.str.strip().str.lower()
    att_df.columns = att_df.columns.str.strip().str.lower()
    
    # -----------------------------
    # 🔥 CLEAN DATA (FIXED)
    # -----------------------------
    reg_df["student_id"] = (
        reg_df["student_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    att_df["student_id"] = (
        att_df["student_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    att_df["direction"] = (
        att_df["direction"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    att_df["scan_date"] = pd.to_datetime(att_df["scan_date"], errors="coerce")
    
    # Remove duplicates
    reg_df = reg_df.drop_duplicates(subset=["student_id"])
    
    # -----------------------------
    # PRESENT LEARNERS (IN ONLY)
    # -----------------------------
    
    # st.markdown(f"""
    # <div class="kpi-box">
    #     #<div class="kpi-title">Total Attendance</div>
    #     <div class="kpi-value">{total_records}</div>
    # </div>
    # """, unsafe_allow_html=True)
    
    present_df = att_df[
        (att_df["scan_date"].dt.normalize() == selected_date) &
        (att_df["direction"].isin(["IN", "LATE"]))
    ]
    
    present_ids = present_df["student_id"].drop_duplicates()
    
    # -----------------------------
    # 🔥 ABSENT LEARNERS (FIXED MATCHING)
    # -----------------------------
    absent_df = reg_df[
        ~reg_df["student_id"].isin(present_ids)
    ].copy()
    
    # -----------------------------
    # TIMES ABSENT (ALL DAYS)
    # -----------------------------
    attendance_all = att_df[att_df["direction"].isin(["IN", "LATE"])]
    
    present_counts = (
        attendance_all.groupby("student_id")["scan_date"]
        .nunique()
        .reset_index(name="days_present")
    )
    
    all_dates = att_df["scan_date"].dt.normalize().dropna().unique()
    total_days = len(all_dates)
    
    absent_summary = reg_df.merge(present_counts, on="student_id", how="left")
    absent_summary["days_present"] = absent_summary["days_present"].fillna(0)
    absent_summary["times_absent"] = total_days - absent_summary["days_present"]
    
    absent_df = absent_df.merge(
        absent_summary[["student_id", "times_absent"]],
        on="student_id",
        how="left"
    )
    
    # -----------------------------
    # METRICS
    # -----------------------------
    total_registered = reg_df["student_id"].nunique()
    total_present = present_ids.nunique()
    total_absent = absent_df["student_id"].nunique()
    
    st.info(f"Date: {selected_date.date()}")
    
    # col1, col3 = st.columns(2)
    
    # col1.metric("Registered", total_registered)
    # #col2.metric("Present", total_present)
    # col3.metric("Absent", total_absent)
    
    # -----------------------------
    # FINAL TABLE
    # -----------------------------
    absent_df = absent_df.drop_duplicates(subset=["student_id"])
    
    display_df = absent_df[
        ["student_id", "child's name", "grade", "gender", "times_absent"]
    ]
    
    st.dataframe(display_df, use_container_width=True)
    
    # -----------------------------
    # ✅ EXPORT TO EXCEL (ADDED)
    # -----------------------------
    import io
       
    csv_data = display_df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="📥 Export Absent Learners to Excel",
        data=csv_data,
        file_name="absent_learners.csv",
        mime="text/csv"
    )
    
    # -----------------------------
    # LEARNER ABSENCE ANALYSIS
    # -----------------------------
    st.markdown("---")
    st.subheader("Days When Learner Was Absent")
    
    # Get absent learner names
    absent_names = absent_df["child's name"].dropna().unique()
    
    if len(absent_names) > 0:
    
        selected_name = st.selectbox(
            "Select Learner",
            sorted(absent_names)
        )
    
        learner_row = absent_df[absent_df["child's name"] == selected_name]
    
        if not learner_row.empty:
    
            learner_id = learner_row["student_id"].values[0]
    
            all_dates = (
                att_df["scan_date"]
                .dropna()
                .dt.normalize()
                .sort_values()
                .unique()
            )
    
            all_dates = pd.to_datetime(all_dates)
    
            learner_attendance = att_df[
                att_df["student_id"] == learner_id
            ]
    
            present_dates = learner_attendance["scan_date"].dt.normalize().unique()
            present_dates = pd.to_datetime(present_dates)
    
            absent_dates = sorted(set(all_dates) - set(present_dates))
            absent_dates = pd.to_datetime(absent_dates)
    
            if len(absent_dates) > 0:
    
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                
                fig, ax = plt.subplots(figsize=(20, 4))
                plt.rcParams.update({
                "font.size": 18   # 🔁 change this (e.g. 10, 14, 16)
                })
                
                ax.vlines(absent_dates, ymin=0, ymax=1)
                ax.scatter(absent_dates, [1]*len(absent_dates), s=100)
                
                for spine in ax.spines.values():
                    spine.set_visible(False)
                
                ax.grid(False)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b %Y'))
                ax.tick_params(axis='x', labelsize=10)
                plt.xticks(rotation=0)
                
                ax.set_ylim(0, 1.2)
                ax.set_yticks([])
                ax.set_title(f"Absence Days - {selected_name}", fontsize = 14)
                ax.set_xlabel("Date", fontsize = 18)
                
                st.pyplot(fig)
            else:
                st.success("No absences for this learner 🎉")

with tab5:
    
    import streamlit as st
    import pandas as pd
    import sqlite3
    from datetime import datetime, timedelta
    
    # =====================================================
    # PAGE CONFIG
    # =====================================================
    
    st.set_page_config(
        page_title="Automatic School Timetable Generator",
        layout="wide"
    )
    
    st.title("📚 Automatic School Timetable Generator")
    
    # =====================================================
    # DATABASE CONNECTION
    # =====================================================
    
    conn = sqlite3.connect("school.db", check_same_thread=False)
    c = conn.cursor()
    
    
    # =====================================================
    # CREATE TABLES
    # =====================================================
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS school_settings (
        day TEXT,
        start_time TEXT,
        end_time TEXT,
        lunch_start TEXT,
        lunch_end TEXT,
        period_duration INTEGER
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_name TEXT,
        subject TEXT
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS grade_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grade TEXT,
        subject TEXT,
        periods_per_week INTEGER
    )
    """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grade TEXT,
        day TEXT,
        start_time TEXT,
        end_time TEXT,
        subject TEXT,
        teacher TEXT
    )
    """)
    
    conn.commit()
    
    # =====================================================
    # SIDEBAR MENU
    # =====================================================
    
    menu = st.sidebar.selectbox(
        "Menu",
        [
            "School Settings",
            "Teachers",
            "Grade Subjects",
            "Generate Timetable",
            "View Timetable"
        ]
    )
    
    # =====================================================
    # SCHOOL SETTINGS
    # =====================================================
    
    if menu == "School Settings":
    
        st.header("⚙️ School Settings")
    
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday"
        ]
    
        selected_day = st.selectbox(
            "Select Day",
            days
        )
    
        start_time = st.time_input(
            "School Start Time"
        )
    
        end_time = st.time_input(
            "School End Time"
        )
    
        lunch_start = st.time_input(
            "Lunch Start Time"
        )
    
        lunch_end = st.time_input(
            "Lunch End Time"
        )
    
        period_duration = st.number_input(
            "Period Duration (Minutes)",
            min_value=30,
            max_value=90,
            value=45
        )
    
        if st.button("Save Settings"):
    
            # DELETE OLD SETTINGS
            c.execute("""
            DELETE FROM school_settings
            WHERE day = ?
            """, (selected_day,))
    
            # INSERT NEW SETTINGS
            c.execute("""
            INSERT INTO school_settings
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                selected_day,
                str(start_time),
                str(end_time),
                str(lunch_start),
                str(lunch_end),
                period_duration
            ))
    
            conn.commit()
    
            st.success("✅ School Settings Saved")
    
    # =====================================================
    # TEACHERS
    # =====================================================
    
    if menu == "Teachers":
    
        st.header("👨‍🏫 Teachers")
    
        teacher_name = st.text_input(
            "Teacher Name"
        )
    
        subject = st.text_input(
            "Subject"
        )
    
        if st.button("Add Teacher"):
    
            c.execute("""
            INSERT INTO teachers
            (teacher_name, subject)
            VALUES (?, ?)
            """, (
                teacher_name,
                subject
            ))
    
            conn.commit()
    
            st.success("✅ Teacher Added")
    
        teachers_df = pd.read_sql(
            "SELECT * FROM teachers",
            conn
        )
    
        st.dataframe(
            teachers_df,
            use_container_width=True
        )
    
    # =====================================================
    # GRADE SUBJECTS
    # =====================================================
    
    if menu == "Grade Subjects":
    
        st.header("📘 Grade Subjects")
    
        grade = st.selectbox(
            "Select Class",
            [
                "Grade 8A",
                "Grade 8B",
                "Grade 9A",
                "Grade 9B",
                "Grade 10A"
            ]
        )
    
        subject = st.text_input(
            "Subject"
        )
    
        periods_per_week = st.number_input(
            "Periods Per Week",
            min_value=1,
            max_value=10,
            value=5
        )
    
        if st.button("Save Subject"):
    
            c.execute("""
            INSERT INTO grade_subjects
            (grade, subject, periods_per_week)
            VALUES (?, ?, ?)
            """, (
                grade,
                subject,
                periods_per_week
            ))
    
            conn.commit()
    
            st.success("✅ Subject Saved")
    
        subjects_df = pd.read_sql(
            "SELECT * FROM grade_subjects",
            conn
        )
    
        st.dataframe(
            subjects_df,
            use_container_width=True
        )
    
    # =====================================================
    # GENERATE PERIODS FUNCTION
    # =====================================================
    
    def generate_periods(
        start_time,
        end_time,
        lunch_start,
        lunch_end,
        duration
    ):
    
        periods = []
    
        current = datetime.strptime(
            start_time,
            "%H:%M:%S"
        )
    
        end = datetime.strptime(
            end_time,
            "%H:%M:%S"
        )
    
        lunch_s = datetime.strptime(
            lunch_start,
            "%H:%M:%S"
        )
    
        lunch_e = datetime.strptime(
            lunch_end,
            "%H:%M:%S"
        )
    
        while current < end:
    
            next_period = current + timedelta(
                minutes=duration
            )
    
            # SKIP LUNCH
            if current >= lunch_s and current < lunch_e:
    
                current = lunch_e
                continue
    
            periods.append((
                current.strftime("%H:%M"),
                next_period.strftime("%H:%M")
            ))
    
            current = next_period
    
        return periods
    
    # =====================================================
    # GENERATE TIMETABLE
    # =====================================================
    
    if menu == "Generate Timetable":
    
        st.header("🧠 Generate Timetable")
    
        if st.button("Generate Weekly Timetable"):
    
            # CLEAR OLD TIMETABLE
            c.execute("DELETE FROM timetable")
            conn.commit()
    
            settings_df = pd.read_sql(
                "SELECT * FROM school_settings",
                conn
            )
    
            subjects_df = pd.read_sql(
                "SELECT * FROM grade_subjects",
                conn
            )
    
            teachers_df = pd.read_sql(
                "SELECT * FROM teachers",
                conn
            )
            st.write("SETTINGS")
            st.write(settings_df)
            
            st.write("SUBJECTS")
            st.write(subjects_df)
            
            st.write("TEACHERS")
            st.write(teachers_df)
    
            timetable_entries = []
    
            teacher_schedule = {}
            class_schedule = {}
    
            days = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday"
            ]
    
            # LOOP THROUGH CLASSES
            for grade in subjects_df["grade"].unique():
    
                grade_subjects = subjects_df[
                    subjects_df["grade"] == grade
                ]
    
                daily_subject_count = {}
    
                for day in days:
    
                    setting = settings_df[
                        settings_df["day"] == day
                    ]
    
                    if setting.empty:
                        continue
    
                    setting = setting.iloc[0]
    
                    periods = generate_periods(
                        setting["start_time"],
                        setting["end_time"],
                        setting["lunch_start"],
                        setting["lunch_end"],
                        setting["period_duration"]
                    )
    
                    period_index = 0
    
                    for _, row in grade_subjects.iterrows():
    
                        subject = row["subject"]
    
                        periods_needed = row["periods_per_week"]
    
                        # DISTRIBUTE SUBJECTS
                        subject_per_day = max(
                            1,
                            round(periods_needed / 5)
                        )
    
                        # DAILY LIMIT
                        if daily_subject_count.get(
                            (grade, day, subject),
                            0
                        ) >= subject_per_day:
    
                            continue
    
                        # FIND TEACHER
                        teacher_match = teachers_df[
                            teachers_df["subject"] == subject
                        ]
    
                        if teacher_match.empty:
                            continue
    
                        teacher = teacher_match.iloc[0][
                            "teacher_name"
                        ]
    
                        for p in range(subject_per_day):
    
                            if period_index >= len(periods):
                                break
    
                            start_p, end_p = periods[
                                period_index
                            ]
    
                            teacher_key = (
                                f"{teacher}_{day}_{start_p}"
                            )
    
                            class_key = (
                                f"{grade}_{day}_{start_p}"
                            )
    
                            # TEACHER CLASH
                            if teacher_key in teacher_schedule:
    
                                period_index += 1
                                continue
    
                            # CLASS CLASH
                            if class_key in class_schedule:
    
                                period_index += 1
                                continue
    
                            # SAVE SCHEDULE
                            teacher_schedule[
                                teacher_key
                            ] = True
    
                            class_schedule[
                                class_key
                            ] = True
    
                            timetable_entries.append((
                                grade,
                                day,
                                start_p,
                                end_p,
                                subject,
                                teacher
                            ))
    
                            daily_subject_count[
                                (grade, day, subject)
                            ] = daily_subject_count.get(
                                (grade, day, subject),
                                0
                            ) + 1
    
                            period_index += 1
    
            # INSERT TIMETABLE
            st.write(timetable_entries)
            st.write("Total Entries:", len(timetable_entries))
            c.executemany("""
            INSERT INTO timetable
            (
                grade,
                day,
                start_time,
                end_time,
                subject,
                teacher
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """, timetable_entries)
    
            conn.commit()
    
            st.success(
                "✅ Weekly Timetable Generated Successfully!"
            )
    
    # =====================================================
    # VIEW TIMETABLE
    # =====================================================
    
    if menu == "View Timetable":
    
        st.header("📅 View Timetable")
    
        selected_grade = st.selectbox(
            "Select Class",
            [
                "Grade 8A",
                "Grade 8B",
                "Grade 9A",
                "Grade 9B",
                "Grade 10A"
            ]
        )
    
        query = f"""
        SELECT
            day,
            start_time || ' - ' || end_time AS Time,
            subject,
            teacher
        FROM timetable
        WHERE grade = '{selected_grade}'
        """
    
        df = pd.read_sql(query, conn)
    
        if df.empty:
    
            st.warning(
                "⚠️ No timetable generated."
            )
    
        else:
    
            pivot_df = df.pivot(
                index="Time",
                columns="day",
                values="subject"
            )
    
            st.subheader(
                f"{selected_grade} Timetable"
            )
    
            st.dataframe(
                pivot_df,
                use_container_width=True
            )
    
            st.subheader(
                "Detailed Timetable"
            )
    
            st.dataframe(
                df,
                use_container_width=True
            )
    
    # =====================================================
    # CLOSE CONNECTION
    # =====================================================
    
    conn.close()
