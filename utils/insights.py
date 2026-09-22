"""
insights.py
------------
Generates plain-English, automatically-derived insights from the dataset.

Rule: Every insight here MUST be calculated directly from the data.
Nothing is invented or guessed. Each insight is returned as a simple
string so it can be displayed as a bullet point in Streamlit.
"""

import pandas as pd


def generate_insights(df: pd.DataFrame, column_types: dict) -> list:
    """
    Build a list of insight strings covering:
        - Dataset size
        - Numeric column stats (max, min, average, total)
        - Categorical dominance (most common category)
        - Correlations between numeric columns
        - Missing data warnings
        - Duplicate data warnings
        - Basic outlier detection (IQR method)

    Returns
    -------
    list[str]
    """
    insights = []
    numeric_cols = column_types.get("numeric", [])
    categorical_cols = column_types.get("categorical", [])

    insights.extend(_dataset_size_insights(df))
    insights.extend(_numeric_insights(df, numeric_cols))
    insights.extend(_categorical_insights(df, categorical_cols))
    insights.extend(_correlation_insights(df, numeric_cols))
    insights.extend(_missing_data_insights(df))
    insights.extend(_duplicate_insights(df))
    insights.extend(_outlier_insights(df, numeric_cols))

    if not insights:
        insights.append(
            "Not enough data patterns were found to generate insights. "
            "Try uploading a dataset with more rows or a mix of numeric and category columns."
        )

    return insights


def _dataset_size_insights(df: pd.DataFrame) -> list:
    rows, cols = df.shape
    return [f"The dataset contains **{rows:,} rows** and **{cols} columns**."]


def _numeric_insights(df: pd.DataFrame, numeric_cols: list) -> list:
    results = []
    # Limit to first 3 numeric columns so the insights list stays readable
    for col in numeric_cols[:3]:
        series = df[col].dropna()
        if series.empty:
            continue

        total = series.sum()
        average = series.mean()
        max_val = series.max()
        min_val = series.min()

        results.append(
            f"**{col}** — Total: {total:,.2f}, Average: {average:,.2f}, "
            f"Highest: {max_val:,.2f}, Lowest: {min_val:,.2f}."
        )
    return results


def _categorical_insights(df: pd.DataFrame, categorical_cols: list) -> list:
    results = []
    for col in categorical_cols[:3]:
        series = df[col].dropna()
        if series.empty:
            continue

        value_counts = series.value_counts()
        top_value = value_counts.index[0]
        top_count = value_counts.iloc[0]
        top_pct = round((top_count / len(series)) * 100, 1)

        results.append(
            f"In **{col}**, the most common value is **'{top_value}'**, "
            f"appearing {top_count} times ({top_pct}% of records)."
        )

        # Top 5 categories, if there are enough unique values to be interesting
        if len(value_counts) >= 3:
            top5 = ", ".join(
                f"{name} ({count})" for name, count in value_counts.head(5).items()
            )
            results.append(f"Top categories in **{col}**: {top5}.")

    return results


def _correlation_insights(df: pd.DataFrame, numeric_cols: list) -> list:
    results = []
    if len(numeric_cols) < 2:
        return results

    corr_matrix = df[numeric_cols].corr()
    seen_pairs = set()

    for col1 in numeric_cols:
        for col2 in numeric_cols:
            if col1 == col2:
                continue
            pair = tuple(sorted([col1, col2]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            corr_value = corr_matrix.loc[col1, col2]
            if pd.isna(corr_value):
                continue

            if abs(corr_value) >= 0.7:
                direction = "positive" if corr_value > 0 else "negative"
                results.append(
                    f"There is a strong {direction} correlation ({corr_value:.2f}) "
                    f"between **{col1}** and **{col2}**."
                )

    return results[:3]  # keep it concise


def _missing_data_insights(df: pd.DataFrame) -> list:
    results = []
    total_missing = df.isna().sum().sum()

    if total_missing > 0:
        worst_col = df.isna().sum().idxmax()
        worst_count = df.isna().sum().max()
        results.append(
            f"⚠️ The dataset has **{int(total_missing)} missing values** in total. "
            f"The column with the most missing data is **{worst_col}** "
            f"({int(worst_count)} missing)."
        )
    else:
        results.append("✅ No missing values were found in this dataset.")

    return results


def _duplicate_insights(df: pd.DataFrame) -> list:
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        return [f"⚠️ Found **{int(duplicate_count)} duplicate rows** in the dataset."]
    return ["✅ No duplicate rows were found."]


def _outlier_insights(df: pd.DataFrame, numeric_cols: list) -> list:
    """
    Very simple outlier detection using the IQR (Interquartile Range) method.
    This is a standard, beginner-friendly statistical technique:
        - Anything below Q1 - 1.5*IQR or above Q3 + 1.5*IQR is an outlier.
    """
    results = []
    for col in numeric_cols[:3]:
        series = df[col].dropna()
        if len(series) < 5:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = series[(series < lower_bound) | (series > upper_bound)]

        if len(outliers) > 0:
            results.append(
                f"Detected **{len(outliers)} potential outlier(s)** in **{col}** "
                f"(values outside the typical range)."
            )

    return results
