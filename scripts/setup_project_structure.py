#!/usr/bin/env python3
"""
Crea y verifica la estructura de directorios del proyecto MonografiaIPIM.

- Idempotente: puede ejecutarse varias veces sin efectos colaterales.
- No mueve ni borra archivos por defecto (evita romper rutas en config y scripts).
- Las rutas canónicas de datos siguen siendo Database/ y outputs/ según src/ffr_gamma_pipeline/config.py.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def directories_to_ensure(root: Path) -> list[Path]:
    """
    Directorios que deben existir para que el pipeline y la documentación sean coherentes.

    Nota: `data/raw`, `data/interim` y `data/processed` son convención tipo "data science";
    los datos crudos reales del repositorio viven hoy en `Database/`. No se reubican aquí
    para no invalidar DATABASE_ROOT en config.
    """
    return [
        root / "Database" / "CT",
        root / "Database" / "Camara_Gamma",
        root / "outputs",
        root / "scripts",
        root / "docs",
        root / "src",
        root / "src" / "ffr_gamma_pipeline",
        root / "data" / "raw",
        root / "data" / "interim",
        root / "data" / "processed",
    ]


def ensure_gitkeep(path: Path, dry_run: bool) -> bool:
    """Crea un .gitkeep en carpetas vacías de data/ para versionar la estructura."""
    if dry_run or not path.is_dir():
        return False
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepara la estructura de carpetas del proyecto (creación segura)."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo muestra qué haría, sin crear carpetas ni archivos.",
    )
    parser.add_argument(
        "--gitkeep-data",
        action="store_true",
        help="Crea .gitkeep en data/raw, data/interim y data/processed si no existen.",
    )
    args = parser.parse_args()

    root = project_root()
    print(f"Raíz del proyecto: {root}")

    created: list[Path] = []
    existed: list[Path] = []

    for d in directories_to_ensure(root):
        if args.dry_run:
            status = "crearía" if not d.exists() else "ya existe"
            print(f"  [{status}] {d.relative_to(root)}")
            continue
        if d.exists():
            existed.append(d)
        else:
            d.mkdir(parents=True, exist_ok=True)
            created.append(d)

    if not args.dry_run:
        print("\nCarpetas creadas:")
        for p in created:
            print(f"  + {p.relative_to(root)}")
        if not created:
            print("  (ninguna; todas las rutas requeridas ya existían)")

        print("\nCarpetas verificadas (ya existían):")
        for p in existed:
            print(f"  ✓ {p.relative_to(root)}")

        if args.gitkeep_data:
            for sub in ("raw", "interim", "processed"):
                p = root / "data" / sub
                if ensure_gitkeep(p, dry_run=False):
                    print(f"  + {p.relative_to(root)}/.gitkeep")

    print(
        "\nNota: los scripts usan Database/ y outputs/. "
        "No se mueven datos automáticamente; ver docs/matching_ct_gamma.md."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
