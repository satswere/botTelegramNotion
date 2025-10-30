"""
IMessageExtractor - Interfaz de Extractor de Mensajes

Define el contrato para extracción de datos de mensajes sin conocer la plataforma.
Permite soportar múltiples plataformas (Telegram, Discord, WhatsApp, etc.).
"""

from typing import Protocol, Dict, Any, Optional
from datetime import datetime


class IMessageExtractor(Protocol):
    """
    Puerto (Interface) para extracción de datos de mensajes.

    Esta interfaz define las operaciones para extraer información
    de mensajes sin depender de una plataforma específica.

    Implementaciones:
        - TelegramMessageExtractor (actual)
        - DiscordMessageExtractor (futuro)
        - WhatsAppMessageExtractor (futuro)
        - MockMessageExtractor (tests)

    Ejemplo de uso:
        >>> extractor = TelegramMessageExtractor()
        >>> metadata = extractor.extract_metadata(telegram_message)
        >>> print(metadata["user_name"])
    """

    def extract_metadata(self, message: Any) -> Dict[str, Any]:
        """
        Extrae metadatos del mensaje de forma genérica.

        Args:
            message: Objeto de mensaje (tipo específico de la plataforma)

        Returns:
            Dict con metadatos extraídos:
                - message_id: str - ID único del mensaje
                - user_id: str - ID del usuario
                - user_name: str - Nombre del usuario
                - username: Optional[str] - Username (@usuario)
                - timestamp: datetime - Fecha y hora del mensaje
                - chat_id: str - ID del chat/canal
                - chat_type: str - Tipo de chat (private, group, channel)
                - is_forwarded: bool - Si es un mensaje reenviado
                - forward_info: Optional[Dict] - Info del mensaje original
                - has_media: bool - Si tiene archivos adjuntos
                - text: Optional[str] - Texto del mensaje

        Example:
            >>> metadata = extractor.extract_metadata(message)
            >>> print(f"Usuario: {metadata['user_name']}")
            >>> print(f"Fecha: {metadata['timestamp']}")
            >>> if metadata['is_forwarded']:
            ...     print(f"Reenviado de: {metadata['forward_info']['from']}")
        """
        ...

    def extract_forward_info(self, message: Any) -> Optional[Dict[str, Any]]:
        """
        Extrae información detallada de mensajes reenviados.

        Args:
            message: Objeto de mensaje

        Returns:
            Dict con información de reenvío o None si no es reenviado:
                - origin_user_id: Optional[str] - ID usuario original
                - origin_user_name: Optional[str] - Nombre usuario original
                - origin_username: Optional[str] - Username original
                - origin_chat_id: Optional[str] - ID chat original
                - origin_chat_title: Optional[str] - Título chat original
                - origin_date: Optional[datetime] - Fecha mensaje original
                - is_anonymous: bool - Si el origen es anónimo
                - unique_identifier: str - ID único del reenvío

        Example:
            >>> forward_info = extractor.extract_forward_info(message)
            >>> if forward_info:
            ...     print(f"Original de: {forward_info['origin_user_name']}")
            ...     print(f"Fecha original: {forward_info['origin_date']}")
        """
        ...

    async def extract_file(self, message: Any) -> Optional[Dict[str, Any]]:
        """
        Extrae información del archivo adjunto en el mensaje.

        Args:
            message: Objeto de mensaje con archivo adjunto

        Returns:
            Dict con información del archivo o None si no tiene:
                - file_id: str - ID único del archivo
                - file_name: str - Nombre del archivo
                - file_size: int - Tamaño en bytes
                - mime_type: str - Tipo MIME
                - file_type: str - Tipo (photo, document, video, etc.)
                - download_url: Optional[str] - URL de descarga

        Example:
            >>> file_info = await extractor.extract_file(message)
            >>> if file_info:
            ...     print(f"Archivo: {file_info['file_name']}")
            ...     print(f"Tamaño: {file_info['file_size']} bytes")
        """
        ...

    def is_valid_message(self, message: Any) -> bool:
        """
        Valida que el mensaje sea procesable.

        Args:
            message: Objeto de mensaje

        Returns:
            bool: True si es válido, False en caso contrario

        Example:
            >>> if extractor.is_valid_message(message):
            ...     metadata = extractor.extract_metadata(message)
        """
        ...
