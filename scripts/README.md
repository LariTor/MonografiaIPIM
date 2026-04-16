# Scripts del pipeline (orden recomendado)

Esta carpeta reúne puntos de entrada ejecutables del proyecto. El flujo recomendado depende de si querés correr desde los archivos crudos (XLS) en `Database/` o desde los CSV ya normalizados en `outputs/`.

## 1) Flujo desde datos crudos en `Database/`

1. `python scripts/setup_project_structure.py`
   - Solo crea/verifica carpetas necesarias (idempotente).
2. `python scripts/clean_validate_ids.py`
   - Lee `Database/CT/` y `Database/Camara_Gamma/`.
   - Normaliza el identificador documental a `patient_id` (solo dígitos).
   - Exporta CSV en `outputs/` con el DNI normalizado y un resumen de calidad.
3. `python scripts/run_patient_matching.py`
   - Carga y unifica CT y cámara gamma.
   - Cruza pacientes usando exclusivamente `patient_id` (merge `inner`).
   - Exporta:
     - CSV unificados de CT y gamma,
     - `outputs/pacientes_con_ambos_estudios.csv`,
     - `outputs/pacientes_coincidentes_ct_gamma.csv`,
     - `outputs/pacientes_coincidentes_resumen.xlsx`,
     - `outputs/reporte_cruce_ct_gamma.md`.

## 2) Cruce alternativo desde CSV ya normalizados

- `python scripts/match_patients.py`
  - Lee `outputs/ct_con_dni_normalizado.csv` y `outputs/camara_gamma_con_dni_normalizado.csv`.
  - Realiza el matching por `patient_id` y exporta resultados a `outputs/`.

## 3) Nota sobre salidas

El repositorio usa **una sola** carpeta de salidas canónica: `outputs/` (definida por `src/ffr_gamma_pipeline/config.py`).

