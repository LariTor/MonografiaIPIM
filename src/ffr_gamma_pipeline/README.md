# ffr_gamma_pipeline (paquete interno)

Paquete Python que concentra la lógica compartida del proyecto:

- rutas y columnas candidatas (config),
- carga de tablas desde XLS/XLSX/CSV (io_utils),
- limpieza y normalización del identificador de paciente (cleaning),
- cruce por `patient_id` entre cohortes CT y cámara gamma (matching),
- utilidades de exportación y reporte (exporting).

## Módulos

### `config.py`
- Define rutas canónicas:
  - `Database/CT`,
  - `Database/Camara_Gamma`,
  - `outputs/` (salidas).
- Define `PATIENT_ID_CANDIDATES`, la lista de nombres de columna posibles para el documento/DNI.

### `io_utils.py`
- `load_table(path)`: carga según extensión (CSV/XLS/XLSX).
- `load_many(folder, source_name)`: concatena múltiples archivos de una modalidad y agrega trazabilidad.

### `cleaning.py`
- `choose_id_column(...)`: elige la columna de documento dentro del dataset (con tolerancia a variaciones de nombre).
- `normalize_dni(...)`: deja solo dígitos y estandariza el formato.
- `clean_patient_id(...)`: crea `patient_id` y descarta filas sin DNI util.

### `matching.py`
- `intersect_patients(ct_df, gamma_df)`: reduce cada modalidad a una fila por `patient_id` y realiza un `inner merge`.

### `exporting.py`
- `export_csv(df, path)`: exporta CSV asegurando creación de carpeta.
- `write_markdown_report(...)`: genera un reporte reproducible en Markdown del cruce.

## Referencia de uso

- Los scripts “entrypoint” en `scripts/` llaman a estas funciones para implementar el pipeline completo sin duplicar lógica.

