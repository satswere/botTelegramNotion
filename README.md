# Bot de Telegram con Integración a Notion

Bot de Telegram que recibe mensajes e imágenes y los sube automáticamente a una base de datos de Notion. Implementación con **Arquitectura Hexagonal** (Clean Architecture).

## 🏗️ Arquitectura

El proyecto sigue los principios de **Hexagonal Architecture** (Ports & Adapters):

- **Domain Layer**: Lógica de negocio pura (Bet, Money, BetStatus)
- **Application Layer**: Casos de uso y orquestación
- **Infrastructure Layer**: Adaptadores externos (Notion, Telegram, OpenAI, Storage)
- **Presentation Layer**: Handlers de Telegram

## 🚀 Funcionalidades Principales

### 📸 Recepción y Análisis de Imágenes
- **Recibe imágenes** desde Telegram automáticamente
- **Análisis con IA** (OpenAI Vision) para extraer información de apuestas
- **Subida REAL a Notion** usando el proceso oficial de 3 pasos
- **Soporte múltiples formatos**: JPG, PNG, GIF, BMP, WebP, TIFF
- **Cola de procesamiento** para manejo eficiente de múltiples imágenes

### 📊 Integración Completa con Notion
- **Creación de registros** en base de datos de Notion
- **Subida de archivos** con URLs públicas
- **Propiedades estructuradas**: evento, cuota, stake, estado, etc.
- **Actualización de estado** de apuestas
- **Consulta de estadísticas** y listado de apuestas

### 🔧 Características Técnicas
- **Arquitectura hexagonal** con separación clara de capas
- **Dependency Injection** para máxima testabilidad
- **Manejo de errores robusto** con logging detallado
- **Configuración mediante variables de entorno**
- **Tests unitarios y de integración** (121+ tests)
- **Type hints** completos para mejor mantenibilidad

## 📋 Requisitos

- **Python 3.8+**
- **python-telegram-bot** - Interfaz con API de Telegram
- **notion-client** - Cliente oficial de Notion
- **openai** - Cliente de OpenAI para análisis de imágenes
- **python-dotenv** - Manejo de variables de entorno
- **aiohttp** - Peticiones HTTP asíncronas
- **Pillow** - Procesamiento de imágenes
- **pytest** - Framework de testing

## ⚙️ Configuración

### 1. Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configuración de Variables de Entorno
Copia el archivo `.env.example` a `.env` y configura tus tokens:

```env
# Tokens requeridos
TELEGRAM_BOT_TOKEN=tu_telegram_bot_token_aqui
NOTION_TOKEN=tu_notion_token_aqui
OPENAI_API_KEY=tu_openai_api_key_aqui

# ID de la base de datos de Notion
NOTION_DATABASE_ID=tu_database_id_aqui

# Configuración opcional
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Ejecución del Bot

**Nuevo punto de entrada unificado:**
```bash
python main.py
```

⚠️ **Deprecated (se eliminará pronto):**
- ~~`python bot_main.py`~~ (legacy)
- ~~`python bot_main_v2.py`~~ (arquitectura v2)

### 4. Tests

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar solo tests unitarios
pytest tests/unit/ -v

# Ejecutar con coverage
pytest tests/ --cov=application --cov=domain --cov=infrastructure

# Tests de integración (requieren credenciales configuradas)
pytest tests/integration/ -v
```

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
├── infrastructure/                # 🔌 Capa de infraestructura
│   ├── notion/                    # Adapter de Notion
│   │   └── notion_repository.py
│   ├── telegram/                  # Adapter de Telegram
│   │   └── telegram_extractor.py
│   ├── openai/                    # Adapter de OpenAI
│   │   └── openai_analyzer.py
│   └── storage/                   # Adapter de almacenamiento
│       └── file_storage.py
│
├── presentation/                  # 🎨 Capa de presentación
│   └── handlers/                  # Handlers de Telegram
│       ├── start_handler.py
│       ├── help_handler.py
│       ├── status_handler.py
│       └── image_handler.py
│
├── tests/                         # 🧪 Tests
│   ├── unit/                      # Tests unitarios (121 tests)
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   └── integration/               # Tests de integración
│
├── storage/                       # 📁 Almacenamiento temporal
│   ├── images/                    # Imágenes descargadas
│   └── logs/                      # Logs de la aplicación
│
├── requirements.txt               # Dependencias
├── pytest.ini                     # Configuración de pytest
├── .env.example                   # Ejemplo de configuración
└── README.md                      # Esta documentación
```

## 🚀 Uso

### Comandos del Bot

Una vez iniciado el bot, puedes usar los siguientes comandos en Telegram:

- `/start` - Iniciar el bot y ver mensaje de bienvenida
- `/help` - Mostrar ayuda y comandos disponibles
- `/status` - Ver estadísticas de apuestas y estado del sistema

### Envío de Apuestas

1. **Envía una imagen** de tu apuesta al bot
2. El bot **descarga y analiza** la imagen con IA
3. **Extrae automáticamente**: evento, cuota, stake, etc.
4. **Crea un registro** en Notion con toda la información
5. **Responde con confirmación** y detalles de la apuesta

### Ejemplo de Flujo

```
Usuario → [Envía imagen de apuesta]
Bot     → ⏳ Procesando imagen...
Bot     → ✅ Apuesta procesada exitosamente!
          📊 Evento: Lakers vs Warriors
          💰 Stake: $100.00
          📈 Cuota: 2.50
          🔗 Ver en Notion
```

## 🧪 Testing

El proyecto cuenta con **121+ tests** organizados en:

### Tests Unitarios
```bash
# Domain layer tests
pytest tests/unit/domain/ -v

# Application layer tests  
pytest tests/unit/application/ -v

# Infrastructure layer tests
pytest tests/unit/infrastructure/ -v
```

### Tests de Integración
```bash
# Requieren credenciales configuradas
pytest tests/integration/ -v
```

### Coverage
```bash
# Generar reporte de cobertura
pytest tests/ --cov=application --cov=domain --cov=infrastructure --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html  # Linux/Mac
start htmlcov/index.html # Windows
```

## 🔧 Desarrollo y Debugging

### Logs
- Los logs se guardan en `bot.log`
- También se muestran en consola con colores
- Usa `LOG_LEVEL=DEBUG` en `.env` para más detalle

### Estructura de Logs
```
2024-01-01 10:00:00 - INFO - 🚀 Starting bot...
2024-01-01 10:00:01 - INFO - ✅ Infrastructure layer ready
2024-01-01 10:00:02 - INFO - ✅ Application layer ready
2024-01-01 10:00:03 - INFO - 🤖 Bot is running
```

## 📚 Documentación Adicional

- **ARCHITECTURE_ANALYSIS.md**: Análisis detallado de la arquitectura
- **FOLDER_STRUCTURE.md**: Estructura completa del proyecto
- **REFACTOR_COMPLETE.md**: Resumen de refactorizaciones
- **INFRASTRUCTURE_IMPROVEMENTS.md**: Mejoras de infraestructura

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 👤 Autor

**satswere**

---

⭐ Si este proyecto te fue útil, considera darle una estrella en GitHub!

## 📋 Campos de la Base de Datos de Notion

El bot crea registros con los siguientes campos:

- **Nombre**: Texto con el nombre del archivo
- **Fecha**: Fecha de creación del registro
- **Archivo**: Archivo subido (imagen)
- **Usuario**: Información del usuario de Telegram
- **Chat ID**: ID del chat de Telegram
- **Message ID**: ID del mensaje

## 📄 Licencia

Proyecto de uso personal/educativo.