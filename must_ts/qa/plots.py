"""Small QA plotting helpers."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm


def write_basic_figures(
    df: pd.DataFrame,
    output_dir: Path,
    *,
    parent_df: pd.DataFrame | None = None,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    if df.empty and (parent_df is None or parent_df.empty):
        return
    comparison_df = parent_df if parent_df is not None and not parent_df.empty else df
    if not df.empty:
        _write_sky_distribution(df, output_dir / "sky_distribution.png")
        _write_magnitude_histograms(df, output_dir / "magnitude_histograms.png")
        _write_color_color(df, output_dir / "color_color.png")
        _write_redshift_distribution(df, output_dir / "redshift_distribution.png")
    _write_spatial_overlay(comparison_df, df, output_dir / "reference_spatial_overlay.png")
    _write_redshift_overlay(comparison_df, df, output_dir / "reference_redshift_overlay.png")
    _write_color_color_overlay(comparison_df, df, output_dir / "reference_color_color_overlay.png")
    _write_magnitude_color_overlay(
        comparison_df,
        df,
        output_dir / "reference_magnitude_color_overlay.png",
    )


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


def _write_spatial_overlay(parent_df: pd.DataFrame, selected_df: pd.DataFrame, path: Path) -> None:
    if not {"ra", "dec"}.issubset(parent_df.columns) or not {"ra", "dec"}.issubset(
        selected_df.columns
    ):
        return
    parent_ra = _finite_series(parent_df["ra"])
    parent_dec = _finite_series(parent_df["dec"])
    if parent_ra.empty or parent_dec.empty:
        return
    xlim = _robust_limits(parent_ra, lower_percentile=0.1, upper_percentile=99.9)
    ylim = _robust_limits(parent_dec, lower_percentile=0.1, upper_percentile=99.9)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    _hist2d(ax, parent_df["ra"], parent_df["dec"], xlim=xlim, ylim=ylim)
    _scatter_selected(ax, selected_df["ra"], selected_df["dec"], xlim=xlim, ylim=ylim)
    ax.set_xlabel("RA [deg]")
    ax.set_ylabel("Dec [deg]")
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.invert_xaxis()
    ax.set_title("COSMOS Reference Sample and Selected Targets")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _write_redshift_overlay(parent_df: pd.DataFrame, selected_df: pd.DataFrame, path: Path) -> None:
    if "z_best" not in parent_df.columns or "z_best" not in selected_df.columns:
        return
    parent_z = _finite_series(pd.to_numeric(parent_df["z_best"], errors="coerce"))
    selected_z = _finite_series(pd.to_numeric(selected_df["z_best"], errors="coerce"))
    if parent_z.empty:
        return
    xlim = _robust_limits(parent_z, lower_percentile=0.5, upper_percentile=99.5)
    bins = np.linspace(xlim[0], xlim[1], 60)
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.hist(
        parent_z, bins=bins, histtype="stepfilled", color="#B8C4D6", alpha=0.8, label="Reference"
    )
    if not selected_z.empty:
        ax.hist(
            selected_z,
            bins=bins,
            histtype="step",
            color="#C23B22",
            linewidth=1.8,
            label="Selected",
        )
    ax.set_xlim(xlim)
    ax.set_xlabel("z_best")
    ax.set_ylabel("Rows")
    ax.set_title("Reference Redshift Distribution")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _write_color_color_overlay(
    parent_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    path: Path,
) -> None:
    if not {"g_minus_r", "r_minus_z"}.issubset(parent_df.columns) or not {
        "g_minus_r",
        "r_minus_z",
    }.issubset(selected_df.columns):
        return
    _write_2d_overlay(
        parent_df,
        selected_df,
        path=path,
        x_column="r_minus_z",
        y_column="g_minus_r",
        x_label="r - z",
        y_label="g - r",
        title="Reference Color-Color Distribution",
    )


def _write_magnitude_color_overlay(
    parent_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    path: Path,
) -> None:
    if not {"g_aperture_mag", "g_minus_r"}.issubset(parent_df.columns) or not {
        "g_aperture_mag",
        "g_minus_r",
    }.issubset(selected_df.columns):
        return
    _write_2d_overlay(
        parent_df,
        selected_df,
        path=path,
        x_column="g_aperture_mag",
        y_column="g_minus_r",
        x_label="HSC seeing80 g aperture magnitude",
        y_label="g - r",
        title="Reference Magnitude-Color Distribution",
        invert_xaxis=True,
    )


def _write_2d_overlay(
    parent_df: pd.DataFrame,
    selected_df: pd.DataFrame,
    *,
    path: Path,
    x_column: str,
    y_column: str,
    x_label: str,
    y_label: str,
    title: str,
    invert_xaxis: bool = False,
) -> None:
    parent_x = _finite_series(parent_df[x_column])
    parent_y = _finite_series(parent_df[y_column])
    if parent_x.empty or parent_y.empty:
        return
    xlim = _robust_limits(parent_x)
    ylim = _robust_limits(parent_y)
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    _hist2d(ax, parent_df[x_column], parent_df[y_column], xlim=xlim, ylim=ylim)
    _scatter_selected(ax, selected_df[x_column], selected_df[y_column], xlim=xlim, ylim=ylim)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    if invert_xaxis:
        ax.invert_xaxis()
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _hist2d(
    ax,
    x_values: pd.Series,
    y_values: pd.Series,
    *,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    x = pd.to_numeric(x_values, errors="coerce")
    y = pd.to_numeric(y_values, errors="coerce")
    mask = x.between(xlim[0], xlim[1], inclusive="both") & y.between(
        ylim[0],
        ylim[1],
        inclusive="both",
    )
    ax.hist2d(
        x.loc[mask],
        y.loc[mask],
        bins=90,
        range=[xlim, ylim],
        norm=LogNorm(),
        cmap="Greys",
    )


def _scatter_selected(
    ax,
    x_values: pd.Series,
    y_values: pd.Series,
    *,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> None:
    x = pd.to_numeric(x_values, errors="coerce")
    y = pd.to_numeric(y_values, errors="coerce")
    mask = x.between(xlim[0], xlim[1], inclusive="both") & y.between(
        ylim[0],
        ylim[1],
        inclusive="both",
    )
    ax.scatter(
        x.loc[mask],
        y.loc[mask],
        s=4,
        color="#C23B22",
        alpha=0.35,
        linewidths=0,
        label="Selected",
    )


def _finite_series(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    return numeric[np.isfinite(numeric)]


def _robust_limits(
    values: pd.Series,
    *,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0,
) -> tuple[float, float]:
    finite = _finite_series(values)
    if finite.empty:
        return (0.0, 1.0)
    lower, upper = np.nanpercentile(
        finite.to_numpy(dtype=float), [lower_percentile, upper_percentile]
    )
    if not np.isfinite(lower) or not np.isfinite(upper) or lower == upper:
        center = float(finite.median())
        return (center - 0.5, center + 0.5)
    padding = 0.04 * (upper - lower)
    return (float(lower - padding), float(upper + padding))
