"""
Bet DTOs

Data Transfer Objects for Bet operations.
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class BetDTO:
    """DTO for complete bet information (read operations)."""
    
    # Identity
    id: Optional[str]
    
    # Core bet data
    event: str
    bet_type: str
    stake_amount: Optional[float]
    stake_currency: Optional[str]
    odds_value: Optional[float]
    potential_profit_amount: Optional[float]
    potential_profit_currency: Optional[str]
    status: str
    
    # User information
    telegram_user_id: int
    telegram_username: Optional[str]
    
    # Metadata
    created_at: str
    updated_at: str
    
    # Additional data
    has_images: bool
    is_forwarded: bool
    notes: Optional[str] = None


@dataclass
class CreateBetDTO:
    """DTO for creating a new bet."""
    
    # Required fields
    telegram_user_id: int
    telegram_username: Optional[str]
    telegram_message_id: int
    
    # Image information
    image_filename: Optional[str] = None
    image_file_path: Optional[str] = None
    
    # Analysis results (from image)
    analysis_data: Optional[Dict[str, Any]] = None
    
    # Forwarding metadata
    message_metadata: Optional[Dict[str, Any]] = None
    
    # Notion integration
    notion_file_id: Optional[str] = None


@dataclass
class UpdateBetDTO:
    """DTO for updating an existing bet."""
    
    # Identity
    bet_id: str
    
    # Fields that can be updated
    event: Optional[str] = None
    bet_type: Optional[str] = None
    stake_amount: Optional[float] = None
    stake_currency: Optional[str] = None
    odds_value: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
