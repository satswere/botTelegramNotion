# Bot Telegram → Notion | Arquitectura Hexagonal

Bot de Telegram que recibe imágenes de tickets de apuestas, las analiza con IA (OpenAI Vision) y las registra automáticamente en una base de datos Notion.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-green)
![Tests](https://img.shields.io/badge/Tests-121+-success)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Características

### 🎯 Funcionalidades Principales

- ✅ **Análisis Automático con IA**: OpenAI GPT-4 Vision extrae 12 campos de tickets de apuestas
- ✅ **Integración Completa con Notion**: Creación de registros con archivos adjuntos reales
- ✅ **Cola de Procesamiento**: Manejo eficiente de múltiples imágenes simultáneas
- ✅ **Arquitectura Limpia**: Clean Architecture con separación clara de capas
- ✅ **Alta Testabilidad**: 121+ tests con >85% de cobertura
- ✅ **Logging Profesional**: Sistema de logs estructurado y detallado

### 📊 Campos Extraídos Automáticamente

1. **ID_Ticket** - Identificador del ticket
2. **Deporte** - Deporte del evento (Fútbol, Baloncesto, etc.)
3. **Evento** - Nombre del partido (ej: "Lakers vs Celtics")
4. **Mercado** - Tipo de apuesta (Ganador, Over/Under, etc.)
5. **Selección** - Opción apostada
6. **Cuota** - Cuota decimal
7. **Monto_Apostado** - Importe con símbolo de moneda
8. **Ganancia_Potencial** - Ganancia esperada
9. **Estado_Apuesta** - Pendiente/Ganada/Perdida
10. **Numero_Apuestas** - Simple (1) o Combinada (2+)
11. **Fecha_Evento** - Fecha del evento
12. **Casa_Apuestas** - Nombre de la casa de apuestas

## 🏗️ Arquitectura

### Clean Architecture (Hexagonal)

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION                             │
│                   (Telegram Handlers)                        │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                     APPLICATION                              │
│              (Use Cases & Orchestration)                     │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                       DOMAIN                                 │
│               (Business Logic & Entities)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                   INFRASTRUCTURE                             │
│         (Notion, Telegram, OpenAI, Storage)                  │
└─────────────────────────────────────────────────────────────┘
```

**Beneficios**:
- 🔒 Lógica de negocio independiente de frameworks
- 🧪 Alta testabilidad con mocks
- 🔄 Fácil intercambio de adaptadores (ej: cambiar de Notion a Airtable)
- 📖 Código mantenible y legible

## 🚀 Inicio Rápido

## 📁 Estructura del Proyecto

```
botTelegramNotion/
├── main.py                        # 🎯 Punto de entrada principal (NUEVO)
├── bot_main.py                    # ⚠️ DEPRECATED
├── bot_main_v2.py                 # ⚠️ DEPRECATED
│
├── domain/                        # 🏛️ Capa de dominio
│   ├── entities/                  # Entidades de negocio
│   │   └── bet.py                 # Entidad principal: Apuesta
│   ├── value_objects/             # Value Objects
│   │   ├── bet_status.py          # Estados de apuesta
│   │   └── money.py               # Dinero con validación
│   └── repositories/              # Interfaces de repositorios (ports)
│       └── bet_repository.py
│
├── application/                   # 💼 Capa de aplicación
│   ├── use_cases/                 # Casos de uso
│   │   ├── create_bet_use_case.py
│   │   ├── process_bet_image_use_case.py
│   │   └── update_bet_status_use_case.py
│   ├── orchestration/             # Orquestadores
│   │   ├── message_processor.py   # Orquesta procesamiento de mensajes
│   │   └── command_orchestrator.py # Coordina comandos
│   └── dtos/                      # Data Transfer Objects
│       ├── bet_dto.py
│       ├── image_dto.py
│       └── message_dto.py
│
### 1. Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd botTelegramNotion

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configuración

Copia `.env.example` a `.env` y configura:

```env
# Tokens requeridos
TELEGRAM_BOT_TOKEN=tu_telegram_bot_token_aqui
NOTION_TOKEN=tu_notion_token_aqui
OPENAI_API_KEY=tu_openai_api_key_aqui
NOTION_DATABASE_ID=tu_database_id_aqui

# Opcional
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 3. Ejecutar el Bot

```bash
python main.py
```

### 4. Tests

```bash
# Todos los tests
pytest tests/ -v

# Con coverage
pytest --cov=application --cov=domain --cov=infrastructure --cov-report=html

# Tests de integración (requieren credenciales)
pytest tests/integration/ -v
```

## 💬 Uso

### Comandos Telegram

- `/start` - Iniciar el bot
- `/help` - Ver ayuda
- `/status` - Ver estadísticas

### Procesamiento de Apuestas

1. Envía una **imagen** de tu ticket
2. El bot **analiza** con IA (OpenAI GPT-4 Vision)
3. **Extrae** todos los campos automáticamente
4. **Crea registro** en Notion con imagen adjunta
5. **Responde** con detalles completos

**Ejemplo de respuesta:**

```
✅ Apuesta procesada exitosamente!

⚽ Evento: Real Madrid vs Barcelona
🎲 Tipo: Ganador Partido
📊 Cuota: 2.50
💰 Importe: $100.00
💎 Ganancia potencial: $250.00
🔄 Estado: Pendiente

🔗 Ver en Notion
```

## 📁 Estructura del Proyecto

```
botTelegramNotion/
├── main.py                        # 🚀 Punto de entrada principal
│
├── domain/                        # 🎯 Lógica de negocio
│   ├── entities/                  # Entidades (Bet)
│   ├── value_objects/             # Value Objects (Money, BetStatus)
│   ├── repositories/              # Interfaces de repositorios
│   └── services/                  # Servicios de dominio
│
├── application/                   # 🔄 Casos de uso
│   ├── use_cases/                 # Use cases
│   │   ├── create_bet.py
│   │   ├── process_bet_image.py
│   │   └── update_bet_status.py
│   ├── orchestration/             # Orquestación
│   │   ├── message_processor.py
│   │   └── command_orchestrator.py
│   └── dtos/                      # Data Transfer Objects
│
├── infrastructure/                # 🔌 Adaptadores externos
│   ├── notion/                    # Notion API
│   ├── openai/                    # OpenAI Vision
│   ├── telegram/                  # Telegram API
│   └── storage/                   # File storage
│
├── presentation/                  # 🎨 Handlers de Telegram
│   └── handlers/
│       ├── start_handler.py
│       ├── help_handler.py
│       ├── status_handler.py
│       └── image_handler.py
│
├── tests/                         # 🧪 Tests (121+)
│   ├── unit/
│   └── integration/
│
├── docs/                          # 📚 Documentación
│   ├── LOGGING.md                 # Guía de logging
│   ├── TIPSTER_RELATION_SETUP.md  # Configuración de Tipster
│   └── RELEASE_NOTES_v2.0.0.md    # Notas de versión
│
├── scripts/                       # 🛠️ Scripts de desarrollo
│   ├── debug_openai_response.py   # Debug de extracción OpenAI
│   └── validate_extraction.py     # Validación de flujo completo
│
├── storage/                       # 📦 Archivos temporales
│   └── images/                    # Imágenes temporales
│
├── CONTRIBUTING.md                # Guía de desarrollo
├── CHANGELOG.md                   # Historial de cambios
├── requirements.txt               # Dependencias
└── pytest.ini                     # Config de tests
```

## 🔧 Desarrollo

### Logs Profesionales

El proyecto usa un sistema de logging estructurado:

```bash
# Ver logs en tiempo real
tail -f storage/logs/bot.log

# Filtrar por nivel
grep "ERROR" storage/logs/bot.log
grep "🚨" storage/logs/bot.log  # CRITICAL
```

Ver [docs/LOGGING.md](docs/LOGGING.md) para guía completa.

### Convenciones de Código

- **Clean Architecture**: Separación estricta de capas
- **Type Hints**: En todas las funciones
- **Docstrings**: Formato Google style
- **Tests**: Coverage mínimo 85%
- **Commits**: Conventional Commits

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para guía completa de desarrollo.

## 📚 Documentación

- [CONTRIBUTING.md](CONTRIBUTING.md) - Guía de desarrollo
- [docs/LOGGING.md](docs/LOGGING.md) - Sistema de logging
- [CHANGELOG.md](CHANGELOG.md) - Historial de cambios

## 🤝 Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para instrucciones detalladas.

## 📄 Licencia

MIT License - Proyecto de código abierto

## 👤 Autor

**satswere**

---

⭐ **Si este proyecto te ayudó, dale una estrella en GitHub!**