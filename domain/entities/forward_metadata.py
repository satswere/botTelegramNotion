"""
ForwardMetadata Entity

Represents metadata about forwarded Telegram messages.
Encapsulates origin information and forwarding details.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib


@dataclass
class ForwardMetadata:
    """Metadata extracted from a forwarded Telegram message."""

    # Identification
    unique_identifier: Optional[str]
    is_forwarded: bool

    # Origin information
    origin_sender_user_id: Optional[int] = None
    origin_sender_name: Optional[str] = None
    origin_sender_username: Optional[str] = None
    origin_chat_id: Optional[int] = None
    origin_chat_title: Optional[str] = None
    origin_chat_username: Optional[str] = None

    # Timestamps
    forward_date: Optional[datetime] = None
    origin_date: Optional[datetime] = None

    # Flags
    is_automatic_forward: bool = False
    is_private_user: bool = False

    @property
    def origin_display_name(self) -> str:
        """Get a display-friendly name for the origin."""
        if self.origin_sender_name:
            return self.origin_sender_name
        if self.origin_sender_username:
            return f"@{self.origin_sender_username}"
        if self.origin_chat_title:
            return self.origin_chat_title
        if self.origin_chat_username:
            return f"@{self.origin_chat_username}"
        return "Unknown"

    @property
    def is_from_channel(self) -> bool:
        """Check if message was forwarded from a channel."""
        return bool(self.origin_chat_id and not self.origin_sender_user_id)

    @property
    def is_from_user(self) -> bool:
        """Check if message was forwarded from a user."""
        return bool(self.origin_sender_user_id or self.origin_sender_name)

    @classmethod
    def create_from_message_data(
        cls, message_data: dict
    ) -> Optional["ForwardMetadata"]:
        """
        Create ForwardMetadata from extracted message data.

        Args:
            message_data: Dictionary with forwarding information

        Returns:
            ForwardMetadata instance or None if not forwarded
        """
        forwarding = message_data.get("forwarding", {})

        if not forwarding.get("is_forwarded"):
            return None

        origin_info = forwarding.get("origin_info", {})

        # Parse dates
        forward_date = None
        origin_date = None

        if forwarding.get("forward_date"):
            try:
                forward_date = datetime.fromisoformat(forwarding["forward_date"])
            except (ValueError, TypeError):
                pass

        if origin_info.get("origin_date"):
            try:
                origin_date = datetime.fromisoformat(origin_info["origin_date"])
            except (ValueError, TypeError):
                pass

        # Determine if user is private
        is_private = bool(
            origin_info.get("origin_sender_name")
            and not origin_info.get("origin_sender_user_id")
        )

        return cls(
            unique_identifier=forwarding.get("unique_identifier"),
            is_forwarded=True,
            origin_sender_user_id=origin_info.get("origin_sender_user_id"),
            origin_sender_name=origin_info.get("origin_sender_name"),
            origin_sender_username=origin_info.get("origin_sender_username"),
            origin_chat_id=origin_info.get("origin_chat_id"),
            origin_chat_title=origin_info.get("origin_chat_title"),
            origin_chat_username=origin_info.get("origin_chat_username"),
            forward_date=forward_date,
            origin_date=origin_date,
            is_automatic_forward=forwarding.get("is_automatic_forward", False),
            is_private_user=is_private,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "unique_identifier": self.unique_identifier,
            "is_forwarded": self.is_forwarded,
            "origin_display_name": self.origin_display_name,
            "origin_sender_user_id": self.origin_sender_user_id,
            "origin_sender_name": self.origin_sender_name,
            "origin_sender_username": self.origin_sender_username,
            "origin_chat_id": self.origin_chat_id,
            "origin_chat_title": self.origin_chat_title,
            "origin_chat_username": self.origin_chat_username,
            "forward_date": (
                self.forward_date.isoformat() if self.forward_date else None
            ),
            "origin_date": self.origin_date.isoformat() if self.origin_date else None,
            "is_automatic_forward": self.is_automatic_forward,
            "is_private_user": self.is_private_user,
            "is_from_channel": self.is_from_channel,
            "is_from_user": self.is_from_user,
        }
