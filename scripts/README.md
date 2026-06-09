# Scripts de Desarrollo

Scripts de utilidad para desarrollo, depuración y mantenimiento del proyecto.

## 📜 Scripts Disponibles

### 🔍 debug_openai_response.py

Depura la respuesta de OpenAI Vision para la última imagen procesada.

```bash
python scripts/debug_openai_response.py
```

**Uso**:
- Envía una imagen al bot
- Ejecuta el script para ver la respuesta completa de OpenAI
- Útil para depurar problemas de extracción de datos

**Salida**:
- Muestra todos los campos extraídos por OpenAI
- Indica qué campos están presentes/ausentes
- Útil para ajustar el prompt de extracción

---

### ✅ validate_extraction.py

Valida el flujo completo de extracción y creación en Notion.

```bash
python scripts/validate_extraction.py
```

**Uso**:
- Ejecuta después de cambios en la lógica de extracción
- Verifica que todos los servicios estén funcionando
- Valida la integración end-to-end

**Verifica**:
1. ✅ Variables de entorno configuradas
2. ✅ Servicios de infraestructura funcionando
3. ✅ Use cases operativos
4. ✅ Extracción de campos completa
5. ✅ Creación en Notion exitosa

---

### 🧹 clean_storage.py

Limpia archivos temporales antiguos del proyecto.

```bash
python scripts/clean_storage.py
```

**Limpia**:
- 📸 **Imágenes**: Elimina imágenes procesadas más antiguas de 7 días
- 📝 **Logs**: Elimina logs antiguos más de 30 días
- 🐍 **__pycache__**: Elimina todos los caches de Python

**Salida**:
- Muestra tamaño antes y después
- Indica cuántos archivos se eliminaron
- Reporta espacio liberado

---

## 🛠️ Crear Nuevos Scripts

Al crear nuevos scripts de desarrollo:

1. **Ubicación**: Guardar en `scripts/`
2. **Naming**: Usar snake_case descriptivo (ej: `test_feature.py`)
3. **Documentación**: Agregar docstring y actualizar este README
4. **Dependencias**: Usar imports relativos desde la raíz del proyecto
5. **Ayuda**: Agregar descripción con `--help` si usa argparse

**Ejemplo**:

```python
"""
Descripción breve del script

Descripción más detallada de lo que hace.
"""

import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports del proyecto
from domain.entities import Bet
from infrastructure.notion import NotionBetRepository


def main():
    """Función principal del script"""
    print("🚀 Ejecutando script...")
    # Tu lógica aquí


if __name__ == "__main__":
    main()
```

---

## 📚 Recursos Adicionales

- [CONTRIBUTING.md](../CONTRIBUTING.md) - Guía de desarrollo completa
- [docs/LOGGING.md](../docs/LOGGING.md) - Guía de logging
- [README.md](../README.md) - Documentación principal
