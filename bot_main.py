#!/usr/bin/env python3
"""
⚠️  DEPRECATED - USE main.py INSTEAD ⚠️
=======================================

This file is deprecated and will be removed in a future version.
Please use the new unified entry point:

    python main.py

The new main.py provides:
- Cleaner architecture with better separation of concerns
- Improved dependency injection
- Better error handling
- Enhanced logging
- Modern code structure

For migration guide, see: README.md
"""

import sys
import warnings

# Show deprecation warning
warnings.warn(
    "bot_main.py is deprecated. Use 'python main.py' instead.",
    DeprecationWarning,
    stacklevel=2
)

print("=" * 70)
print("⚠️  DEPRECATION WARNING")
print("=" * 70)
print("")
print("This script (bot_main.py) is deprecated and will be removed soon.")
print("")
print("Please use the new unified entry point instead:")
print("    python main.py")
print("")
print("The application will start in 5 seconds...")
print("Press Ctrl+C to cancel.")
print("=" * 70)
print("")

import time
time.sleep(5)

# Original code follows
import json

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
from testingApi.openai_handler import OpenAIHandler
from infrastructure.notion import NotionBetRepository
from infrastructure.telegram import TelegramMessageExtractor
from infrastructure.storage import LocalFileStorage
from infrastructure.openai import OpenAIImageAnalyzer

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
        
        # Inicializar adapters (usando inyección de dependencias)
        self.bet_repository = NotionBetRepository(self.notion_client, self.database_id)
        self.message_extractor = TelegramMessageExtractor()
        self.file_storage = LocalFileStorage(str(self.images_path))
        self.image_analyzer = OpenAIImageAnalyzer()
        
        # Sistema de cola para procesar imágenes
        self.processing_queue = asyncio.Queue()
        self.is_processing = False
        self.queue_task = None
        
        # Configuración de la cola
        self.max_concurrent_processing = 1  # Procesar 1 imagen a la vez para evitar rate limiting
        self.delay_between_messages = 1.0  # Segundos entre mensajes
        
        logger.info(f"📁 Carpeta de imágenes: {self.images_path.absolute()}")
        logger.info(f"⚙️ Cola de procesamiento: máximo {self.max_concurrent_processing} imagen(es) simultánea(s)")
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
    
    # REMOVED: _extract_forward_info and _analyze_forward_origin
    # Now using TelegramMessageExtractor adapter for this functionality
    
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
        
        # Estado de la cola
        queue_size = self.processing_queue.qsize()
        queue_status = f"{queue_size} imagen(es) en espera" if queue_size > 0 else "✅ Vacía"
        
        status_message = (
            f"📊 **Estado del Sistema**\n\n"
            f"🤖 **Bot**: ✅ Activo\n"
            f"📝 **Notion**: {notion_status}\n"
            f"🗃️ **Base de datos**: {database_name}\n"
            f"📁 **Carpeta**: {self.images_path.name}/\n"
            f"📸 **Imágenes guardadas**: {len(list(self.images_path.glob('*')))}\n"
            f"⏳ **Cola de procesamiento**: {queue_status}\n\n"
            f"🔧 **ID Base de datos**: `{self.database_id}`"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    # =============================================================================
    # SISTEMA DE COLA PARA PROCESAMIENTO
    # =============================================================================
    
    async def queue_processor(self):
        """Procesa la cola de imágenes de manera secuencial"""
        logger.info("🔄 Iniciando procesador de cola...")
        
        while True:
            try:
                # Obtener siguiente tarea de la cola
                task_data = await self.processing_queue.get()
                
                if task_data is None:  # Señal de parada
                    break
                
                update, context = task_data
                queue_size = self.processing_queue.qsize()
                
                logger.info(f"📦 Procesando imagen desde cola (quedan {queue_size} en espera)")
                
                # Procesar la imagen
                await self._process_image_internal(update, context)
                
                # Marcar tarea como completada
                self.processing_queue.task_done()
                
                # Pequeña pausa entre procesamiento para evitar rate limiting
                if queue_size > 0:
                    await asyncio.sleep(self.delay_between_messages)
                    
            except Exception as e:
                logger.error(f"❌ Error en procesador de cola: {e}")
                self.processing_queue.task_done()
    
    async def handle_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Recibe imágenes y las agrega a la cola de procesamiento"""
        message = update.message
        if not message:
            return
        
        # Agregar a la cola
        queue_size = self.processing_queue.qsize()
        await self.processing_queue.put((update, context))
        
        # Informar al usuario sobre la posición en la cola
        if queue_size == 0:
            try:
                await message.reply_text("🔄 Procesando tu imagen...")
            except Exception as e:
                logger.warning(f"No se pudo enviar mensaje de estado: {e}")
        else:
            try:
                await message.reply_text(f"⏳ Tu imagen está en la cola. Posición: {queue_size + 1}")
            except Exception as e:
                logger.warning(f"No se pudo enviar mensaje de cola: {e}")
        
        logger.info(f"📥 Imagen agregada a la cola (total en cola: {queue_size + 1})")
    
    async def _process_image_internal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Procesa una imagen internamente (llamado por el procesador de cola)"""
        message = update.message
        if not message:
            return
        
        # Mensaje de estado inicial (solo uno para evitar rate limiting)
        status = None
        try:
            status = await message.reply_text("🔄 Procesando imagen...")
        except Exception as e:
            logger.warning(f"No se pudo enviar mensaje de estado: {e}")
        
        try:
            # 0. EXTRAER INFORMACIÓN COMPLETA DEL MENSAJE (incluye reenvío)
            message_data = self.message_extractor.extract_metadata(message)
            
            # 1. DESCARGAR IMAGEN
            logger.info("⬇️ Descargando imagen...")
            filename = await self._download_image(message)
            if not filename:
                if status:
                    await status.edit_text("❌ Error descargando imagen")
                return
            
            # 2. SUBIR A NOTION (PROCESO REAL)
            logger.info("🔄 Subiendo archivo a Notion...")
            file_upload_id = await self._upload_file_to_notion(filename)
            if not file_upload_id:
                if status:
                    await status.edit_text("❌ Error subiendo archivo")
                return
            
            # 3. ANALIZAR IMAGEN CON OPENAI
            logger.info("🔍 Analizando imagen con OpenAI...")
            image_path = str(self.images_path / filename)
            extraction_prompt = """Eres un sistema de extracción de campos para tickets de apuesta generados por Bet365. Tu tarea es identificar y extraer información clave a partir de un texto que describe los detalles de un ticket. La información debe estructurarse en campos específicos según el formato definido.

# Campos que debes identificar y extraer:

1. **ID del Ticket:** El número identificador único del ticket (ej: "123456")
2. **Deporte:** El deporte relacionado con el evento (ej: "Fútbol", "Tenis", "Baloncesto")
3. **Evento:** Nombre específico del evento o partido (ej: "Barcelona vs Real Madrid")
4. **Mercado:** El tipo de apuesta realizada (ej: "Ganador del partido", "Over/Under 2.5")
5. **Selección:** La elección del apostador (ej: "Barcelona", "Más de 2.5 goles")
6. **Cuota:** La cuota asociada a la apuesta (ej: "1.75", "2.10")
7. **Monto apostado:** Cantidad en la moneda definida (ej: "€20", "€50")
8. **Ganancia potencial:** Cantidad que se puede ganar (ej: "€35", "€105")
9. **Estado de la apuesta:** Estado actual del ticket (ej: "Ganada", "Perdida", "Pendiente")

# Formato de salida esperado:
Debes devolver SIEMPRE un objeto JSON con esta estructura exacta:

```json
{
  "ID_Ticket": "123456",
  "Deporte": "Fútbol",
  "Evento": "Barcelona vs Real Madrid",
  "Mercado": "Ganador del partido",
  "Seleccion": "Barcelona",
  "Cuota": "1.80",
  "Monto_Apostado": "€50",
  "Ganancia_Potencial": "€90",
  "Estado_Apuesta": "Pendiente"
}
```

# Ejemplos adicionales:

Ejemplo 1 (Tenis):
```json
{
  "ID_Ticket": "789012",
  "Deporte": "Tenis",
  "Evento": "Nadal vs Djokovic",
  "Mercado": "Ganador del partido",
  "Seleccion": "Nadal",
  "Cuota": "2.10",
  "Monto_Apostado": "€30",
  "Ganancia_Potencial": "€63",
  "Estado_Apuesta": "Ganada"
}
```

Ejemplo 2 (Campos no identificados):
```json
{
  "ID_Ticket": "No especificado",
  "Deporte": "Baloncesto",
  "Evento": "Lakers vs Bulls",
  "Mercado": "Total puntos",
  "Seleccion": "Más de 198.5",
  "Cuota": "1.90",
  "Monto_Apostado": "No especificado",
  "Ganancia_Potencial": "No especificado",
  "Estado_Apuesta": "Pendiente"
}
```

# Reglas importantes:
1. SIEMPRE devuelve un objeto JSON con TODOS los campos.
2. Si no puedes identificar un campo, usa EXACTAMENTE "No especificado" como valor.
3. Mantén los nombres de los campos EXACTAMENTE como se muestran en los ejemplos.
4. Las cuotas deben ser strings con formato decimal (ej: "1.90", "2.10").
5. Los montos deben incluir el símbolo de la moneda (ej: "€50", "€100").
6. El estado de la apuesta debe ser "Ganada", "Perdida" o "Pendiente"."""
            try:
                analysis_result = await self.image_analyzer.analyze_image(image_path, extraction_prompt)
                logger.info(f"✅ Análisis de imagen completado: {filename}")
            except Exception as e:
                logger.error(f"❌ Error en análisis de imagen: {e}")
                analysis_result = "Error en el análisis"

            # 4. CREAR REGISTRO EN NOTION CON INFORMACIÓN COMPLETA
            logger.info("📝 Creando registro en Notion...")
            
            # Preparar datos para el repositorio
            user_name = self._get_user_name(message)
            bet_data = {
                "title": f"Apuesta {user_name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                "analyzed_data": analysis_result,
                "file_upload_id": file_upload_id,
                "filename": filename,
                "message_metadata": message_data
            }
            
            # Usar repositorio para guardar
            try:
                page_id = await self.bet_repository.save(bet_data)
            except Exception as e:
                logger.error(f"Error usando repositorio: {e}")
                if status:
                    await status.edit_text("❌ Error creando registro")
                return
            
            # 4.5. ELIMINAR IMAGEN TEMPORAL DESPUÉS DE SUBIR EXITOSAMENTE
            await self.file_storage.delete(filename)
            
            # 5. CONFIRMACIÓN FINAL CON INFORMACIÓN DE REENVÍO
            user_name = self._get_user_name(message)
            
            # Agregar resultado del análisis al mensaje de éxito
            success_message = (
                f"✅ **¡Imagen procesada exitosamente!**\n\n"
                f"📄 **Registro creado en Notion**\n"
                f"👤 **Usuario**: {user_name}\n"
                f"📁 **Archivo**: `{filename}`\n"
                f"🆔 **Page ID**: `{page_id[:20]}...`\n\n"
                f"🔍 **Análisis de la imagen**:\n```json\n{analysis_result}\n```"
            )
            # success_message ya está definido arriba
            
            # Agregar información de reenvío si aplica
            forward_response = self._format_forward_response(message_data.get("forwarding", {}))
            if forward_response:
                success_message += forward_response
            
            success_message += "\n\n🔗 Revisa tu base de datos de Notion para ver el registro completo."
            
            # Enviar mensaje final (evitando rate limiting)
            if status:
                try:
                    await status.edit_text(success_message, parse_mode='Markdown')
                except Exception as e:
                    logger.warning(f"No se pudo editar mensaje de estado: {e}")
                    # Intentar enviar un nuevo mensaje
                    try:
                        await message.reply_text(success_message, parse_mode='Markdown')
                    except Exception as e2:
                        logger.error(f"No se pudo enviar mensaje de éxito: {e2}")
            
            # Log con información completa
            self._log_message_info(message_data, True, filename)
            logger.info(f"✅ Imagen procesada: {filename} -> {page_id}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}")
            if status:
                try:
                    await status.edit_text(f"❌ Error: {str(e)[:100]}...")
                except Exception:
                    logger.error("No se pudo enviar mensaje de error")
    
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
    
    async def _create_notion_record(self, message: Message, filename: str, file_upload_id: str, message_data: Optional[dict] = None, analysis_result: Optional[str] = None) -> Optional[str]:
        """
        PASO 3: Crear registro en Notion con archivo real adjunto, información completa de reenvío y análisis de OpenAI
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
            
            # Procesar el resultado del análisis si está disponible
            analyzed_data = {}
            if analysis_result:
                try:
                    if isinstance(analysis_result, str):
                        # Eliminar posibles marcadores de código
                        cleaned_json = analysis_result.replace('```json', '').replace('```', '').strip()
                        logger.info(f"Intentando parsear JSON: {cleaned_json}")
                        analyzed_data = json.loads(cleaned_json)
                        logger.info(f"JSON parseado exitosamente: {analyzed_data}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error decodificando JSON del análisis: {e}\nJSON recibido: {analysis_result}")
                except Exception as e:
                    logger.error(f"Error inesperado procesando JSON: {e}\nJSON recibido: {analysis_result}")

            # Extraer y limpiar valores del análisis
            cuota = "0"
            monto = "0"
            if analyzed_data:
                cuota = analyzed_data.get("Cuota", "0").replace(",", ".")
                monto = analyzed_data.get("Monto_Apostado", "0").replace("€", "").strip()
            
            try:
                cuota = float(cuota)
            except ValueError:
                cuota = 0
                
            try:
                monto = float(monto or "0")
            except ValueError:
                monto = 0

            # Propiedades del registro (usando nombres correctos de la base de datos)
            properties = {
                "Evento / Selección": {
                    "title": [
                        {
                            "text": {
                                "content": analyzed_data.get("Evento", title)
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
                }, "Casa de apuestas": {
                    "select": {
                        "name": "bet365"
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
                "Mercado": {
                    "rich_text": [
                        {
                            "text": {
                                "content": analyzed_data.get("Mercado", "")
                            }
                        }
                    ]
                },
                "Seleccion": {
                    "rich_text": [
                        {
                            "text": {
                                "content": analyzed_data.get("Seleccion", "")
                            }
                        }
                    ]
                },
                "Cuota": {
                    "number": float(analyzed_data.get("Cuota", "0").replace(",", "."))
                },
                "Importe apostado": {
                    "number": 500
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
    
    # REMOVED: _delete_temp_image
    # Now using LocalFileStorage adapter for file operations
            return False
    
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
            message_data = self.message_extractor.extract_metadata(message)
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
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Maneja errores globales de la aplicación"""
        logger.error(f"Error en actualización: {context.error}")
        
        # Manejar rate limiting específicamente
        if "RetryAfter" in str(type(context.error).__name__):
            retry_after = getattr(context.error, 'retry_after', 20)
            logger.warning(f"⚠️ Rate limit alcanzado. Esperando {retry_after} segundos...")
            await asyncio.sleep(retry_after)
            return
        
        # Para otros errores, solo loguear
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Ocurrió un error procesando tu mensaje. Por favor intenta de nuevo."
                )
            except Exception:
                logger.error("No se pudo enviar mensaje de error al usuario")
    
    def run(self):
        """Inicia el bot y lo mantiene funcionando"""
        logger.info("🚀 Iniciando aplicación de Telegram...")
        
        # Crear aplicación
        if not self.telegram_token:
            raise ValueError("Token de Telegram no disponible")
            
        application = Application.builder().token(self.telegram_token).build()
        
        # Agregar manejador de errores PRIMERO
        application.add_error_handler(self.error_handler)
        
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
        print(f"⚙️  Sistema de cola: {self.max_concurrent_processing} imagen(es) simultánea(s)")
        print("📸 Envía imágenes al bot para procesarlas")
        print("⏹️  Presiona Ctrl+C para detener")
        print("="*60)
        
        # Iniciar procesador de cola en segundo plano
        async def post_init(app):
            """Inicia el procesador de cola después de que la app se inicializa"""
            self.queue_task = asyncio.create_task(self.queue_processor())
            logger.info("✅ Procesador de cola iniciado")
        
        async def post_shutdown(app):
            """Detiene el procesador de cola al cerrar"""
            if self.queue_task and not self.queue_task.done():
                await self.processing_queue.put(None)  # Señal de parada
                try:
                    await asyncio.wait_for(self.queue_task, timeout=5.0)
                except asyncio.TimeoutError:
                    self.queue_task.cancel()
                logger.info("✅ Procesador de cola detenido")
        
        application.post_init = post_init
        application.post_shutdown = post_shutdown
        
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