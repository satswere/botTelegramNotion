#!/usr/bin/env python3
"""
BOT DE TELEGRAM CON INTEGRACIÓN COMPLETA A NOTION
===============================================

Script principal consolidado que combina:
- Bot de Telegram funcional (base: bot_working.py)
- Subida REAL de archivos a Notion (base: test_real_upload.py)
- Extracción COMPLETA de información de mensajes reenviados (base: bot_test.py)
- Manejo correcto de propiedades de Notion
- Logs y manejo de errores

Funcionalidades:
✅ Recibe mensajes e imágenes desde Telegram
✅ Sube archivos REALES a Notion (proceso de 3 pasos)
✅ Crea registros en la base de datos con propiedades correctas
✅ EXTRACCIÓN COMPLETA de información de mensajes reenviados:
   - Identifica usuarios originales (incluso con privacidad)
   - Extrae información de canales/grupos origen
   - Genera identificadores únicos para reenvíos
   - Maneja tanto API moderna (forward_origin) como legacy
   - Guarda toda la información en los registros de Notion
✅ Manejo de errores y logging completo
✅ Variables de entorno seguras

NUEVA FUNCIONALIDAD DE REENVÍOS:
- Detecta automáticamente si un mensaje es reenviado
- Extrae información del usuario/canal original
- Maneja usuarios con privacidad activada
- Genera identificadores únicos basados en hash
- Guarda toda la información en Notion de forma estructurada
"""

import logging
import os
import asyncio
import aiohttp
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

from telegram import Update, Message
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from notion_client import Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramNotionBot:
    """Bot principal de Telegram con integración completa a Notion"""
    
    def __init__(self):
        """Inicializa el bot con todas las configuraciones necesarias"""
        logger.info("🤖 Inicializando Bot de Telegram con Notion...")
        
        # Variables de entorno
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.notion_token = os.getenv('NOTION_TOKEN') 
        self.database_id = os.getenv('NOTION_DATABASE_ID', '27aa8baa-ff5a-808b-8cc4-d3cc8f010fa0')
        
        # Validación de configuración
        self._validate_config()
        
        # Cliente Notion
        self.notion_client = None
        try:
            self.notion_client = Client(auth=self.notion_token)
            logger.info("✅ Cliente Notion inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando Notion: {e}")
            raise
        
        # Configuración para API de Notion (subida de archivos)
        self.notion_api_base = "https://api.notion.com/v1"
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28"
        }
        
        # Carpeta para imágenes
        self.images_path = Path("storage/images")
        self.images_path.mkdir(exist_ok=True)
        
        logger.info(f"📁 Carpeta de imágenes: {self.images_path.absolute()}")
        logger.info("✅ Bot inicializado correctamente")
    
    def _validate_config(self):
        """Valida que todas las variables de entorno estén configuradas"""
        if not self.telegram_token or self.telegram_token.startswith('your_'):
            raise ValueError("TELEGRAM_BOT_TOKEN no configurado correctamente")
        
        if not self.notion_token or self.notion_token.startswith('your_'):
            raise ValueError("NOTION_TOKEN no configurado correctamente")
        
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID no configurado")
        
        logger.info("✅ Configuración validada")
    
    # =============================================================================
    # EXTRACCIÓN DE INFORMACIÓN DE MENSAJES REENVIADOS
    # =============================================================================
    
    def _extract_forward_info(self, message: Message) -> dict:
        """Extrae información completa de mensajes reenviados"""
        # Información básica del mensaje
        message_data = {
            "timestamp": datetime.now().isoformat(),
            "message_id": message.message_id,
            "date": message.date.isoformat() if message.date else None,
        }
        
        # Información del usuario que envía
        user = message.from_user
        if user:
            message_data["sender"] = {
                "user_id": user.id,
                "username": getattr(user, 'username', None),
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
        is_automatic_forward = getattr(message, 'is_automatic_forward', False)
        
        # Campo moderno de origen
        forward_origin = getattr(message, 'forward_origin', None)
        
        # Inicializar información de origen
        origin_info = {}
        
        # Analizar forward_origin (API moderna)
        if forward_origin:
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
        origin_date = getattr(forward_origin, 'date', None) if forward_origin else None
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
            
            if origin_info.get("origin_sender_user_id"):
                identifier_parts.append(f"USER_{origin_info['origin_sender_user_id']}")
            elif origin_info.get("origin_sender_name"):
                # Hash del nombre para usuarios privados
                sender_name = origin_info["origin_sender_name"]
                if sender_name:
                    name_hash = hashlib.md5(sender_name.encode('utf-8')).hexdigest()[:8]
                    identifier_parts.append(f"PRIVATE_{name_hash}")
            elif origin_info.get("origin_chat_id"):
                identifier_parts.append(f"CHAT_{origin_info['origin_chat_id']}")
            
            # Agregar fecha
            date_str = origin_info.get("origin_date") or (forward_date.isoformat() if forward_date else None)
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
            name = origin.get("origin_sender_name")
            
            user_info = f"ID: {user_id}"
            if username:
                user_info += f" (@{username})"
            elif name:
                user_info += f" ({name})"
            
            return f"\n\n🔄 **Mensaje reenviado de usuario**\n👤 {user_info}"
            
        elif origin.get("origin_sender_name"):
            # Usuario con privacidad (solo nombre)
            name = origin["origin_sender_name"]
            return f"\n\n🔄 **Mensaje reenviado**\n👤 Usuario: {name} (perfil privado)"
            
        elif origin.get("origin_chat_id"):
            # Canal o grupo
            chat_id = origin["origin_chat_id"]
            title = origin.get("origin_chat_title")
            username = origin.get("origin_chat_username")
            
            chat_info = f"ID: {chat_id}"
            if username:
                chat_info += f" (@{username})"
            elif title:
                chat_info += f" ({title})"
            
            return f"\n\n🔄 **Mensaje reenviado de canal/grupo**\n📢 {chat_info}"
        
        # Fallback a métodos antiguos
        legacy = forward_info.get("legacy_sender")
        if legacy:
            return f"\n\n🔄 **Mensaje reenviado**\n👤 {legacy.get('full_name', 'Usuario')} (ID: {legacy.get('user_id')})"
        
        return f"\n\n🔄 **Mensaje reenviado**\n📝 ID único: {unique_id or 'N/A'}"

    # =============================================================================
    # COMANDOS DEL BOT
    # =============================================================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida"""
        if not update.message:
            return
            
        welcome_message = (
            "🤖 **Bot de Telegram con Notion** 🤖\n\n"
            "✨ **Funcionalidades:**\n"
            "📸 Recibe y procesa imágenes\n"
            "📝 Crea registros automáticos en Notion\n"
            "🔗 Sube archivos REALES (no solo referencias)\n"
            "🔍 Extrae información de mensajes reenviados\n\n"
            "📋 **Comandos:**\n"
            "• `/start` - Este mensaje\n"
            "• `/help` - Ayuda detallada\n"
            "• `/status` - Estado del sistema\n\n"
            "🚀 **¡Envía una imagen para comenzar!**"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        user_name = "Usuario"
        if update.effective_user and update.effective_user.first_name:
            user_name = update.effective_user.first_name
        logger.info(f"👋 Usuario {user_name} inició el bot")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /help - Ayuda detallada"""
        if not update.message:
            return
            
        help_message = (
            "🆘 **Ayuda del Bot**\n\n"
            "📸 **Para usar el bot:**\n"
            "1️⃣ Envía una imagen (JPG, PNG, etc.)\n"
            "2️⃣ El bot la descargará automáticamente\n"
            "3️⃣ Subirá el archivo REAL a Notion\n"
            "4️⃣ Creará un registro en tu base de datos\n\n"
            "🔧 **Campos que se guardan:**\n"
            "• **Evento / Selección**: Título generado automáticamente\n"
            "• **Fecha**: Fecha y hora actuales\n"
            "• **Resultado**: 'Pendiente' (por defecto)\n"
            "• **Tipo de apuesta**: 'Simple' (por defecto)\n"
            "• **Captura / Comprobante**: Archivo real subido\n"
            "• **Mercado / Selección**: Texto adicional del mensaje\n\n"
            "⚠️ **Nota**: El bot solo procesa imágenes por ahora."
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status - Estado del sistema"""
        if not update.message:
            return
            
        try:
            # Probar conexión con Notion
            if self.notion_client:
                database = self.notion_client.databases.retrieve(self.database_id)
                # database es un dict, no un awaitable
                if isinstance(database, dict):
                    database_name = database.get('title', [{}])[0].get('plain_text', 'Base de datos') if database.get('title') else 'Base de datos'
                else:
                    database_name = "Base de datos"
                notion_status = "✅ Conectado"
            else:
                database_name = "Error"
                notion_status = "❌ Cliente no inicializado"
        except Exception as e:
            database_name = "Error"
            notion_status = f"❌ Error: {str(e)[:50]}..."
        
        status_message = (
            f"📊 **Estado del Sistema**\n\n"
            f"🤖 **Bot**: ✅ Activo\n"
            f"📝 **Notion**: {notion_status}\n"
            f"🗃️ **Base de datos**: {database_name}\n"
            f"📁 **Carpeta**: {self.images_path.name}/\n"
            f"📸 **Imágenes guardadas**: {len(list(self.images_path.glob('*')))}\n\n"
            f"🔧 **ID Base de datos**: `{self.database_id}`"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    # =============================================================================
    # PROCESAMIENTO DE IMÁGENES
    # =============================================================================
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa imágenes recibidas y las sube a Notion"""
        message = update.message
        if not message:
            return
        
        # Mensaje de estado
        status = await message.reply_text("🔄 Procesando imagen...")
        
        try:
            # 0. EXTRAER INFORMACIÓN COMPLETA DEL MENSAJE (incluye reenvío)
            message_data = self._extract_forward_info(message)
            
            # 1. DESCARGAR IMAGEN
            await status.edit_text("⬇️ Descargando imagen...")
            filename = await self._download_image(message)
            if not filename:
                await status.edit_text("❌ Error descargando imagen")
                return
            
            # 2. SUBIR A NOTION (PROCESO REAL)
            await status.edit_text("🔄 Subiendo archivo a Notion...")
            file_upload_id = await self._upload_file_to_notion(filename)
            if not file_upload_id:
                await status.edit_text("❌ Error subiendo archivo")
                return
            
            # 3. CREAR REGISTRO EN NOTION CON INFORMACIÓN COMPLETA
            await status.edit_text("📝 Creando registro en Notion...")
            page_id = await self._create_notion_record(message, filename, file_upload_id, message_data)
            if not page_id:
                await status.edit_text("❌ Error creando registro")
                return
            
            # 4. CONFIRMACIÓN FINAL CON INFORMACIÓN DE REENVÍO
            user_name = self._get_user_name(message)
            success_message = (
                f"✅ **¡Imagen procesada exitosamente!**\n\n"
                f"📄 **Registro creado en Notion**\n"
                f"👤 **Usuario**: {user_name}\n"
                f"📁 **Archivo**: `{filename}`\n"
                f"🆔 **Page ID**: `{page_id[:20]}...`"
            )
            
            # Agregar información de reenvío si aplica
            forward_response = self._format_forward_response(message_data.get("forwarding", {}))
            if forward_response:
                success_message += forward_response
            
            success_message += "\n\n🔗 Revisa tu base de datos de Notion para ver el registro completo."
            
            await status.edit_text(success_message, parse_mode='Markdown')
            
            # Log con información completa
            self._log_message_info(message_data, True, filename)
            logger.info(f"✅ Imagen procesada: {filename} -> {page_id}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
            await status.edit_text(f"❌ Error: {str(e)[:100]}...")
    
    async def _download_image(self, message: Message) -> Optional[str]:
        """Descarga la imagen del mensaje y devuelve el nombre del archivo"""
        try:
            if message.photo:
                # Obtener la foto de mayor resolución
                file_info = await message.photo[-1].get_file()
            elif message.document and message.document.mime_type and message.document.mime_type.startswith('image/'):
                file_info = await message.document.get_file()
            else:
                logger.warning("No se encontró imagen en el mensaje")
                return None
            
            # Generar nombre único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            file_path = file_info.file_path or ""
            extension = file_path.split('.')[-1] if '.' in file_path and file_path else 'jpg'
            filename = f"photo_{timestamp}.{extension}"
            
            # Descargar
            file_path = self.images_path / filename
            await file_info.download_to_drive(str(file_path))
            
            if file_path.exists():
                logger.info(f"📁 Imagen descargada: {filename}")
                return filename
            else:
                logger.error("El archivo descargado no existe")
                return None
                
        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
            return None
    
    # =============================================================================
    # SUBIDA REAL DE ARCHIVOS A NOTION (PROCESO DE 3 PASOS)
    # =============================================================================
    
    async def _upload_file_to_notion(self, filename: str) -> Optional[str]:
        """
        Sube el archivo REAL a Notion usando el proceso oficial de 3 pasos
        Returns: file_upload_id si es exitoso, None si falla
        """
        file_path = self.images_path / filename
        
        if not file_path.exists():
            logger.error(f"Archivo no encontrado: {filename}")
            return None
        
        try:
            file_size = file_path.stat().st_size
            logger.info(f"🚀 Iniciando subida REAL: {filename} ({file_size} bytes)")
            
            async with aiohttp.ClientSession() as session:
                # PASO 1: Crear File Upload Object
                logger.info("1️⃣ Creando File Upload Object...")
                
                create_url = f"{self.notion_api_base}/file_uploads"
                headers = {
                    **self.notion_headers,
                    "Content-Type": "application/json"
                }
                
                async with session.post(create_url, headers=headers, json={}) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Error creando file upload object: {response.status} - {error_text}")
                    
                    upload_data = await response.json()
                    file_upload_id = upload_data.get("id")
                    upload_url = upload_data.get("upload_url")
                    
                    if not file_upload_id or not upload_url:
                        raise Exception("No se obtuvo ID o URL de subida")
                    
                    logger.info(f"✅ File Upload Object creado: {file_upload_id}")
                
                # PASO 2: Subir el contenido del archivo
                logger.info("2️⃣ Subiendo contenido del archivo...")
                
                with open(file_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', f, filename=filename)
                    
                    upload_headers = {
                        "Authorization": f"Bearer {self.notion_token}",
                        "Notion-Version": "2022-06-28"
                    }
                    
                    async with session.post(upload_url, headers=upload_headers, data=form_data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Error subiendo archivo: {response.status} - {error_text}")
                        
                        upload_result = await response.json()
                        status = upload_result.get("status")
                        
                        if status != "uploaded":
                            raise Exception(f"Estado del archivo no es 'uploaded': {status}")
                        
                        logger.info(f"✅ Archivo subido exitosamente: {filename}")
                        return file_upload_id
                        
        except Exception as e:
            logger.error(f"❌ Error en subida real: {e}")
            return None
    
    # =============================================================================
    # CREACIÓN DE REGISTROS EN NOTION
    # =============================================================================
    
    async def _create_notion_record(self, message: Message, filename: str, file_upload_id: str, message_data: Optional[dict] = None) -> Optional[str]:
        """
        PASO 3: Crear registro en Notion con archivo real adjunto y información completa de reenvío
        """
        try:
            logger.info("3️⃣ Creando registro con archivo real adjunto...")
            
            # Generar título
            user_name = self._get_user_name(message)
            title = f"Apuesta {user_name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            # Extraer información adicional
            text_content = message.text or message.caption or ""
            forward_info = message_data.get("forwarding", {}) if message_data else {}
            is_forwarded = forward_info.get("is_forwarded", False)
            
            # Información adicional para Mercado / Selección
            additional_info = []
            if text_content.strip():
                additional_info.append(f"Texto: {text_content[:300]}")
            
            # Agregar información detallada de reenvío
            if is_forwarded:
                additional_info.append("🔄 MENSAJE REENVIADO")
                
                origin = forward_info.get("origin_info", {})
                unique_id = forward_info.get("unique_identifier")
                
                # Información del origen
                if origin.get("origin_sender_user_id"):
                    user_id = origin.get("origin_sender_user_id")
                    username = origin.get("origin_sender_username", "")
                    name = origin.get("origin_sender_name", "")
                    additional_info.append(f"👤 Origen: ID {user_id}")
                    if username:
                        additional_info.append(f"   @{username}")
                    if name:
                        additional_info.append(f"   {name}")
                        
                elif origin.get("origin_sender_name"):
                    sender_name = origin.get("origin_sender_name")
                    if sender_name:
                        additional_info.append(f"👤 Usuario privado: {sender_name}")
                    
                elif origin.get("origin_chat_id"):
                    chat_id = origin.get("origin_chat_id")
                    title_chat = origin.get("origin_chat_title", "")
                    username_chat = origin.get("origin_chat_username", "")
                    if chat_id:
                        additional_info.append(f"📢 Canal/Grupo: ID {chat_id}")
                        if username_chat:
                            additional_info.append(f"   @{username_chat}")
                        elif title_chat:
                            additional_info.append(f"   {title_chat}")
                
                # Fecha original y ID único
                if origin.get("origin_date"):
                    origin_date = origin.get("origin_date")
                    if origin_date and len(origin_date) >= 10:
                        additional_info.append(f"📅 Fecha original: {origin_date[:10]}")
                if unique_id:
                    additional_info.append(f"🆔 ID único: {unique_id}")
                
                # Información del que reenvía
                sender = message_data.get("sender", {}) if message_data else {}
                if sender:
                    additional_info.append(f"📤 Reenviado por: {sender.get('full_name', 'Usuario')} (ID: {sender.get('user_id', 'N/A')})")
            else:
                additional_info.append(f"📤 Usuario: {user_name}")
            
            # Información de archivo
            additional_info.append(f"📁 Archivo: {filename}")
            
            market_info = "\n".join(additional_info)
            
            # Propiedades del registro (usando nombres correctos de la base de datos)
            properties = {
                "Evento / Selección": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                "Fecha": {
                    "date": {
                        "start": datetime.now().isoformat()[:10]
                    }
                },
                "Resultado": {
                    "select": {
                        "name": "Pendiente"
                    }
                },
                "Tipo de apuesta": {
                    "select": {
                        "name": "Simple"
                    }
                },
                # ARCHIVO REAL usando file_upload_id
                "Captura / Comprobante": {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {
                                "id": file_upload_id
                            },
                            "name": filename
                        }
                    ]
                },
                # Información adicional (incluyendo información de reenvío)
                "Mercado / Selección": {
                    "rich_text": [
                        {
                            "text": {
                                "content": market_info
                            }
                        }
                    ]
                }
            }
            
            # Crear el registro
            if self.notion_client:
                response = self.notion_client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                
                if isinstance(response, dict) and "id" in response:
                    page_id = response["id"]
                    logger.info(f"✅ Registro creado con archivo REAL: {page_id}")
                    return page_id
                else:
                    logger.error("Respuesta inesperada de Notion API")
                    return None
            else:
                logger.error("Cliente Notion no disponible")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error creando registro: {e}")
            return None
    
    # =============================================================================
    # UTILIDADES
    # =============================================================================
    
    def _log_message_info(self, message_data: dict, has_image: bool, filename: Optional[str] = None):
        """Registra información completa del mensaje procesado"""
        try:
            print("\n" + "="*80)
            print("🖼️ IMAGEN PROCESADA" if has_image else "💬 MENSAJE PROCESADO")
            print("="*80)
            
            # Log resumido
            sender = message_data.get("sender", {})
            sender_name = sender.get("full_name", "Usuario")
            sender_id = sender.get("user_id", "N/A")
            
            forward_info = message_data.get("forwarding", {})
            log_msg = f"{'Imagen' if has_image else 'Mensaje'} procesado de {sender_name} ({sender_id})"
            
            if filename:
                log_msg += f" - Archivo: {filename}"
            
            if forward_info.get("is_forwarded"):
                origin = forward_info.get("origin_info", {})
                if origin.get("origin_sender_user_id"):
                    origin_name = origin.get("origin_sender_username") or origin.get("origin_sender_name")
                    origin_id = origin.get("origin_sender_user_id")
                    log_msg += f" - REENVIADO DE: {origin_name} (ID: {origin_id})"
                elif origin.get("origin_sender_name"):
                    sender_name = origin.get("origin_sender_name")
                    log_msg += f" - REENVIADO DE: {sender_name} (privado)"
                elif origin.get("origin_chat_id"):
                    chat_name = origin.get("origin_chat_username") or origin.get("origin_chat_title")
                    chat_id = origin.get("origin_chat_id")
                    log_msg += f" - REENVIADO DE CANAL: {chat_name} (ID: {chat_id})"
            
            # Log detallado en JSON (para debugging)
            print(json.dumps(message_data, indent=2, ensure_ascii=False, default=str))
            print("="*80 + "\n")
            
            logger.info(log_msg)
            
        except Exception as e:
            logger.error(f"Error en logging: {e}")
    
    def _get_user_name(self, message: Message) -> str:
        """Obtiene el nombre del usuario de manera segura"""
        if not message.from_user:
            return "Usuario desconocido"
        
        user = message.from_user
        parts = []
        if user.first_name:
            parts.append(user.first_name)
        if user.last_name:
            parts.append(user.last_name)
        
        if parts:
            return " ".join(parts)
        elif user.username:
            return f"@{user.username}"
        else:
            return f"Usuario {user.id}"
    
    async def handle_other_messages(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes que no son imágenes pero extrae información de reenvío"""
        message = update.message
        if not message:
            return
        
        try:
            # Extraer información del mensaje (incluye reenvío)
            message_data = self._extract_forward_info(message)
            forward_info = message_data.get("forwarding", {})
            
            # Respuesta base
            help_text = "📸 **Solo proceso imágenes por ahora**\n\n"
            
            # Si es un mensaje reenviado, mostrar información
            if forward_info.get("is_forwarded"):
                forward_response = self._format_forward_response(forward_info)
                help_text += f"**Mensaje analizado:**{forward_response}\n\n"
            
            help_text += (
                "Para usar el bot:\n"
                "1️⃣ Envía una imagen (JPG, PNG, etc.)\n"
                "2️⃣ El bot la procesará automáticamente\n\n"
                "💡 Usa `/help` para más información"
            )
            
            await message.reply_text(help_text, parse_mode='Markdown')
            
            # Log de la información extraída
            self._log_message_info(message_data, False)
            
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            await message.reply_text("📸 **Solo proceso imágenes por ahora**\n\n💡 Usa `/help` para más información")
    
    # =============================================================================
    # EJECUCIÓN DEL BOT
    # =============================================================================
    
    def run(self):
        """Inicia el bot y lo mantiene funcionando"""
        logger.info("🚀 Iniciando aplicación de Telegram...")
        
        # Crear aplicación
        if not self.telegram_token:
            raise ValueError("Token de Telegram no disponible")
            
        application = Application.builder().token(self.telegram_token).build()
        
        # Agregar handlers
        application.add_handler(CommandHandler("start", self.cmd_start))
        application.add_handler(CommandHandler("help", self.cmd_help))
        application.add_handler(CommandHandler("status", self.cmd_status))
        
        # Handler para imágenes (fotos y documentos de imagen)
        application.add_handler(MessageHandler(
            (filters.PHOTO | filters.Document.IMAGE) & ~filters.COMMAND,
            self.handle_image
        ))
        
        # Handler para otros mensajes
        application.add_handler(MessageHandler(
            filters.ALL & ~filters.COMMAND & ~filters.PHOTO & ~filters.Document.IMAGE,
            self.handle_other_messages
        ))
        
        # Información de inicio
        print("\n" + "="*60)
        print("🤖 BOT DE TELEGRAM CON NOTION - INICIADO")
        print("="*60)
        print(f"📁 Carpeta de imágenes: {self.images_path.absolute()}")
        print(f"🗃️ Base de datos Notion: {self.database_id}")
        print("📸 Envía imágenes al bot para procesarlas")
        print("⏹️  Presiona Ctrl+C para detener")
        print("="*60)
        
        # Iniciar polling
        try:
            application.run_polling()
        except KeyboardInterrupt:
            logger.info("🛑 Bot detenido por el usuario")
        except Exception as e:
            logger.error(f"❌ Error ejecutando bot: {e}")
            raise


def main():
    """Función principal del script"""
    try:
        print("🤖 Inicializando Bot de Telegram con Notion...")
        bot = TelegramNotionBot()
        bot.run()
        
    except ValueError as e:
        logger.error(f"❌ Error de configuración: {e}")
        print(f"\n❌ {e}")
        print("\n💡 Configuración necesaria:")
        print("1. Crea un archivo .env con:")
        print("   TELEGRAM_BOT_TOKEN=tu_token_aqui")
        print("   NOTION_TOKEN=tu_token_notion_aqui")
        print("   NOTION_DATABASE_ID=id_de_tu_base_de_datos")
        print("2. Ejecuta: python bot_main.py")
        
    except KeyboardInterrupt:
        print("\n👋 ¡Bot detenido!")
        
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()