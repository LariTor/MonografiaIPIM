<p align="left">
  <img src="logoib.png" alt="Logo Instituto Balseiro" width="150">
</p>

# Proyecto Final IPIM — Introducción al Procesamiento de Imágenes Médicas

**Comparación entre FFR y SPECT en la evaluación de isquemia** (línea de trabajo del proyecto de maestría), mediante **análisis de datos** tabulares.

## Información institucional y académica

| | |
|--|--|
| **Autora** | **Torletti Lara** — [lara.torletti@ib.edu.ar](mailto:lara.torletti@ib.edu.ar) |
| **Institución** | [Instituto Balseiro](https://www.ib.edu.ar) |
| **Carrera** | Maestría en Física Médica |
| **Materia** | Introducción al Procesamiento de Imágenes Médicas (IPIM) |
| **Profesores** | Dr. Roberto Isoardi · Lic. Federico González Nicolini · Mgr. Daniel Fino |
| **Fecha de entrega** | xx de mayo de 2026 |

Este repositorio contiene el código para **cargar bases de turnos/estudios**, **normalizar identificadores (DNI)** y **cruzar pacientes entre tomografía (CT) y cámara gamma**, con exportación reproducible de tablas y reportes.

---

## Objetivo del repositorio

- Disponer de un flujo **reproducible** (Python, pandas) para integrar datos administrativos de distintas modalidades de imagen.
- Identificar pacientes con **ambos estudios** (CT y cámara gamma) usando el **documento normalizado** como clave principal.
- Documentar el proceso en `docs/` y dejar salidas claras en carpetas de resultados.

Para el detalle metodológico del cruce y del filtrado por DNI, véanse:

- [`docs/matching_ct_gamma.md`](docs/matching_ct_gamma.md)
- [`docs/filtrado_por_dni.md`](docs/filtrado_por_dni.md)

---

## Requisitos

- Python 3.10+ (recomendado; el proyecto usa dependencias listadas en `requirements.txt`).
- Instalación de dependencias:

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

Los scripts asumen que se ejecutan desde la **raíz del repositorio** (donde está `README.md`).

---

## Estructura de carpetas

| Ruta | Descripción |
|------|-------------|
| `Database/CT/` | Archivos fuente (p. ej. `.xls`) de estudios de CT. **Entrada principal** del pipeline de matching. |
| `Database/Camara_Gamma/` | Archivos fuente de cámara gamma. |
| `src/ffr_gamma_pipeline/` | Paquete Python: carga de tablas, limpieza de DNI, cruce, exportación. |
| `scripts/` | Scripts ejecutables (matching, limpieza, utilidades). |
| `outputs/` | **Única carpeta de salidas** del pipeline (`OUTPUT_DIR` en `config.py`): limpieza de DNI, unificados, coincidentes, Excel resumen, reportes. |
| `data/raw/`, `data/interim/`, `data/processed/` | Carpetas opcionales para organización futura; los datos crudos canónicos del código siguen en `Database/`. |
| `docs/` | Documentación en Markdown y plantillas. |

Para crear o verificar carpetas estándar:

```bash
python scripts/setup_project_structure.py
```

Opcional: `python scripts/setup_project_structure.py --gitkeep-data`

---

## Flujo de trabajo (visión general)

1. **Preparar entorno** (venv + `requirements.txt`).
2. **Opcional:** `setup_project_structure.py` para asegurar directorios.
3. **Limpieza y validación de DNI** sobre los Excel de cada modalidad → CSV con `patient_id` normalizado en `outputs/`.
4. **Matching CT ↔ cámara gamma** desde `Database/` → tablas de pacientes coincidentes y resumen en `outputs/`.

---

## Scripts principales

| Script | Rol |
|--------|-----|
| [`scripts/setup_project_structure.py`](scripts/setup_project_structure.py) | Crea/verifica carpetas del proyecto (idempotente). No mueve datos por defecto. |
| [`scripts/clean_validate_ids.py`](scripts/clean_validate_ids.py) | Lee `Database/CT` y `Database/Camara_Gamma`, normaliza DNI, exporta CSV limpios y resumen de calidad en `outputs/`. |
| [`scripts/run_patient_matching.py`](scripts/run_patient_matching.py) | Pipeline completo: carga unificada, limpieza, intersección por `patient_id`, tabla de coincidentes con fechas, Excel resumen. Todo en `outputs/`. |
| [`scripts/match_patients.py`](scripts/match_patients.py) | Cruce alternativo leyendo **CSV ya generados** en `outputs/` y escribiendo también en `outputs/`. Útil si ya existe la etapa de limpieza. |

---

## Orden recomendado de ejecución

**Flujo mínimo desde datos en `Database/`:**

1. `python scripts/setup_project_structure.py` *(opcional)*
2. `python scripts/clean_validate_ids.py` — genera p. ej. `outputs/ct_con_dni_normalizado.csv`, `outputs/camara_gamma_con_dni_normalizado.csv`, `outputs/resumen_limpieza_dni.csv`
3. `python scripts/run_patient_matching.py` — genera unificados, coincidentes y reporte (véase tabla de salidas abajo)

**Si solo querés cruzar a partir de CSV ya normalizados:**

1. Asegurate de existir `outputs/ct_con_dni_normalizado.csv` y `outputs/camara_gamma_con_dni_normalizado.csv`
2. `python scripts/match_patients.py`

---

## Outputs generados (referencia)

Rutas típicas; los nombres exactos están fijados en cada script.

### Limpieza de DNI (`clean_validate_ids.py`)

- `outputs/resumen_limpieza_dni.csv`
- `outputs/ct_con_dni_normalizado.csv`
- `outputs/camara_gamma_con_dni_normalizado.csv`

### Matching principal (`run_patient_matching.py`)

- `outputs/ct_unificado_limpio.csv`, `outputs/camara_gamma_unificado_limpio.csv`
- `outputs/pacientes_con_ambos_estudios.csv`
- `outputs/reporte_cruce_ct_gamma.md`
- `outputs/pacientes_coincidentes_ct_gamma.csv`
- `outputs/pacientes_coincidentes_resumen.xlsx`

### Matching desde CSV (`match_patients.py`)

- `outputs/dnis_en_ambas_bases.csv`
- `outputs/pacientes_coincidentes_ct_gamma.csv`
- `outputs/resumen_match_ct_gamma.csv`

---

## Documentación adicional

- [`docs/metodologia_cruce.md`](docs/metodologia_cruce.md) — metodología resumida del cruce.
- [`docs/columnas_detectadas.md`](docs/columnas_detectadas.md) — notas sobre columnas en los datos.
