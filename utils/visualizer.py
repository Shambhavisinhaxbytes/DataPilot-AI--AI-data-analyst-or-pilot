"""
visualizer.py
--------------
Automatically decides which charts make sense for the given dataset and
builds them using Plotly. Every function returns a Plotly Figure object
(or None if the chart cannot be built), so app.py can safely check:

    fig = build_bar_chart(df, cat_col, num_col)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
"""

import pandas as pd
import plotly.express as px

# A consistent, professional color theme used across all charts
COLOR_SEQUENCE = px.colors.qualitative.Bold
TEMPLATE = "plotly_white"

MAX_CATEGORIES_FOR_CHART = 15  # avoid unreadable charts with too many bars/slices


def build_bar_chart(df: pd.DataFrame, category_col: str, numeric_col: str):
    """Bar chart: sum of a numeric column grouped by a categorical column."""
    if category_col is None or numeric_col is None:
        return None

    grouped = (
        df.groupby(category_col)[numeric_col]
        .sum()
        .sort_values(ascending=False)
        .head(MAX_CATEGORIES_FOR_CHART)
        .reset_index()
    )

    if grouped.empty:
        return None

    fig = px.bar(
        grouped, x=category_col, y=numeric_col,
        title=f"{numeric_col} by {category_col}",
        color=category_col, color_discrete_sequence=COLOR_SEQUENCE,
        template=TEMPLATE,
    )
    fig.update_layout(showlegend=False, xaxis_title=category_col, yaxis_title=numeric_col)
    return fig


def build_line_chart(df: pd.DataFrame, date_col: str, numeric_col: str):
    """Line chart: numeric column trend over time."""
    if date_col is None or numeric_col is None:
        return None

    temp = df[[date_col, numeric_col]].copy()
    temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
    temp = temp.dropna(subset=[date_col]).sort_values(date_col)

    if temp.empty:
        return None

    grouped = temp.groupby(date_col)[numeric_col].sum().reset_index()

    fig = px.line(
        grouped, x=date_col, y=numeric_col,
        title=f"{numeric_col} Over Time",
        template=TEMPLATE, markers=True,
        color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(xaxis_title=date_col, yaxis_title=numeric_col)
    return fig


def build_scatter_chart(df: pd.DataFrame, numeric_col_x: str, numeric_col_y: str):
    """Scatter plot to explore the relationship between two numeric columns."""
    if numeric_col_x is None or numeric_col_y is None:
        return None

    temp = df[[numeric_col_x, numeric_col_y]].dropna()
    if temp.empty:
        return None

    # NOTE: we intentionally do NOT pass trendline="ols" here, because that
    # feature requires the extra 'statsmodels' package which is not in our
    # requirements.txt. Keeping the project dependency-light avoids errors.
    fig = px.scatter(
        temp, x=numeric_col_x, y=numeric_col_y,
        title=f"{numeric_col_x} vs {numeric_col_y}",
        template=TEMPLATE, color_discrete_sequence=COLOR_SEQUENCE,
    )
    return fig


def build_pie_chart(df: pd.DataFrame, category_col: str):
    """Pie chart showing the distribution of a categorical column."""
    if category_col is None:
        return None

    value_counts = df[category_col].value_counts().head(MAX_CATEGORIES_FOR_CHART)
    if value_counts.empty:
        return None

    fig = px.pie(
        names=value_counts.index, values=value_counts.values,
        title=f"Distribution of {category_col}",
        template=TEMPLATE, color_discrete_sequence=COLOR_SEQUENCE,
        hole=0.35,  # donut style looks more modern
    )
    return fig


def build_histogram(df: pd.DataFrame, numeric_col: str):
    """Histogram showing the distribution of a single numeric column."""
    if numeric_col is None:
        return None

    temp = df[numeric_col].dropna()
    if temp.empty:
        return None

    fig = px.histogram(
        temp, x=numeric_col, nbins=30,
        title=f"Distribution of {numeric_col}",
        template=TEMPLATE, color_discrete_sequence=COLOR_SEQUENCE,
    )
    fig.update_layout(yaxis_title="Frequency")
    return fig


def build_correlation_heatmap(corr_matrix: pd.DataFrame):
    """Heatmap for a correlation matrix (needs at least 2 numeric columns)."""
    if corr_matrix is None or corr_matrix.empty:
        return None

    fig = px.imshow(
        corr_matrix, text_auto=True, aspect="auto",
        title="Correlation Heatmap (Numeric Columns)",
        color_continuous_scale="RdBu_r", template=TEMPLATE,
        zmin=-1, zmax=1,
    )
    return fig


def auto_generate_charts(df: pd.DataFrame, column_types: dict) -> list:
    """
    The "brain" of automatic visualization. Looks at what column types are
    available and decides which charts are worth generating.

    Returns a list of dicts: [{"title": str, "figure": plotly.Figure}, ...]
    so app.py can simply loop through and render each one.
    """
    charts = []

    numeric_cols = column_types.get("numeric", [])
    categorical_cols = column_types.get("categorical", [])
    datetime_cols = column_types.get("datetime", [])

    # 1. Category + numeric -> Bar chart (use the first reasonable pair)
    cat_for_bar = _best_categorical_for_charts(df, categorical_cols)
    if cat_for_bar and numeric_cols:
        fig = build_bar_chart(df, cat_for_bar, numeric_cols[0])
        if fig:
            charts.append({"title": f"{numeric_cols[0]} by {cat_for_bar}", "figure": fig})

    # 2. Date + numeric -> Line chart
    if datetime_cols and numeric_cols:
        fig = build_line_chart(df, datetime_cols[0], numeric_cols[0])
        if fig:
            charts.append({"title": f"{numeric_cols[0]} Trend Over Time", "figure": fig})

    # 3. Two numeric columns -> Scatter plot
    if len(numeric_cols) >= 2:
        fig = build_scatter_chart(df, numeric_cols[0], numeric_cols[1])
        if fig:
            charts.append({
                "title": f"{numeric_cols[0]} vs {numeric_cols[1]}", "figure": fig
            })

    # 4. Category distribution -> Pie chart
    if cat_for_bar:
        fig = build_pie_chart(df, cat_for_bar)
        if fig:
            charts.append({"title": f"Distribution of {cat_for_bar}", "figure": fig})

    # 5. Numeric column -> Histogram
    if numeric_cols:
        fig = build_histogram(df, numeric_cols[0])
        if fig:
            charts.append({"title": f"Distribution of {numeric_cols[0]}", "figure": fig})

    # 6. Multiple numeric columns -> Correlation heatmap
    if len(numeric_cols) >= 2:
        from utils.analyzer import get_correlation_matrix  # local import avoids circular import
        corr_matrix = get_correlation_matrix(df, numeric_cols)
        fig = build_correlation_heatmap(corr_matrix)
        if fig:
            charts.append({"title": "Correlation Heatmap", "figure": fig})

    return charts


def _best_categorical_for_charts(df: pd.DataFrame, categorical_cols: list):
    """
    Pick the most 'chart-friendly' categorical column: one that has more
    than 1 unique value but not too many (otherwise the chart becomes
    unreadable with hundreds of bars/slices).
    """
    best_col = None
    best_unique_count = None

    for col in categorical_cols:
        unique_count = df[col].nunique(dropna=True)
        if 1 < unique_count <= 50:
            if best_unique_count is None or unique_count < best_unique_count:
                best_col = col
                best_unique_count = unique_count

    return best_col
