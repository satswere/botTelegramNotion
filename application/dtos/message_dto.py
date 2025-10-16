"""
Message DTO

Data Transfer Object for Telegram message information.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class MessageDTO:
    """DTO for Telegram message data."""
    
    # Message identification
    message_id: int
    chat_id: int
    
    # User information
    user_id: int
    username: Optional[str]
    user_full_name: str
    
    # Message content
    text: Optional[str] = None
    caption: Optional[str] = None
    
    # File information
    has_photo: bool = False
    has_document: bool = False
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    
    # Forwarding information
    is_forwarded: bool = False
    forward_metadata: Optional[Dict[str, Any]] = None
    
    # Timestamps
    message_date: Optional[str] = None
    
    @classmethod
    def from_telegram_update(cls, message) -> 'MessageDTO':
        """
        Create DTO from Telegram message object.
        
        Args:
            message: Telegram Message object
            
        Returns:
            MessageDTO instance
        """
        user = message.from_user
        
        # Check for photo
        has_photo = bool(message.photo)
        file_id = None
        if has_photo:
            file_id = message.photo[-1].file_id  # Largest photo
        
        # Check for document
        has_document = bool(message.document)
        file_name = None
        if has_document:
            file_id = message.document.file_id
            file_name = message.document.file_name
        
        return cls(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=user.id,
            username=getattr(user, 'username', None),
            user_full_name=f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
            text=message.text,
            caption=message.caption,
            has_photo=has_photo,
            has_document=has_document,
            file_id=file_id,
            file_name=file_name,
            is_forwarded=bool(getattr(message, 'forward_date', None)),
            message_date=message.date.isoformat() if message.date else None
        )
