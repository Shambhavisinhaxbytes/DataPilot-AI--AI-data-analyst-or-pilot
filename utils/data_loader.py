"""
data_loader.py
----------------
Responsible for safely reading uploaded files (CSV, XLSX, XLS) into a
pandas DataFrame. Handles common real-world problems like:
    - Corrupted files
    - Empty files
    - Wrong/unsupported extensions
    - Encoding issues in CSV files

Every function here returns a tuple: (dataframe_or_None, error_message_or_None)
This pattern makes it very easy for app.py to check:
    df, error = load_file(uploaded_file)
    if error:
        st.error(error)
    else:
        # use df safely
"""

import pandas as pd


# File extensions we officially support in this project
SUPPORTED_EXTENSIONS = ["csv", "xlsx", "xls"]


def get_file_extension(filename: str) -> str:
    """Return the lowercase extension of a filename, without the dot."""
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def load_file(uploaded_file):
    """
    Load an uploaded file (from st.file_uploader) into a pandas DataFrame.

    Parameters
    ----------
    uploaded_file : UploadedFile
        The file object returned by Streamlit's file_uploader widget.

    Returns
    -------
    (df, error) : tuple
        df    -> pandas.DataFrame if successful, otherwise None
        error -> str with a friendly error message if something went wrong,
                 otherwise None
    """
    if uploaded_file is None:
        return None, "No file was uploaded."

    filename = uploaded_file.name
    extension = get_file_extension(filename)

    if extension not in SUPPORTED_EXTENSIONS:
        return None, (
            f"Unsupported file type '.{extension}'. "
            f"Please upload one of: {', '.join(SUPPORTED_EXTENSIONS)}."
        )

    try:
        if extension == "csv":
            df = _read_csv_safely(uploaded_file)
        else:  # xlsx or xls
            df = pd.read_excel(uploaded_file)
    except Exception as exc:  # noqa: BLE001 - we want to catch anything here
        return None, f"We couldn't read this file. It may be corrupted. Details: {exc}"

    # After reading, run a few sanity checks
    if df is None or df.empty:
        return None, "The uploaded file is empty. Please upload a file that contains data."

    if df.shape[1] == 0:
        return None, "The uploaded file does not contain any columns."

    # Drop fully empty rows/columns that sometimes appear from Excel exports
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    if df.empty:
        return None, "After removing empty rows, this file has no usable data."

    # Clean up column names: strip whitespace so later logic is reliable
    df.columns = [str(col).strip() for col in df.columns]

    return df, None


def _read_csv_safely(uploaded_file):
    """
    Try reading a CSV with a couple of common encodings, since real-world
    CSV files (especially exported from Excel) are not always UTF-8.
    """
    encodings_to_try = ["utf-8", "latin1", "cp1252"]
    last_error = None

    for encoding in encodings_to_try:
        try:
            uploaded_file.seek(0)  # reset pointer before each attempt
            return pd.read_csv(uploaded_file, encoding=encoding)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            continue

    # If every encoding failed, raise the last error so the caller can
    # wrap it into a friendly message.
    raise last_error


def get_basic_file_info(uploaded_file, df: pd.DataFrame) -> dict:
    """
    Return a small dictionary with basic info about the uploaded file,
    used for the KPI cards on the Overview tab.
    """
    return {
        "file_name": uploaded_file.name,
        "file_size_kb": round(uploaded_file.size / 1024, 2) if uploaded_file.size else 0,
        "rows": df.shape[0],
        "columns": df.shape[1],
    }
