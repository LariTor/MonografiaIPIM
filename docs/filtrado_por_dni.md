# Filtrado y normalización del identificador documental (DNI)

## 1. Por qué el DNI como identificador principal

En bases clínicas administrativas, los **nombres y apellidos** son propensos a:

- variaciones de escritura, tildes y orden (apellido/nombre);
- homonimia entre pacientes;
- errores de carga manual.

El **documento nacional de identidad** (o equivalente numérico almacenado en el campo de documento del sistema) ofrece, en este contexto, una clave **más estable** para enlazar registros entre modalidades, siempre que el valor esté presente y sea interpretable.

Por ello, el diseño del pipeline prioriza columnas candidatas de tipo documento (`Documento`, `DNI`, etc.) definidas en `PATIENT_ID_CANDIDATES` en `src/ffr_gamma_pipeline/config.py`.

## 2. Por qué no se usa el nombre para el cruce automático

El código de matching entre cohortes (`intersect_patients` en `src/ffr_gamma_pipeline/matching.py` y el `merge` en `scripts/run_patient_matching.py`) opera sobre **`patient_id`**, derivado exclusivamente del campo de documento normalizado.

Los nombres pueden aparecer en tablas de salida para **lectura humana** o control secundario, pero **no** definen la intersección automática, para reducir ambigüedad y falsos vínculos.

## 3. Cómo se elige la columna de documento

La función `choose_id_column` (`src/ffr_gamma_pipeline/cleaning.py`):

1. Busca coincidencia **exacta** entre los nombres de columnas del archivo y la lista de candidatos.
2. Si no hay coincidencia exacta, compara nombres **normalizados** (sin tildes, sin caracteres no alfanuméricos) para tolerar diferencias de etiquetado.

Si ninguna candidata coincide, se lanza un error explícito: no se asume una columna inexistente.

## 4. Normalización del valor (`normalize_dni`)

Implementación en `src/ffr_gamma_pipeline/cleaning.py`:

```python
def normalize_dni(value: object) -> str | None:
    ...
```

Pasos conceptuales:

1. Valores nulos o vacíos → `None`.
2. Conversión a cadena, eliminación de espacios internos y extremos.
3. Eliminación de separadores habituales (`.` y `-`).
4. Extracción de **solo dígitos** mediante expresión regular (`\D+` eliminado).

Si no queda ningún dígito, el resultado es `None`.

Esto homogeneiza formatos del tipo `12.345.678`, `12-345-678`, espacios, etc.

## 5. Filtrado de filas sin identificador válido

La función `clean_patient_id`:

1. Crea la columna `patient_id` aplicando `normalize_dni` a la columna cruda elegida.
2. **Descarta** todas las filas donde `patient_id` es `None`.

Así, el cruce posterior solo opera sobre identificadores que pudieron reducirse a una cadena numérica no vacía.

## 6. Validación y métricas de calidad

En `scripts/clean_validate_ids.py` se utiliza `summarize_dni_quality` (`cleaning.py`), que calcula, entre otras:

- total de filas;
- filas con DNI válido;
- filas sin DNI útil tras limpieza;
- indicadores de duplicación por identificador normalizado.

Esto permite auditar la calidad **por archivo** y **por modalidad** antes de depender de los CSV consolidados.

## 7. Criterio de validez práctica

Un identificador se considera **válido** para el pipeline si, tras `normalize_dni`, existe al menos un dígito y el resultado no es `None`. No se impone en este módulo un rango fijo de longitud (p. ej. 7 u 8 dígitos): el criterio es **presencia de dígitos** tras limpieza.

**Limitación:** DNIs mal cargados que compartan los mismos dígitos erróneos podrían colisionar; DNIs ausentes o no numéricos se excluyen y no participan del cruce.

## 8. Archivos típicos generados por la etapa de limpieza

Al ejecutar `scripts/clean_validate_ids.py` (rutas relativas a la raíz del proyecto):

- `outputs/resumen_limpieza_dni.csv` — métricas agregadas;
- `outputs/ct_con_dni_normalizado.csv` — CT con `patient_id` normalizado;
- `outputs/camara_gamma_con_dni_normalizado.csv` — cámara gamma con `patient_id` normalizado.

Estos archivos alimentan flujos posteriores (por ejemplo `scripts/match_patients.py`) sin repetir la lógica de limpieza en cada script.
