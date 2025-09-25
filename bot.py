#!/usr/bin/env python3
"""
Bot de Telegram que guarda mensajes, fotos y archivos en una base de datos de Notion.

Funcionalidades:
- Recibe texto, fotos y archivos desde Telegram
- Los guarda en Notion con campos: Título, Tipo, Fecha, Usuario, URL, Texto adicional
- Envía confirmación al usuario tras guardar exitosamente
"""

import logging
import os
from datetime import datetime
from typing import Optional
import asyncio

from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from notion_client import Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración del logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL, logging.INFO)
)
logger = logging.getLogger(__name__)


class NotionTelegramBot:
    """Bot principal que integra Telegram con Notion"""
    
    def __init__(self):
        """Inicializa el bot con tokens y configuración"""
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        # Validar que todas las variables estén configuradas
        if not all([self.telegram_token, self.notion_token, self.database_id]):
            raise ValueError("Faltan variables de entorno. Revisa el archivo .env")
        
        # Inicializar clientes
        self.notion = Client(auth=self.notion_token)
        
        # Verificar conexión con Notion
        self._verify_notion_connection()
    
    def _verify_notion_connection(self):
        """Verifica que la conexión con Notion funcione correctamente"""
        try:
            # Intentar obtener información de la base de datos
            self.notion.databases.retrieve(database_id=self.database_id)
            logger.info("Conexión con Notion verificada exitosamente")
        except Exception as e:
            logger.error(f"Error al conectar con Notion: {e}")
            raise
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /start"""
        welcome_message = (
            "¡Hola! 👋\n\n"
            "Soy un bot que guarda tus mensajes en Notion.\n"
            "Puedes enviarme:\n"
            "• Texto\n"
            "• Fotos\n"
            "• Archivos\n\n"
            "Todo se guardará automáticamente en tu base de datos de Notion."
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja el comando /help"""
        help_message = (
            "Comandos disponibles:\n"
            "/start - Mensaje de bienvenida\n"
            "/help - Mostrar esta ayuda\n\n"
            "Simplemente envía cualquier mensaje, foto o archivo "
            "y lo guardaré en Notion automáticamente."
        )
        await update.message.reply_text(help_message)
    
    def _get_message_type(self, message: Message) -> str:
        """Determina el tipo de mensaje recibido"""
        if message.photo:
            return "Foto"
        elif message.document:
            return "Archivo"
        elif message.text:
            return "Texto"
        else:
            return "Otro"
    
    def _get_file_url(self, message: Message) -> Optional[str]:
        """Obtiene la URL del archivo si está disponible"""
        if message.photo:
            # Obtener la foto de mayor resolución
            return message.photo[-1].file_id
        elif message.document:
            return message.document.file_id
        return None
    
    def _get_title(self, message: Message) -> str:
        """Genera un título para el mensaje basado en su contenido"""
        msg_type = self._get_message_type(message)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        if message.text and len(message.text) > 0:
            # Usar las primeras palabras del texto como título
            title = message.text[:50]
            if len(message.text) > 50:
                title += "..."
            return f"{title}"
        elif message.caption:
            # Usar el caption si está disponible
            caption = message.caption[:50]
            if len(message.caption) > 50:
                caption += "..."
            return f"{caption}"
        else:
            # Título por defecto basado en tipo y fecha
            return f"{msg_type} - {timestamp}"
    
    def _get_additional_text(self, message: Message) -> str:
        """Obtiene texto adicional del mensaje"""
        additional_text = ""
        
        if message.text:
            additional_text = message.text
        elif message.caption:
            additional_text = message.caption
        
        # Agregar información del archivo si existe
        if message.document:
            file_info = f"\nArchivo: {message.document.file_name or 'Sin nombre'}"
            file_info += f"\nTamaño: {message.document.file_size or 'Desconocido'} bytes"
            additional_text += file_info
        elif message.photo:
            additional_text += "\nTipo: Imagen"
        
        return additional_text
    
    async def save_to_notion(self, message: Message) -> bool:
        """Guarda el mensaje en la base de datos de Notion"""
        try:
            # Obtener información del usuario
            user = message.from_user
            username = user.username or f"{user.first_name} {user.last_name or ''}".strip()
            
            # Preparar datos para Notion
            notion_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Título": {
                        "title": [{"text": {"content": self._get_title(message)}}]
                    },
                    "Tipo": {
                        "select": {"name": self._get_message_type(message)}
                    },
                    "Fecha": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "Usuario": {
                        "rich_text": [{"text": {"content": username}}]
                    },
                    "Texto adicional": {
                        "rich_text": [{"text": {"content": self._get_additional_text(message)}}]
                    }
                }
            }
            
            # Agregar URL si existe un archivo
            file_url = self._get_file_url(message)
            if file_url:
                notion_data["properties"]["URL"] = {
                    "url": f"https://api.telegram.org/file/bot{self.telegram_token}/{file_url}"
                }
            
            # Crear página en Notion
            response = self.notion.pages.create(**notion_data)
            logger.info(f"Mensaje guardado en Notion: {response['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar en Notion: {e}")
            return False
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todos los tipos de mensajes (texto, fotos, archivos)"""
        message = update.message
        
        # Mostrar que el bot está procesando
        await message.reply_text("Guardando en Notion... ⏳")
        
        # Intentar guardar en Notion
        success = await self.save_to_notion(message)
        
        if success:
            await message.reply_text("✅ Guardado exitosamente en Notion!")
        else:
            await message.reply_text("❌ Error al guardar en Notion. Inténtalo de nuevo.")
    
    def run(self):
        """Inicia el bot"""
        # Crear aplicación
        application = Application.builder().token(self.telegram_token).build()
        
        # Agregar manejadores
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        
        # Manejar mensajes de texto
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Manejar fotos
        application.add_handler(MessageHandler(filters.PHOTO, self.handle_message))
        
        # Manejar documentos/archivos
        application.add_handler(MessageHandler(filters.Document.ALL, self.handle_message))
        
        logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
        
        # Iniciar el bot
        application.run_polling()


def main():
    """Función principal"""
    try:
        bot = NotionTelegramBot()
        bot.run()
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        print("Por favor, copia .env.example a .env y configura las variables necesarias.")
    except KeyboardInterrupt:
        logger.info("Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")


if __name__ == "__main__":
    main()