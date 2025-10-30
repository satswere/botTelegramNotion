"""
Unit Tests for CreateBetUseCase
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from application.use_cases import CreateBetUseCase
from application.dtos import CreateBetDTO, BetDTO
from domain.entities import Bet
from domain.value_objects import Money, Odds, BetStatus


class TestCreateBetUseCase:

    @pytest.fixture
    def mock_repository(self):
        """Create mock bet repository."""
        repo = AsyncMock()
        repo.save = AsyncMock(return_value="bet_123")
        return repo

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create use case with mocked dependencies."""
        return CreateBetUseCase(mock_repository)

    @pytest.mark.asyncio
    async def test_create_bet_minimal_data(self, use_case, mock_repository):
        """Test creating bet with minimal required data."""
        dto = CreateBetDTO(
            telegram_user_id=12345,
            telegram_username="testuser",
            telegram_message_id=67890,
        )

        result = await use_case.execute(dto)

        assert isinstance(result, BetDTO)
        assert result.id == "bet_123"
        assert result.telegram_user_id == 12345
        assert result.telegram_username == "testuser"
        assert result.status == "Pendiente"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bet_with_image(self, use_case, mock_repository):
        """Test creating bet with image information."""
        dto = CreateBetDTO(
            telegram_user_id=12345,
            telegram_username="testuser",
            telegram_message_id=67890,
            image_filename="bet.jpg",
            image_file_path="/tmp/bet.jpg",
            notion_file_id="notion_file_123",
        )

        result = await use_case.execute(dto)

        assert result.has_images
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bet_with_analysis_data(self, use_case, mock_repository):
        """Test creating bet with analysis data."""
        dto = CreateBetDTO(
            telegram_user_id=12345,
            telegram_username="testuser",
            telegram_message_id=67890,
            analysis_data={
                "evento": "Real Madrid vs Barcelona",
                "tipo_apuesta": "1X2",
                "cuota": "2.50",
                "monto": "€100",
                "ganancia_potencial": "€150",
                "estado": "Pendiente",
            },
        )

        result = await use_case.execute(dto)

        assert result.event == "Real Madrid vs Barcelona"
        assert result.bet_type == "1X2"
        assert result.odds_value == 2.50
        assert result.stake_amount == 100.0
        assert result.stake_currency == "EUR"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bet_with_forward_metadata(self, use_case, mock_repository):
        """Test creating bet with forwarding metadata."""
        dto = CreateBetDTO(
            telegram_user_id=12345,
            telegram_username="testuser",
            telegram_message_id=67890,
            message_metadata={
                "forwarding": {
                    "is_forwarded": True,
                    "unique_identifier": "USER_999",
                    "origin_info": {"origin_sender_name": "Original User"},
                }
            },
        )

        result = await use_case.execute(dto)

        assert result.is_forwarded
        mock_repository.save.assert_called_once()
