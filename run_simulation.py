#!/usr/bin/env python3
"""
Script simple para ejecutar la simulación desde la raíz del proyecto.
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from run import run

if __name__ == "__main__":
    # Ejecutar simulación
    firms_df, summary_df = run()
    
    print("\n=== Resumen Ejecutivo ===")
    print(summary_df.to_string())

