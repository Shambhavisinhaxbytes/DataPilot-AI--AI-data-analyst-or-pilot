"""
analyzer.py
------------
Handles automatic data profiling and data quality analysis.

This module never modifies the original DataFrame - it only reads it and
returns summary information (dicts / DataFrames) that app.py can display.
"""

import pandas as pd
import numpy as np


def classify_columns(df: pd.DataFrame) -> dict:
    """
    Classify every column of the dataset into one of three buckets:
    numeric, categorical, or datetime.

    A column is treated as a "potential datetime" column if its name
    hints at a date/time OR pandas can successfully parse most of its
    values as dates. This keeps the logic simple and beginner-friendly
    while still being reasonably smart.
    """
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []

    for col in df.columns:
        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(col)
            continue

        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
            continue

        # Try to detect date-like columns by name or by attempting a parse
        if _looks_like_datetime(col, series):
            datetime_cols.append(col)
        else:
            categorical_cols.append(col)

    return {
        "numeric": numeric_cols,
        "categorical": categorical_cols,
        "datetime": datetime_cols,
    }


def _looks_like_datetime(col_name: str, series: pd.Series) -> bool:
    """Heuristic check to decide if a text column is really a date column."""
    name_hints = ["date", "time", "day", "month", "year"]
    name_lower = str(col_name).lower()

    if any(hint in name_lower for hint in name_hints):
        try:
            parsed = pd.to_datetime(series, errors="coerce")
            # If most values parsed successfully, treat it as a date column
            if parsed.notna().mean() > 0.7:
                return True
        except Exception:  # noqa: BLE001
            return False

    return False


def get_dataset_profile(df: pd.DataFrame) -> dict:
    """
    Build the main profiling summary used on the Overview tab.

    Returns a dictionary with counts and lists that are easy to render
    as KPI cards in Streamlit.
    """
    column_types = classify_columns(df)

    profile = {
        "total_rows": df.shape[0],
        "total_columns": df.shape[1],
        "numeric_columns": column_types["numeric"],
        "categorical_columns": column_types["categorical"],
        "datetime_columns": column_types["datetime"],
        "numeric_count": len(column_types["numeric"]),
        "categorical_count": len(column_types["categorical"]),
        "datetime_count": len(column_types["datetime"]),
        "missing_values_total": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
    }
    return profile


def get_missing_values_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a tidy table of missing values per column (count + %)."""
    missing_count = df.isna().sum()
    missing_percent = (missing_count / len(df) * 100).round(2)

    table = pd.DataFrame({
        "Column": missing_count.index,
        "Missing Values": missing_count.values,
        "Missing %": missing_percent.values,
        "Data Type": [str(df[col].dtype) for col in df.columns],
    })

    table = table[table["Missing Values"] > 0].sort_values(
        "Missing Values", ascending=False
    ).reset_index(drop=True)

    return table


def get_data_quality_report(df: pd.DataFrame) -> dict:
    """
    Build a data quality report describing common issues:
        - Duplicate rows
        - Fully empty columns
        - Constant-value columns (same value in every row - not useful)
        - Columns with very high missing percentage
    """
    duplicate_rows = int(df.duplicated().sum())

    empty_columns = [col for col in df.columns if df[col].isna().all()]

    constant_columns = [
        col for col in df.columns
        if df[col].nunique(dropna=True) == 1 and col not in empty_columns
    ]

    high_missing_columns = []
    for col in df.columns:
        missing_pct = df[col].isna().mean() * 100
        if missing_pct >= 50 and col not in empty_columns:
            high_missing_columns.append((col, round(missing_pct, 2)))

    issues_found = (
        len(empty_columns) + len(constant_columns) +
        len(high_missing_columns) + (1 if duplicate_rows > 0 else 0)
    )

    return {
        "duplicate_rows": duplicate_rows,
        "empty_columns": empty_columns,
        "constant_columns": constant_columns,
        "high_missing_columns": high_missing_columns,
        "total_issues": issues_found,
    }


def get_numeric_summary(df: pd.DataFrame, numeric_columns: list) -> pd.DataFrame:
    """Return descriptive statistics (min, max, mean, etc.) for numeric columns."""
    if not numeric_columns:
        return pd.DataFrame()

    summary = df[numeric_columns].describe().T
    summary = summary.round(2)
    summary.insert(0, "Column", summary.index)
    summary = summary.reset_index(drop=True)
    return summary


def get_correlation_matrix(df: pd.DataFrame, numeric_columns: list) -> pd.DataFrame:
    """Return a correlation matrix if there are at least 2 numeric columns."""
    if len(numeric_columns) < 2:
        return pd.DataFrame()
    return df[numeric_columns].corr().round(2)
