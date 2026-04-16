# Reporte de cruce CT vs Camara Gamma

## 1) Archivos leidos
- `CT/Turno-1170.xls`
- `CT/Turno-220.xls`
- `CT/Turno-2688.xls`
- `CT/Turno-4001.xls`
- `CT/Turno-5965.xls`
- `Camara_Gamma/Turno-1773.xls`
- `Camara_Gamma/Turno-3248.xls`
- `Camara_Gamma/Turno-3456.xls`
- `Camara_Gamma/Turno-3935.xls`
- `Camara_Gamma/Turno-8569.xls`

## 2) Columnas usadas para ID
- CT: `Documento`
- Camara Gamma: `Documento`

## 3) Limpieza aplicada
- Se conservaron solo digitos en el identificador.
- Se eliminaron filas sin DNI/ID valido.

## 4) Registros antes y despues de limpiar
- CT: 2612 antes, 2612 despues
- Camara Gamma: 6841 antes, 6841 despues

## 5) Pacientes coincidentes
- Pacientes con ambos estudios: 340

> Nota: el cruce se realizo exclusivamente por DNI/ID normalizado.