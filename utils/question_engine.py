"""
question_engine.py
--------------------
Powers the "Ask DataPilot" feature.

This is a RULE-BASED natural language question answering engine. It looks
for keywords in the user's question (average, highest, lowest, count,
missing, duplicate, top, etc.) and combines them with column-name matching
to run the correct Pandas operation.

FUTURE UPGRADE PATH (see README "Future Enhancements"):
    This function is intentionally kept isolated from the Streamlit UI.
    To connect a real LLM later, you would replace/extend `answer_question()`
    so that instead of (or in addition to) keyword matching, it sends the
    question + a description of the dataset to an LLM API (e.g. OpenAI,
    Gemini, or Anthropic's Claude) and lets the model decide which pandas
    operation to run, or generate the answer directly. The rest of the app
    (app.py) does not need to change at all - it just calls
    answer_question(df, question) and displays the returned string.
"""

import re
import pandas as pd


def answer_question(df: pd.DataFrame, question: str, column_types: dict) -> str:
    """
    Main entry point. Takes the user's free-text question and the dataset,
    and returns a plain-English answer string.

    Parameters
    ----------
    df : pd.DataFrame
        The (cleaned or original) dataset currently loaded.
    question : str
        The raw question typed by the user.
    column_types : dict
        Output of analyzer.classify_columns(df) -> {"numeric": [...], ...}

    Returns
    -------
    str : the answer, or a helpful fallback message if the question
          could not be understood.
    """
    if not question or not question.strip():
        return "Please type a question first."

    q = question.lower().strip()
    numeric_cols = column_types.get("numeric", [])
    categorical_cols = column_types.get("categorical", [])

    # 1. Row count questions
    if _matches_any(q, ["how many rows", "number of rows", "row count", "total rows"]):
        return f"The dataset has **{df.shape[0]:,} rows**."

    # 2. Column count questions
    if _matches_any(q, ["how many columns", "number of columns", "column count"]):
        return f"The dataset has **{df.shape[1]} columns**."

    # 3. Missing values questions
    if _matches_any(q, ["missing value", "missing data", "null value", "nan"]):
        total_missing = int(df.isna().sum().sum())
        if total_missing == 0:
            return "✅ No, there are no missing values in this dataset."
        worst_col = df.isna().sum().idxmax()
        return (
            f"Yes, there are **{total_missing} missing values** in total. "
            f"The column with the most missing values is **{worst_col}**."
        )

    # 4. Duplicate questions
    if _matches_any(q, ["duplicate"]):
        dup_count = int(df.duplicated().sum())
        if dup_count == 0:
            return "✅ No duplicate rows were found."
        return f"There are **{dup_count} duplicate rows** in the dataset."

    # 5. Try to find a numeric column mentioned in the question
    target_numeric_col = _find_column_in_question(q, numeric_cols)

    # 6. Average / mean questions
    if _matches_any(q, ["average", "mean"]):
        if target_numeric_col:
            value = df[target_numeric_col].mean()
            return f"The average **{target_numeric_col}** is **{value:,.2f}**."
        elif numeric_cols:
            value = df[numeric_cols[0]].mean()
            return f"The average **{numeric_cols[0]}** is **{value:,.2f}**."
        return "I couldn't find a numeric column to calculate the average for."

    # 7. Highest / maximum questions (could refer to a numeric value OR a
    #    "which category has highest X" type question)
    if _matches_any(q, ["highest", "maximum", "max", "top", "largest"]):
        # "Which <category> has the highest <numeric>" style question
        target_cat_col = _find_column_in_question(q, categorical_cols)

        # "top 5 categories" style question
        top_n_match = re.search(r"top\s+(\d+)", q)
        if top_n_match and target_cat_col:
            n = int(top_n_match.group(1))
            return _top_n_categories(df, target_cat_col, n)
        if top_n_match and not target_cat_col and categorical_cols:
            n = int(top_n_match.group(1))
            return _top_n_categories(df, categorical_cols[0], n)

        if target_cat_col and (target_numeric_col or numeric_cols):
            num_col = target_numeric_col or numeric_cols[0]
            return _best_category_by_metric(df, target_cat_col, num_col, highest=True)

        if target_numeric_col:
            value = df[target_numeric_col].max()
            return f"The highest **{target_numeric_col}** is **{value:,.2f}**."
        elif numeric_cols:
            value = df[numeric_cols[0]].max()
            return f"The highest **{numeric_cols[0]}** is **{value:,.2f}**."

        return "I couldn't find a numeric column to find the highest value for."

    # 8. Lowest / minimum questions
    if _matches_any(q, ["lowest", "minimum", "min", "smallest"]):
        target_cat_col = _find_column_in_question(q, categorical_cols)

        if target_cat_col and (target_numeric_col or numeric_cols):
            num_col = target_numeric_col or numeric_cols[0]
            return _best_category_by_metric(df, target_cat_col, num_col, highest=False)

        if target_numeric_col:
            value = df[target_numeric_col].min()
            return f"The lowest **{target_numeric_col}** is **{value:,.2f}**."
        elif numeric_cols:
            value = df[numeric_cols[0]].min()
            return f"The lowest **{numeric_cols[0]}** is **{value:,.2f}**."

        return "I couldn't find a numeric column to find the lowest value for."

    # 9. Total / sum questions
    if _matches_any(q, ["total", "sum"]):
        if target_numeric_col:
            value = df[target_numeric_col].sum()
            return f"The total **{target_numeric_col}** is **{value:,.2f}**."
        elif numeric_cols:
            value = df[numeric_cols[0]].sum()
            return f"The total **{numeric_cols[0]}** is **{value:,.2f}**."
        return "I couldn't find a numeric column to sum."

    # 10. "Which <category> performs best" style question (no explicit metric)
    target_cat_col = _find_column_in_question(q, categorical_cols)
    if target_cat_col and _matches_any(q, ["perform best", "best", "top performing"]):
        if numeric_cols:
            return _best_category_by_metric(df, target_cat_col, numeric_cols[0], highest=True)

    # 11. Unique values questions
    if _matches_any(q, ["unique value", "how many unique", "distinct value"]):
        col = target_numeric_col or _find_column_in_question(q, categorical_cols)
        if col:
            return f"**{col}** has **{df[col].nunique()} unique values**."
        return "Please mention a column name so I can count unique values."

    # If nothing matched, return a helpful fallback (never crash!)
    return (
        "🤔 I couldn't understand that question yet. Try asking things like:\n\n"
        "- What is the average [column name]?\n"
        "- Which [category column] has the highest [numeric column]?\n"
        "- What is the highest / lowest [column name]?\n"
        "- How many rows are there?\n"
        "- Are there missing values?\n"
        "- What are the top 5 [category column]?"
    )


def _matches_any(text: str, keywords: list) -> bool:
    """Return True if any keyword phrase appears in the text."""
    return any(keyword in text for keyword in keywords)


def _find_column_in_question(question: str, columns: list):
    """
    Try to find which column (from a given list) is mentioned in the
    question text. Matching is case-insensitive, handles column names
    that contain spaces or underscores, and also checks a simple plural
    form (e.g. a column called "Category" should match the word
    "categories" or "categorys" in a question).
    """
    best_match = None
    best_match_len = 0

    for col in columns:
        col_normalized = str(col).lower().replace("_", " ")
        candidates = [col_normalized]

        # Simple pluralization so "category" also matches "categories"
        if col_normalized.endswith("y"):
            candidates.append(col_normalized[:-1] + "ies")
        else:
            candidates.append(col_normalized + "s")

        for candidate in candidates:
            if candidate in question and len(candidate) > best_match_len:
                best_match = col
                best_match_len = len(candidate)

    return best_match


def _best_category_by_metric(df: pd.DataFrame, category_col: str,
                              numeric_col: str, highest: bool = True) -> str:
    """Find which category has the highest/lowest total for a numeric column."""
    grouped = df.groupby(category_col)[numeric_col].sum()

    if grouped.empty:
        return f"I couldn't compute results for {category_col} and {numeric_col}."

    if highest:
        best_name = grouped.idxmax()
        best_value = grouped.max()
        label = "highest"
    else:
        best_name = grouped.idxmin()
        best_value = grouped.min()
        label = "lowest"

    return (
        f"**{best_name}** has the {label} total **{numeric_col}** "
        f"with a value of **{best_value:,.2f}**."
    )


def _top_n_categories(df: pd.DataFrame, category_col: str, n: int) -> str:
    """Return the top N most frequent values in a categorical column."""
    value_counts = df[category_col].value_counts().head(n)

    if value_counts.empty:
        return f"I couldn't find category data in {category_col}."

    lines = [f"{i+1}. {name} ({count} records)" for i, (name, count) in enumerate(value_counts.items())]
    return f"Top {n} in **{category_col}**:\n\n" + "\n".join(lines)
