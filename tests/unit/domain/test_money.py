"""
Unit Tests for Money Value Object
"""

import pytest
from decimal import Decimal
from domain.value_objects import Money


class TestMoney:

    def test_create_money_with_valid_values(self):
        """Test creating money with valid amount and currency."""
        money = Money(Decimal("100.50"), "EUR")
        assert money.amount == Decimal("100.50")
        assert money.currency == "EUR"

    def test_money_auto_converts_float_to_decimal(self):
        """Test that float amounts are converted to Decimal."""
        money = Money(100.50, "USD")
        assert isinstance(money.amount, Decimal)
        assert money.amount == Decimal("100.50")

    def test_money_string_representation(self):
        """Test string formatting with currency symbols."""
        eur = Money(Decimal("50"), "EUR")
        usd = Money(Decimal("100"), "USD")

        assert str(eur) == "€50.00"
        assert str(usd) == "$100.00"

    def test_money_addition_same_currency(self):
        """Test adding two money objects with same currency."""
        m1 = Money(Decimal("50"), "EUR")
        m2 = Money(Decimal("30"), "EUR")
        result = m1 + m2

        assert result.amount == Decimal("80")
        assert result.currency == "EUR"

    def test_money_addition_different_currency_raises_error(self):
        """Test that adding different currencies raises error."""
        m1 = Money(Decimal("50"), "EUR")
        m2 = Money(Decimal("30"), "USD")

        with pytest.raises(ValueError, match="Cannot add EUR and USD"):
            m1 + m2

    def test_money_subtraction_same_currency(self):
        """Test subtracting two money objects."""
        m1 = Money(Decimal("100"), "EUR")
        m2 = Money(Decimal("30"), "EUR")
        result = m1 - m2

        assert result.amount == Decimal("70")

    def test_money_multiply_by_factor(self):
        """Test multiplying money by a factor."""
        money = Money(Decimal("50"), "EUR")
        result = money.multiply(Decimal("2.5"))

        assert result.amount == Decimal("125")
        assert result.currency == "EUR"

    def test_from_string_with_euro_symbol(self):
        """Test parsing from string with € symbol."""
        money = Money.from_string("€50.00")

        assert money.amount == Decimal("50.00")
        assert money.currency == "EUR"

    def test_from_string_with_dollar_symbol(self):
        """Test parsing from string with $ symbol."""
        money = Money.from_string("$100")

        assert money.amount == Decimal("100")
        assert money.currency == "USD"

    def test_from_string_with_currency_code(self):
        """Test parsing from string with currency code."""
        money = Money.from_string("50 EUR")

        assert money.amount == Decimal("50")
        assert money.currency == "EUR"

    def test_from_string_no_specified_returns_none(self):
        """Test that 'No especificado' returns None."""
        result = Money.from_string("No especificado")
        assert result is None

    def test_negative_amount_raises_error(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Money(Decimal("-50"), "EUR")

    def test_invalid_currency_raises_error(self):
        """Test that invalid currency codes are rejected."""
        with pytest.raises(ValueError, match="3-letter ISO code"):
            Money(Decimal("50"), "E")

    def test_to_dict(self):
        """Test dictionary serialization."""
        money = Money(Decimal("50.50"), "EUR")
        data = money.to_dict()

        assert data["amount"] == 50.50
        assert data["currency"] == "EUR"
        assert data["formatted"] == "€50.50"
