"""
Data analysis pipeline.
Accepts CSV / Excel files, performs EDA, generates Plotly visualisations,
and lets the LLM reason about the dataset.
"""

import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

from backend.core.config import settings
from backend.models.llm import LLMFactory, build_messages

logger = logging.getLogger(__name__)

SUPPORTED_DATA_TYPES = {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".json"}


# ── Data loading ────────────────────────────────────────────────────────────

def load_dataframe(file_path: str) -> pd.DataFrame:
    """Load a tabular file into a pandas DataFrame."""
    suffix = Path(file_path).suffix.lower()
    loaders = {
        ".csv": lambda p: pd.read_csv(p),
        ".tsv": lambda p: pd.read_csv(p, sep="\t"),
        ".xlsx": lambda p: pd.read_excel(p),
        ".xls": lambda p: pd.read_excel(p),
        ".parquet": lambda p: pd.read_parquet(p),
        ".json": lambda p: pd.read_json(p),
    }
    if suffix not in loaders:
        raise ValueError(
            f"Unsupported data format '{suffix}'. Supported: {list(loaders.keys())}"
        )
    df = loaders[suffix](file_path)
    logger.info("Loaded dataframe: %d rows × %d cols from %s", len(df), len(df.columns), file_path)
    return df


# ── EDA ─────────────────────────────────────────────────────────────────────

def compute_eda(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute exploratory data analysis statistics.

    Returns:
        Dict with: shape, dtypes, missing, describe, correlations, sample.
    """
    numeric_df = df.select_dtypes(include=[np.number])

    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)

    eda: Dict[str, Any] = {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "missing_values": missing[missing > 0].to_dict(),
        "missing_percent": missing_pct[missing_pct > 0].to_dict(),
        "numeric_columns": list(numeric_df.columns),
        "categorical_columns": list(df.select_dtypes(include=["object", "category"]).columns),
        "describe": df.describe(include="all").to_dict(),
        "sample": df.head(5).to_dict(orient="records"),
    }

    # Correlation matrix for numeric columns
    if len(numeric_df.columns) > 1:
        eda["correlations"] = numeric_df.corr().round(3).to_dict()

    # Unique values for low-cardinality categorical columns
    cat_uniques = {}
    for col in eda["categorical_columns"]:
        n_unique = df[col].nunique()
        if n_unique <= 20:
            cat_uniques[col] = df[col].value_counts().head(20).to_dict()
    eda["categorical_distributions"] = cat_uniques

    return eda


# ── Visualisations ──────────────────────────────────────────────────────────

def generate_visualisations(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Auto-generate a set of Plotly chart specs from the dataframe.

    Returns:
        List of dicts, each with: title, chart_type, plotly_json.
    """
    import plotly.express as px
    import plotly.graph_objects as go

    charts = []
    numeric_cols = list(df.select_dtypes(include=[np.number]).columns)
    cat_cols = list(df.select_dtypes(include=["object", "category"]).columns)

    def _fig_to_json(fig) -> str:
        return fig.to_json()

    # 1. Histogram for each numeric column (max 5)
    for col in numeric_cols[:5]:
        fig = px.histogram(
            df, x=col, nbins=30, title=f"Distribution of {col}",
            template="plotly_white",
        )
        charts.append({
            "title": f"Distribution: {col}",
            "chart_type": "histogram",
            "plotly_json": _fig_to_json(fig),
        })

    # 2. Correlation heatmap
    if len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()
        fig = px.imshow(
            corr, text_auto=".2f", aspect="auto",
            title="Correlation Matrix", template="plotly_white",
        )
        charts.append({
            "title": "Correlation Heatmap",
            "chart_type": "heatmap",
            "plotly_json": _fig_to_json(fig),
        })

    # 3. Bar charts for categorical columns (max 3)
    for col in cat_cols[:3]:
        counts = df[col].value_counts().head(15).reset_index()
        counts.columns = [col, "count"]
        fig = px.bar(
            counts, x=col, y="count", title=f"Top values: {col}",
            template="plotly_white",
        )
        charts.append({
            "title": f"Top Values: {col}",
            "chart_type": "bar",
            "plotly_json": _fig_to_json(fig),
        })

    # 4. Scatter plot of the two highest-correlated numeric columns
    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        color_col = cat_cols[0] if cat_cols else None
        fig = px.scatter(
            df.head(settings.MAX_ROWS_DISPLAY),
            x=x_col, y=y_col, color=color_col,
            title=f"Scatter: {x_col} vs {y_col}",
            template="plotly_white",
        )
        charts.append({
            "title": f"Scatter: {x_col} vs {y_col}",
            "chart_type": "scatter",
            "plotly_json": _fig_to_json(fig),
        })

    # 5. Box plots
    for col in numeric_cols[:3]:
        fig = px.box(df, y=col, title=f"Box Plot: {col}", template="plotly_white")
        charts.append({
            "title": f"Box Plot: {col}",
            "chart_type": "box",
            "plotly_json": _fig_to_json(fig),
        })

    logger.info("Generated %d visualisations", len(charts))
    return charts


# ── LLM-powered analysis ────────────────────────────────────────────────────

def generate_ai_insights(df: pd.DataFrame, eda: Dict[str, Any]) -> str:
    """
    Ask the LLM to provide high-level insights from the EDA summary.
    """
    llm = LLMFactory.get_chat_llm(temperature=0.3)

    # Build a concise EDA summary string (avoid sending too many tokens)
    summary_lines = [
        f"Dataset shape: {eda['shape']['rows']} rows × {eda['shape']['columns']} columns",
        f"Numeric columns: {eda['numeric_columns']}",
        f"Categorical columns: {eda['categorical_columns']}",
        f"Missing values: {eda.get('missing_values', {})}",
        f"Sample statistics: {str(eda.get('describe', {}))[:1500]}",
    ]
    summary = "\n".join(summary_lines)

    messages = build_messages(
        system_prompt=(
            "You are an expert data scientist. "
            "Analyse the EDA summary and provide:\n"
            "1. Key observations\n"
            "2. Data quality issues\n"
            "3. Interesting patterns or correlations\n"
            "4. Recommended next analysis steps\n"
            "5. Potential ML use cases"
        ),
        conversation_history=[],
        user_message=f"EDA Summary:\n{summary}",
    )
    response = llm.invoke(messages)
    return response.content


def answer_data_question(
    df: pd.DataFrame,
    question: str,
    eda: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Answer a natural language question about the dataset using pandas code generation.

    The LLM generates Python/pandas code which is safely executed against the dataframe.
    """
    llm = LLMFactory.get_chat_llm(temperature=0.1)

    schema_info = f"""
DataFrame schema:
- Shape: {df.shape}
- Columns: {list(df.columns)}
- Dtypes: {df.dtypes.astype(str).to_dict()}
- Sample (first 3 rows):
{df.head(3).to_string()}
"""

    messages = build_messages(
        system_prompt=(
            "You are a senior data analyst. The user has a pandas DataFrame called `df`.\n"
            "Write a single Python code block that answers their question.\n"
            "Store the FINAL answer as a variable named `result` (string or number).\n"
            "The code must be safe – no file I/O, no imports beyond pandas/numpy.\n"
            "Output ONLY the Python code block, no explanation."
        ),
        conversation_history=[],
        user_message=f"{schema_info}\n\nQuestion: {question}",
    )
    response = llm.invoke(messages)
    code = response.content.strip().lstrip("```python").rstrip("```").strip()

    # Safe execution
    try:
        local_vars: Dict[str, Any] = {"df": df.copy(), "pd": pd, "np": np}
        exec(compile(code, "<llm_code>", "exec"), {"__builtins__": {}}, local_vars)  # noqa: S102
        result = local_vars.get("result", "No result variable was set.")
        return str(result)
    except Exception as e:
        logger.warning("LLM-generated code failed: %s\nCode:\n%s", e, code)
        # Fallback: let the LLM answer directly
        fallback_messages = build_messages(
            system_prompt="You are a data analyst. Answer based on the schema below.",
            conversation_history=[],
            user_message=f"{schema_info}\n\nQuestion: {question}",
        )
        fallback = LLMFactory.get_chat_llm(temperature=0.4).invoke(fallback_messages)
        return fallback.content
