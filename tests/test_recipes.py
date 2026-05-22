from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from must_ts.recipes.evaluator import Recipe, apply_recipe


def test_apply_recipe_builds_derived_columns_and_cutflow():
    recipe = Recipe(
        target_class="elg",
        version="test",
        description="",
        science_approved=False,
        required_columns=("object_id", "g_flux", "r_flux", "a_g", "a_r"),
        derived_columns=(
            {"name": "g_mag", "expression": "mag_from_flux(g_flux, a_g)"},
            {"name": "r_mag", "expression": "mag_from_flux(r_flux, a_r)"},
            {"name": "g_minus_r", "expression": "g_mag - r_mag"},
        ),
        cuts=(
            {"name": "finite", "expression": "is_finite(g_mag) and is_finite(r_mag)"},
            {"name": "blue", "expression": "g_minus_r < 0.5"},
        ),
        output_columns=("object_id", "g_mag", "r_mag", "g_minus_r"),
    )
    df = pd.DataFrame(
        {
            "object_id": [1, 2],
            "g_flux": [100.0, 10.0],
            "r_flux": [80.0, 100.0],
            "a_g": [0.0, 0.0],
            "a_r": [0.0, 0.0],
        }
    )

    selected, working, cutflow = apply_recipe(df, recipe)

    assert "g_mag" in working.columns
    assert selected["object_id"].tolist() == [1]
    assert cutflow["cut_name"].tolist() == ["input", "finite", "blue"]
    assert selected["target_class"].tolist() == ["elg"]


def test_apply_recipe_rejects_unknown_names():
    recipe = Recipe(
        target_class="elg",
        version="test",
        description="",
        science_approved=False,
        required_columns=("object_id",),
        derived_columns=(),
        cuts=({"name": "bad", "expression": "missing_column < 1"},),
        output_columns=("object_id",),
    )

    with pytest.raises(ValueError, match="unknown expression name"):
        apply_recipe(pd.DataFrame({"object_id": [1]}), recipe)


def test_mag_from_flux_marks_nonpositive_flux_nan():
    recipe = Recipe(
        target_class="elg",
        version="test",
        description="",
        science_approved=False,
        required_columns=("object_id", "flux", "a"),
        derived_columns=({"name": "mag", "expression": "mag_from_flux(flux, a)"},),
        cuts=({"name": "finite", "expression": "is_finite(mag)"},),
        output_columns=("object_id", "mag"),
    )
    selected, working, _ = apply_recipe(
        pd.DataFrame({"object_id": [1, 2], "flux": [0.0, 100.0], "a": [0.0, 0.0]}),
        recipe,
    )

    assert np.isnan(working.loc[0, "mag"])
    assert selected["object_id"].tolist() == [2]


def test_hsc_elg_proxy_recipe_selects_clean_lop_row():
    recipe = Recipe.from_yaml(
        Path("recipes/elg/elg_desi_lop/hsc_s23b_i_cmod_25.2/v0.2_hsc_seeing80.yaml")
    )
    row = {
        "object_id": 1,
        "ra": 150.0,
        "dec": 2.0,
        "tract": 9813,
        "g_cmodel_flux": 39.810717,
        "r_cmodel_flux": 47.863009,
        "z_cmodel_flux": 63.095734,
        "g_cmodel_fluxerr": 1.0,
        "r_cmodel_fluxerr": 1.0,
        "z_cmodel_fluxerr": 1.0,
        "g_seeing80_aper_6pix_flux": 25.118864,
        "g_seeing80_aper_6pix_flux_err": 1.0,
        "g_seeing80_aper_6pix_flag": "False",
        "g_inputcount_value": 1,
        "r_inputcount_value": 1,
        "z_inputcount_value": 1,
        "a_g": 0.0,
        "a_r": 0.0,
        "a_z": 0.0,
    }
    for band in ["g", "r", "z"]:
        for flag in [
            "pixelflags_offimage",
            "pixelflags_edge",
            "pixelflags_saturatedcenter",
            "pixelflags_crcenter",
            "pixelflags_bad",
            "pixelflags_suspectcenter",
            "mask_brightstar_halo",
            "mask_brightstar_ghost",
            "mask_brightstar_blooming",
        ]:
            row[f"{band}_{flag}"] = "False"

    selected, _, cutflow = apply_recipe(pd.DataFrame([row]), recipe)

    assert selected["object_id"].tolist() == [1]
    assert cutflow["kept_rows"].iloc[-1] == 1
