# Metodologia de cruce entre CT cardiaco y Camara Gamma

## Objetivo

Identificar pacientes con presencia de ambos estudios (CT y Camara Gamma) usando un identificador robusto de paciente (DNI/ID), sin utilizar nombres para el matching automatico.

## Justificacion metodologica

1. **Unificacion por fuente**  
   Cada modalidad se encuentra fragmentada en varios archivos. Se concatena cada carpeta por separado para construir dos cohortes comparables.

2. **Identificador primario**  
   Se utiliza la columna de documento del paciente como clave principal. Este criterio reduce el riesgo de falsos positivos por variaciones ortograficas en nombres.

3. **Normalizacion de identificador**  
   El documento se convierte a una cadena con solo dígitos. Asi se absorben formatos heterogeneos (puntos, guiones, espacios).

4. **Exclusion de registros invalidos**  
   Filas sin identificador util se eliminan antes del cruce para evitar coincidencias espurias.

5. **Cruce por interseccion**  
   Se realiza un `inner join` por `patient_id` entre cohortes deduplicadas por paciente para obtener la poblacion compartida.

## Reproducibilidad

- El pipeline registra archivos leidos.
- Informa columnas usadas para ID.
- Reporta conteos antes y despues de limpieza.
- Exporta resultados intermedios y finales en `outputs/`.

## Texto sugerido para la monografia

"La integración entre bases de CT cardíaco y Cámara Gamma se implementó mediante un pipeline reproducible en Python (pandas), estructurado en etapas de carga, limpieza, cruce y exportación. Dado el riesgo de inconsistencia en nombres y apellidos, se adoptó como clave principal el identificador documental del paciente. El campo fue normalizado a un formato numérico homogéneo (solo dígitos), y se excluyeron registros sin identificador válido. Posteriormente, se realizó una intersección por identificador entre ambas cohortes, previamente unificadas por modalidad. Este procedimiento permitió determinar de manera trazable la cantidad de pacientes con ambos estudios, minimizando sesgos por errores de digitación nominal." 

