"""
Update Bet Status Use Case

Handles updating the status of an existing bet.
"""

from domain.entities import Bet
from domain.value_objects import BetStatus
from domain.repositories import IBetRepository
from domain.services import BetValidator


class UpdateBetStatusUseCase:
    """Use case for updating bet status."""

    def __init__(self, bet_repository: IBetRepository):
        """
        Initialize use case.

        Args:
            bet_repository: Repository for bet persistence
        """
        self._bet_repository = bet_repository

    async def execute(self, bet_id: str, new_status: str) -> bool:
        """
        Update bet status.

        Args:
            bet_id: ID of the bet to update
            new_status: New status string (e.g., "Ganada", "Perdida")

        Returns:
            True if update successful

        Raises:
            ValueError: If bet not found or status transition invalid
        """
        # Find bet
        bet = await self._bet_repository.find_by_id(bet_id)
        if not bet:
            raise ValueError(f"Bet not found: {bet_id}")

        # Parse new status
        status = BetStatus.from_string(new_status)
        if not status:
            raise ValueError(f"Invalid status: {new_status}")

        # Validate transition
        is_valid, error_msg = BetValidator.validate_status_transition(
            bet.status, status
        )

        if not is_valid:
            raise ValueError(error_msg)

        # Update status
        bet.update_status(status)

        # Persist changes
        return await self._bet_repository.update_status(bet_id, str(status))
