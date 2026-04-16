"""Cruce de pacientes CT vs Camara Gamma usando exclusivamente DNI."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ffr_gamma_pipeline.cleaning import normalize_dni  # noqa: E402
from ffr_gamma_pipeline.config import OUTPUT_DIR  # noqa: E402


def load_clean_dataset(path: Path, source_name: str) -> pd.DataFrame:
    """Carga dataset limpio y valida que tenga columna de DNI normalizada."""
    if not path.exists():
        raise FileNotFoundError(f"No se encontró archivo esperado: {path}")

    df = pd.read_csv(path)
    if "patient_id" not in df.columns:
        raise ValueError(
            f"El archivo {path.name} no tiene columna 'patient_id'. "
            "Ejecutá primero la etapa de limpieza."
        )

    work = df.copy()
    # Re-normalizamos por seguridad para asegurar formato homogéneo.
    work["patient_id"] = work["patient_id"].apply(normalize_dni)
    work = work[work["patient_id"].notna()].copy()
    work["patient_id"] = work["patient_id"].astype(str)
    work["source_modality"] = source_name
    return work


def unique_patients(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deja una fila por paciente (DNI) para evitar sobreconteo.

    Se usa `drop_duplicates(subset=["patient_id"])` para garantizar que cada
    paciente cuente una única vez aunque tenga múltiples turnos/estudios.
    """
    return df.sort_values("patient_id").drop_duplicates(subset=["patient_id"]).copy()


def build_matched_table(ct_unique: pd.DataFrame, gamma_unique: pd.DataFrame) -> pd.DataFrame:
    """
    Construye tabla de pacientes coincidentes con merge interno.

    Operación clave: `pd.merge(..., how="inner", on="patient_id")`.
    - `inner` devuelve únicamente DNIs presentes en ambas tablas.
    - `on="patient_id"` fuerza el cruce exclusivo por DNI.
    """
    ct_cols = [c for c in ["patient_id", "Nombres", "Apellido Paterno", "Apellido Materno"] if c in ct_unique.columns]
    gamma_cols = [c for c in ["patient_id", "Nombres", "Apellido Paterno", "Apellido Materno"] if c in gamma_unique.columns]

    ct_view = ct_unique[ct_cols].copy().add_prefix("ct_")
    gamma_view = gamma_unique[gamma_cols].copy().add_prefix("gamma_")
    ct_view = ct_view.rename(columns={"ct_patient_id": "patient_id"})
    gamma_view = gamma_view.rename(columns={"gamma_patient_id": "patient_id"})

    matched = pd.merge(ct_view, gamma_view, how="inner", on="patient_id")
    return matched.sort_values("patient_id").reset_index(drop=True)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ct_path = OUTPUT_DIR / "ct_con_dni_normalizado.csv"
    gamma_path = OUTPUT_DIR / "camara_gamma_con_dni_normalizado.csv"

    ct_df = load_clean_dataset(ct_path, source_name="CT")
    gamma_df = load_clean_dataset(gamma_path, source_name="Camara_Gamma")

    ct_unique = unique_patients(ct_df)
    gamma_unique = unique_patients(gamma_df)

    matched_table = build_matched_table(ct_unique, gamma_unique)

    # Lista de DNIs presentes en ambas bases (sin duplicados).
    dni_both = matched_table[["patient_id"]].copy()

    total_matches = int(len(dni_both))
    ct_unique_count = int(len(ct_unique))
    gamma_unique_count = int(len(gamma_unique))

    # Exportaciones pedidas.
    dni_both.to_csv(OUTPUT_DIR / "dnis_en_ambas_bases.csv", index=False)
    matched_table.to_csv(OUTPUT_DIR / "pacientes_coincidentes_ct_gamma.csv", index=False)
    summary_df = pd.DataFrame(
        [
            {
                "ct_total_filas_limpias": len(ct_df),
                "gamma_total_filas_limpias": len(gamma_df),
                "ct_pacientes_unicos": ct_unique_count,
                "gamma_pacientes_unicos": gamma_unique_count,
                "pacientes_coincidentes": total_matches,
            }
        ]
    )
    summary_df.to_csv(OUTPUT_DIR / "resumen_match_ct_gamma.csv", index=False)

    # Consola: resumen claro para auditoría rápida.
    print("=== Match de pacientes por DNI ===")
    print(f"Archivo CT leído: {ct_path.relative_to(PROJECT_ROOT)}")
    print(f"Archivo Cámara Gamma leído: {gamma_path.relative_to(PROJECT_ROOT)}")
    print("\nValidación anti-sobreconteo:")
    print("- Se deduplicó por 'patient_id' antes del merge")
    print("- El cruce se hizo con merge interno (inner) exclusivamente por DNI")
    print(f"\nPacientes únicos CT: {ct_unique_count}")
    print(f"Pacientes únicos Cámara Gamma: {gamma_unique_count}")
    print(f"Pacientes con ambos estudios (coincidencias): {total_matches}")
    print("\nArchivos exportados en outputs/:")
    print("- outputs/dnis_en_ambas_bases.csv")
    print("- outputs/pacientes_coincidentes_ct_gamma.csv")
    print("- outputs/resumen_match_ct_gamma.csv")


if __name__ == "__main__":
    main()

