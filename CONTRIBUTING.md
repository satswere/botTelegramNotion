# Guía de Contribución

Este documento consolida toda la información necesaria para contribuir al proyecto Bot Telegram → Notion.

## 📋 Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Configuración del Entorno](#configuración-del-entorno)
- [Guía de Desarrollo](#guía-de-desarrollo)
- [Testing](#testing)
- [Convenciones de Código](#convenciones-de-código)
- [Logging](#logging)
- [Deployment](#deployment)

## 🏗️ Arquitectura

### Clean Architecture (Hexagonal)

El proyecto sigue los principios de Clean Architecture con 4 capas:

```
├── domain/              # Lógica de negocio pura (sin dependencias externas)
│   ├── entities/        # Entidades del dominio (Bet, BetImage, ForwardMetadata)
│   ├── value_objects/   # Value Objects (Money, Odds, BetStatus)
│   ├── services/        # Servicios del dominio (BetValidator, BetEnrichmentService)
│   └── repositories/    # Interfaces (puertos) para infraestructura
│
├── application/         # Casos de uso y orquestación
│   ├── use_cases/       # CreateBet, ProcessBetImage, UpdateBetStatus
│   ├── orchestration/   # MessageProcessor, CommandOrchestrator
│   └── dtos/            # Data Transfer Objects
│
├── infrastructure/      # Adaptadores (implementaciones concretas)
│   ├── notion/          # Notion API (NotionBetRepository, NotionFileUploader)
│   ├── telegram/        # Telegram API (TelegramMessageExtractor)
│   ├── openai/          # OpenAI Vision API (OpenAIImageAnalyzer)
│   └── storage/         # File storage local
│
└── presentation/        # Capa de presentación (Telegram handlers)
    └── handlers/        # StartHandler, HelpHandler, ImageHandler, StatusHandler
```

### Flujo de Datos

```
Usuario → Telegram Handler → Use Case → Domain Service → Repository → External API
                                ↓
                           Infrastructure
```

## ⚙️ Configuración del Entorno

### Requisitos

- Python 3.8+
- Cuenta de Notion con API token
- Bot de Telegram (BotFather token)
- OpenAI API key (para GPT-4 Vision)

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/satswere/botTelegramNotion.git
cd botTelegramNotion

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuración
cp .env.example .env

# Editar .env con tus credenciales
# TELEGRAM_BOT_TOKEN=...
# NOTION_TOKEN=...
# NOTION_DATABASE_ID=...
# OPENAI_API_KEY=...
```

## 🔨 Guía de Desarrollo

### Crear Nueva Funcionalidad

1. **Definir en Domain**: Crear entidad/value object/servicio si es lógica de negocio
2. **Crear Use Case**: Implementar caso de uso en `application/use_cases/`
3. **Implementar Adaptador**: Si necesita infraestructura externa
4. **Agregar Handler**: Si es un comando de Telegram
5. **Escribir Tests**: Unit tests en `tests/unit/`, integration en `tests/integration/`

### Ejemplo: Agregar Nuevo Campo a Bet

```python
# 1. Domain Entity
class Bet:
    def __init__(self, ..., new_field: str):
        self.new_field = new_field

# 2. DTO
class BetDTO:
    new_field: str

# 3. Repository
async def save(self, bet_data: Dict):
    properties["Nuevo Campo"] = {"rich_text": [{"text": {"content": bet_data["new_field"]}}]}

# 4. Use Case (si aplica)
class ProcessBetImageUseCase:
    # Incluir nuevo campo en el análisis
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Solo unit tests
pytest tests/unit/

# Con coverage
pytest --cov=. --cov-report=html

# Test específico
pytest tests/unit/domain/test_bet.py
```

### Escribir Tests

```python
# tests/unit/domain/test_my_entity.py
import pytest
from domain.entities.my_entity import MyEntity

def test_my_entity_creation():
    entity = MyEntity(field="value")
    assert entity.field == "value"

def test_my_entity_validation():
    with pytest.raises(ValueError):
        MyEntity(field=None)
```

## 📝 Convenciones de Código

### Python Style Guide

- **PEP 8** para estilo de código
- **Type hints** obligatorios en funciones públicas
- **Docstrings** en clases y funciones públicas (formato Google)
- **Async/await** para operaciones IO
- **Dependency Injection** en constructores

### Naming Conventions

```python
# Clases: PascalCase
class NotionBetRepository:
    pass

# Funciones/métodos: snake_case
async def process_bet_image():
    pass

# Constantes: UPPER_SNAKE_CASE
MAX_RETRIES = 3

# Variables privadas: prefijo _
def _internal_method(self):
    pass
```

### Imports

```python
# Orden:
# 1. Standard library
import asyncio
import logging
from typing import Dict, Any

# 2. Third-party
from notion_client import Client
from telegram import Update

# 3. Local
from domain.entities import Bet
from infrastructure.notion import NotionBetRepository
```

## 📊 Logging

Ver [LOGGING.md](./docs/LOGGING.md) para guía completa del sistema de logging.

### Niveles de Log

```python
logger.debug("🔍 Información detallada para debugging")
logger.info("✅ Operación exitosa normal")
logger.warning("⚠️ Situación anormal pero manejable")
logger.error("❌ Error que impide operación")
logger.critical("🚨 Fallo crítico del sistema")
```

### Formato

```python
# ✅ CORRECTO
logger.info(f"✅ Apuesta guardada: {bet_id}")
logger.error(f"❌ Error guardando apuesta: {e}", exc_info=True)

# ❌ INCORRECTO  
print("Apuesta guardada")  # No usar print
logger.info("Error!")  # Sin contexto
```

## 🚀 Deployment

### Producción

```bash
# 1. Verificar tests
pytest

# 2. Actualizar variables de entorno
# Editar .env en servidor

# 3. Reiniciar bot
python main.py
```

### Monitoring

- Logs en `bot.log`
- Errores críticos visible en consola
- Comando `/status` para health check

## 🔄 Workflow de Git

```bash
# 1. Crear branch desde main
git checkout -b feature/nombre-feature

# 2. Commit frecuente
git add .
git commit -m "feat: descripción del cambio"

# 3. Push y crear PR
git push origin feature/nombre-feature

# 4. Review y merge
```

### Convención de Commits

```
feat: Nueva funcionalidad
fix: Corrección de bug
refactor: Refactorización sin cambio funcional
docs: Cambios en documentación
test: Agregar/modificar tests
chore: Cambios en build, CI, etc.
```

## 📚 Recursos

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Notion API Docs](https://developers.notion.com/)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)
- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)

## ❓ FAQ

### ¿Cómo agrego un nuevo handler de Telegram?

1. Crear archivo en `presentation/handlers/`
2. Implementar método `handle(update, context)`
3. Registrar en `main.py`

### ¿Dónde va la lógica de negocio?

- **Domain layer** (`domain/`): Lógica pura sin dependencias externas
- **Application layer** (`application/`): Casos de uso coordinando domain
- **Infrastructure layer** NO debe tener lógica de negocio

### ¿Cómo debuggeo un problema con OpenAI?

```bash
python debug_openai_response.py
```

## 🆘 Soporte

- **Issues**: GitHub Issues
- **Documentación**: Este archivo + README.md
- **Logs**: Revisar `bot.log`
