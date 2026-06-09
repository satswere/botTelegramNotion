# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [3.0.0] - 2025-10-16

### 🎯 Arquitectura Hexagonal Completa

Gran refactorización del proyecto implementando arquitectura hexagonal (Ports & Adapters) con Clean Architecture.

#### Added
- **main.py**: Nuevo punto de entrada unificado con composition root
  - Dependency injection completa
  - Lifecycle management (startup/shutdown callbacks)
  - Queue processing para procesamiento secuencial de imágenes
  - Separación clara: Config → Infrastructure → Application → Presentation

- **Domain Layer**: Lógica de negocio pura
  - Entities: `Bet`, `BetImage`, `ForwardMetadata`
  - Value Objects: `Money`, `Odds`, `BetStatus`
  - Repository interfaces (Ports): `IBetRepository`, `IImageAnalyzer`, `IFileStorage`, `IMessageExtractor`
  - Domain Services: `BetValidator`

- **Application Layer**: Casos de uso y orquestación
  - Use Cases: `CreateBetUseCase`, `UpdateBetStatusUseCase`, `ProcessBetImageUseCase`
  - DTOs: `BetDTO`, `CreateBetDTO`, `UpdateBetDTO`, `ImageDTO`, `MessageDTO`
  - Orchestrators: `MessageProcessor`, `CommandOrchestrator`

- **Infrastructure Layer**: Adaptadores a servicios externos
  - `NotionBetRepository`: Persistencia en Notion
  - `TelegramMessageExtractor`: Extracción de datos de Telegram
  - `LocalFileStorage`: Almacenamiento local de archivos
  - `OpenAIImageAnalyzer`: Análisis de imágenes con GPT-4 Vision

- **Presentation Layer**: Handlers de Telegram
  - `StartHandler`, `HelpHandler`, `StatusHandler`, `ImageHandler`
  - Separación de responsabilidades de presentación

- **Tests**: Suite completa de tests unitarios
  - 121 tests unitarios (domain + application + infrastructure + orchestration)
  - 3 tests de integración
  - Configuración pytest con cobertura

#### Changed
- **Estructura del proyecto**: De monolito (1,187 líneas) a arquitectura en capas (4 layers)
- **Acoplamiento**: De alto (dependencias directas a APIs) a bajo (inversión de dependencias)
- **Testabilidad**: De 0% a ~50% de cobertura
- **Complejidad ciclomática**: De 7.6 a ~3.2

#### Removed
- `bot_main.py` (1,056 líneas): Código legacy monolítico
- `bot_main_v2.py` (263 líneas): Versión intermedia de refactorización
- `testingApi/`: Carpeta de pruebas legacy (migrado a infrastructure/openai/)
- `test_notion_connection.py`: Tests legacy (migrado a tests/integration/)
- `test_real_upload.py`: Tests legacy (migrado a tests/integration/)
- Documentación temporal de refactorización:
  - `ARCHITECTURE_ANALYSIS.md`
  - `ARCHITECTURE_DIAGRAM.md`
  - `FOLDER_STRUCTURE.md`
  - `PROGRESS.md`
  - `REFACTORING_ROADMAP.md`
  - `REFACTOR_COMPLETE.md`
  - `REFACTOR_STATUS.md`
  - `FINAL_COMMIT_SUMMARY.md`
  - `INFRASTRUCTURE_IMPROVEMENTS.md`

#### Fixed
- Error handling robusto en todos los adaptadores
- Logging consistente con niveles DEBUG/INFO/WARNING/ERROR
- Exception chaining para preservar stack traces
- Validación de configuración al inicio

#### Performance
- Tests ejecutan en 0.85s (121 tests)
- Processing queue evita sobrecarga de APIs
- Async/await en toda la aplicación

#### Security
- Validación de variables de entorno al inicio 
- Separación de secretos en .env
- Type hints completos para seguridad de tipos

---

## [2.0.0] - 2024

### 🧩 Subida Real a Notion | Reenvíos Inteligentes | Análisis con OpenAI

#### Added
- **Subida real a Notion**: Flujo oficial de 3 pasos
  - `file_uploads` → upload multipart → `pages.create`
  - Archivos adjuntos reales (no enlaces externos)
  
- **Análisis de imágenes con OpenAI Vision**
  - Extracción automática de datos de tickets (Bet365)
  - JSON estructurado: Evento, Mercado, Selección, Cuota, Monto, Ganancia Potencial, Estado
  - Prompt especializado para apuestas
  
- **Detección avanzada de reenvíos**
  - Compatibilidad con API moderna (`forward_origin`) y legacy
  - Hash MD5 único de origen para usuarios privados
  - Estructura completa de metadata

- **Comandos de Telegram**
  - `/start`: Mensaje de bienvenida
  - `/help`: Ayuda detallada
  - `/status`: Estado del sistema

#### Changed
- Timestamp granular en archivos: `photo_YYYYmmdd_HHMMSS_mmm.ext`
- Propiedades Notion alineadas con nombres descriptivos
- Logging consistente (archivo + consola)
- Parsing tolerante de números (cuota, importe)

#### Removed
- Scripts `bot_*` antiguos eliminados
- Código duplicado y legacy

---

## [1.0.0] - 2024 (Inicial)

### Primera versión funcional

#### Added
- Bot básico de Telegram
- Conexión a Notion
- Procesamiento de imágenes
- Almacenamiento local

---

## Leyenda de Tipos de Cambios

- **Added**: Nuevas funcionalidades
- **Changed**: Cambios en funcionalidades existentes
- **Deprecated**: Funcionalidades marcadas como obsoletas
- **Removed**: Funcionalidades eliminadas
- **Fixed**: Correcciones de bugs
- **Security**: Mejoras de seguridad
- **Performance**: Mejoras de rendimiento

---

[3.0.0]: https://github.com/satswere/botTelegramNotion/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/satswere/botTelegramNotion/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/satswere/botTelegramNotion/releases/tag/v1.0.0
