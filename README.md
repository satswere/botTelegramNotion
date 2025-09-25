# botTelegramNotion

Bot de Telegram en Python que recibe mensajes, fotos y archivos desde un grupo o chat y los guarda automáticamente en una base de datos de Notion usando la API oficial.

## Características

- ✅ Compatible con python-telegram-bot 22.x
- ✅ Integración con Notion API usando notion-client
- ✅ Manejo de texto, fotos y archivos
- ✅ Configuración via archivo .env
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
