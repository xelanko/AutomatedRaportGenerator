"""
Chart generation. Charts are rendered to PNG files so they can be embedded
in both PDF (ReportLab) and Excel (openpyxl) outputs.
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # headless rendering, no GUI backend needed
import matplotlib.pyplot as plt
import pandas as pd
import logger_setup

log = logger_setup.get_logger(__name__)


def _records_to_df(records) -> pd.DataFrame:
    return pd.DataFrame([r.model_dump() for r in records])


def revenue_by_category_bar(records, output_path: Path) -> Path:
    df = _records_to_df(records)
    grouped = df.groupby("category")["revenue"].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(6, 4))
    grouped.plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_title("Revenue by Category")
    ax.set_ylabel("Revenue")
    ax.set_xlabel("Category")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info(f"Saved chart: {output_path}")
    return output_path


def revenue_trend_line(records, output_path: Path) -> Path:
    df = _records_to_df(records)
    df["record_date"] = pd.to_datetime(df["record_date"])
    grouped = df.groupby("record_date")["revenue"].sum().sort_index()

    fig, ax = plt.subplots(figsize=(6, 4))
    grouped.plot(kind="line", marker="o", ax=ax, color="#55A868")
    ax.set_title("Revenue Trend Over Time")
    ax.set_ylabel("Revenue")
    ax.set_xlabel("Date")
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info(f"Saved chart: {output_path}")
    return output_path


def region_share_pie(records, output_path: Path) -> Path:
    df = _records_to_df(records)
    grouped = df.groupby("region")["revenue"].sum()

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(grouped.values, labels=grouped.index, autopct="%1.1f%%", startangle=90)
    ax.set_title("Revenue Share by Region")
    plt.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    log.info(f"Saved chart: {output_path}")
    return output_path