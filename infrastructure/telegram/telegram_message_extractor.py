"""Telegram Message Extractor - Extrae datos de mensajes de Telegram"""

import logging
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from telegram import Message

logger = logging.getLogger(__name__)


class TelegramMessageExtractor:
    """Extractor de información de mensajes de Telegram"""
    
    def extract_metadata(self, message: Message) -> Dict[str, Any]:
        """Extrae metadatos completos del mensaje"""
        message_data = {
            "timestamp": datetime.now().isoformat(),
            "message_id": message.message_id,
            "date": message.date.isoformat() if message.date else None,
        }
        
        # Información del usuario
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
        
        # Información de reenvío
        forward_info = self.extract_forward_info(message)
        message_data["forwarding"] = forward_info
        
        # Texto del mensaje
        message_data["text"] = message.text or message.caption or ""
        
        # Información de medios
        message_data["has_media"] = bool(message.photo or message.document)
        
        return message_data
    
    def extract_forward_info(self, message: Message) -> Optional[Dict[str, Any]]:
        """Extrae información de mensajes reenviados"""
        forward_from = getattr(message, 'forward_from', None)
        forward_from_chat = getattr(message, 'forward_from_chat', None)
        forward_sender_name = getattr(message, 'forward_sender_name', None)
        forward_date = getattr(message, 'forward_date', None)
        is_automatic_forward = getattr(message, 'is_automatic_forward', False)
        forward_origin = getattr(message, 'forward_origin', None)
        
        origin_info = {}
        
        # API moderna
        if forward_origin:
            if hasattr(forward_origin, 'sender_user') and forward_origin.sender_user:
                sender_user = forward_origin.sender_user
                origin_info["origin_sender_user_id"] = sender_user.id
                origin_info["origin_sender_name"] = f"{getattr(sender_user, 'first_name', '') or ''} {getattr(sender_user, 'last_name', '') or ''}".strip()
                origin_info["origin_sender_username"] = getattr(sender_user, 'username', None)
                
            elif hasattr(forward_origin, 'sender_user_name') and forward_origin.sender_user_name:
                origin_info["origin_sender_name"] = getattr(forward_origin, 'sender_user_name', None)
                
            elif hasattr(forward_origin, 'chat') and forward_origin.chat:
                chat = forward_origin.chat
                origin_info["origin_chat_id"] = chat.id
                origin_info["origin_chat_title"] = getattr(chat, 'title', None)
                origin_info["origin_chat_username"] = getattr(chat, 'username', None)
        
        # Fecha origen
        origin_date = getattr(forward_origin, 'date', None) if forward_origin else None
        if origin_date:
            origin_info["origin_date"] = origin_date.isoformat()
        
        # Determinar si es reenviado
        is_forwarded = bool(
            forward_from or forward_from_chat or forward_sender_name or 
            forward_date or forward_origin or is_automatic_forward
        )
        
        if not is_forwarded:
            return {
                "is_forwarded": False,
                "origin_info": {}
            }
        
        # Generar ID único
        unique_identifier = self._generate_unique_identifier(origin_info, forward_date)
        
        forward_info = {
            "is_forwarded": True,
            "forward_date": forward_date.isoformat() if forward_date else None,
            "is_automatic_forward": is_automatic_forward,
            "unique_identifier": unique_identifier,
            "origin_info": origin_info
        }
        
        # Compatibilidad con API legacy
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
    
    async def extract_file(self, message: Message) -> Optional[Dict[str, Any]]:
        """Extrae información del archivo adjunto"""
        if message.photo:
            photo = message.photo[-1]  # Mayor resolución
            return {
                "file_id": photo.file_id,
                "file_type": "photo",
                "file_size": photo.file_size,
                "width": photo.width,
                "height": photo.height,
            }
        elif message.document:
            doc = message.document
            return {
                "file_id": doc.file_id,
                "file_name": doc.file_name,
                "file_type": "document",
                "file_size": doc.file_size,
                "mime_type": doc.mime_type,
            }
        return None
    
    def is_valid_message(self, message: Message) -> bool:
        """Valida que el mensaje sea procesable"""
        return message is not None and message.from_user is not None
    
    def _generate_unique_identifier(self, origin_info: Dict, forward_date) -> Optional[str]:
        """Genera ID único para el reenvío"""
        identifier_parts = []
        
        if origin_info.get("origin_sender_user_id"):
            identifier_parts.append(f"USER_{origin_info['origin_sender_user_id']}")
        elif origin_info.get("origin_sender_name"):
            sender_name = origin_info["origin_sender_name"]
            if sender_name:
                name_hash = hashlib.md5(sender_name.encode('utf-8')).hexdigest()[:8]
                identifier_parts.append(f"PRIVATE_{name_hash}")
        elif origin_info.get("origin_chat_id"):
            identifier_parts.append(f"CHAT_{origin_info['origin_chat_id']}")
        
        # Fecha
        date_str = origin_info.get("origin_date") or (forward_date.isoformat() if forward_date else None)
        if date_str:
            identifier_parts.append(f"DATE_{date_str[:10]}")
        
        return "_".join(identifier_parts) if identifier_parts else None
