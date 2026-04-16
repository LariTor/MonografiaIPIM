"""Limpieza y normalizacion de identificadores de paciente."""

from __future__ import annotations

import re

import pandas as pd


def choose_id_column(columns: list[str], id_candidates: list[str]) -> str:
    """
    Selecciona columna de identificador priorizando coincidencia exacta.

    Si no existe coincidencia exacta, intenta una comparacion flexible sin tildes
    ni separadores para reducir errores de formato.
    """
    normalized_map = {_normalize_column_name(col): col for col in columns}

    for candidate in id_candidates:
        if candidate in columns:
            return candidate

    for candidate in id_candidates:
        normalized = _normalize_column_name(candidate)
        if normalized in normalized_map:
            return normalized_map[normalized]

    raise ValueError(
        "No se encontró columna de ID de paciente. "
        f"Columnas detectadas: {columns}"
    )


def normalize_dni(value: object) -> str | None:
    """
    Conserva solo digitos para DNI/ID.

    Retorna None cuando el campo está vacío, nulo o sin dígitos útiles.
    """
    if pd.isna(value):
        return None

    # 1) Convertir a string
    raw = str(value)
    # 2) Quitar espacios en bordes y dentro del texto
    raw = raw.strip().replace(" ", "")
    # 3) Quitar separadores comunes de documento
    raw = raw.replace(".", "").replace("-", "")
    if not raw:
        return None

    # 4) Conservar solo digitos para absorber formatos heterogeneos.
    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return None

    return digits


def clean_patient_id(df: pd.DataFrame, raw_id_column: str) -> pd.DataFrame:
    """
    Agrega columna `patient_id` y elimina filas sin ID valido.
    """
    cleaned = df.copy()
    cleaned["patient_id"] = cleaned[raw_id_column].apply(normalize_dni)
    cleaned = cleaned[cleaned["patient_id"].notna()].copy()
    cleaned["patient_id"] = cleaned["patient_id"].astype(str)
    return cleaned


def prepare_patient_id_columns(
    df: pd.DataFrame, id_candidates: list[str]
) -> tuple[pd.DataFrame, str]:
    """
    Identifica la columna de DNI/ID, crea `patient_id` y marca validez.
    """
    id_column = choose_id_column([str(c) for c in df.columns], id_candidates)
    prepared = df.copy()
    prepared["patient_id"] = prepared[id_column].apply(normalize_dni)
    prepared["patient_id_valid"] = prepared["patient_id"].notna()
    return prepared, id_column


def summarize_dni_quality(
    df: pd.DataFrame, normalized_column: str = "patient_id"
) -> dict[str, int]:
    """
    Resume calidad de identificadores en un DataFrame.

    Metricas:
    - total_rows: total de filas.
    - valid_dni: filas con ID normalizado no nulo.
    - missing_or_invalid_dni: filas sin ID util tras limpieza.
    - duplicated_rows_by_dni: filas con DNI repetido (contando todas las repetidas).
    - duplicated_unique_dni: cantidad de DNIs distintos que aparecen repetidos.
    """
    if normalized_column not in df.columns:
        raise ValueError(f"No existe columna '{normalized_column}' para resumir calidad")

    total_rows = int(len(df))
    valid_mask = df[normalized_column].notna()
    valid_dni = int(valid_mask.sum())
    missing_or_invalid_dni = int(total_rows - valid_dni)

    valid_series = df.loc[valid_mask, normalized_column].astype(str)
    duplicated_rows_by_dni = int(valid_series.duplicated(keep=False).sum())
    duplicated_unique_dni = int(valid_series[valid_series.duplicated(keep=False)].nunique())

    return {
        "total_rows": total_rows,
        "valid_dni": valid_dni,
        "missing_or_invalid_dni": missing_or_invalid_dni,
        "duplicated_rows_by_dni": duplicated_rows_by_dni,
        "duplicated_unique_dni": duplicated_unique_dni,
    }


def _normalize_column_name(name: str) -> str:
    lowered = name.lower()
    lowered = lowered.replace("á", "a").replace("é", "e").replace("í", "i")
    lowered = lowered.replace("ó", "o").replace("ú", "u").replace("°", "o")
    lowered = lowered.replace("ñ", "n")
    return re.sub(r"[^a-z0-9]+", "", lowered)

