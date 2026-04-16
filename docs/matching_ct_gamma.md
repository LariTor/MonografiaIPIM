# Cruce de pacientes entre tomografía (CT) y cámara gamma

## 1. Objetivo

Identificar pacientes que tienen **al menos un estudio de CT cardíaco** y **al menos un estudio en cámara gamma** en las bases exportadas, usando un identificador de persona **normalizado** (derivado del documento/DNI), de forma **reproducible** y **trazable**.

El matching automático **no** utiliza nombres ni apellidos como clave de unión; esos campos se usan solo como apoyo descriptivo en tablas de salida (véase `docs/filtrado_por_dni.md`).

## 2. Fuentes de datos utilizadas

En el repositorio, los archivos tabulares de origen se organizan así:

| Ubicación | Contenido |
|-----------|-----------|
| `Database/CT/` | Archivos `.xls` / `.xlsx` de turnos/estudios de CT |
| `Database/Camara_Gamma/` | Archivos `.xls` / `.xlsx` de turnos/estudios de cámara gamma |

La carga admite CSV, XLS y XLSX según `src/ffr_gamma_pipeline/io_utils.py` (`load_table`, `load_many`).

## 3. Unificación por modalidad (CT y cámara gamma)

Para cada carpeta (`CT` y `Camara_Gamma`):

1. Se listan todos los archivos soportados en la carpeta.
2. Cada archivo se lee en un `DataFrame` y se añaden columnas de trazabilidad (`source_file`, `source_modality`).
3. Se **concatenan** todos los archivos de esa modalidad en una única tabla unificada.

Esto resuelve la fragmentación en varios turnos/archivos por modalidad y permite tratar cada modalidad como una cohorte única antes del cruce.

Implementación: `load_many` en `src/ffr_gamma_pipeline/io_utils.py`; invocación principal en `scripts/run_patient_matching.py`.

## 4. Identificación del paciente y limpieza

- Se detecta la columna de documento entre candidatas definidas en `src/ffr_gamma_pipeline/config.py` (`PATIENT_ID_CANDIDATES`, p. ej. `Documento`, `DNI`, etc.).
- Sobre esa columna se aplica `normalize_dni` y se construye `patient_id` (solo dígitos).
- Se **eliminan** filas sin identificador válido (`clean_patient_id` en `src/ffr_gamma_pipeline/cleaning.py`).

Detalle del criterio de validez y normalización: `docs/filtrado_por_dni.md`.

## 5. Definición de “pacientes coincidentes” en el pipeline principal

El script `scripts/run_patient_matching.py` implementa dos niveles de resultado:

### 5.1 Conteo por intersección de cohortes

Función `intersect_patients` (`src/ffr_gamma_pipeline/matching.py`):

- Se reduce cada cohorte a **una fila por `patient_id`** (`unique_patients` + `drop_duplicates`).
- Se hace un **`inner join`** entre las tablas `has_ct` y `has_gamma` sobre `patient_id`.

Tipo de join: **inner** (intersección): solo permanecen identificadores presentes en **ambas** modalidades.

Estrategia: minimizar falsos positivos por homonimia; el documento normalizado actúa como clave principal.

### 5.2 Tabla detallada de coincidentes con nombres y fechas

Además del conteo, se construye una tabla enriquecida (`build_matched_table` en `scripts/run_patient_matching.py`):

- Por cada modalidad se genera una vista con **una fila por paciente** (deduplicación por `patient_id`), conservando columnas de contexto (p. ej. `Fecha Turno` detectada entre nombres de columna reales).
- Se fusionan las vistas CT y gamma con **`merge(..., how="inner", on="patient_id")`**.
- Se define una columna `fecha` para el estudio combinando fechas parseadas: **prioridad a la fecha de cámara gamma**; si no es válida, **fallback a CT** (`pd.to_datetime(..., errors="coerce")`).
- El conjunto se ordena por `fecha` en orden cronológico ascendente.

Archivos generados por este script (rutas relativas a la raíz del proyecto):

| Salida | Descripción |
|--------|-------------|
| `outputs/ct_unificado_limpio.csv` | CT unificado tras limpieza de ID |
| `outputs/camara_gamma_unificado_limpio.csv` | Cámara gamma unificada tras limpieza de ID |
| `outputs/pacientes_con_ambos_estudios.csv` | Lista de `patient_id` con ambos estudios (`has_ct`, `has_gamma`) |
| `outputs/reporte_cruce_ct_gamma.md` | Reporte breve en Markdown del cruce |
| `outputs/pacientes_coincidentes_ct_gamma.csv` | Coincidentes con columnas CT/gamma y `fecha` |
| `outputs/pacientes_coincidentes_resumen.xlsx` | Resumen (`patient_id`, `fecha`, `dni`, `nombre`, `apellido`) |

## 6. Flujo alternativo basado en CSV ya normalizados

Existe además `scripts/match_patients.py`, que **no** lee directamente `Database/`, sino los CSV generados por la etapa de validación de DNI:

- `outputs/ct_con_dni_normalizado.csv`
- `outputs/camara_gamma_con_dni_normalizado.csv`

y escribe en `outputs/` archivos como `dnis_en_ambas_bases.csv`, `pacientes_coincidentes_ct_gamma.csv` y `resumen_match_ct_gamma.csv`. Los conteos exactos dependen de la corrida y del estado de esos CSV; un ejemplo de filas del resumen agregado (archivo presente en el repositorio) es:

```text
ct_total_filas_limpias,gamma_total_filas_limpias,ct_pacientes_unicos,gamma_pacientes_unicos,pacientes_coincidentes
2612,6841,2579,6663,340
```

Para reproducir el flujo **desde fuentes crudas** con el mismo criterio que documenta `outputs/reporte_cruce_ct_gamma.md`, el punto de entrada principal es `scripts/run_patient_matching.py`.

## 7. Orden sugerido de ejecución (reproducibilidad)

1. (Opcional) `python scripts/setup_project_structure.py` — asegura carpetas.
2. `python scripts/clean_validate_ids.py` — genera CSV con DNI normalizado y resumen de calidad en `outputs/` (necesario si se usa `match_patients.py`).
3. `python scripts/run_patient_matching.py` — pipeline completo desde `Database/` hasta CSV/Excel de coincidentes.

## 8. Relación con otra documentación

- Metodología resumida previa: `docs/metodologia_cruce.md`.
- Este documento amplía el detalle alineado con el código actual en `scripts/run_patient_matching.py` y `src/ffr_gamma_pipeline/`.
