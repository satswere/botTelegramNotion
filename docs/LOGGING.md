# Sistema de Logging Profesional

Guía completa del sistema de logging del proyecto Bot Telegram → Notion.

## 📋 Tabla de Contenidos

- [Filosofía](#filosofía)
- [Configuración](#configuración)
- [Niveles de Log](#niveles-de-log)
- [Formato Estándar](#formato-estándar)
- [Emojis y Convenciones](#emojis-y-convenciones)
- [Mejores Prácticas](#mejores-prácticas)
- [Ejemplos por Capa](#ejemplos-por-capa)
- [Troubleshooting](#troubleshooting)

## 🎯 Filosofía

### Principios

1. **Claridad**: Cada log debe ser auto-explicativo
2. **Contexto**: Incluir datos relevantes para diagnóstico
3. **Consistencia**: Formato uniforme en todo el proyecto
4. **Sensibilidad**: NO loguear datos sensibles (tokens, passwords)
5. **Performance**: Usar logging asíncrono cuando sea posible

### Objetivos

- ✅ Facilitar debugging en desarrollo
- ✅ Monitorear salud del sistema en producción
- ✅ Auditar operaciones críticas
- ✅ Diagnosticar errores rápidamente

## ⚙️ Configuración

### Setup Básico

```python
import logging

logger = logging.getLogger(__name__)
```

### Configuración Global (`main.py`)

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()  # Console
    ]
)
```

### Niveles por Entorno

```python
# Desarrollo
logging.getLogger().setLevel(logging.DEBUG)

# Producción  
logging.getLogger().setLevel(logging.INFO)

# Debug específico
logging.getLogger('infrastructure.notion').setLevel(logging.DEBUG)
```

## 📊 Niveles de Log

### DEBUG (🔍)

**Cuándo usar**: Información muy detallada para debugging

```python
logger.debug(f"🔍 Buscando apuesta: {bet_id}")
logger.debug(f"🔍 Request params: {params}")
logger.debug(f"🔍 Filename sanitizado: '{original}' -> '{sanitized}'")
```

**Características**:
- Flujo interno de funciones
- Valores de variables intermedias
- Decisiones condicionales
- NO debe aparecer en producción

### INFO (✅ ℹ️ 📊)

**Cuándo usar**: Eventos normales importantes

```python
logger.info(f"✅ Apuesta guardada exitosamente: {bet_id}")
logger.info(f"📸 Procesando imagen de usuario {user_id}")
logger.info(f"🚀 Bot iniciado correctamente")
```

**Características**:
- Inicio/fin de operaciones importantes
- Hitos del flujo principal
- Confirmaciones de acciones
- Default en producción

### WARNING (⚠️)

**Cuándo usar**: Situación anormal pero manejable

```python
logger.warning(f"⚠️ No se encontró Monto_Apostado en analyzed_data")
logger.warning(f"⚠️ Reintentando operación ({attempt}/{max_attempts})")
logger.warning(f"⚠️ Campo opcional vacío: {field_name}")
```

**Características**:
- Datos faltantes no críticos
- Configuración subóptima
- Reintentos automáticos
- Valores por defecto aplicados

### ERROR (❌)

**Cuándo usar**: Error que impide completar una operación

```python
logger.error(f"❌ Error guardando apuesta: {e}", exc_info=True)
logger.error(f"❌ API de Notion respondió con código {status_code}")
logger.error(f"❌ No se pudo parsear JSON: {raw_data}")
```

**Características**:
- Excepciones capturadas
- Fallos de API externas
- Validaciones fallidas
- SIEMPRE incluir `exc_info=True` para traceback

### CRITICAL (🚨)

**Cuándo usar**: Fallo crítico que afecta todo el sistema

```python
logger.critical(f"🚨 No se pudo conectar a base de datos Notion")
logger.critical(f"🚨 Token de Telegram inválido - bot detenido")
logger.critical(f"🚨 Disco lleno - no se pueden guardar archivos")
```

**Características**:
- Sistema no puede continuar
- Requiere intervención inmediata
- Datos de configuración críticos faltantes

## 🎨 Formato Estándar

### Template General

```python
# [EMOJI] [ACCIÓN] [CONTEXTO]: [DETALLES]

logger.info(f"✅ Apuesta guardada exitosamente: {bet_id}")
#           ↑  ↑                              ↑
#         Emoji Acción                    Contexto
```

### Emojis por Tipo

| Categoría | Emojis | Uso |
|-----------|--------|-----|
| **Éxito** | ✅ | Operación completada |
| **Proceso** | 📸 🔄 📦 📨 | En progreso |
| **Info** | ℹ️ 📊 📋 | Información general |
| **Debug** | 🔍 🔬 | Debugging |
| **Warning** | ⚠️ | Advertencias |
| **Error** | ❌ | Errores |
| **Critical** | 🚨 | Crítico |
| **Usuario** | 👤 👋 | Acciones de usuario |
| **Red** | 🌐 🔌 | Conectividad |
| **Archivo** | 💾 📁 🗑️ | Operaciones de archivo |
| **Tiempo** | ⏱️ ⏰ | Timeouts, duración |
| **Dinero** | 💰 💵 💸 | Operaciones financieras |

## 💡 Mejores Prácticas

### ✅ HACER

```python
# 1. Incluir contexto relevante
logger.info(f"✅ Archivo subido: {filename} ({file_size} bytes)")

# 2. Usar f-strings para formateo
logger.error(f"❌ Error procesando apuesta {bet_id}: {e}")

# 3. Incluir stack trace en errores
logger.error(f"❌ Excepción inesperada: {e}", exc_info=True)

# 4. Loguear inicio y fin de operaciones importantes
logger.info("📸 Iniciando procesamiento de imagen")
# ... operación ...
logger.info("✅ Imagen procesada exitosamente")

# 5. Usar variables descriptivas
user_id = update.effective_user.id
logger.info(f"👋 Usuario {user_id} inició bot")
```

### ❌ NO HACER

```python
# 1. NO usar print
print("Apuesta guardada")  # ❌ Usar logger.info()

# 2. NO loguear datos sensibles
logger.info(f"Token: {NOTION_TOKEN}")  # ❌ NUNCA
logger.info(f"Password: {password}")    # ❌ NUNCA

# 3. NO loguear en bucles intensivos
for item in millions_of_items:
    logger.debug(f"Processing {item}")  # ❌ Overhead masivo

# 4. NO usar logs genéricos
logger.info("Error!")  # ❌ Sin contexto
logger.error("Something went wrong")  # ❌ Inútil

# 5. NO duplicar mensajes
logger.info("Processing...")
logger.info("Processing...")  # ❌ Redundante
```

### 🔒 Datos Sensibles

**NUNCA loguear**:
- Tokens de API (`TELEGRAM_BOT_TOKEN`, `NOTION_TOKEN`, `OPENAI_API_KEY`)
- Credenciales de usuario
- Información personal identificable (PII)
- Datos financieros completos

**Sanitizar si es necesario**:

```python
# ✅ CORRECTO
logger.info(f"🔐 Usuario autenticado: {user_id}")
logger.info(f"💰 Apuesta creada por valor de {amount} {currency}")

# ❌ INCORRECTO
logger.info(f"Token completo: {api_token}")
logger.info(f"Tarjeta: {credit_card_number}")
```

## 📂 Ejemplos por Capa

### Domain Layer

```python
# domain/entities/bet.py
logger = logging.getLogger(__name__)

class Bet:
    def validate(self):
        logger.debug(f"🔍 Validando apuesta: {self.id}")
        
        if not self.odds:
            logger.warning(f"⚠️ Cuota no especificada para apuesta {self.id}")
            
        logger.debug(f"✅ Apuesta {self.id} válida")
```

### Application Layer

```python
# application/use_cases/create_bet.py
logger = logging.getLogger(__name__)

async def execute(self, dto: CreateBetDTO):
    logger.info(f"📝 Creando apuesta: {dto.event}")
    
    try:
        bet_id = await self._repository.save(bet_data)
        logger.info(f"✅ Apuesta creada: {bet_id}")
        return bet_id
        
    except ValidationError as e:
        logger.warning(f"⚠️ Validación fallida: {e}")
        raise
        
    except Exception as e:
        logger.error(f"❌ Error creando apuesta: {e}", exc_info=True)
        raise
```

### Infrastructure Layer

```python
# infrastructure/notion/notion_bet_repository.py
logger = logging.getLogger(__name__)

async def save(self, bet_data: Dict) -> str:
    logger.debug(f"💾 Guardando apuesta en Notion: {bet_data.get('title')}")
    
    try:
        response = self.client.pages.create(...)
        page_id = response["id"]
        
        logger.info(f"✅ Apuesta guardada en Notion: {page_id}")
        return page_id
        
    except APIResponseError as e:
        logger.error(f"❌ Error de API Notion [{e.code}]: {e}", exc_info=True)
        raise
        
    except Exception as e:
        logger.error(f"❌ Error inesperado guardando apuesta: {e}", exc_info=True)
        raise
```

### Presentation Layer

```python
# presentation/handlers/image_handler.py
logger = logging.getLogger(__name__)

async def handle(self, update: Update, context):
    user = update.effective_user
    logger.info(f"📸 Imagen recibida de usuario {user.id}")
    
    try:
        await self._processor.process(update.message)
        logger.info(f"✅ Imagen procesada exitosamente")
        
    except ProcessingError as e:
        logger.error(f"❌ Error procesando imagen: {e}")
        await update.message.reply_text("Error procesando imagen")
```

## 🔧 Troubleshooting

### Problema: Logs duplicados

```python
# ❌ CAUSA
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())  # Duplica handlers

# ✅ SOLUCIÓN
logger = logging.getLogger(__name__)  # Sin addHandler
```

### Problema: Logs no aparecen

```python
# Verificar nivel
logging.getLogger().setLevel(logging.DEBUG)

# Verificar que el logger tenga nombre
logger = logging.getLogger(__name__)  # ✅
logger = logging.getLogger()          # ⚠️ Root logger
```

### Problema: Logs muy verbosos en producción

```python
# Configurar por módulo
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('infrastructure').setLevel(logging.INFO)
```

## 📈 Monitoring en Producción

### Análisis de Logs

```bash
# Ver solo errores
grep "❌" bot.log

# Ver actividad de un usuario
grep "Usuario 123456" bot.log

# Ver últimas 50 líneas
tail -n 50 bot.log

# Seguir logs en tiempo real
tail -f bot.log
```

### Métricas Clave

```bash
# Contar errores por tipo
grep "❌" bot.log | cut -d'-' -f4 | sort | uniq -c

# Apuestas procesadas hoy
grep "✅ Apuesta guardada" bot.log | grep "$(date +%Y-%m-%d)" | wc -l

# Usuarios activos
grep "👋 Usuario" bot.log | cut -d' ' -f8 | sort -u | wc -l
```

## 🎯 Checklist de Logging

Al implementar nueva funcionalidad, verificar:

- [ ] Logger inicializado: `logger = logging.getLogger(__name__)`
- [ ] Nivel apropiado usado (DEBUG/INFO/WARNING/ERROR/CRITICAL)
- [ ] Emoji descriptivo incluido
- [ ] Contexto suficiente (IDs, valores relevantes)
- [ ] NO se loguean datos sensibles
- [ ] Errores incluyen `exc_info=True`
- [ ] Mensajes son claros y accionables
- [ ] Formato consistente con el resto del proyecto

---

**Última actualización**: Diciembre 2025  
**Mantenido por**: Equipo de Desarrollo
