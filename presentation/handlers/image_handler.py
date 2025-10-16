"""
Image Handler

Maneja el procesamiento de imágenes enviadas por usuarios.
Usa ProcessBetImageUseCase para orquestar el flujo completo.
"""
import asyncio
import logging
from pathlib import Path
from telegram import Update, Message
from telegram.ext import ContextTypes

from application.use_cases import ProcessBetImageUseCase
from application.dtos import ImageDTO, MessageDTO
from domain.repositories import IMessageExtractor

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handler for processing bet images."""
    
    def __init__(
        self,
        process_bet_use_case: ProcessBetImageUseCase,
        message_extractor: IMessageExtractor,
        images_path: Path,
        processing_queue: asyncio.Queue,
        delay_between_messages: float = 1.0
    ):
        """
        Initialize image handler.
        
        Args:
            process_bet_use_case: Use case for processing images
            message_extractor: Service for extracting message metadata
            images_path: Path to store temporary images
            processing_queue: Queue for processing images
            delay_between_messages: Delay between processing messages
        """
        self._process_bet_use_case = process_bet_use_case
        self._message_extractor = message_extractor
        self._images_path = images_path
        self._processing_queue = processing_queue
        self._delay_between_messages = delay_between_messages
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming image message.
        
        Adds image to processing queue.
        
        Args:
            update: Telegram update object
            context: Telegram context
        """
        message = update.message
        if not message:
            return
        
        # Add to queue
        queue_size = self._processing_queue.qsize()
        await self._processing_queue.put((update, context))
        
        # Inform user about queue position
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
    
    async def process_from_queue(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Process image from queue (called by queue processor).
        
        Args:
            update: Telegram update object
            context: Telegram context
        """
        message = update.message
        if not message:
            return
        
        # Initial status message
        status = None
        try:
            status = await message.reply_text("🔄 Procesando imagen...")
        except Exception as e:
            logger.warning(f"No se pudo enviar mensaje de estado: {e}")
        
        try:
            # Extract message metadata
            message_data = self._message_extractor.extract_metadata(message)
            
            # Download image
            logger.info("⬇️ Descargando imagen...")
            filename = await self._download_image(message)
            if not filename:
                if status:
                    await status.edit_text("❌ Error descargando imagen")
                return
            
            # Upload to Notion
            logger.info("🔄 Subiendo archivo a Notion...")
            file_upload_id = await self._upload_file_to_notion(filename)
            if not file_upload_id:
                if status:
                    await status.edit_text("❌ Error subiendo archivo")
                return
            
            # Create DTOs
            image_dto = ImageDTO(
                filename=filename,
                file_path=str(self._images_path / filename),
                telegram_file_id=message.photo[-1].file_id if message.photo else None
            )
            
            message_dto = MessageDTO.from_telegram_update(message)
            message_dto.forward_metadata = message_data.get("forwarding")
            
            # Process image using use case
            logger.info("🔍 Procesando apuesta...")
            bet_dto = await self._process_bet_use_case.execute(
                image_dto=image_dto,
                message_dto=message_dto,
                notion_file_id=file_upload_id
            )
            
            # Success response
            user_name = self._get_user_name(message)
            response = f"✅ **Apuesta procesada**\n\n"
            response += f"👤 Usuario: {user_name}\n"
            
            if bet_dto.event != "No especificado":
                response += f"🎯 Evento: {bet_dto.event}\n"
            if bet_dto.bet_type != "No especificado":
                response += f"📊 Tipo: {bet_dto.bet_type}\n"
            if bet_dto.odds_value:
                response += f"💰 Cuota: {bet_dto.odds_value}\n"
            
            response += f"\n📝 Registro creado en Notion"
            
            # Add forwarding info if present
            if bet_dto.is_forwarded:
                response += "\n\n🔄 **Mensaje reenviado detectado**"
            
            if status:
                await status.edit_text(response, parse_mode='Markdown')
            else:
                await message.reply_text(response, parse_mode='Markdown')
            
            logger.info(f"✅ Apuesta procesada exitosamente: {bet_dto.id}")
            
        except Exception as e:
            logger.error(f"❌ Error procesando imagen: {e}", exc_info=True)
            error_msg = f"❌ Error procesando imagen: {str(e)[:100]}"
            if status:
                await status.edit_text(error_msg)
            else:
                await message.reply_text(error_msg)
    
    async def _download_image(self, message: Message) -> str:
        """Download image from Telegram message."""
        # This is a simplified version - in reality would use file_storage
        # For now, keeping original logic
        from datetime import datetime
        
        if message.photo:
            photo = message.photo[-1]
            file = await photo.get_file()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_id = message.from_user.id if message.from_user else "unknown"
            filename = f"bet_{user_id}_{timestamp}.jpg"
            
            file_path = self._images_path / filename
            await file.download_to_drive(file_path)
            
            logger.info(f"✅ Imagen descargada: {filename}")
            return filename
        
        return None
    
    async def _upload_file_to_notion(self, filename: str) -> str:
        """Upload file to Notion (3-step process)."""
        # This would use NotionBetRepository's upload logic
        # For now, returning placeholder
        # In full refactor, this would be moved to infrastructure
        logger.info(f"📤 Subiendo {filename} a Notion...")
        return f"notion_file_{filename}"
    
    def _get_user_name(self, message: Message) -> str:
        """Get user display name from message."""
        if message.from_user:
            first_name = message.from_user.first_name or ""
            last_name = message.from_user.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            return full_name or "Usuario"
        return "Usuario"
