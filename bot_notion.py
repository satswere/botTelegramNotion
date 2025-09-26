#!/usr/bin/env python3
"""
Bot de Telegram - Extractor de Imágenes e Información de Usuarios con integración a Notion
Funcionalidades principales:
- Descarga automática de imágenes
- Extracción completa de información de mensajes reenviados
- Identificación de usuarios originales (incluso con privacidad)
- Envío automático a base de datos de Notion
"""

import logging
import os
import sys
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Configuración del logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Agregar el directorio src al path para importar módulos
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from services.notion_service import get_notion_service
    NOTION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Notion no disponible: {e}")
    NOTION_AVAILABLE = False

# Cargar variables de entorno
load_dotenv()


class TelegramImageBotWithNotion:
    """Bot de Telegram que extrae imágenes e información y las envía a Notion"""
    
    def __init__(self):
        """Inicializa el bot con token y servicio de Notion"""
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not self.telegram_token:
            raise ValueError("Falta TELEGRAM_BOT_TOKEN en el archivo .env")
        
        # Crear carpeta para imágenes recibidas
        self.images_folder = Path("imagenes_recibidas")
        self.images_folder.mkdir(exist_ok=True)
        logger.info(f"Carpeta de imágenes: {self.images_folder.absolute()}")
        
        # Inicializar servicio de Notion
        try:
            if NOTION_AVAILABLE:
                self.notion_service = get_notion_service()
                # Probar conexión
                if self.notion_service.test_connection():
                    logger.info("✅ Notion integrado correctamente")
                else:
                    logger.warning("⚠️ Notion configurado pero conexión falló")
            else:
                self.notion_service = None
        except Exception as e:
            logger.warning(f"⚠️ Notion no disponible: {e}")
            self.notion_service = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        notion_status = "✅ Conectado" if (self.notion_service and self.notion_service.test_connection()) else "❌ No disponible"
        
        welcome_message = (
            "🤖 Bot Extractor de Imágenes y Usuarios con Notion\n\n"
            "Funcionalidades:\n"
            "📸 Descarga automática de imágenes\n"
            "🔄 Identificación de mensajes reenviados\n"
            "👤 Extracción de información de usuarios originales\n"
            "📊 Información completa en JSON\n"
            f"📝 Notion: {notion_status}\n\n"
            "Envía cualquier imagen o mensaje reenviado para procesarlo.\n"
            "Si es un mensaje reenviado de un tipster, se guardará automáticamente en Notion."
        )
        await update.message.reply_text(welcome_message)
    
    async def test_notion_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /test_notion para probar la conexión"""
        if not self.notion_service:
            await update.message.reply_text("❌ Notion no está configurado")
            return
        
        try:
            if self.notion_service.test_connection():
                db_info = self.notion_service.get_database_info()
                db_title = "Base de datos de apuestas" 
                if db_info and isinstance(db_info, dict) and "title" in db_info:
                    db_title = db_info["title"][0]["plain_text"] if db_info["title"] else "Base de datos"
                
                await update.message.reply_text(f"✅ Conexión exitosa con Notion\n📝 Base de datos: {db_title}")
            else:
                await update.message.reply_text("❌ Error conectando con Notion")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")
    
    def _is_image_file(self, message: Message) -> bool:
        """Verifica si el mensaje contiene una imagen"""
        if message.photo:
            return True
        
        if message.document:
            file_name = message.document.file_name or ""
            mime_type = message.document.mime_type or ""
            
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff']
            has_image_extension = any(file_name.lower().endswith(ext) for ext in image_extensions)
            has_image_mime = mime_type.startswith('image/')
            
            return has_image_extension or has_image_mime
        
        return False
    
    def _generate_filename(self, message: Message) -> str:
        """Genera nombre único para el archivo"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        
        if message.photo:
            return f"photo_{timestamp}.jpg"
        elif message.document and message.document.file_name:
            name, ext = os.path.splitext(message.document.file_name)
            return f"{name}_{timestamp}{ext}"
        else:
            return f"image_{timestamp}.bin"
    
    def _extract_forward_info(self, message: Message) -> dict:
        """Extrae información completa de mensajes reenviados"""
        # Información básica del mensaje
        message_data = {
            "timestamp": datetime.now().isoformat(),
            "message_id": message.message_id,
            "date": message.date.isoformat() if message.date else None,
            "text": getattr(message, 'text', None),
            "caption": getattr(message, 'caption', None),
        }
        
        # Información del usuario que envía el mensaje
        user = message.from_user
        if user:
            message_data["sender"] = {
                "user_id": user.id,
                "username": getattr(user, 'username', None),
                "first_name": getattr(user, 'first_name', None),
                "last_name": getattr(user, 'last_name', None),
                "full_name": f"{getattr(user, 'first_name', '') or ''} {getattr(user, 'last_name', '') or ''}".strip(),
                "is_bot": getattr(user, 'is_bot', None),
                "language_code": getattr(user, 'language_code', None)
            }
        
        # Información del chat
        chat = message.chat
        message_data["chat"] = {
            "chat_id": chat.id,
            "chat_type": chat.type,
            "title": getattr(chat, 'title', None),
            "username": getattr(chat, 'username', None)
        }
        
        # **INFORMACIÓN DE REENVÍO - PARTE PRINCIPAL**
        forward_info = self._analyze_forward_origin(message)
        message_data["forwarding"] = forward_info
        
        return message_data
    
    def _analyze_forward_origin(self, message: Message) -> dict:
        """Analiza el origen del mensaje reenviado"""
        # Campos de reenvío estándar
        forward_from = getattr(message, 'forward_from', None)
        forward_from_chat = getattr(message, 'forward_from_chat', None)
        forward_sender_name = getattr(message, 'forward_sender_name', None)
        forward_date = getattr(message, 'forward_date', None)
        is_automatic_forward = getattr(message, 'is_automatic_forward', None)
        
        # Campo moderno de Telegram (más completo)
        forward_origin = getattr(message, 'forward_origin', None)
        
        # Información del origen
        origin_info: dict = {
            "origin_type": None,
            "origin_sender_user_id": None,
            "origin_sender_name": None,
            "origin_sender_username": None,
            "origin_chat_id": None,
            "origin_chat_title": None,
            "origin_chat_username": None,
            "origin_date": None
        }
        
        # Extraer información del forward_origin (método más moderno)
        if forward_origin:
            origin_info["origin_type"] = getattr(forward_origin, 'type', None)
            
            if hasattr(forward_origin, 'sender_user') and forward_origin.sender_user:
                # Usuario específico (sin privacidad)
                sender_user = forward_origin.sender_user
                origin_info["origin_sender_user_id"] = sender_user.id
                origin_info["origin_sender_name"] = f"{getattr(sender_user, 'first_name', '') or ''} {getattr(sender_user, 'last_name', '') or ''}".strip()
                origin_info["origin_sender_username"] = getattr(sender_user, 'username', None)
                
            elif hasattr(forward_origin, 'sender_user_name') and forward_origin.sender_user_name:
                # Usuario con privacidad activada (solo nombre visible)
                origin_info["origin_sender_name"] = getattr(forward_origin, 'sender_user_name', None)
                
            elif hasattr(forward_origin, 'chat') and forward_origin.chat:
                # Canal o grupo
                chat = forward_origin.chat
                origin_info["origin_chat_id"] = chat.id
                origin_info["origin_chat_title"] = getattr(chat, 'title', None)
                origin_info["origin_chat_username"] = getattr(chat, 'username', None)
            
            # Fecha del origen
            origin_date = getattr(forward_origin, 'date', None)
            if origin_date:
                origin_info["origin_date"] = origin_date.isoformat()
        
        # Determinar si es mensaje reenviado
        is_forwarded = bool(
            forward_from or forward_from_chat or forward_sender_name or 
            forward_date or forward_origin or is_automatic_forward
        )
        
        # Generar identificador único para el reenvío
        unique_identifier = None
        if is_forwarded:
            identifier_parts = []
            
            if origin_info["origin_sender_user_id"]:
                identifier_parts.append(f"USER_{origin_info['origin_sender_user_id']}")
            elif origin_info["origin_sender_name"]:
                # Hash del nombre para usuarios privados
                name_hash = hashlib.md5(origin_info["origin_sender_name"].encode('utf-8')).hexdigest()[:8]
                identifier_parts.append(f"PRIVATE_{name_hash}")
            elif origin_info["origin_chat_id"]:
                identifier_parts.append(f"CHAT_{origin_info['origin_chat_id']}")
            
            # Agregar fecha
            date_str = origin_info["origin_date"] or (forward_date.isoformat() if forward_date else None)
            if date_str:
                identifier_parts.append(f"DATE_{date_str[:10]}")
            
            if identifier_parts:
                unique_identifier = "_".join(identifier_parts)
        
        # Información de reenvío consolidada
        forward_info = {
            "is_forwarded": is_forwarded,
            "forward_date": forward_date.isoformat() if forward_date else None,
            "is_automatic_forward": is_automatic_forward,
            "unique_identifier": unique_identifier,
            "origin_info": origin_info
        }
        
        # Información de métodos antiguos (compatibilidad)
        if forward_from:
            forward_info["legacy_sender"] = {
                "user_id": forward_from.id,
                "username": getattr(forward_from, 'username', None),
                "full_name": f"{getattr(forward_from, 'first_name', '') or ''} {getattr(forward_from, 'last_name', '') or ''}".strip()
            }
        
        if forward_from_chat:
            forward_info["legacy_chat"] = {
                "chat_id": forward_from_chat.id,
                "title": getattr(forward_from_chat, 'title', None),
                "username": getattr(forward_from_chat, 'username', None)
            }
        
        if forward_sender_name:
            forward_info["legacy_sender_name"] = forward_sender_name
        
        return forward_info
    
    def _get_tipster_name(self, forward_info: dict) -> str:
        """Extrae el nombre del tipster del mensaje reenviado"""
        if not forward_info.get("is_forwarded"):
            return "Usuario directo"
        
        origin = forward_info.get("origin_info", {})
        
        # Priorizar información moderna
        if origin.get("origin_chat_title"):
            # Es un canal - usar el título del canal como tipster
            return origin["origin_chat_title"]
        elif origin.get("origin_sender_username"):
            # Usuario con username
            return f"@{origin['origin_sender_username']}"
        elif origin.get("origin_sender_name"):
            # Usuario con nombre (privado)
            return origin["origin_sender_name"]
        
        # Fallback a métodos antiguos
        legacy_chat = forward_info.get("legacy_chat")
        legacy_sender = forward_info.get("legacy_sender")
        legacy_name = forward_info.get("legacy_sender_name")
        
        if legacy_chat and legacy_chat.get("title"):
            return legacy_chat["title"]
        elif legacy_sender and legacy_sender.get("username"):
            return f"@{legacy_sender['username']}"
        elif legacy_sender and legacy_sender.get("full_name"):
            return legacy_sender["full_name"]
        elif legacy_name:
            return legacy_name
        
        return "Tipster desconocido"
    
    def _format_forward_response(self, forward_info: dict) -> str:
        """Formatea la respuesta sobre el reenvío para el usuario"""
        if not forward_info.get("is_forwarded"):
            return ""
        
        origin = forward_info.get("origin_info", {})
        unique_id = forward_info.get("unique_identifier")
        
        # Priorizar información moderna
        if origin.get("origin_sender_user_id"):
            # Usuario con ID conocido
            user_id = origin["origin_sender_user_id"]
            username = origin.get("origin_sender_username")
            name = origin.get("origin_sender_name", "Usuario")
            
            if username:
                return f"\n🔄 Reenviado de: @{username} (ID: {user_id})"
            else:
                return f"\n🔄 Reenviado de: {name} (ID: {user_id})"
                
        elif origin.get("origin_sender_name"):
            # Usuario con privacidad
            name = origin["origin_sender_name"]
            response = f"\n🔄 Reenviado de: {name} (privado)"
            if unique_id:
                response += f"\n🆔 ID: {unique_id}"
            return response
            
        elif origin.get("origin_chat_id"):
            # Canal o grupo
            chat_id = origin["origin_chat_id"]
            title = origin.get("origin_chat_title")
            username = origin.get("origin_chat_username")
            
            if username:
                return f"\n🔄 Reenviado del canal: @{username} (ID: {chat_id})"
            else:
                return f"\n🔄 Reenviado de: {title or 'Canal'} (ID: {chat_id})"
        
        # Fallback a métodos antiguos
        legacy_sender = forward_info.get("legacy_sender")
        legacy_chat = forward_info.get("legacy_chat")
        legacy_name = forward_info.get("legacy_sender_name")
        
        if legacy_sender:
            username = legacy_sender.get("username")
            name = legacy_sender.get("full_name")
            user_id = legacy_sender.get("user_id")
            
            if username:
                return f"\n🔄 Reenviado de: @{username} (ID: {user_id})"
            else:
                return f"\n🔄 Reenviado de: {name} (ID: {user_id})"
                
        elif legacy_chat:
            username = legacy_chat.get("username")
            title = legacy_chat.get("title")
            chat_id = legacy_chat.get("chat_id")
            
            if username:
                return f"\n🔄 Reenviado del canal: @{username} (ID: {chat_id})"
            else:
                return f"\n🔄 Reenviado de: {title} (ID: {chat_id})"
                
        elif legacy_name:
            response = f"\n🔄 Reenviado de: {legacy_name} (privado)"
            if unique_id:
                response += f"\n🆔 ID: {unique_id}"
            return response
        
        return "\n🔄 Mensaje reenviado"
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa cualquier mensaje (con o sin imagen)"""
        message = update.message
        
        if not message:
            return
        
        try:
            # Extraer información completa
            message_data = self._extract_forward_info(message)
            has_image = self._is_image_file(message)
            
            # Procesar imagen si existe
            image_path = None
            if has_image:
                image_path = await self._download_image(message, context, message_data)
            
            # Procesar con Notion si es un mensaje reenviado
            notion_result = None
            if message_data.get("forwarding", {}).get("is_forwarded") and self.notion_service:
                notion_result = await self._send_to_notion(message_data, image_path)
            
            # Responder al usuario
            response = "✅ Mensaje procesado"
            if has_image:
                filename = message_data.get('download_info', {}).get('filename', 'imagen')
                response = f"✅ Imagen descargada: {filename}"
            
            # Agregar información de reenvío
            forward_response = self._format_forward_response(message_data.get("forwarding", {}))
            response += forward_response
            
            # Agregar información de Notion
            if notion_result:
                response += f"\n📝 Guardado en Notion: ✅"
            elif message_data.get("forwarding", {}).get("is_forwarded") and self.notion_service:
                response += f"\n📝 Guardado en Notion: ❌"
            
            await message.reply_text(response)
            
            # Mostrar información completa en consola
            self._log_message_info(message_data, has_image, notion_result)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            await message.reply_text("❌ Error al procesar el mensaje")
    
    async def _download_image(self, message: Message, context, message_data: dict) -> Optional[Path]:
        """Descarga la imagen y retorna el path"""
        try:
            file_obj = None
            
            if message.photo:
                file_obj = message.photo[-1]  # Mayor resolución
                message_data["image_info"] = {
                    "type": "photo",
                    "width": file_obj.width,
                    "height": file_obj.height,
                    "file_size": file_obj.file_size
                }
            elif message.document:
                file_obj = message.document
                message_data["image_info"] = {
                    "type": "document",
                    "filename": file_obj.file_name,
                    "mime_type": file_obj.mime_type,
                    "file_size": file_obj.file_size
                }
            
            if file_obj:
                # Descargar archivo
                file = await context.bot.get_file(file_obj.file_id)
                filename = self._generate_filename(message)
                file_path = self.images_folder / filename
                
                await file.download_to_drive(file_path)
                
                message_data["download_info"] = {
                    "filename": filename,
                    "local_path": str(file_path.absolute()),
                    "file_size_bytes": file_path.stat().st_size if file_path.exists() else None
                }
                
                return file_path
                
        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
        
        return None
    
    async def _send_to_notion(self, message_data: dict, image_path: Optional[Path] = None) -> bool:
        """Envía los datos a Notion"""
        try:
            if not self.notion_service:
                return False
            
            forward_info = message_data.get("forwarding", {})
            tipster_name = self._get_tipster_name(forward_info)
            
            # Generar título del evento basado en el contenido del mensaje
            text_content = message_data.get("text") or message_data.get("caption") or ""
            if text_content:
                # Usar las primeras palabras como título
                event_title = text_content[:100] + "..." if len(text_content) > 100 else text_content
            else:
                event_title = f"Apuesta de {tipster_name}"
            
            # Enviar a Notion
            page_id = self.notion_service.create_bet_entry(
                event_title=event_title,
                tipster_name=tipster_name,
                image_path=image_path,
                additional_data=message_data
            )
            
            return page_id is not None
            
        except Exception as e:
            logger.error(f"Error enviando a Notion: {e}")
            return False
    
    def _log_message_info(self, message_data: dict, has_image: bool, notion_result: Optional[bool] = None):
        """Registra información del mensaje"""
        print("\n" + "="*80)
        print("🖼️ IMAGEN PROCESADA" if has_image else "💬 MENSAJE PROCESADO")
        if notion_result is not None:
            print(f"📝 NOTION: {'✅ GUARDADO' if notion_result else '❌ ERROR'}")
        print("="*80)
        print(json.dumps(message_data, indent=2, ensure_ascii=False))
        print("="*80 + "\n")
        
        # Log simplificado
        sender = message_data.get("sender", {})
        sender_name = sender.get("full_name", "Usuario")
        sender_id = sender.get("user_id", "N/A")
        
        forward_info = message_data.get("forwarding", {})
        log_msg = f"{'Imagen' if has_image else 'Mensaje'} procesado de {sender_name} ({sender_id})"
        
        if forward_info.get("is_forwarded"):
            tipster_name = self._get_tipster_name(forward_info)
            log_msg += f" - REENVIADO DE: {tipster_name}"
        
        if notion_result is not None:
            log_msg += f" - NOTION: {'OK' if notion_result else 'ERROR'}"
        
        logger.info(log_msg)
    
    def run(self):
        """Inicia el bot"""
        application = Application.builder().token(self.telegram_token).build()
        
        # Comandos
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("test_notion", self.test_notion_command))
        
        # Manejar todos los mensajes
        application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, self.process_message))
        
        notion_status = "✅" if (self.notion_service and self.notion_service.test_connection()) else "❌"
        
        logger.info("🤖 Bot iniciado - Extractor de Imágenes y Usuarios con Notion")
        logger.info(f"📁 Carpeta: {self.images_folder.absolute()}")
        logger.info(f"📝 Notion: {notion_status}")
        logger.info("⏹️ Presiona Ctrl+C para detener")
        
        application.run_polling()


def main():
    """Función principal"""
    try:
        bot = TelegramImageBotWithNotion()
        bot.run()
    except ValueError as e:
        logger.error(f"Error de configuración: {e}")
        print(f"\n❌ {e}")
        print("💡 Asegúrate de tener TELEGRAM_BOT_TOKEN, NOTION_TOKEN y NOTION_DATABASE_ID en el archivo .env")
    except KeyboardInterrupt:
        logger.info("🛑 Bot detenido")
        print("\n👋 ¡Bot detenido!")
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()