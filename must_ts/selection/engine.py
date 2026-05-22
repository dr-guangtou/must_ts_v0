"""Evaluation and production run engine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from must_ts.catalogs.readers import read_catalog_partitions
from must_ts.catalogs.registry import CatalogContract
from must_ts.qa.plots import write_basic_figures
from must_ts.recipes.evaluator import Recipe, apply_recipe
from must_ts.selection.reference import select_reference_catalog_in_footprint


@dataclass(frozen=True)
class RunConfig:
    """Selection run configuration."""

    name: str
    mode: str
    photometric_catalog: str
    recipe: str
    footprint: str
    output_root: Path
    reference_catalog: str | None = None
    tract_ids: tuple[int, ...] | None = None
    max_partitions: int | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> "RunConfig":
        with path.open() as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"run config YAML must contain a mapping: {path}")
        tract_ids = data.get("tract_ids")
        return cls(
            name=str(data["name"]),
            mode=str(data["mode"]),
            photometric_catalog=str(data["photometric_catalog"]),
            reference_catalog=data.get("reference_catalog"),
            recipe=str(data["recipe"]),
            footprint=str(data["footprint"]),
            output_root=Path(data["output_root"]).expanduser(),
            tract_ids=tuple(int(value) for value in tract_ids) if tract_ids else None,
            max_partitions=data.get("max_partitions"),
        )


def run_configured_selection(run_config_path: Path, *, repo_root: Path) -> dict[str, Any]:
    run_config = RunConfig.from_yaml(run_config_path)
    photometric_contract = CatalogContract.from_yaml(
        repo_root / "phot_cat" / run_config.photometric_catalog / "catalog.yaml",
        repo_root=repo_root,
    )
    reference_contract = None
    if run_config.reference_catalog is not None:
        reference_contract = CatalogContract.from_yaml(
            repo_root / "ref_cat" / run_config.reference_catalog / "catalog.yaml",
            repo_root=repo_root,
        )
    recipe_path = _resolve_recipe_path(repo_root=repo_root, recipe_label=run_config.recipe)
    recipe = Recipe.from_yaml(recipe_path)
    return run_selection(
        run_config=run_config,
        photometric_contract=photometric_contract,
        reference_contract=reference_contract,
        recipe=recipe,
        repo_root=repo_root,
    )


def run_selection(
    *,
    run_config: RunConfig,
    photometric_contract: CatalogContract,
    reference_contract: CatalogContract | None,
    recipe: Recipe,
    repo_root: Path,
) -> dict[str, Any]:
    if run_config.mode not in {"evaluation", "production", "reference_evaluation"}:
        raise ValueError(f"unsupported run mode: {run_config.mode}")
    if run_config.mode in {"evaluation", "reference_evaluation"} and reference_contract is None:
        raise ValueError(f"{run_config.mode} runs require a reference catalog")
    _reject_repo_local_output_root(run_config.output_root, repo_root=repo_root)

    footprint = photometric_contract.footprints[run_config.footprint]
    if run_config.mode == "reference_evaluation":
        return _run_reference_evaluation(
            run_config=run_config,
            photometric_contract=photometric_contract,
            reference_contract=reference_contract,
            recipe=recipe,
            footprint=footprint,
            repo_root=repo_root,
        )

    raw_columns = _build_photometric_read_columns(photometric_contract, recipe)
    parent_df = read_catalog_partitions(
        photometric_contract,
        columns=raw_columns,
        footprint=footprint,
        tract_ids=run_config.tract_ids,
        max_partitions=run_config.max_partitions,
    )
    selected_df, working_df, cutflow_df = apply_recipe(parent_df, recipe)

    if reference_contract is not None:
        selected_df = _join_reference_truth(
            selected_df,
            reference_contract=reference_contract,
            tract_ids=run_config.tract_ids,
            max_partitions=run_config.max_partitions,
        )

    run_root = run_config.output_root / "runs" / run_config.mode / run_config.name
    _prepare_output_tree(run_root)
    _write_run_outputs(
        run_root=run_root,
        run_config=run_config,
        photometric_contract=photometric_contract,
        reference_contract=reference_contract,
        recipe=recipe,
        footprint=footprint,
        parent_row_count=len(parent_df),
        selected_df=selected_df,
        cutflow_df=cutflow_df,
        parent_df=working_df,
    )
    return {
        "run_root": str(run_root),
        "parent_row_count": int(len(parent_df)),
        "selected_row_count": int(len(selected_df)),
    }


def _run_reference_evaluation(
    *,
    run_config: RunConfig,
    photometric_contract: CatalogContract,
    reference_contract: CatalogContract | None,
    recipe: Recipe,
    footprint,
    repo_root: Path,
) -> dict[str, Any]:
    if reference_contract is None:
        raise ValueError("reference_evaluation runs require a reference catalog")
    reference_selection = select_reference_catalog_in_footprint(
        reference_contract=reference_contract,
        footprint=reference_contract.footprints[run_config.footprint],
        tract_ids=run_config.tract_ids,
        max_partitions=run_config.max_partitions,
    )
    raw_columns = _build_photometric_read_columns(photometric_contract, recipe)
    photometric_df = read_catalog_partitions(
        photometric_contract,
        columns=raw_columns,
        footprint=footprint,
        tract_ids=run_config.tract_ids,
        max_partitions=run_config.max_partitions,
    )
    parent_df = reference_selection.dataframe.merge(
        photometric_df,
        on=photometric_contract.object_id_column,
        how="inner",
        validate="one_to_one",
        suffixes=("_reference", ""),
    )
    _collapse_duplicate_coordinate_columns(parent_df, columns=("ra", "dec", "tract", "patch"))
    selected_df, working_df, cutflow_df = apply_recipe(parent_df, recipe)
    selected_df = _restore_reference_columns(
        selected_df,
        parent_df=working_df,
        object_id_column=photometric_contract.object_id_column,
        reference_columns=reference_contract.default_columns,
    )
    run_root = run_config.output_root / "runs" / run_config.mode / run_config.name
    _prepare_output_tree(run_root)
    reference_selection.spatial_partition_summary.to_csv(
        run_root / "tables" / "reference_spatial_partition_summary.csv",
        index=False,
    )
    reference_selection.reference_partition_summary.to_csv(
        run_root / "tables" / "reference_partition_summary.csv",
        index=False,
    )
    _write_run_outputs(
        run_root=run_root,
        run_config=run_config,
        photometric_contract=photometric_contract,
        reference_contract=reference_contract,
        recipe=recipe,
        footprint=footprint,
        parent_row_count=len(parent_df),
        selected_df=selected_df,
        cutflow_df=cutflow_df,
        parent_df=working_df,
        extra_summary={
            "reference_selected_row_count": reference_selection.summary[
                "selected_reference_row_count"
            ],
            "reference_photometry_joined_row_count": int(len(parent_df)),
            "reference_photometry_missing_row_count": int(
                reference_selection.summary["selected_reference_row_count"] - len(parent_df)
            ),
            "reference_surface_density_per_deg2": reference_selection.summary[
                "surface_density_per_deg2"
            ],
        },
    )
    return {
        "run_root": str(run_root),
        "parent_row_count": int(len(parent_df)),
        "selected_row_count": int(len(selected_df)),
    }


def _build_photometric_read_columns(contract: CatalogContract, recipe: Recipe) -> list[str]:
    columns = [
        contract.object_id_column,
        contract.ra_column,
        contract.dec_column,
        *recipe.required_columns,
    ]
    return [column for column in dict.fromkeys(columns) if column is not None]


def _join_reference_truth(
    selected_df: pd.DataFrame,
    *,
    reference_contract: CatalogContract,
    tract_ids: tuple[int, ...] | None,
    max_partitions: int | None,
) -> pd.DataFrame:
    reference_columns = [
        reference_contract.object_id_column,
        *reference_contract.default_columns,
    ]
    reference_df = read_catalog_partitions(
        reference_contract,
        columns=list(dict.fromkeys(reference_columns)),
        tract_ids=tract_ids,
        max_partitions=max_partitions,
    )
    return selected_df.merge(
        reference_df,
        on=reference_contract.object_id_column,
        how="left",
        validate="one_to_one",
    )


def _prepare_output_tree(run_root: Path) -> None:
    for subdir in ["tables", "figures", "logs"]:
        (run_root / subdir).mkdir(parents=True, exist_ok=True)


def _write_run_outputs(
    *,
    run_root: Path,
    run_config: RunConfig,
    photometric_contract: CatalogContract,
    reference_contract: CatalogContract | None,
    recipe: Recipe,
    footprint,
    parent_row_count: int,
    selected_df: pd.DataFrame,
    cutflow_df: pd.DataFrame,
    parent_df: pd.DataFrame | None = None,
    extra_summary: dict[str, Any] | None = None,
) -> None:
    selected_df.to_parquet(run_root / "selected_targets.parquet", index=False)
    selected_df.to_csv(run_root / "selected_targets.csv", index=False)
    cutflow_df.to_csv(run_root / "tables" / "cutflow.csv", index=False)
    density_df = pd.DataFrame(
        [
            {
                "selected_count": int(len(selected_df)),
                "effective_area_deg2": footprint.effective_area_deg2,
                "surface_density_per_deg2": len(selected_df) / footprint.effective_area_deg2,
                "area_status": footprint.area_status,
            }
        ]
    )
    density_df.to_csv(run_root / "tables" / "density_summary.csv", index=False)
    _write_redshift_summary(selected_df, run_root / "tables" / "redshift_summary.csv")
    write_basic_figures(selected_df, run_root / "figures", parent_df=parent_df)

    resolved_inputs = {
        "photometric_catalog": photometric_contract.name,
        "photometric_manifest_path": str(photometric_contract.manifest_path),
        "reference_catalog": reference_contract.name if reference_contract else None,
        "reference_manifest_path": str(reference_contract.manifest_path)
        if reference_contract
        else None,
        "recipe": recipe.label,
        "footprint": footprint.__dict__,
    }
    summary = {
        "run_name": run_config.name,
        "mode": run_config.mode,
        "target_class": recipe.target_class,
        "recipe_version": recipe.version,
        "science_approved": recipe.science_approved,
        "parent_row_count": int(parent_row_count),
        "selected_count": int(len(selected_df)),
        "effective_area_deg2": footprint.effective_area_deg2,
        "surface_density_per_deg2": len(selected_df) / footprint.effective_area_deg2,
        "area_status": footprint.area_status,
    }
    if extra_summary is not None:
        summary.update(extra_summary)
    _write_yaml(run_root / "run_config.yaml", run_config.__dict__)
    _write_yaml(run_root / "resolved_inputs.yaml", resolved_inputs)
    (run_root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (run_root / "logs" / "run.log").write_text(json.dumps(summary, sort_keys=True) + "\n")


def _write_redshift_summary(df: pd.DataFrame, path: Path) -> None:
    if "z_best" not in df.columns:
        pd.DataFrame([{"attached_redshift_count": 0, "finite_z_best_count": 0}]).to_csv(
            path, index=False
        )
        return
    summary = {
        "attached_redshift_count": int(df["z_best"].notna().sum()),
        "finite_z_best_count": int(pd.to_numeric(df["z_best"], errors="coerce").notna().sum()),
    }
    pd.DataFrame([summary]).to_csv(path, index=False)


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    safe_data = {key: _stringify_paths(value) for key, value in data.items()}
    path.write_text(yaml.safe_dump(safe_data, sort_keys=True))


def _stringify_paths(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    return value


def _collapse_duplicate_coordinate_columns(
    df: pd.DataFrame,
    *,
    columns: tuple[str, ...],
) -> None:
    for column in columns:
        reference_column = f"{column}_reference"
        if reference_column in df.columns and column in df.columns:
            df.drop(columns=[reference_column], inplace=True)


def _restore_reference_columns(
    selected_df: pd.DataFrame,
    *,
    parent_df: pd.DataFrame,
    object_id_column: str,
    reference_columns: tuple[str, ...],
) -> pd.DataFrame:
    columns_to_restore = [
        column
        for column in reference_columns
        if column != object_id_column
        and column in parent_df.columns
        and column not in selected_df.columns
    ]
    if not columns_to_restore:
        return selected_df
    return selected_df.merge(
        parent_df[[object_id_column, *columns_to_restore]],
        on=object_id_column,
        how="left",
        validate="one_to_one",
    )


def _resolve_recipe_path(*, repo_root: Path, recipe_label: str) -> Path:
    target_class, version = recipe_label.split("/", 1)
    return repo_root / "recipes" / target_class / f"{version}.yaml"


def _reject_repo_local_output_root(output_root: Path, *, repo_root: Path) -> None:
    resolved_output = output_root.resolve(strict=False)
    resolved_repo = repo_root.resolve(strict=False)
    if resolved_output == resolved_repo or resolved_repo in resolved_output.parents:
        raise ValueError("run output_root must be outside the repository")
