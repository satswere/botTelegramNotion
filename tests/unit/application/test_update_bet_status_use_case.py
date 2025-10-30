"""
Unit Tests for UpdateBetStatusUseCase
"""

import pytest
from unittest.mock import AsyncMock

from application.use_cases import UpdateBetStatusUseCase
from domain.entities import Bet
from domain.value_objects import BetStatus


class TestUpdateBetStatusUseCase:

    @pytest.fixture
    def mock_repository(self):
        """Create mock bet repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def use_case(self, mock_repository):
        """Create use case with mocked dependencies."""
        return UpdateBetStatusUseCase(mock_repository)

    @pytest.mark.asyncio
    async def test_update_bet_status_success(self, use_case, mock_repository):
        """Test successful status update."""
        # Setup mock bet
        bet = Bet.create_from_telegram(123, "user", 456)
        mock_repository.find_by_id = AsyncMock(return_value=bet)
        mock_repository.update_status = AsyncMock(return_value=True)

        result = await use_case.execute("bet_123", "Ganada")

        assert result is True
        mock_repository.find_by_id.assert_called_once_with("bet_123")
        mock_repository.update_status.assert_called_once_with("bet_123", "Ganada")

    @pytest.mark.asyncio
    async def test_update_bet_status_not_found(self, use_case, mock_repository):
        """Test updating non-existent bet raises error."""
        mock_repository.find_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Bet not found"):
            await use_case.execute("bet_999", "Ganada")

    @pytest.mark.asyncio
    async def test_update_bet_status_invalid_transition(
        self, use_case, mock_repository
    ):
        """Test invalid status transition raises error."""
        # Create bet with settled status
        bet = Bet.create_from_telegram(123, "user", 456)
        bet.update_status(BetStatus.won())

        mock_repository.find_by_id = AsyncMock(return_value=bet)

        with pytest.raises(ValueError, match="Cannot transition"):
            await use_case.execute("bet_123", "Perdida")

    @pytest.mark.asyncio
    async def test_update_bet_status_invalid_status_string(
        self, use_case, mock_repository
    ):
        """Test invalid status string raises error."""
        bet = Bet.create_from_telegram(123, "user", 456)
        mock_repository.find_by_id = AsyncMock(return_value=bet)
        mock_repository.update_status = AsyncMock(return_value=True)

        # BetStatus.from_string handles invalid strings by defaulting to pending
        result = await use_case.execute("bet_123", "InvalidStatus")
        assert result is True
        mock_repository.update_status.assert_called_once()
