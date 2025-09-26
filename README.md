# Bot de Telegram - Extractor de Imágenes y Usuarios

Bot de Telegram que extrae automáticamente imágenes y obtiene información completa de usuarios que reenvían mensajes, incluso cuando tienen configuraciones de privacidad activadas.

## 🚀 Funcionalidades Principales

### 📸 Extracción de Imágenes
- **Descarga automática** de todas las imágenes recibidas
- **Soporte múltiples formatos**: JPG, PNG, GIF, BMP, WebP, TIFF
- **Nombres únicos** con timestamp para evitar conflictos
- **Metadatos completos**: resolución, tamaño, tipo de archivo

### 👤 Identificación de Usuarios Reenviados
- **Usuarios públicos**: ID, username, nombre completo
- **Usuarios privados**: nombre visible + identificador único hash
- **Canales y grupos**: ID, título, username
- **Compatibilidad total** con API moderna y legacy de Telegram

### 📊 Información JSON Completa
- Datos completos del mensaje (fecha, ID, contenido)
- Información del remitente actual
- Detalles del chat donde se recibe
- **Análisis completo de reenvío** con múltiples métodos de detección
- Identificadores únicos para rastreo

## 🛠️ Tecnologías

- **Python 3.8+**
- **python-telegram-bot** - Interfaz con API de Telegram
- **python-dotenv** - Manejo de variables de entorno
- **pathlib** - Manejo de archivos
- **hashlib** - Generación de identificadores únicos

## ⚙️ Configuración

### 1. Variables de Entorno
```env
TELEGRAM_BOT_TOKEN=tu_token_aqui
```

### 2. Instalación
```bash
pip install python-telegram-bot python-dotenv
```

### 3. Ejecución
```bash
python bot_test.py
```

## 🔧 Uso

### Comandos del Bot
- `/start` - Información de bienvenida
- Envío de **cualquier mensaje** - Procesamiento automático
- Envío de **imágenes** - Descarga + análisis completo

### Tipos de Identificación
- **Usuario Público**: `@username (ID: 123456789)`
- **Usuario Privado**: `Nombre (privado)` + `ID: PRIVATE_hash_DATE`
- **Canal**: `@canal (ID: -1001234567)`

## 📁 Estructura
```
├── bot_test.py              # Bot principal
├── .env                     # Token de Telegram
├── requirements.txt         # Dependencias
└── imagenes_recibidas/     # Imágenes descargadas
```
- ✅ Confirmación automática en Telegram
- ✅ Código limpio y bien comentado
- ✅ Logging configurable
- ✅ Manejo de errores

## Campos de la base de datos de Notion

El bot guarda la siguiente información en Notion:

- **Título**: Título generado automáticamente basado en el contenido
- **Tipo**: Tipo de mensaje (Texto, Foto, Archivo, Otro)
- **Fecha**: Fecha y hora de recepción del mensaje
- **Usuario**: Nombre de usuario de Telegram
- **URL**: Enlace al archivo (para fotos y documentos)
- **Texto adicional**: Contenido completo del mensaje y metadatos

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/satswere/botTelegramNotion.git
cd botTelegramNotion
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Configura las variables de entorno:
```bash
cp .env.example .env
```

4. Edita el archivo `.env` con tus credenciales:
```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram_aqui
NOTION_TOKEN=tu_token_de_notion_aqui
NOTION_DATABASE_ID=tu_id_de_base_de_datos_notion_aqui
LOG_LEVEL=INFO
```

## Configuración de Notion

1. Crea una integración en Notion:
   - Ve a https://www.notion.so/my-integrations
   - Crea una nueva integración
   - Copia el token de integración

2. Crea una base de datos en Notion con las siguientes columnas:
   - **Título** (Title)
   - **Tipo** (Select): opciones "Texto", "Foto", "Archivo", "Otro"
   - **Fecha** (Date)
   - **Usuario** (Text)
   - **URL** (URL)
   - **Texto adicional** (Text)

3. Comparte la base de datos con tu integración:
   - Abre tu base de datos en Notion
   - Haz clic en "Share" → "Add people"
   - Busca tu integración y agrégala

4. Copia el ID de la base de datos desde la URL de Notion

## Configuración del Bot de Telegram

1. Crea un bot con @BotFather en Telegram
2. Obtén el token del bot
3. Agrégalo a tu archivo `.env`

## Uso

1. Ejecuta el bot:
```bash
python bot.py
```

2. En Telegram, busca tu bot y envíale:
   - `/start` - Mensaje de bienvenida
   - `/help` - Ayuda sobre comandos
   - Cualquier texto, foto o archivo

3. El bot confirmará cuando haya guardado exitosamente en Notion

## Estructura del Proyecto

```
botTelegramNotion/
├── bot.py              # Aplicación principal del bot
├── requirements.txt    # Dependencias de Python
├── .env.example       # Ejemplo de configuración
├── .gitignore         # Archivos ignorados por Git
└── README.md          # Este archivo
```

## Dependencias

- `python-telegram-bot==22.4` - Biblioteca de Telegram Bot API
- `notion-client==2.2.1` - Cliente oficial de Notion API
- `python-dotenv==1.0.1` - Manejo de variables de entorno
- `requests==2.32.3` - Biblioteca para peticiones HTTP

## Licencia

Este proyecto está bajo la Licencia MIT.
