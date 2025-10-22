"""
Bet Entity (Aggregate Root)

Core domain entity representing a sports bet.
Encapsulates all bet-related business logic and validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..value_objects import Money, Odds, BetStatus
from .bet_image import BetImage
from .forward_metadata import ForwardMetadata


@dataclass
class Bet:
    """
    Aggregate Root for Bet domain.

    A Bet represents a sports betting transaction with associated
    images, analysis, and metadata.
    """

    # Identity
    id: Optional[str] = None

    # Core bet information
    event: str = "No especificado"
    bet_type: str = "No especificado"
    stake: Optional[Money] = None
    odds: Optional[Odds] = None
    potential_profit: Optional[Money] = None

    # Status
    status: BetStatus = field(default_factory=BetStatus.pending)

    # Associated entities
    images: List[BetImage] = field(default_factory=list)
    forward_metadata: Optional[ForwardMetadata] = None

    # Telegram metadata
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    telegram_message_id: Optional[int] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    event_date: Optional[datetime] = None

    # Additional data
    notes: Optional[str] = None
    raw_analysis: Optional[Dict[str, Any]] = None

    @property
    def has_images(self) -> bool:
        """Check if bet has associated images."""
        return len(self.images) > 0

    @property
    def primary_image(self) -> Optional[BetImage]:
        """Get the first/primary image."""
        return self.images[0] if self.images else None

    @property
    def is_analyzed(self) -> bool:
        """Check if bet has been analyzed."""
        return bool(
            self.raw_analysis or (self.primary_image and self.primary_image.is_analyzed)
        )

    @property
    def is_from_forwarded_message(self) -> bool:
        """Check if bet was created from a forwarded message."""
        return bool(self.forward_metadata and self.forward_metadata.is_forwarded)

    @property
    def expected_return(self) -> Optional[Money]:
        """Calculate expected return (stake + profit)."""
        if not self.stake or not self.potential_profit:
            return None
        return self.stake + self.potential_profit

    def add_image(self, image: BetImage) -> None:
        """Add an image to the bet."""
        if not image.is_valid_image:
            raise ValueError(f"Invalid image format: {image.filename}")
        self.images.append(image)
        self.updated_at = datetime.now()

    def update_status(self, new_status: BetStatus) -> None:
        """
        Update bet status with validation.

        Args:
            new_status: New status to set

        Raises:
            ValueError: If status transition is invalid
        """
        if not self.status.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}. "
                "Settled bets cannot change status."
            )

        self.status = new_status
        self.updated_at = datetime.now()

    def calculate_profit(self) -> Optional[Money]:
        """
        Calculate actual profit based on stake and odds.
        Formula: stake * (odds - 1)
        """
        if not self.stake or not self.odds:
            return None

        profit_factor = self.odds.calculate_profit_factor()
        return self.stake.multiply(profit_factor)

    def set_forward_metadata(self, metadata: ForwardMetadata) -> None:
        """Set forwarding metadata for the bet."""
        self.forward_metadata = metadata
        self.updated_at = datetime.now()

    def update_from_analysis(self, analysis_data: Dict[str, Any]) -> None:
        """
        Update bet details from image analysis results.

        Args:
            analysis_data: Dictionary with analyzed bet information
        """
        self.raw_analysis = analysis_data

        # Función auxiliar para obtener valor con diferentes variantes
        def get_field(data, *keys):
            for key in keys:
                if key in data and data[key] and str(data[key]).strip() and str(data[key]) != "No especificado":
                    return data[key]
            return None

        # Update fields if present in analysis (soporta múltiples formatos)
        evento = get_field(analysis_data, "Evento", "evento")
        if evento:
            self.event = str(evento)

        tipo_apuesta = get_field(analysis_data, "tipo_apuesta", "Tipo_Apuesta")
        if tipo_apuesta:
            self.bet_type = str(tipo_apuesta)

        cuota = get_field(analysis_data, "Cuota", "cuota")
        if cuota:
            odds = Odds.from_string(str(cuota))
            if odds:
                self.odds = odds

        monto = get_field(analysis_data, "Monto_Apostado", "monto", "Monto")
        if monto:
            stake = Money.from_string(str(monto))
            if stake:
                self.stake = stake

        ganancia = get_field(analysis_data, "Ganancia_Potencial", "ganancia_potencial", "Ganancia")
        if ganancia:
            profit = Money.from_string(str(ganancia))
            if profit:
                self.potential_profit = profit

        estado = get_field(analysis_data, "Estado_Apuesta", "estado", "Estado")
        if estado:
            status = BetStatus.from_string(str(estado))
            if status:
                self.status = status

        fecha = get_field(analysis_data, "fecha", "Fecha")
        if fecha:
            try:
                self.event_date = datetime.fromisoformat(str(fecha))
            except (ValueError, TypeError):
                pass

        self.updated_at = datetime.now()

    @classmethod
    def create_from_telegram(
        cls,
        telegram_user_id: int,
        telegram_username: Optional[str],
        telegram_message_id: int,
        image: Optional[BetImage] = None,
        forward_metadata: Optional[ForwardMetadata] = None,
    ) -> "Bet":
        """
        Create a new bet from a Telegram message.

        Args:
            telegram_user_id: Telegram user ID
            telegram_username: Telegram username
            telegram_message_id: Telegram message ID
            image: Optional initial image
            forward_metadata: Optional forwarding metadata

        Returns:
            New Bet instance
        """
        bet = cls(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            telegram_message_id=telegram_message_id,
            forward_metadata=forward_metadata,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        if image:
            bet.add_image(image)

        return bet

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "event": self.event,
            "bet_type": self.bet_type,
            "stake": self.stake.to_dict() if self.stake else None,
            "odds": self.odds.to_dict() if self.odds else None,
            "potential_profit": (
                self.potential_profit.to_dict() if self.potential_profit else None
            ),
            "status": self.status.to_dict(),
            "images": [img.to_dict() for img in self.images],
            "forward_metadata": (
                self.forward_metadata.to_dict() if self.forward_metadata else None
            ),
            "telegram_user_id": self.telegram_user_id,
            "telegram_username": self.telegram_username,
            "telegram_message_id": self.telegram_message_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "event_date": self.event_date.isoformat() if self.event_date else None,
            "notes": self.notes,
            "has_images": self.has_images,
            "is_analyzed": self.is_analyzed,
            "is_from_forwarded_message": self.is_from_forwarded_message,
            "expected_return": (
                self.expected_return.to_dict() if self.expected_return else None
            ),
        }
