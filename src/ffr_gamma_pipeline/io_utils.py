"""Carga de archivos tabulares (CSV/XLS/XLSX) y trazabilidad de ingreso."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}


def list_supported_files(folder: Path) -> list[Path]:
    """Lista archivos soportados en una carpeta en orden reproducible."""
    files = [
        path
        for path in sorted(folder.glob("*"))
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return files


def load_table(path: Path) -> pd.DataFrame:
    """Carga una tabla según extensión, evitando supuestos implícitos."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xls", ".xlsx"}:
        return pd.read_excel(path)
    raise ValueError(f"Extensión no soportada: {path.suffix}")


def load_many(folder: Path, source_name: str) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """
    Carga todos los archivos de una fuente y concatena.

    Devuelve:
    - DataFrame unificado con metadatos de origen
    - Lista con trazas de lectura por archivo para reporte
    """
    files = list_supported_files(folder)
    if not files:
        raise FileNotFoundError(f"No se encontraron archivos en {folder}")

    frames: list[pd.DataFrame] = []
    ingest_log: list[dict[str, object]] = []

    for file_path in files:
        df = load_table(file_path)
        df = df.copy()
        df["source_file"] = file_path.name
        df["source_modality"] = source_name
        frames.append(df)
        ingest_log.append(
            {
                "source": source_name,
                "file": file_path.name,
                "rows": int(len(df)),
                "columns": [str(col) for col in df.columns],
            }
        )

    unified = pd.concat(frames, ignore_index=True)
    return unified, ingest_log

