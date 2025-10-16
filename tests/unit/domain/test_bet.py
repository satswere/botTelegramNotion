"""
Unit Tests for Bet Entity
"""
import pytest
from decimal import Decimal
from datetime import datetime

from domain.entities import Bet, BetImage, ForwardMetadata
from domain.value_objects import Money, Odds, BetStatus


class TestBet:
    
    def test_create_bet_from_telegram(self):
        """Test creating a bet from Telegram message."""
        bet = Bet.create_from_telegram(
            telegram_user_id=12345,
            telegram_username="testuser",
            telegram_message_id=67890
        )
        
        assert bet.telegram_user_id == 12345
        assert bet.telegram_username == "testuser"
        assert bet.telegram_message_id == 67890
        assert bet.status.is_pending()
    
    def test_add_image_to_bet(self):
        """Test adding an image to a bet."""
        bet = Bet.create_from_telegram(123, "user", 456)
        image = BetImage(filename="test.jpg")
        
        bet.add_image(image)
        
        assert bet.has_images
        assert len(bet.images) == 1
        assert bet.primary_image == image
    
    def test_add_invalid_image_raises_error(self):
        """Test that invalid image format raises error."""
        bet = Bet.create_from_telegram(123, "user", 456)
        image = BetImage(filename="test.txt")  # Invalid extension
        
        with pytest.raises(ValueError, match="Invalid image format"):
            bet.add_image(image)
    
    def test_update_status_valid_transition(self):
        """Test valid status transition."""
        bet = Bet.create_from_telegram(123, "user", 456)
        
        new_status = BetStatus.won()
        bet.update_status(new_status)
        
        assert bet.status.is_won()
    
    def test_update_status_invalid_transition(self):
        """Test that settled bets cannot change status."""
        bet = Bet.create_from_telegram(123, "user", 456)
        bet.update_status(BetStatus.won())
        
        with pytest.raises(ValueError, match="Cannot transition"):
            bet.update_status(BetStatus.lost())
    
    def test_calculate_profit(self):
        """Test profit calculation."""
        bet = Bet.create_from_telegram(123, "user", 456)
        bet.stake = Money(Decimal("100"), "EUR")
        bet.odds = Odds(Decimal("2.50"))
        
        profit = bet.calculate_profit()
        
        assert profit.amount == Decimal("150")  # 100 * (2.50 - 1)
        assert profit.currency == "EUR"
    
    def test_expected_return(self):
        """Test expected return calculation."""
        bet = Bet.create_from_telegram(123, "user", 456)
        bet.stake = Money(Decimal("100"), "EUR")
        bet.potential_profit = Money(Decimal("150"), "EUR")
        
        expected = bet.expected_return
        
        assert expected.amount == Decimal("250")  # 100 + 150
    
    def test_update_from_analysis(self):
        """Test updating bet from analysis data."""
        bet = Bet.create_from_telegram(123, "user", 456)
        
        analysis_data = {
            "evento": "Real Madrid vs Barcelona",
            "tipo_apuesta": "1X2",
            "cuota": "2.50",
            "monto": "€100",
            "ganancia_potencial": "€150",
            "estado": "Pendiente"
        }
        
        bet.update_from_analysis(analysis_data)
        
        assert bet.event == "Real Madrid vs Barcelona"
        assert bet.bet_type == "1X2"
        assert bet.odds.value == Decimal("2.50")
        assert bet.stake.amount == Decimal("100")
        assert bet.potential_profit.amount == Decimal("150")
        assert bet.status.is_pending()
    
    def test_is_from_forwarded_message(self):
        """Test checking if bet is from forwarded message."""
        metadata = ForwardMetadata(
            unique_identifier="USER_123",
            is_forwarded=True,
            origin_sender_name="Original User"
        )
        
        bet = Bet.create_from_telegram(
            123, "user", 456,
            forward_metadata=metadata
        )
        
        assert bet.is_from_forwarded_message
    
    def test_to_dict_serialization(self):
        """Test dictionary serialization."""
        bet = Bet.create_from_telegram(123, "testuser", 456)
        bet.stake = Money(Decimal("100"), "EUR")
        bet.odds = Odds(Decimal("2.50"))
        
        data = bet.to_dict()
        
        assert data["telegram_user_id"] == 123
        assert data["telegram_username"] == "testuser"
        assert data["stake"]["amount"] == 100.0
        assert data["odds"]["value"] == 2.50
        assert "created_at" in data
