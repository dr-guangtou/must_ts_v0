"""Safe expression evaluator for versioned selection recipes."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import yaml


@dataclass(frozen=True)
class Recipe:
    """Selection recipe loaded from YAML."""

    target_class: str
    version: str
    description: str
    science_approved: bool
    required_columns: tuple[str, ...]
    derived_columns: tuple[dict[str, str], ...]
    cuts: tuple[dict[str, str], ...]
    output_columns: tuple[str, ...]

    @property
    def label(self) -> str:
        return f"{self.target_class}/{self.version}"

    @classmethod
    def from_yaml(cls, path: Path) -> "Recipe":
        with path.open() as handle:
            data = yaml.safe_load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"recipe YAML must contain a mapping: {path}")
        return cls(
            target_class=str(data["target_class"]),
            version=str(data["version"]),
            description=str(data.get("description", "")),
            science_approved=bool(data.get("science_approved", False)),
            required_columns=tuple(data.get("required_columns", [])),
            derived_columns=tuple(data.get("derived_columns", [])),
            cuts=tuple(data.get("cuts", [])),
            output_columns=tuple(data.get("output_columns", [])),
        )


def apply_recipe(
    df: pd.DataFrame,
    recipe: Recipe,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return selected rows, all rows with derived columns, and cutflow."""
    missing = sorted(set(recipe.required_columns) - set(df.columns))
    if missing:
        raise ValueError(f"recipe {recipe.label} missing required columns: {missing}")

    working_df = df.copy()
    evaluator = ExpressionEvaluator(working_df)
    for derived_column in recipe.derived_columns:
        name = derived_column["name"]
        working_df[name] = evaluator.evaluate(derived_column["expression"])

    keep = pd.Series(True, index=working_df.index)
    rows = []
    rows.append({"cut_name": "input", "kept_rows": int(keep.sum()), "removed_rows": 0})
    for cut in recipe.cuts:
        cut_mask = ExpressionEvaluator(working_df).evaluate(cut["expression"])
        if not pd.api.types.is_bool_dtype(cut_mask):
            raise ValueError(f"cut {cut['name']} did not evaluate to a boolean mask")
        previous_count = int(keep.sum())
        keep &= cut_mask.fillna(False)
        kept_count = int(keep.sum())
        rows.append(
            {
                "cut_name": cut["name"],
                "kept_rows": kept_count,
                "removed_rows": previous_count - kept_count,
            }
        )

    selected_df = working_df.loc[keep].reset_index(drop=True)
    cutflow_df = pd.DataFrame(rows)
    output_columns = [column for column in recipe.output_columns if column in selected_df.columns]
    if output_columns:
        selected_df = selected_df[output_columns]
    selected_df["target_class"] = recipe.target_class
    selected_df["recipe_version"] = recipe.version
    return selected_df, working_df, cutflow_df


class ExpressionEvaluator:
    """Evaluate a restricted Python expression against DataFrame columns."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.functions: dict[str, Callable[..., Any]] = {
            "abs": np.abs,
            "is_finite": np.isfinite,
            "mag_from_flux": mag_from_flux,
        }

    def evaluate(self, expression: str) -> Any:
        tree = ast.parse(expression, mode="eval")
        return self._eval(tree.body)

    def _eval(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Name):
            if node.id not in self.df.columns:
                raise ValueError(f"unknown expression name: {node.id}")
            return self.df[node.id]
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return self._eval_binop(node)
        if isinstance(node, ast.UnaryOp):
            return self._eval_unaryop(node)
        if isinstance(node, ast.BoolOp):
            return self._eval_boolop(node)
        if isinstance(node, ast.Compare):
            return self._eval_compare(node)
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        raise ValueError(f"unsupported expression syntax: {ast.dump(node)}")

    def _eval_binop(self, node: ast.BinOp) -> Any:
        left = self._eval(node.left)
        right = self._eval(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        raise ValueError(f"unsupported binary operator: {ast.dump(node.op)}")

    def _eval_unaryop(self, node: ast.UnaryOp) -> Any:
        value = self._eval(node.operand)
        if isinstance(node.op, ast.USub):
            return -value
        if isinstance(node.op, ast.Not):
            return ~as_boolean_mask(value)
        raise ValueError(f"unsupported unary operator: {ast.dump(node.op)}")

    def _eval_boolop(self, node: ast.BoolOp) -> Any:
        values = [self._eval(value) for value in node.values]
        result = values[0]
        for value in values[1:]:
            if isinstance(node.op, ast.And):
                result = result & value
            elif isinstance(node.op, ast.Or):
                result = result | value
            else:
                raise ValueError(f"unsupported boolean operator: {ast.dump(node.op)}")
        return result

    def _eval_compare(self, node: ast.Compare) -> Any:
        left = self._eval(node.left)
        result = pd.Series(True, index=self.df.index)
        for operator, comparator in zip(node.ops, node.comparators, strict=True):
            right = self._eval(comparator)
            if isinstance(operator, ast.Lt):
                current = left < right
            elif isinstance(operator, ast.LtE):
                current = left <= right
            elif isinstance(operator, ast.Gt):
                current = left > right
            elif isinstance(operator, ast.GtE):
                current = left >= right
            elif isinstance(operator, ast.Eq):
                current = left == right
            elif isinstance(operator, ast.NotEq):
                current = left != right
            else:
                raise ValueError(f"unsupported comparison operator: {ast.dump(operator)}")
            result &= current
            left = right
        return result

    def _eval_call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name) or node.func.id not in self.functions:
            raise ValueError("only approved helper function calls are allowed")
        if node.keywords:
            raise ValueError("keyword arguments are not supported in recipe expressions")
        args = [self._eval(arg) for arg in node.args]
        return self.functions[node.func.id](*args)


def mag_from_flux(flux: pd.Series, extinction: pd.Series | float = 0.0) -> pd.Series:
    """Convert HSC nanomaggy-like flux to extinction-corrected AB magnitude."""
    flux_array = pd.Series(flux, copy=False).astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        mag = 27.0 - 2.5 * np.log10(flux_array)
    mag = pd.Series(mag, index=flux_array.index)
    mag[~np.isfinite(mag) | (flux_array <= 0)] = np.nan
    return mag - extinction


def as_boolean_mask(value: Any) -> pd.Series:
    """Interpret bool-like recipe values as a boolean mask."""
    series = pd.Series(value, copy=False)
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    if pd.api.types.is_numeric_dtype(series):
        return series.fillna(0).ne(0)
    normalized = series.astype("string").str.strip().str.lower()
    return normalized.isin({"true", "1", "t", "yes", "y"})
