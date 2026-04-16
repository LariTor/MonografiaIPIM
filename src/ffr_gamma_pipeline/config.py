"""Configuracion central para rutas y columnas candidatas."""

from pathlib import Path

# Raiz del proyecto: .../MonografiaIPIM
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_ROOT = PROJECT_ROOT / "Database"
CT_DIR = DATABASE_ROOT / "CT"
GAMMA_DIR = DATABASE_ROOT / "Camara_Gamma"
# Todas las salidas CSV/Excel/reportes del pipeline viven bajo esta ruta.
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Se prioriza DNI/ID. Nombres quedan para control secundario manual.
PATIENT_ID_CANDIDATES = [
    "Documento",
    "DNI",
    "ID Paciente",
    "ID_Paciente",
    "PacienteID",
]

# Columnas de contexto utiles para auditoria metodologica.
CONTEXT_COLUMNS = [
    "N° Turno",
    "Fecha Turno",
    "Nombres",
    "Apellido Paterno",
    "Apellido Materno",
    "Estudio",
    "Servicio",
]

