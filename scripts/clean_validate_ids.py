"""Script robusto de limpieza y validacion de DNI/ID (sin cruce final)."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ffr_gamma_pipeline.cleaning import (  # noqa: E402
    choose_id_column,
    normalize_dni,
    summarize_dni_quality,
)
from ffr_gamma_pipeline.config import CT_DIR, GAMMA_DIR, OUTPUT_DIR, PATIENT_ID_CANDIDATES  # noqa: E402
from ffr_gamma_pipeline.io_utils import list_supported_files, load_table  # noqa: E402


def process_modality(folder: Path, modality: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Limpia y valida DNI por archivo y consolidado de una modalidad.

    Devuelve:
    - resumen por archivo
    - DataFrame consolidado con patient_id y patient_id_valid
    """
    files = list_supported_files(folder)
    if not files:
        raise FileNotFoundError(f"No hay archivos compatibles en {folder}")

    cleaned_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, object]] = []

    print(f"\n=== {modality} ===")
    print("Archivos analizados:")
    for path in files:
        print(f"- {path.name}")

    for path in files:
        df = load_table(path).copy()
        id_col = choose_id_column([str(c) for c in df.columns], PATIENT_ID_CANDIDATES)
        df["patient_id"] = df[id_col].apply(normalize_dni)
        df["patient_id_valid"] = df["patient_id"].notna()
        df["source_file"] = path.name
        df["source_modality"] = modality
        cleaned_frames.append(df)

        metrics = summarize_dni_quality(df, normalized_column="patient_id")
        metrics.update(
            {
                "modality": modality,
                "file": path.name,
                "id_column_used": id_col,
            }
        )
        summary_rows.append(metrics)

    combined = pd.concat(cleaned_frames, ignore_index=True)
    combined_metrics = summarize_dni_quality(combined, normalized_column="patient_id")
    combined_row = {
        "modality": modality,
        "file": "__TOTAL_MODALITY__",
        "id_column_used": choose_id_column(
            [str(c) for c in combined.columns], PATIENT_ID_CANDIDATES
        ),
        **combined_metrics,
    }
    summary_rows.append(combined_row)

    summary_df = pd.DataFrame(summary_rows)
    return summary_df, combined


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ct_summary, ct_cleaned = process_modality(CT_DIR, "CT")
    gamma_summary, gamma_cleaned = process_modality(GAMMA_DIR, "Camara_Gamma")

    summary_all = pd.concat([ct_summary, gamma_summary], ignore_index=True)

    summary_path = OUTPUT_DIR / "resumen_limpieza_dni.csv"
    ct_clean_path = OUTPUT_DIR / "ct_con_dni_normalizado.csv"
    gamma_clean_path = OUTPUT_DIR / "camara_gamma_con_dni_normalizado.csv"

    summary_all.to_csv(summary_path, index=False)
    ct_cleaned.to_csv(ct_clean_path, index=False)
    gamma_cleaned.to_csv(gamma_clean_path, index=False)

    print("\n=== Resumen de validacion de DNI ===")
    columns_to_show = [
        "modality",
        "file",
        "id_column_used",
        "total_rows",
        "valid_dni",
        "missing_or_invalid_dni",
        "duplicated_rows_by_dni",
        "duplicated_unique_dni",
    ]
    print(summary_all[columns_to_show].to_string(index=False))

    print("\nArchivos exportados:")
    print(f"- {summary_path.relative_to(PROJECT_ROOT)}")
    print(f"- {ct_clean_path.relative_to(PROJECT_ROOT)}")
    print(f"- {gamma_clean_path.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()

