"""
Odds Value Object

Immutable representation of betting odds.
Supports decimal format (European style).
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Odds:
    """Represents betting odds in decimal format."""

    value: Decimal

    def __post_init__(self):
        """Validate odds value object."""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

        if self.value < Decimal("1.01"):
            raise ValueError("Odds must be at least 1.01")

        if self.value > Decimal("1000.0"):
            raise ValueError("Odds cannot exceed 1000.0")

    def __str__(self) -> str:
        """String representation."""
        return f"{self.value:.2f}"

    def calculate_profit_factor(self) -> Decimal:
        """
        Calculate profit factor (odds - 1).
        Example: odds 2.50 = 1.50 profit factor
        """
        return self.value - Decimal("1")

    def is_favorite(self) -> bool:
        """Check if this represents a favorite (odds < 2.0)."""
        return self.value < Decimal("2.0")

    def is_underdog(self) -> bool:
        """Check if this represents an underdog (odds > 3.0)."""
        return self.value > Decimal("3.0")

    def implied_probability(self) -> Decimal:
        """
        Calculate implied probability.
        Formula: 1 / odds
        """
        return Decimal("1") / self.value

    @classmethod
    def from_string(cls, value: str) -> Optional["Odds"]:
        """
        Parse odds from string format.
        Examples: "1.90", "2.50", "3.75"
        """
        if not value or value == "No especificado":
            return None

        value = value.strip()

        try:
            # Remove any non-numeric characters except . and ,
            value = value.replace(",", ".")
            odds_value = Decimal(value)
            return cls(odds_value)
        except (ValueError, ArithmeticError):
            return None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "value": float(self.value),
            "formatted": str(self),
            "implied_probability": float(self.implied_probability()),
            "is_favorite": self.is_favorite(),
            "is_underdog": self.is_underdog(),
        }
