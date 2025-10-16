"""
Create Bet Use Case

Orchestrates the creation of a new bet from Telegram message.
"""
from typing import Optional
from decimal import Decimal

from domain.entities import Bet, BetImage, ForwardMetadata
from domain.value_objects import Money, Odds, BetStatus
from domain.repositories import IBetRepository
from application.dtos import CreateBetDTO, BetDTO


class CreateBetUseCase:
    """Use case for creating a new bet."""
    
    def __init__(self, bet_repository: IBetRepository):
        """
        Initialize use case.
        
        Args:
            bet_repository: Repository for bet persistence
        """
        self._bet_repository = bet_repository
    
    async def execute(self, dto: CreateBetDTO) -> BetDTO:
        """
        Create a new bet from DTO.
        
        Args:
            dto: Data for creating the bet
            
        Returns:
            BetDTO with created bet information
            
        Raises:
            ValueError: If validation fails
        """
        # Extract forward metadata if present
        forward_metadata = None
        if dto.message_metadata:
            forward_metadata = ForwardMetadata.create_from_message_data(
                dto.message_metadata
            )
        
        # Create bet entity
        bet = Bet.create_from_telegram(
            telegram_user_id=dto.telegram_user_id,
            telegram_username=dto.telegram_username,
            telegram_message_id=dto.telegram_message_id,
            forward_metadata=forward_metadata
        )
        
        # Add image if present
        if dto.image_filename and dto.image_file_path:
            image = BetImage.from_telegram_file(
                filename=dto.image_filename,
                file_path=dto.image_file_path
            )
            
            # Mark as uploaded if Notion file ID present
            if dto.notion_file_id:
                image.mark_as_uploaded(dto.notion_file_id)
            
            bet.add_image(image)
        
        # Update from analysis if present
        if dto.analysis_data:
            bet.update_from_analysis(dto.analysis_data)
        
        # Save to repository
        bet_id = await self._bet_repository.save(bet)
        bet.id = bet_id
        
        # Convert to DTO for response
        return self._to_dto(bet)
    
    def _to_dto(self, bet: Bet) -> BetDTO:
        """Convert Bet entity to BetDTO."""
        return BetDTO(
            id=bet.id,
            event=bet.event,
            bet_type=bet.bet_type,
            stake_amount=float(bet.stake.amount) if bet.stake else None,
            stake_currency=bet.stake.currency if bet.stake else None,
            odds_value=float(bet.odds.value) if bet.odds else None,
            potential_profit_amount=float(bet.potential_profit.amount) if bet.potential_profit else None,
            potential_profit_currency=bet.potential_profit.currency if bet.potential_profit else None,
            status=str(bet.status),
            telegram_user_id=bet.telegram_user_id,
            telegram_username=bet.telegram_username,
            created_at=bet.created_at.isoformat(),
            updated_at=bet.updated_at.isoformat(),
            has_images=bet.has_images,
            is_forwarded=bet.is_from_forwarded_message,
            notes=bet.notes
        )
