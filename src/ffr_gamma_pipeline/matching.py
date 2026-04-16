"""Cruce de cohortes por identificador normalizado."""

from __future__ import annotations

import pandas as pd


def unique_patients(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reduce a una fila por paciente para conteo de cohortes.
    """
    return df.sort_values("patient_id").drop_duplicates(subset=["patient_id"])


def intersect_patients(ct_df: pd.DataFrame, gamma_df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve pacientes con ambos estudios usando inner join por `patient_id`.
    """
    ct_unique = unique_patients(ct_df)[["patient_id"]].assign(has_ct=True)
    gamma_unique = unique_patients(gamma_df)[["patient_id"]].assign(has_gamma=True)
    return ct_unique.merge(gamma_unique, on="patient_id", how="inner")

