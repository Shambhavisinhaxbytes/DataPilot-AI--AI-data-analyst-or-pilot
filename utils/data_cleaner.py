"""
data_cleaner.py
-----------------
Provides safe, optional data cleaning operations.

IMPORTANT DESIGN RULE (from the project spec):
    The original uploaded DataFrame must NEVER be modified silently.
    Every cleaning function here works on a COPY of the DataFrame and
    returns a new, cleaned DataFrame plus a human-readable report of what
    was changed. app.py keeps both the original and the cleaned version
    in session_state, and lets the user choose which one to analyze.
"""

import pandas as pd


def clean_dataset(df: pd.DataFrame, remove_duplicates: bool = True,
                   fill_missing_numeric: str = "mean",
                   fill_missing_categorical: str = "mode") -> tuple:
    """
    Perform safe cleaning operations on a COPY of the dataset.

    Parameters
    ----------
    df : pd.DataFrame
        The original dataset (will not be modified).
    remove_duplicates : bool
        Whether to drop duplicate rows.
    fill_missing_numeric : str
        Strategy for numeric missing values: "mean", "median", or "none".
    fill_missing_categorical : str
        Strategy for categorical missing values: "mode", "unknown", or "none".

    Returns
    -------
    (cleaned_df, report) : tuple
        cleaned_df -> a new, cleaned pandas DataFrame
        report     -> dict summarizing exactly what was changed
    """
    cleaned_df = df.copy(deep=True)
    report = {
        "duplicates_removed": 0,
        "numeric_filled": {},
        "categorical_filled": {},
        "rows_before": df.shape[0],
        "rows_after": None,
    }

    # 1. Remove duplicate rows
    if remove_duplicates:
        before = cleaned_df.shape[0]
        cleaned_df = cleaned_df.drop_duplicates()
        report["duplicates_removed"] = before - cleaned_df.shape[0]

    # 2. Fill missing values
    for col in cleaned_df.columns:
        missing_count = cleaned_df[col].isna().sum()
        if missing_count == 0:
            continue

        is_numeric = pd.api.types.is_numeric_dtype(cleaned_df[col])

        if is_numeric and fill_missing_numeric != "none":
            fill_value = _get_numeric_fill_value(cleaned_df[col], fill_missing_numeric)
            if fill_value is not None:
                cleaned_df[col] = cleaned_df[col].fillna(fill_value)
                report["numeric_filled"][col] = {
                    "count": int(missing_count),
                    "strategy": fill_missing_numeric,
                    "value_used": round(float(fill_value), 2),
                }

        elif not is_numeric and fill_missing_categorical != "none":
            fill_value = _get_categorical_fill_value(cleaned_df[col], fill_missing_categorical)
            cleaned_df[col] = cleaned_df[col].fillna(fill_value)
            report["categorical_filled"][col] = {
                "count": int(missing_count),
                "strategy": fill_missing_categorical,
                "value_used": str(fill_value),
            }

    report["rows_after"] = cleaned_df.shape[0]
    return cleaned_df, report


def _get_numeric_fill_value(series: pd.Series, strategy: str):
    """Return the value to use for filling missing numeric data."""
    if series.dropna().empty:
        return None  # nothing to compute a mean/median from

    if strategy == "mean":
        return series.mean()
    elif strategy == "median":
        return series.median()
    return None


def _get_categorical_fill_value(series: pd.Series, strategy: str):
    """Return the value to use for filling missing categorical data."""
    if strategy == "mode":
        mode_values = series.mode(dropna=True)
        if not mode_values.empty:
            return mode_values.iloc[0]
        return "Unknown"
    elif strategy == "unknown":
        return "Unknown"
    return "Unknown"


def remove_duplicate_rows_only(df: pd.DataFrame) -> tuple:
    """Convenience function: remove only duplicate rows, nothing else."""
    before = df.shape[0]
    cleaned_df = df.drop_duplicates().copy()
    removed = before - cleaned_df.shape[0]
    return cleaned_df, removed
