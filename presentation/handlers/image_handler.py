"""
Image Handler - Refactorizado

Maneja el punto de entrada para imágenes de Telegram.
Delega toda la orquestación al MessageProcessor.

Responsabilidades:
- Recibir mensaje con imagen
- Agregar a cola de procesamiento
- Delegar procesamiento al MessageProcessor
- Gestionar respuestas al usuario
"""

import asyncio
import logging
from pathlib import Path
from telegram import Update, Message
from telegram.ext import ContextTypes

from application.orchestration import MessageProcessor, MessageProcessingError

logger = logging.getLogger(__name__)


class ImageHandler:
    """
    Handler para procesar imágenes de apuestas.

    Esta clase actúa como punto de entrada desde Telegram,
    delegando toda la lógica de orquestación al MessageProcessor.
    """

    def __init__(
        self,
        message_processor: MessageProcessor,
        processing_queue: asyncio.Queue,
        delay_between_messages: float = 1.0,
    ):
        """
        Inicializa el handler de imágenes.

        Args:
            message_processor: Procesador de mensajes (orquestador)
            processing_queue: Cola para procesamiento asíncrono
            delay_between_messages: Delay entre procesamiento de mensajes
        """
        self._message_processor = message_processor
        self._processing_queue = processing_queue
        self._delay_between_messages = delay_between_messages

        logger.info("📸 ImageHandler inicializado (refactorizado con MessageProcessor)")

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
                await message.reply_text(
                    f"⏳ Tu imagen está en la cola. Posición: {queue_size + 1}"
                )
            except Exception as e:
                logger.warning(f"No se pudo enviar mensaje de cola: {e}")

        logger.info(f"📥 Imagen agregada a la cola (total en cola: {queue_size + 1})")

    async def process_from_queue(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Procesa imagen desde la cola (llamado por el queue processor).

        Delega todo el procesamiento al MessageProcessor.

        Args:
            update: Update de Telegram
            context: Contexto de Telegram
        """
        message = update.message
        if not message:
            return

        # Mensaje de estado inicial
        status = None
        try:
            status = await message.reply_text("🔄 Procesando imagen...")
        except Exception as e:
            logger.warning(f"No se pudo enviar mensaje de estado: {e}")

        try:
            # Delegar procesamiento al MessageProcessor
            logger.info(f"📨 Delegando procesamiento al MessageProcessor...")

            result = await self._message_processor.process_image_message(
                update, context
            )

            if result["success"]:
                # Formatear respuesta de éxito
                response = self._message_processor.format_success_response(
                    bet_dto=result["bet_dto"],
                    message=message,
                    message_data=result["message_data"],
                )

                # Enviar respuesta
                if status:
                    await status.edit_text(response, parse_mode="Markdown")
                else:
                    await message.reply_text(response, parse_mode="Markdown")

                logger.info(f"✅ Imagen procesada exitosamente")
            else:
                error_msg = f"❌ Error procesando imagen"
                if status:
                    await status.edit_text(error_msg)
                else:
                    await message.reply_text(error_msg)

        except MessageProcessingError as e:
            logger.error(f"❌ Error en procesamiento: {e}")
            error_msg = f"❌ Error procesando imagen: {str(e)[:100]}"
            if status:
                await status.edit_text(error_msg)
            else:
                await message.reply_text(error_msg)

        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}", exc_info=True)
            error_msg = f"❌ Error inesperado procesando imagen"
            if status:
                await status.edit_text(error_msg)
            else:
                await message.reply_text(error_msg)
