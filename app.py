# ----------------------------
# CLEAN DATA (UPDATED FIX)
# ----------------------------
learner_df.columns = learner_df.columns.str.strip().str.lower()
reg_df.columns = reg_df.columns.str.strip().str.lower()

# ----------------------------
# KPI LOGIC (NEW)
# ----------------------------
if "student_id" not in learner_df.columns:
    st.error("student_id missing in Learner Tracker")
    st.stop()

if "student_id" not in reg_df.columns:
    st.error("student_id missing in Registration Form")
    st.stop()

# Remove blanks
learner_df = learner_df[learner_df["student_id"].astype(str).str.strip() != ""]
reg_df = reg_df[reg_df["student_id"].astype(str).str.strip() != ""]

registered = reg_df["student_id"].nunique()
attendance = learner_df["student_id"].nunique()

present_ids = set(learner_df["student_id"])
all_ids = set(reg_df["student_id"])

absent_ids = all_ids - present_ids
absent_df = reg_df[reg_df["student_id"].isin(absent_ids)]

# ----------------------------
# DASHBOARD TAB (REPLACE KPI SECTION ONLY)
# ----------------------------
with tab1:
    st.markdown('<div class="section-title">Summary KPIs</div>', unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)

    with k1:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Registered</div>
            <div class="kpi-value">{registered}</div>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Attendance</div>
            <div class="kpi-value">{attendance}</div>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-title">Absent Learners</div>
            <div class="kpi-value">{len(absent_ids)}</div>
        </div>
        """, unsafe_allow_html=True)

    # ----------------------------
    # NEW CHARTS
    # ----------------------------
    c1, c2 = st.columns(2)

    # ABSENT PIE
    with c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Absent Learners by Gender")

        if "gender" in absent_df.columns:
            counts = absent_df["gender"].value_counts()

            fig, ax = plt.subplots()
            ax.pie(counts, labels=counts.index, autopct='%1.0f%%')
            ax.axis("equal")

            st.pyplot(fig)
        else:
            st.info("No gender data available.")

        st.markdown('</div>', unsafe_allow_html=True)

    # PRESENT BAR
    with c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        st.subheader("Present Learners by Gender")

        present_df = reg_df[reg_df["student_id"].isin(present_ids)]

        if "gender" in present_df.columns:
            counts = present_df["gender"].value_counts()

            fig, ax = plt.subplots()
            bars = ax.bar(counts.index, counts.values)

            for bar in bars:
                ax.text(
                    bar.get_x() + bar.get_width()/2,
                    bar.get_height(),
                    str(int(bar.get_height())),
                    ha="center"
                )

            st.pyplot(fig)
        else:
            st.info("No gender data available.")

        st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------
    # ABSENT TABLE (NEW)
    # ----------------------------
    st.markdown('<div class="chart-box">', unsafe_allow_html=True)
    st.subheader("Absent Learners")

    if not absent_df.empty:
        st.dataframe(absent_df, use_container_width=True)
    else:
        st.success("No absent learners 🎉")

    st.markdown('</div>', unsafe_allow_html=True)
