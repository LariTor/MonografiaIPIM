# Columnas detectadas en la base original

Inspeccion de archivos en:

- `Database/CT/*.xls`
- `Database/Camara_Gamma/*.xls`

Resultado: ambos grupos presentan la misma estructura de columnas en `Sheet0`.

## Columnas observadas

- `N° Turno`
- `Fecha Turno`
- `Apellido Paterno`
- `Apellido Materno`
- `Nombres`
- `Documento`
- `Fecha Nac.`
- `Teléfono Fijo`
- `Celular/WhatsApp`
- `eMail`
- `Estudio`
- `Servicio`
- `Aseguradora`
- `Cuenta`
- `N° Afiliado`
- `Médico / Equipo`
- `Recep. Orden`
- `Estado`
- `Técnico IN`
- `Técnico OUT`
- `Inicio Estudio`
- `Operador`
- `Reprogramar`
- `Tipo Turno`
- `Derivante`
- `Fecha Turno Dado`
- `Accession Number`
- `Arribo`
- `Presentación`
- `Fin Estudio`
- `Informe Finalizado`
- `Centro`
- `Motivo Recitado`

## Mapeo metodologico propuesto para identificacion de paciente

- Clave primaria: `Documento` (normalizada a solo dígitos).
- Claves alternativas solo si `Documento` no existe en una futura actualización:
  - `DNI`
  - `ID Paciente`
  - `ID_Paciente`
  - `PacienteID`

> Nombres (`Nombres`, `Apellido Paterno`, `Apellido Materno`) no se usan para matching automatico; quedan para validacion manual secundaria.

