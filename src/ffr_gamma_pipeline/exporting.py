"""Exportacion de resultados y reporte reproducible en Markdown."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def write_markdown_report(
    output_path: Path,
    files_read: list[str],
    id_columns_used: dict[str, str],
    cleaning_summary: dict[str, dict[str, int]],
    match_count: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Reporte de cruce CT vs Camara Gamma",
        "",
        "## 1) Archivos leidos",
    ]
    lines.extend([f"- `{item}`" for item in files_read])
    lines.extend(
        [
            "",
            "## 2) Columnas usadas para ID",
            f"- CT: `{id_columns_used['ct']}`",
            f"- Camara Gamma: `{id_columns_used['gamma']}`",
            "",
            "## 3) Limpieza aplicada",
            "- Se conservaron solo digitos en el identificador.",
            "- Se eliminaron filas sin DNI/ID valido.",
            "",
            "## 4) Registros antes y despues de limpiar",
            (
                f"- CT: {cleaning_summary['ct']['rows_before']} antes, "
                f"{cleaning_summary['ct']['rows_after']} despues"
            ),
            (
                f"- Camara Gamma: {cleaning_summary['gamma']['rows_before']} antes, "
                f"{cleaning_summary['gamma']['rows_after']} despues"
            ),
            "",
            "## 5) Pacientes coincidentes",
            f"- Pacientes con ambos estudios: {match_count}",
            "",
            "> Nota: el cruce se realizo exclusivamente por DNI/ID normalizado.",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")

