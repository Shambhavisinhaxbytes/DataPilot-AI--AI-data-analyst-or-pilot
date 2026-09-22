# DataPilot AI

**Your AI Data Analyst & Business Intelligence Pilot**

DataPilot AI is an automated data analysis and Business Intelligence dashboard
generator. Upload a CSV or Excel file, and DataPilot AI will automatically
clean, analyze, visualize, and explain your data — no manual chart-building
or coding required.

Built as a beginner-friendly, BCA-level college project using **Python,
Streamlit, Pandas, NumPy, and Plotly**.

---

## Problem Statement

Most beginners and small business users have data (in CSV/Excel form) but
lack the skills to manually clean it, calculate statistics, build charts,
and extract insights. Existing BI tools (Power BI, Tableau) are powerful
but heavy, paid, or require a learning curve.

**DataPilot AI solves this** by automatically turning any raw spreadsheet
into a clean, interactive Business Intelligence dashboard with plain-English
insights and a question-answering assistant — all running locally, for free,
with no external API key required.

---

## Objectives

- Allow users to upload a dataset (CSV/XLSX/XLS) without any technical setup.
- Automatically profile the dataset (rows, columns, data types, missing data).
- Automatically detect and report data quality issues.
- Provide safe, optional data cleaning (without touching the original file).
- Automatically generate suitable, meaningful charts using Plotly.
- Automatically generate plain-English insights based only on real data.
- Allow users to "ask" questions about their data in natural language.
- Keep the whole system modular so a real LLM/API can be added later.

---

## Features

| Feature | Description |
|---|---|
| 🏠 Home Page | Clean landing page with upload area and feature overview |
| 📂 File Upload | Supports CSV, XLSX, XLS with safe error handling |
| 📊 Data Profiling | Auto-detects numeric, categorical, and date columns |
| 🧹 Data Quality | Reports missing values, duplicates, empty/constant columns |
| 🧼 Data Cleaning | Optional duplicate removal & missing-value filling (non-destructive) |
| 📈 Auto Visualization | Bar, line, scatter, pie, histogram & heatmap charts, chosen automatically |
| 💡 Automatic Insights | Plain-English, data-driven insights (max, min, average, correlations, outliers) |
| 💬 Ask DataPilot | Rule-based natural language Q&A about your dataset |
| ⚠️ Robust Error Handling | Handles corrupted, empty, or unusual files gracefully |

---

## Technologies Used

- **Python 3.9+**
- **Streamlit** – web app framework / UI
- **Pandas** – data loading, cleaning, and analysis
- **NumPy** – numerical operations
- **Plotly (Express)** – interactive charts
- **openpyxl** – reading Excel files (.xlsx)

No paid AI API is required. All "AI" features (insights & Q&A) currently run
on local, rule-based Pandas logic.

---

## Project Structure

```
DataPilot_AI/
│
├── app.py                  # Main Streamlit application (entry point)
├── requirements.txt        # Python dependencies
├── README.md                # This file
├── .gitignore
├── sample_data.csv          # Sample business dataset for demo/testing
│
├── utils/
│   ├── __init__.py
│   ├── data_loader.py       # Safely load CSV/Excel files
│   ├── data_cleaner.py      # Duplicate removal & missing-value handling
│   ├── analyzer.py          # Data profiling & data quality analysis
│   ├── visualizer.py        # Automatic Plotly chart generation
│   ├── insights.py          # Automatic, rule-based insights
│   └── question_engine.py   # "Ask DataPilot" natural language Q&A
│
└── assets/                  # (optional) UI assets, empty by default
```

---

## ⚙️ Installation

1. **Clone or download** this project folder onto your computer.
2. Open the folder in **VS Code** (or any IDE) and open a terminal inside it.
3. (Recommended) Create a virtual environment:

   ```bash
   python -m venv venv
   ```

   Activate it:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. Install all dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## How to Run

From inside the `DataPilot_AI` folder, run:

```bash
streamlit run app.py
```

This will open DataPilot AI automatically in your web browser
(usually at `http://localhost:8501`).

---

## How to Upload Data

1. Once the app opens, use the **sidebar** on the left ("Upload Your Dataset").
2. Click **Browse files** and select a `.csv`, `.xlsx`, or `.xls` file.
   - You can use the included `sample_data.csv` to test immediately.
3. DataPilot AI will validate and load the file, then automatically switch
   into the full dashboard view.

If the file is invalid, empty, or corrupted, DataPilot AI will show a clear
error message instead of crashing.

---

##  How the Dashboard Works

The dashboard is organized into 7 tabs:

1. **Overview** – KPI cards showing rows, columns, column types, missing values.
2. **Data Preview** – A scrollable/sliced table preview of your data with data types.
3. **Data Quality** – Missing values, duplicates, empty/constant columns, plus
   an optional data cleaning tool (does not overwrite your original data).
4. **Analysis** – Descriptive statistics for numeric columns, category
   summaries, and a correlation matrix.
5. **Visualizations** – Automatically generated Plotly charts (bar, line,
   scatter, pie, histogram, heatmap) based on what your data actually contains.
6. **Insights** – Plain-English, automatically generated observations about
   your dataset (highest/lowest values, dominant categories, correlations,
   missing/duplicate warnings, potential outliers).
7. **Ask DataPilot** – A chat-style box where you can type questions about
   your data.

A checkbox in the **Data Quality** tab lets you choose whether the rest of
the dashboard (Analysis, Visualizations, Insights, Ask DataPilot) should use
your **original** data or the **cleaned** version.

---

##  How "Ask DataPilot" Works

Ask DataPilot uses **rule-based keyword matching** combined with column-name
detection to understand simple questions and run the matching Pandas
operation. It does not use any external AI API in this version.

### Example Questions

- "What is the average sales?"
- "Which category has the highest sales?"
- "Which region performs best?"
- "What is the highest revenue?"
- "How many rows are there?"
- "Are there missing values?"
- "Which product has the highest value?"
- "What are the top 5 categories?"

If a question isn't understood, DataPilot AI shows a friendly message with
example questions instead of crashing.

---

## Testing Checklist

Use `sample_data.csv` and your own files to verify:

- [ ] Normal CSV file loads and dashboard renders correctly
- [ ] Normal Excel (.xlsx) file loads correctly
- [ ] A dataset with missing values shows correct warnings & can be cleaned
- [ ] A dataset with duplicate rows is detected and can be removed
- [ ] A purely numeric dataset still shows charts/insights sensibly
- [ ] A purely categorical (text-only) dataset doesn't crash
- [ ] A dataset with a date column produces a line/trend chart
- [ ] A very small dataset (a few rows) shows a warning but still works
- [ ] Uploading an unsupported file type (e.g. .txt) shows a clean error
- [ ] Uploading an empty file shows a clean error
- [ ] Asking an unrecognized question in "Ask DataPilot" shows a helpful fallback

---

##  Future Enhancements

DataPilot AI is intentionally built so these can be added without restructuring
the project:

- 🔌 Integration with a real LLM (OpenAI / Gemini / Anthropic Claude) inside
  `question_engine.py` for smarter natural-language understanding.
- 🗣️ Natural-language to SQL query generation.
- 📉 More advanced anomaly/outlier detection (e.g. Isolation Forest).
- 📄 Automated PDF report generation.
- 📊 Export the dashboard/insights as an Excel report.
- 🔐 User authentication & multi-user support.
- 🗄️ Direct database connectivity (MySQL/PostgreSQL) instead of just files.
- 🔮 Predictive analytics (forecasting future sales/trends).

---

## 🎓 About This Project (For Presentation)

DataPilot AI was built as a college-level demonstration of how automated,
rule-based logic (not necessarily a large paid AI model) can simulate an
"AI Business Intelligence Analyst." It shows practical use of Python data
tools (Pandas, NumPy), interactive visualization (Plotly), and web app
development (Streamlit), combined into one cohesive, modular application
that is easy to explain, demo, and extend.
