# Bot de Telegram con Integración a Notion

Bot de Telegram que recibe mensajes e imágenes y los sube automáticamente a una base de datos de Notion. Implementación optimizada y funcional.

## 🚀 Funcionalidades Principales

### 📸 Recepción y Subida de Archivos
- **Recibe imágenes** desde Telegram automáticamente
- **Subida REAL a Notion** usando el proceso oficial de 3 pasos
- **Soporte múltiples formatos**: JPG, PNG, GIF, BMP, WebP, TIFF
- **Almacenamiento local temporal** para procesamiento

### 📊 Integración Completa con Notion
- **Creación de registros** en base de datos de Notion
- **Subida de archivos** con URLs públicas
- **Manejo correcto de propiedades** de la base de datos
- **Logging completo** de todas las operaciones

### 🔧 Características Técnicas
- **Manejo de errores robusto** con logging detallado
- **Configuración mediante variables de entorno**
- **Tests integrados** para validar funcionalidad

## 📋 Requisitos

- **Python 3.8+**
- **python-telegram-bot** - Interfaz con API de Telegram
- **notion-client** - Cliente oficial de Notion
- **python-dotenv** - Manejo de variables de entorno
- **aiohttp** - Peticiones HTTP asíncronas
- **Pillow** - Procesamiento de imágenes

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

# ID de la base de datos de Notion
NOTION_DATABASE_ID=tu_database_id_aqui

# Configuración opcional
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Ejecución del Bot
```bash
python bot_main.py
```

### 4. Tests de Validación
```bash
# Test de conexión a Notion
python test_notion_connection.py

# Test de subida de archivos
python test_real_upload.py
```

## 📁 Estructura del Proyecto

```
botTelegramNotion/
├── bot_main.py              # Script principal del bot
├── test_real_upload.py      # Test de subida de archivos a Notion  
├── test_notion_connection.py # Test de conexión a Notion
├── requirements.txt         # Dependencias del proyecto
├── .env.example            # Ejemplo de configuración
├── .env                    # Configuración (no incluido en Git)
├── .gitignore              # Archivos ignorados por Git
├── README.md               # Esta documentación
└── storage/                # Carpeta para archivos temporales
    ├── images/             # Imágenes descargadas
    └── logs/               # Logs de la aplicación
```

## 🚀 Uso

1. **Inicia el bot**: `python bot_main.py`
2. **Envía imágenes** al bot de Telegram
3. **Verifica** que se creen registros en tu base de datos de Notion
4. **Revisa los logs** para debug si es necesario

## 🔧 Desarrollo y Debugging

- Los logs se guardan en `bot.log` y también se muestran en consola
- Usa `DEBUG=true` en `.env` para logs más detallados
- Los tests ayudan a validar la conexión y funcionalidad

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