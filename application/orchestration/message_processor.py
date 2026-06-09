"""
Message Processor - Capa de Orquestación

Procesa mensajes entrantes y coordina el flujo:
mensaje -> identificación de tipo -> comando -> servicio

Responsabilidades:
- Identificar tipo de mensaje (comando, foto, texto)
- Descargar archivos de Telegram
- Subir archivos a Notion
- Coordinar use cases según el tipo de mensaje
- Gestionar respuestas al usuario
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path
from telegram import Update, Message, File
from telegram.ext import ContextTypes
from notion_client import Client

from application.use_cases import ProcessBetImageUseCase
from application.dtos import ImageDTO, MessageDTO
from domain.repositories import IMessageExtractor
from infrastructure.notion.notion_file_uploader import NotionFileUploader, NotionFileUploaderError

logger = logging.getLogger(__name__)


class MessageProcessingError(Exception):
    """Error durante el procesamiento de mensajes."""

    pass


class MessageProcessor:
    """
    Procesa mensajes de Telegram y coordina el flujo completo.

    Esta clase actúa como orquestador principal que:
    1. Identifica el tipo de mensaje
    2. Ejecuta las acciones necesarias (download, upload)
    3. Invoca los use cases apropiados
    4. Gestiona las respuestas al usuario
    """

    def __init__(
        self,
        process_bet_use_case: ProcessBetImageUseCase,
        message_extractor: IMessageExtractor,
        notion_client: Client,
        database_id: str,
        images_path: Path,
        notion_file_uploader: NotionFileUploader,
    ):
        """
        Inicializa el procesador de mensajes.

        Args:
            process_bet_use_case: Use case para procesar apuestas con imagen
            message_extractor: Extractor de metadatos de mensajes
            notion_client: Cliente de Notion para uploads
            database_id: ID de la base de datos de Notion
            images_path: Ruta para almacenar imágenes temporales
            notion_file_uploader: Servicio para subir archivos a Notion
        """
        self._process_bet_use_case = process_bet_use_case
        self._message_extractor = message_extractor
        self._notion_client = notion_client
        self._database_id = database_id
        self._images_path = images_path
        self._notion_file_uploader = notion_file_uploader

        # Asegurar que existe el directorio
        self._images_path.mkdir(parents=True, exist_ok=True)

    async def process_image_message(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje con imagen.

        Flujo completo:
        1. Extrae metadatos del mensaje
        2. Descarga la imagen
        3. Sube la imagen a Notion
        4. Ejecuta el use case de procesamiento
        5. Retorna el resultado

        Args:
            update: Update de Telegram
            context: Contexto de Telegram

        Returns:
            Diccionario con el resultado del procesamiento

        Raises:
            MessageProcessingError: Si falla algún paso del procesamiento
        """
        message = update.message
        if not message:
            raise MessageProcessingError("Mensaje no disponible en update")

        logger.info(
            f"📸 Procesando mensaje con imagen de usuario {message.from_user.id}"
        )

        try:
            # 1. Extraer metadatos
            message_data = self._extract_message_metadata(message)

            # 2. Descargar imagen
            filename = await self._download_image(message, context)

            # 3. Subir imagen a Notion
            notion_file_id = await self._upload_image_to_notion(filename)

            # 4. Crear DTOs
            image_dto = self._create_image_dto(message, filename)
            message_dto = self._create_message_dto(message, message_data)

            # 5. Ejecutar use case con el file_upload_id
            bet_dto = await self._process_bet_use_case.execute(
                image_dto=image_dto,
                message_dto=message_dto,
                notion_file_id=notion_file_id,
            )

            logger.info(f"Imagen procesada exitosamente - bet_id: {bet_dto.id}")

            return {
                "success": True,
                "bet_dto": bet_dto,
                "message_data": message_data,
                "filename": filename,
            }

        except Exception as e:
            logger.error(f"Error procesando mensaje con imagen: {e}", exc_info=True)
            raise MessageProcessingError(f"Error en procesamiento: {str(e)}") from e

    def _extract_message_metadata(self, message: Message) -> Dict[str, Any]:
        """
        Extrae metadatos del mensaje de Telegram.

        Args:
            message: Mensaje de Telegram

        Returns:
            Diccionario con metadatos extraídos
        """
        try:
            return self._message_extractor.extract_metadata(message)
        except Exception as e:
            logger.error(f"Error extrayendo metadatos: {e}")
            # Retornar metadatos mínimos si falla
            return {
                "message_id": message.message_id,
                "timestamp": message.date.isoformat() if message.date else None,
                "forwarding": {"is_forwarded": False},
            }

    async def _download_image(
        self, message: Message, context: ContextTypes.DEFAULT_TYPE
    ) -> str:
        """
        Descarga la imagen del mensaje de Telegram.

        Args:
            message: Mensaje con foto
            context: Contexto de Telegram

        Returns:
            Nombre del archivo descargado

        Raises:
            MessageProcessingError: Si no hay foto o falla la descarga
        """
        if not message.photo:
            raise MessageProcessingError("Mensaje no contiene foto")

        try:
            # Obtener la foto de mayor resolución
            photo = message.photo[-1]
            file: File = await context.bot.get_file(photo.file_id)

            # Generar nombre único
            filename = f"bet_{message.from_user.id}_{message.message_id}.jpg"
            file_path = self._images_path / filename

            # Descargar
            await file.download_to_drive(str(file_path))

            logger.info(f"Imagen descargada: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error descargando imagen: {e}")
            raise MessageProcessingError(f"Error descargando imagen: {str(e)}") from e

    async def _upload_image_to_notion(self, filename: str) -> Optional[str]:
        """
        Sube la imagen a Notion usando el servicio de upload.

        Args:
            filename: Nombre del archivo a subir

        Returns:
            file_upload_id si es exitoso, None si falla

        Raises:
            MessageProcessingError: Si falla la subida
        """
        file_path = self._images_path / filename

        try:
            file_upload_id = await self._notion_file_uploader.upload_file(file_path)
            
            if file_upload_id:
                logger.info(f"Imagen subida a Notion: {file_upload_id}")
            else:
                logger.warning(f"No se obtuvo file_upload_id para {filename}")
            
            return file_upload_id

        except NotionFileUploaderError as e:
            logger.error(f"Error subiendo imagen a Notion: {e}")
            # No lanzar excepción, solo advertir y continuar sin archivo
            return None
        except Exception as e:
            logger.error(f"Error inesperado subiendo imagen: {e}")
            return None

    def _create_image_dto(self, message: Message, filename: str) -> ImageDTO:
        """
        Crea un ImageDTO desde el mensaje.

        Args:
            message: Mensaje de Telegram
            filename: Nombre del archivo descargado

        Returns:
            ImageDTO configurado
        """
        file_path = str(self._images_path / filename)
        telegram_file_id = message.photo[-1].file_id if message.photo else None

        return ImageDTO(
            filename=filename, file_path=file_path, telegram_file_id=telegram_file_id
        )

    def _create_message_dto(
        self, message: Message, message_data: Dict[str, Any]
    ) -> MessageDTO:
        """
        Crea un MessageDTO desde el mensaje y sus metadatos.

        Args:
            message: Mensaje de Telegram
            message_data: Metadatos extraídos

        Returns:
            MessageDTO configurado
        """
        message_dto = MessageDTO.from_telegram_update(message)
        message_dto.forward_metadata = message_data.get("forwarding")

        return message_dto

    def format_success_response(
        self, bet_dto, message: Message, message_data: Dict[str, Any]
    ) -> str:
        """
        Formatea la respuesta de éxito para el usuario.

        Args:
            bet_dto: DTO de la apuesta procesada
            message: Mensaje original
            message_data: Metadatos del mensaje

        Returns:
            Texto formateado para enviar al usuario
        """
        user_name = self._get_user_name(message)

        response = "✅ **APUESTA PROCESADA EXITOSAMENTE**\n\n"
        response += "📋 **INFORMACIÓN EXTRAÍDA:**\n"
        response += "━━━━━━━━━━━━━━━━━━━━\n\n"

        # Evento
        if bet_dto.event and bet_dto.event != "No especificado":
            response += f"🎯 **Evento:** {bet_dto.event}\n"
        
        # Tipo de apuesta
        if bet_dto.bet_type and bet_dto.bet_type != "No especificado":
            response += f"📊 **Tipo:** {bet_dto.bet_type}\n"
        
        # Cuota
        if bet_dto.odds_value:
            response += f"💰 **Cuota:** {bet_dto.odds_value}\n"
        
        # Importe apostado
        if bet_dto.stake_amount:
            currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£"}.get(bet_dto.stake_currency, bet_dto.stake_currency)
            response += f"💵 **Importe:** {currency_symbol}{bet_dto.stake_amount:.2f}\n"
        
        # Ganancia potencial
        if bet_dto.potential_profit_amount:
            currency_symbol = {"EUR": "€", "USD": "$", "GBP": "£"}.get(bet_dto.potential_profit_currency, bet_dto.potential_profit_currency)
            response += f"🎁 **Ganancia potencial:** {currency_symbol}{bet_dto.potential_profit_amount:.2f}\n"
        
        # Estado
        estado_emoji = {"Pendiente": "⏳", "Ganada": "✅", "Perdida": "❌"}.get(bet_dto.status, "📌")
        response += f"{estado_emoji} **Estado:** {bet_dto.status}\n"

        # Usuario
        response += f"\n👤 **Usuario:** {user_name}\n"
        
        # ID de Notion
        if bet_dto.id:
            response += f"🔗 **ID Notion:** `{bet_dto.id[:20]}...`\n"

        response += "\n━━━━━━━━━━━━━━━━━━━━\n"
        response += "✅ **Guardado en Notion exitosamente**\n"

        # Agregar info de reenvío si existe
        forwarding = message_data.get("forwarding", {})
        if forwarding.get("is_forwarded"):
            origin = forwarding.get("origin_info", {})
            if origin.get("origin_sender_name"):
                response += f"\n↪️ Reenviado de: **{origin['origin_sender_name']}**"

        return response

    @staticmethod
    def _get_user_name(message: Message) -> str:
        """Obtiene el nombre del usuario del mensaje."""
        user = message.from_user
        if not user:
            return "Desconocido"

        name_parts = []
        if user.first_name:
            name_parts.append(user.first_name)
        if user.last_name:
            name_parts.append(user.last_name)

        if name_parts:
            return " ".join(name_parts)
        elif user.username:
            return f"@{user.username}"
        else:
            return f"User #{user.id}"
