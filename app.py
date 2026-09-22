"""
app.py
-------
DataPilot AI - "Your AI Data Analyst & Business Intelligence Pilot"

This is the main entry point of the Streamlit application. It ties
together all the modules inside utils/ to build:
    - A professional landing / upload page
    - A tabbed BI dashboard (Overview, Data Preview, Data Quality,
      Analysis, Visualizations, Insights, Ask DataPilot)

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd

from utils import data_loader
from utils import data_cleaner
from utils import analyzer
from utils import visualizer
from utils import insights as insights_module
from utils import question_engine


# ----------------------------------------------------------------------
# PAGE CONFIGURATION
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="DataPilot AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------------------------------------------------
# SIMPLE CUSTOM CSS - keeps the app looking clean & professional
# ----------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        margin-bottom: 0rem;
        background: linear-gradient(90deg, #2563EB, #7C3AED);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .tagline {
        font-size: 1.15rem;
        color: #6B7280;
        margin-top: 0.2rem;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #111827;
    }
    .kpi-label {
        font-size: 0.85rem;
        color: #6B7280;
    }
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
        color: #111827;
    }
    .insight-item {
        background-color: #F9FAFB;
        border-left: 4px solid #2563EB;
        padding: 0.6rem 1rem;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# ----------------------------------------------------------------------
if "original_df" not in st.session_state:
    st.session_state.original_df = None
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None
if "clean_report" not in st.session_state:
    st.session_state.clean_report = None
if "use_cleaned" not in st.session_state:
    st.session_state.use_cleaned = False
if "file_info" not in st.session_state:
    st.session_state.file_info = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of (question, answer) tuples


def get_active_dataframe():
    """
    Return whichever DataFrame should currently be used for analysis:
    the cleaned version (if the user chose to clean & apply it) or the
    original uploaded version.
    """
    if st.session_state.use_cleaned and st.session_state.cleaned_df is not None:
        return st.session_state.cleaned_df
    return st.session_state.original_df


# ----------------------------------------------------------------------
# HEADER (always visible)
# ----------------------------------------------------------------------
st.markdown('<div class="main-title">🧭 DataPilot AI</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tagline">Your AI Data Analyst &amp; Business Intelligence Pilot</div>',
    unsafe_allow_html=True,
)


# ----------------------------------------------------------------------
# LANDING / UPLOAD SECTION
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Upload Your Dataset")
    st.caption("Supported formats: CSV, XLSX, XLS")

    uploaded_file = st.file_uploader(
        "Choose a file", type=["csv", "xlsx", "xls"], label_visibility="collapsed"
    )

    if uploaded_file is not None:
        df, error = data_loader.load_file(uploaded_file)
        if error:
            st.error(error)
        else:
            # Only reload into session_state if it's a new file
            if (
                st.session_state.file_info is None
                or st.session_state.file_info.get("file_name") != uploaded_file.name
            ):
                st.session_state.original_df = df
                st.session_state.cleaned_df = None
                st.session_state.clean_report = None
                st.session_state.use_cleaned = False
                st.session_state.chat_history = []
                st.session_state.file_info = data_loader.get_basic_file_info(uploaded_file, df)
            st.success(f"✅ Loaded '{uploaded_file.name}' successfully!")

    st.divider()
    st.caption(
        "DataPilot AI analyzes your data locally using Pandas & rule-based "
        "logic — no external AI API key required."
    )

    if st.session_state.original_df is None:
        st.info("👈 Upload a CSV or Excel file to get started.")


# ----------------------------------------------------------------------
# IF NO FILE UPLOADED YET -> SHOW LANDING PAGE
# ----------------------------------------------------------------------
if st.session_state.original_df is None:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📊 Automatic Analysis")
        st.write("Upload any CSV or Excel file and DataPilot AI instantly profiles "
                  "your data — rows, columns, types, and data quality.")
    with col2:
        st.markdown("### 📈 Smart Visualizations")
        st.write("Interactive Plotly charts are generated automatically based on "
                  "the type of data you have — no chart-building needed.")
    with col3:
        st.markdown("### 💬 Ask DataPilot")
        st.write("Ask plain-English questions about your data — like a mini AI "
                  "data analyst — and get instant answers.")

    st.markdown("---")
    st.markdown("#### 🚀 How it works")
    st.markdown(
        """
        1. **Upload** your CSV or Excel file from the sidebar.
        2. DataPilot AI automatically **profiles and cleans** your data.
        3. Explore the **BI Dashboard** across 7 tabs: Overview, Data Preview,
           Data Quality, Analysis, Visualizations, Insights, and Ask DataPilot.
        4. **Ask questions** about your dataset in plain English.
        """
    )
    st.stop()  # Don't render the rest of the app until a file is uploaded


# ----------------------------------------------------------------------
# FILE UPLOADED -> BUILD DASHBOARD
# ----------------------------------------------------------------------
active_df = get_active_dataframe()

# Guard: extremely small datasets still need to work without crashing
if active_df.shape[0] < 2:
    st.warning(
        "⚠️ This dataset has very few rows. Some charts and statistics may not "
        "be meaningful, but DataPilot AI will still try its best!"
    )

column_types = analyzer.classify_columns(active_df)
profile = analyzer.get_dataset_profile(active_df)
quality_report = analyzer.get_data_quality_report(active_df)

tab_names = [
    "🏠 Overview", "🔍 Data Preview", "🧹 Data Quality",
    "📊 Analysis", "📈 Visualizations", "💡 Insights", "💬 Ask DataPilot",
]
tab_overview, tab_preview, tab_quality, tab_analysis, tab_viz, tab_insights, tab_ask = st.tabs(tab_names)


# ----------------------------------------------------------------------
# TAB 1: OVERVIEW
# ----------------------------------------------------------------------
with tab_overview:
    st.markdown('<div class="section-header">Dataset Overview</div>', unsafe_allow_html=True)

    file_info = st.session_state.file_info
    kpi_cols = st.columns(4)
    kpi_values = [
        ("File Name", file_info["file_name"]),
        ("Total Rows", f"{profile['total_rows']:,}"),
        ("Total Columns", f"{profile['total_columns']}"),
        ("File Size (KB)", f"{file_info['file_size_kb']}"),
    ]
    for col, (label, value) in zip(kpi_cols, kpi_values):
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-value">{value}</div>'
                f'<div class="kpi-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    kpi_cols2 = st.columns(4)
    kpi_values2 = [
        ("Numeric Columns", profile["numeric_count"]),
        ("Categorical Columns", profile["categorical_count"]),
        ("Date/Time Columns", profile["datetime_count"]),
        ("Missing Values", profile["missing_values_total"]),
    ]
    for col, (label, value) in zip(kpi_cols2, kpi_values2):
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-value">{value}</div>'
                f'<div class="kpi-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    with st.expander("📋 Column Type Breakdown", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Numeric Columns**")
            st.write(column_types["numeric"] or "None detected")
        with c2:
            st.markdown("**Categorical Columns**")
            st.write(column_types["categorical"] or "None detected")
        with c3:
            st.markdown("**Date/Time Columns**")
            st.write(column_types["datetime"] or "None detected")

    st.info(
        f"💾 Estimated memory usage: **{profile['memory_usage_kb']} KB** | "
        f"🔁 Duplicate rows: **{profile['duplicate_rows']}**"
    )


# ----------------------------------------------------------------------
# TAB 2: DATA PREVIEW
# ----------------------------------------------------------------------
with tab_preview:
    st.markdown('<div class="section-header">Data Preview</div>', unsafe_allow_html=True)
    st.caption("Showing the currently active dataset (original or cleaned, based on your choice below).")

    num_rows = st.slider("Number of rows to preview", min_value=5, max_value=min(100, active_df.shape[0]) or 5,
                          value=min(10, active_df.shape[0]))
    st.dataframe(active_df.head(num_rows), use_container_width=True)

    with st.expander("📐 Column Data Types"):
        dtype_table = pd.DataFrame({
            "Column": active_df.columns,
            "Data Type": [str(dt) for dt in active_df.dtypes],
            "Unique Values": [active_df[c].nunique() for c in active_df.columns],
        })
        st.dataframe(dtype_table, use_container_width=True)


# ----------------------------------------------------------------------
# TAB 3: DATA QUALITY & CLEANING
# ----------------------------------------------------------------------
with tab_quality:
    st.markdown('<div class="section-header">Data Quality Report</div>', unsafe_allow_html=True)

    q_cols = st.columns(4)
    q_values = [
        ("Duplicate Rows", quality_report["duplicate_rows"]),
        ("Empty Columns", len(quality_report["empty_columns"])),
        ("Constant Columns", len(quality_report["constant_columns"])),
        ("High-Missing Columns (>=50%)", len(quality_report["high_missing_columns"])),
    ]
    for col, (label, value) in zip(q_cols, q_values):
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-value">{value}</div>'
                f'<div class="kpi-label">{label}</div></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    missing_table = analyzer.get_missing_values_table(active_df)
    if not missing_table.empty:
        st.markdown("**Missing Values by Column**")
        st.dataframe(missing_table, use_container_width=True)
    else:
        st.success("✅ No missing values found in any column.")

    if quality_report["empty_columns"]:
        st.warning(f"⚠️ Fully empty columns: {', '.join(quality_report['empty_columns'])}")
    if quality_report["constant_columns"]:
        st.warning(f"⚠️ Columns with only one repeated value: {', '.join(quality_report['constant_columns'])}")
    if quality_report["high_missing_columns"]:
        col_list = ", ".join(f"{c} ({p}%)" for c, p in quality_report["high_missing_columns"])
        st.warning(f"⚠️ Columns with 50%+ missing data: {col_list}")

    st.markdown("---")
    st.markdown('<div class="section-header">🧹 Data Cleaning</div>', unsafe_allow_html=True)
    st.caption("Cleaning always works on a COPY of your data. Your original upload is never changed.")

    clean_col1, clean_col2, clean_col3 = st.columns(3)
    with clean_col1:
        remove_dupes = st.checkbox("Remove duplicate rows", value=True)
    with clean_col2:
        numeric_strategy = st.selectbox("Fill missing numeric values with", ["mean", "median", "none"])
    with clean_col3:
        categorical_strategy = st.selectbox("Fill missing categorical values with", ["mode", "unknown", "none"])

    if st.button("🧹 Clean Dataset", type="primary"):
        cleaned_df, report = data_cleaner.clean_dataset(
            st.session_state.original_df,
            remove_duplicates=remove_dupes,
            fill_missing_numeric=numeric_strategy,
            fill_missing_categorical=categorical_strategy,
        )
        st.session_state.cleaned_df = cleaned_df
        st.session_state.clean_report = report
        st.success("Dataset cleaned successfully! Review the summary below, then choose whether to use it.")

    if st.session_state.clean_report:
        report = st.session_state.clean_report
        st.markdown("**Cleaning Summary**")
        st.write(f"- Rows before: {report['rows_before']} → Rows after: {report['rows_after']}")
        st.write(f"- Duplicate rows removed: {report['duplicates_removed']}")

        if report["numeric_filled"]:
            st.write("- Numeric columns filled:")
            for col, info in report["numeric_filled"].items():
                st.write(f"  • {col}: {info['count']} values filled with {info['strategy']} = {info['value_used']}")

        if report["categorical_filled"]:
            st.write("- Categorical columns filled:")
            for col, info in report["categorical_filled"].items():
                st.write(f"  • {col}: {info['count']} values filled with '{info['value_used']}' ({info['strategy']})")

        st.session_state.use_cleaned = st.checkbox(
            "✅ Use cleaned dataset for Analysis, Visualizations, Insights & Ask DataPilot",
            value=st.session_state.use_cleaned,
        )


# ----------------------------------------------------------------------
# TAB 4: ANALYSIS
# ----------------------------------------------------------------------
with tab_analysis:
    st.markdown('<div class="section-header">Statistical Analysis</div>', unsafe_allow_html=True)

    if column_types["numeric"]:
        st.markdown("**Numeric Column Summary**")
        numeric_summary = analyzer.get_numeric_summary(active_df, column_types["numeric"])
        st.dataframe(numeric_summary, use_container_width=True)
    else:
        st.info("No numeric columns were found to summarize.")

    if column_types["categorical"]:
        st.markdown("**Categorical Column Summary**")
        cat_summary_rows = []
        for col in column_types["categorical"]:
            cat_summary_rows.append({
                "Column": col,
                "Unique Values": active_df[col].nunique(),
                "Most Common": active_df[col].mode().iloc[0] if not active_df[col].mode().empty else "N/A",
            })
        st.dataframe(pd.DataFrame(cat_summary_rows), use_container_width=True)
    else:
        st.info("No categorical columns were found to summarize.")

    if len(column_types["numeric"]) >= 2:
        st.markdown("**Correlation Matrix**")
        corr_matrix = analyzer.get_correlation_matrix(active_df, column_types["numeric"])
        st.dataframe(corr_matrix, use_container_width=True)
    else:
        st.info("Need at least 2 numeric columns to calculate correlations.")


# ----------------------------------------------------------------------
# TAB 5: VISUALIZATIONS
# ----------------------------------------------------------------------
with tab_viz:
    st.markdown('<div class="section-header">Automatic Visualizations</div>', unsafe_allow_html=True)
    st.caption("Charts below are automatically chosen based on the columns available in your dataset.")

    charts = visualizer.auto_generate_charts(active_df, column_types)

    if not charts:
        st.warning(
            "⚠️ No suitable charts could be generated automatically. "
            "This usually happens with datasets that have only one column, "
            "or no numeric/categorical data to visualize."
        )
    else:
        # Display charts two per row for a clean dashboard layout
        for i in range(0, len(charts), 2):
            row_charts = charts[i:i + 2]
            cols = st.columns(len(row_charts))
            for col, chart in zip(cols, row_charts):
                with col:
                    st.plotly_chart(chart["figure"], use_container_width=True)


# ----------------------------------------------------------------------
# TAB 6: INSIGHTS
# ----------------------------------------------------------------------
with tab_insights:
    st.markdown('<div class="section-header">💡 Automatically Generated Insights</div>', unsafe_allow_html=True)
    st.caption("All insights below are calculated directly from your uploaded data — nothing is invented.")

    generated_insights = insights_module.generate_insights(active_df, column_types)
    for insight in generated_insights:
        st.markdown(f'<div class="insight-item">{insight}</div>', unsafe_allow_html=True)


# ----------------------------------------------------------------------
# TAB 7: ASK DATAPILOT
# ----------------------------------------------------------------------
with tab_ask:
    st.markdown('<div class="section-header">💬 Ask DataPilot</div>', unsafe_allow_html=True)
    st.caption(
        "Ask questions about your data in plain English. This currently runs on "
        "local rule-based logic (no external AI API needed)."
    )

    with st.expander("💡 Example questions you can try"):
        st.markdown(
            """
            - What is the average sales?
            - Which category has the highest sales?
            - Which region performs best?
            - What is the highest revenue?
            - How many rows are there?
            - Are there missing values?
            - What are the top 5 categories?
            """
        )

    user_question = st.text_input("Type your question about the dataset:", key="ask_input")
    ask_button = st.button("Ask", type="primary")

    if ask_button and user_question.strip():
        answer = question_engine.answer_question(active_df, user_question, column_types)
        st.session_state.chat_history.append((user_question, answer))

    if st.session_state.chat_history:
        st.markdown("---")
        st.markdown("**Conversation History**")
        for q, a in reversed(st.session_state.chat_history):
            st.markdown(f"🧑 **You:** {q}")
            st.markdown(f"🧭 **DataPilot AI:** {a}")
            st.markdown("")


# ----------------------------------------------------------------------
# FOOTER
# ----------------------------------------------------------------------
st.markdown("---")
st.caption("DataPilot AI — Built with Streamlit, Pandas & Plotly | Local rule-based analysis, no API key required.")
