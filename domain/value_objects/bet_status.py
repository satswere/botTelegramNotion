"""
BetStatus Value Object

Immutable representation of bet status.
Enforces valid status transitions.
"""
from enum import Enum
from typing import Optional


class BetStatusType(Enum):
    """Valid bet status types."""
    PENDING = "Pendiente"
    WON = "Ganada"
    LOST = "Perdida"
    VOID = "Anulada"
    CASHOUT = "Cashout"


class BetStatus:
    """Represents the status of a bet with validation."""
    
    def __init__(self, status: BetStatusType):
        """Initialize bet status."""
        if not isinstance(status, BetStatusType):
            raise ValueError(f"Invalid status type: {status}")
        self._status = status
    
    @property
    def value(self) -> BetStatusType:
        """Get status value."""
        return self._status
    
    @property
    def display_name(self) -> str:
        """Get display name."""
        return self._status.value
    
    def is_pending(self) -> bool:
        """Check if bet is pending."""
        return self._status == BetStatusType.PENDING
    
    def is_settled(self) -> bool:
        """Check if bet is settled (won/lost/void)."""
        return self._status in (BetStatusType.WON, BetStatusType.LOST, BetStatusType.VOID)
    
    def is_won(self) -> bool:
        """Check if bet was won."""
        return self._status == BetStatusType.WON
    
    def is_lost(self) -> bool:
        """Check if bet was lost."""
        return self._status == BetStatusType.LOST
    
    def can_transition_to(self, new_status: 'BetStatus') -> bool:
        """
        Check if transition to new status is valid.
        Rules:
        - PENDING can transition to any status
        - Settled bets cannot change
        """
        if self.is_settled():
            return False
        return True
    
    @classmethod
    def from_string(cls, value: str) -> Optional['BetStatus']:
        """
        Parse status from string.
        Accepts: "Pendiente", "Ganada", "Perdida", "Anulada", "Cashout"
        """
        if not value:
            return None
        
        value = value.strip()
        
        # Map strings to enum values
        status_map = {
            "Pendiente": BetStatusType.PENDING,
            "Ganada": BetStatusType.WON,
            "Perdida": BetStatusType.LOST,
            "Anulada": BetStatusType.VOID,
            "Cashout": BetStatusType.CASHOUT,
            # English alternatives
            "pending": BetStatusType.PENDING,
            "won": BetStatusType.WON,
            "lost": BetStatusType.LOST,
            "void": BetStatusType.VOID,
            "cashout": BetStatusType.CASHOUT
        }
        
        status_type = status_map.get(value)
        if not status_type:
            return cls(BetStatusType.PENDING)  # Default to pending
        
        return cls(status_type)
    
    @classmethod
    def pending(cls) -> 'BetStatus':
        """Create pending status."""
        return cls(BetStatusType.PENDING)
    
    @classmethod
    def won(cls) -> 'BetStatus':
        """Create won status."""
        return cls(BetStatusType.WON)
    
    @classmethod
    def lost(cls) -> 'BetStatus':
        """Create lost status."""
        return cls(BetStatusType.LOST)
    
    def __str__(self) -> str:
        """String representation."""
        return self.display_name
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, BetStatus):
            return False
        return self._status == other._status
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self._status)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "value": self._status.name,
            "display_name": self.display_name,
            "is_pending": self.is_pending(),
            "is_settled": self.is_settled()
        }
