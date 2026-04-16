"""Ejecucion principal del flujo de carga, limpieza, cruce y exportacion."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ffr_gamma_pipeline.cleaning import choose_id_column, clean_patient_id, normalize_dni
from ffr_gamma_pipeline.config import CT_DIR, GAMMA_DIR, OUTPUT_DIR, PATIENT_ID_CANDIDATES
from ffr_gamma_pipeline.exporting import export_csv, write_markdown_report
from ffr_gamma_pipeline.io_utils import load_many
from ffr_gamma_pipeline.matching import intersect_patients


def _compact(text: str) -> str:
    return "".join(ch for ch in text.lower().strip() if ch.isalnum())


def _detect_column(columns: list[str], candidates: list[str], label: str) -> str:
    normalized = {_compact(col): col for col in columns}
    for candidate in candidates:
        if candidate in columns:
            return candidate
    for candidate in candidates:
        key = _compact(candidate)
        if key in normalized:
            return normalized[key]
    raise ValueError(
        f"No se encontró columna para '{label}'. "
        f"Candidatas: {candidates}. Columnas detectadas: {columns}"
    )


def _clean_text(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True).str.upper()


def _build_modality_patient_view(
    df: pd.DataFrame, prefix: str
) -> tuple[pd.DataFrame, dict[str, str | None]]:
    """
    Una fila por patient_id con nombre, apellido y la fecha de turno original
    (columna real del Excel, p. ej. Fecha Turno), sin eliminar ese campo.
    """
    columns = [str(c) for c in df.columns]
    fecha_turno_col = _detect_column(
        columns,
        ["Fecha Turno", "Inicio Estudio", "Fin Estudio", "Fecha Turno Dado"],
        f"{prefix} fecha turno",
    )
    name_col = _detect_column(columns, ["Nombres", "Nombre"], f"{prefix} nombre")
    ap_pat_col = _detect_column(
        columns,
        ["Apellido Paterno", "Apellido", "Apellidos", "Apellido Paciente"],
        f"{prefix} apellido paterno",
    )

    ap_mat_col: str | None = None
    try:
        ap_mat_col = _detect_column(
            columns,
            ["Apellido Materno", "Segundo Apellido", "Apellido Materno Paciente"],
            f"{prefix} apellido materno",
        )
    except ValueError:
        ap_mat_col = None

    work = df.copy()
    work["patient_id"] = work["patient_id"].apply(normalize_dni)
    work = work[work["patient_id"].notna()].copy()
    work["__nombre"] = _clean_text(work[name_col])
    work["__ap_pat"] = _clean_text(work[ap_pat_col])
    work["__ap_mat"] = _clean_text(work[ap_mat_col]) if ap_mat_col else ""
    work["__apellido"] = (
        (work["__ap_pat"] + " " + work["__ap_mat"])
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

    work["__sort_fecha"] = pd.to_datetime(work[fecha_turno_col], errors="coerce")
    work = (
        work.sort_values(
            ["patient_id", "__sort_fecha"],
            ascending=[True, True],
            na_position="last",
        )
        .drop_duplicates(subset=["patient_id"], keep="first")
        .copy()
    )

    out_fecha_name = f"{prefix}_{fecha_turno_col}"
    view = work[["patient_id", fecha_turno_col, "__nombre", "__apellido"]].rename(
        columns={
            fecha_turno_col: out_fecha_name,
            "__nombre": f"{prefix}_nombre",
            "__apellido": f"{prefix}_apellido",
        }
    )
    view["patient_id"] = view["patient_id"].astype(str)

    used_columns: dict[str, str | None] = {
        "fecha_turno": fecha_turno_col,
        "name": name_col,
        "apellido_paterno": ap_pat_col,
        "apellido_materno": ap_mat_col,
    }
    return view, used_columns


def build_matched_table(
    ct_clean: pd.DataFrame, gamma_clean: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, dict[str, str | None]], dict[str, object]]:
    ct_view, ct_used = _build_modality_patient_view(ct_clean, prefix="ct")
    gamma_view, gamma_used = _build_modality_patient_view(gamma_clean, prefix="gamma")
    matched = ct_view.merge(gamma_view, on="patient_id", how="inner")
    # Columnas de fecha cruzadas (nombres reales con prefijo ct_/gamma_), p. ej. ct_Fecha Turno.
    ct_fecha_col = f"ct_{ct_used['fecha_turno']}"
    gamma_fecha_col = f"gamma_{gamma_used['fecha_turno']}"
    gamma_parsed = pd.to_datetime(matched[gamma_fecha_col], errors="coerce")
    ct_parsed = pd.to_datetime(matched[ct_fecha_col], errors="coerce")
    # Estrategia: preferir fecha de Cámara Gamma; si NaT o ausente, usar CT.
    matched = matched.copy()
    matched["fecha"] = gamma_parsed.where(gamma_parsed.notna(), ct_parsed)
    fecha_nat_count = int(matched["fecha"].isna().sum())
    matched = matched.sort_values(by="fecha", ascending=True, na_position="last").reset_index(
        drop=True
    )
    fecha_meta: dict[str, object] = {
        "gamma_fecha_col": gamma_fecha_col,
        "ct_fecha_col": ct_fecha_col,
        "fecha_nat_count": fecha_nat_count,
    }
    return matched, {"ct": ct_used, "gamma": gamma_used}, fecha_meta


def build_summary_dataframe(matched: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Resumen para Excel: patient_id, fecha, dni, nombre, apellido (mismo orden cronológico que coincidentes)."""
    out = matched.copy()
    out["patient_id"] = out["patient_id"].apply(normalize_dni)

    # CT primero; Gamma como respaldo si CT viene vacio.
    out["nombre"] = out["ct_nombre"].where(
        out["ct_nombre"].notna() & (out["ct_nombre"].astype(str).str.strip() != ""),
        out["gamma_nombre"],
    )
    out["apellido"] = out["ct_apellido"].where(
        out["ct_apellido"].notna() & (out["ct_apellido"].astype(str).str.strip() != ""),
        out["gamma_apellido"],
    )
    out["dni"] = out["patient_id"].apply(normalize_dni)
    out["fecha"] = pd.to_datetime(out["fecha"], errors="coerce")

    out["nombre"] = _clean_text(out["nombre"])
    out["apellido"] = _clean_text(out["apellido"])

    initial_rows = len(out)
    out = out[out["patient_id"].notna()].copy()
    dropped_no_patient = initial_rows - len(out)

    out = out.sort_values(by="fecha", ascending=True, na_position="last").reset_index(drop=True)
    summary = out[["patient_id", "fecha", "dni", "nombre", "apellido"]].copy()
    return summary, dropped_no_patient


def main() -> None:
    print("Iniciando pipeline reproducible CT vs Camara Gamma")

    ct_raw, ct_log = load_many(CT_DIR, source_name="CT")
    gamma_raw, gamma_log = load_many(GAMMA_DIR, source_name="Camara_Gamma")

    ct_columns = [str(c) for c in ct_raw.columns]
    gamma_columns = [str(c) for c in gamma_raw.columns]

    ct_id_col = choose_id_column(ct_columns, PATIENT_ID_CANDIDATES)
    gamma_id_col = choose_id_column(gamma_columns, PATIENT_ID_CANDIDATES)

    ct_before = len(ct_raw)
    gamma_before = len(gamma_raw)

    ct_clean = clean_patient_id(ct_raw, ct_id_col)
    gamma_clean = clean_patient_id(gamma_raw, gamma_id_col)

    ct_after = len(ct_clean)
    gamma_after = len(gamma_clean)

    both = intersect_patients(ct_clean, gamma_clean)
    matched_table, used_cols, fecha_meta = build_matched_table(ct_clean, gamma_clean)
    summary_df, dropped_no_patient = build_summary_dataframe(matched_table)

    export_csv(ct_clean, OUTPUT_DIR / "ct_unificado_limpio.csv")
    export_csv(gamma_clean, OUTPUT_DIR / "camara_gamma_unificado_limpio.csv")
    export_csv(both, OUTPUT_DIR / "pacientes_con_ambos_estudios.csv")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    matched_csv_path = OUTPUT_DIR / "pacientes_coincidentes_ct_gamma.csv"
    summary_xlsx_path = OUTPUT_DIR / "pacientes_coincidentes_resumen.xlsx"
    export_csv(matched_table, matched_csv_path)
    summary_df.to_excel(summary_xlsx_path, index=False)

    files_read = [
        f"CT/{entry['file']}" for entry in ct_log
    ] + [
        f"Camara_Gamma/{entry['file']}" for entry in gamma_log
    ]
    write_markdown_report(
        output_path=OUTPUT_DIR / "reporte_cruce_ct_gamma.md",
        files_read=files_read,
        id_columns_used={"ct": ct_id_col, "gamma": gamma_id_col},
        cleaning_summary={
            "ct": {"rows_before": ct_before, "rows_after": ct_after},
            "gamma": {"rows_before": gamma_before, "rows_after": gamma_after},
        },
        match_count=len(both),
    )

    print("\n=== Archivos leidos ===")
    for item in files_read:
        print(f"- {item}")

    print("\n=== Columnas usadas para ID ===")
    print(f"- CT: {ct_id_col}")
    print(f"- Camara Gamma: {gamma_id_col}")

    print("\n=== Limpieza aplicada ===")
    print("- Se conservan solo digitos en DNI/ID")
    print("- Se descartan filas sin DNI/ID valido")

    print("\n=== Conteos antes y despues ===")
    print(f"- CT: {ct_before} -> {ct_after}")
    print(f"- Camara Gamma: {gamma_before} -> {gamma_after}")

    print("\n=== Coincidencias ===")
    print(f"- Pacientes con ambos estudios: {len(both)}")

    print("\n=== Resumen de pacientes coincidentes ===")
    print(f"- Ruta resumen: {summary_xlsx_path.relative_to(PROJECT_ROOT)}")
    print(f"- Filas exportadas: {len(summary_df)}")
    print("- Fecha del estudio (columna `fecha`):")
    print(
        f"  - Preferencia: {fecha_meta['gamma_fecha_col']} parseada con pd.to_datetime(..., errors='coerce')"
    )
    print(
        f"  - Fallback si Gamma es NaT: {fecha_meta['ct_fecha_col']} parseada con pd.to_datetime(..., errors='coerce')"
    )
    print(f"  - Filas con fecha NaT tras combinar: {fecha_meta['fecha_nat_count']}")
    print("- Columnas originales usadas:")
    print(f"- dni: patient_id normalizado (origen ID CT={ct_id_col}, Gamma={gamma_id_col})")
    print(
        "- nombre: "
        f"CT.{used_cols['ct']['name']} (fallback Camara_Gamma.{used_cols['gamma']['name']})"
    )
    print(
        "- apellido: "
        f"CT.{used_cols['ct']['apellido_paterno']} + CT.{used_cols['ct']['apellido_materno']} "
        f"(fallback Camara_Gamma.{used_cols['gamma']['apellido_paterno']} + "
        f"Camara_Gamma.{used_cols['gamma']['apellido_materno']})"
    )
    print(f"- Filas descartadas sin patient_id: {dropped_no_patient}")

    print("\nPipeline finalizado. Resultados en carpeta outputs/")


if __name__ == "__main__":
    main()
