"""Sky-footprint helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Footprint:
    """Rectangular footprint with an explicit effective area."""

    name: str
    kind: str
    ra_min: float
    ra_max: float
    dec_min: float
    dec_max: float
    effective_area_deg2: float
    area_status: str = "assumed"

    @classmethod
    def from_mapping(cls, name: str, mapping: dict) -> "Footprint":
        if mapping.get("kind") != "radec_box_assumed_area":
            raise ValueError(f"unsupported footprint kind for {name}: {mapping.get('kind')}")
        return cls(
            name=name,
            kind=mapping["kind"],
            ra_min=float(mapping["ra_min"]),
            ra_max=float(mapping["ra_max"]),
            dec_min=float(mapping["dec_min"]),
            dec_max=float(mapping["dec_max"]),
            effective_area_deg2=float(mapping["effective_area_deg2"]),
            area_status=str(mapping.get("area_status", "assumed")),
        )

    def filter_dataframe(
        self,
        df: pd.DataFrame,
        *,
        ra_column: str,
        dec_column: str,
    ) -> pd.DataFrame:
        mask = df[ra_column].between(self.ra_min, self.ra_max, inclusive="both") & df[
            dec_column
        ].between(self.dec_min, self.dec_max, inclusive="both")
        return df.loc[mask].reset_index(drop=True)
