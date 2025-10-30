"""
Money Value Object

Immutable representation of monetary amounts with currency.
Following Value Object pattern: equality by value, immutable.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Money:
    """Represents a monetary amount with currency."""

    amount: Decimal
    currency: str = "EUR"

    def __post_init__(self):
        """Validate money value object."""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code (e.g., EUR, USD)")

    def __str__(self) -> str:
        """String representation with currency symbol."""
        symbols = {"EUR": "€", "USD": "$", "GBP": "£"}
        symbol = symbols.get(self.currency, self.currency)
        return f"{symbol}{self.amount:.2f}"

    def __add__(self, other: "Money") -> "Money":
        """Add two money objects (same currency only)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract two money objects (same currency only)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: Decimal) -> "Money":
        """Multiply money by a factor (for odds calculations)."""
        return Money(self.amount * factor, self.currency)

    @classmethod
    def from_string(cls, value: str) -> Optional["Money"]:
        """
        Parse money from string format.
        Examples: "€50", "$100", "50 EUR", "100.50"
        """
        if not value or value == "No especificado":
            return None

        value = value.strip()

        # Extract currency symbol/code
        currency_map = {"€": "EUR", "$": "USD", "£": "GBP"}
        currency = "EUR"  # Default

        for symbol, code in currency_map.items():
            if symbol in value:
                currency = code
                value = value.replace(symbol, "").strip()
                break

        # Check for currency code at the end
        parts = value.split()
        if len(parts) == 2 and len(parts[1]) == 3:
            currency = parts[1].upper()
            value = parts[0]

        # Parse amount
        try:
            # Remove any remaining non-numeric characters except . and ,
            value = value.replace(",", ".")
            amount = Decimal(value)
            return cls(amount, currency)
        except (ValueError, ArithmeticError):
            return None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "amount": float(self.amount),
            "currency": self.currency,
            "formatted": str(self),
        }
