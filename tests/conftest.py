"""
Configuración de pytest para el proyecto
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))

# Configuración de pytest
pytest_plugins = []
