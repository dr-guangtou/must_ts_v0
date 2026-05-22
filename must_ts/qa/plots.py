"""Small QA plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def write_basic_figures(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if df.empty:
        return
    _write_sky_distribution(df, output_dir / "sky_distribution.png")
    _write_magnitude_histograms(df, output_dir / "magnitude_histograms.png")
    _write_color_color(df, output_dir / "color_color.png")
    _write_redshift_distribution(df, output_dir / "redshift_distribution.png")


def _write_sky_distribution(df: pd.DataFrame, path: Path) -> None:
    if not {"ra", "dec"}.issubset(df.columns):
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(df["ra"], df["dec"], s=2, alpha=0.4)
    ax.set_xlabel("RA [deg]")
    ax.set_ylabel("Dec [deg]")
    ax.invert_xaxis()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_magnitude_histograms(df: pd.DataFrame, path: Path) -> None:
    columns = [column for column in df.columns if column.endswith("_mag_mw")]
    if not columns:
        return
    fig, ax = plt.subplots(figsize=(7, 5))
    for column in columns[:5]:
        ax.hist(df[column].dropna(), bins=40, histtype="step", label=column)
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Rows")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_color_color(df: pd.DataFrame, path: Path) -> None:
    if not {"g_minus_r", "r_minus_i"}.issubset(df.columns):
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(df["g_minus_r"], df["r_minus_i"], s=2, alpha=0.4)
    ax.set_xlabel("g-r")
    ax.set_ylabel("r-i")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def _write_redshift_distribution(df: pd.DataFrame, path: Path) -> None:
    if "z_best" not in df.columns:
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.hist(df["z_best"].dropna(), bins=50, histtype="stepfilled", alpha=0.7)
    ax.set_xlabel("z_best")
    ax.set_ylabel("Rows")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
