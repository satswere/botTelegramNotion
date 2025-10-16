"""
BetValidator Domain Service

Provides validation logic for Bet entities.
Implements business rules that don't belong to a single entity.
"""
from typing import List, Optional, Tuple
from decimal import Decimal

from ..entities import Bet
from ..value_objects import Money, Odds, BetStatus


class ValidationError(Exception):
    """Raised when bet validation fails."""
    pass


class BetValidator:
    """Domain service for validating bets."""
    
    @staticmethod
    def validate_bet(bet: Bet) -> Tuple[bool, List[str]]:
        """
        Validate a bet entity.
        
        Args:
            bet: Bet to validate
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required fields
        if not bet.event or bet.event == "No especificado":
            errors.append("Event description is required")
        
        # Validate stake
        if bet.stake:
            stake_errors = BetValidator._validate_stake(bet.stake)
            errors.extend(stake_errors)
        
        # Validate odds
        if bet.odds:
            odds_errors = BetValidator._validate_odds(bet.odds)
            errors.extend(odds_errors)
        
        # Validate stake/odds consistency
        if bet.stake and bet.odds and bet.potential_profit:
            consistency_errors = BetValidator._validate_profit_calculation(
                bet.stake, bet.odds, bet.potential_profit
            )
            errors.extend(consistency_errors)
        
        # Validate images
        if bet.has_images:
            for idx, image in enumerate(bet.images):
                if not image.is_valid_image:
                    errors.append(f"Image {idx + 1} has invalid format: {image.filename}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_stake(stake: Money) -> List[str]:
        """Validate stake amount."""
        errors = []
        
        if stake.amount <= 0:
            errors.append("Stake must be positive")
        
        if stake.amount < Decimal("0.01"):
            errors.append("Stake must be at least 0.01")
        
        if stake.amount > Decimal("1000000"):
            errors.append("Stake exceeds maximum allowed (1,000,000)")
        
        return errors
    
    @staticmethod
    def _validate_odds(odds: Odds) -> List[str]:
        """Validate odds value."""
        errors = []
        
        if odds.value < Decimal("1.01"):
            errors.append("Odds must be at least 1.01")
        
        if odds.value > Decimal("1000"):
            errors.append("Odds exceed maximum allowed (1000)")
        
        return errors
    
    @staticmethod
    def _validate_profit_calculation(
        stake: Money,
        odds: Odds,
        potential_profit: Money
    ) -> List[str]:
        """Validate that profit calculation is consistent."""
        errors = []
        
        # Calculate expected profit
        expected_profit = stake.multiply(odds.calculate_profit_factor())
        
        # Allow small rounding differences (0.01)
        difference = abs(expected_profit.amount - potential_profit.amount)
        
        if difference > Decimal("0.01"):
            errors.append(
                f"Profit calculation inconsistent: "
                f"expected {expected_profit}, got {potential_profit}"
            )
        
        return errors
    
    @staticmethod
    def validate_status_transition(
        current_status: BetStatus,
        new_status: BetStatus
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate status transition.
        
        Args:
            current_status: Current bet status
            new_status: Proposed new status
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not current_status.can_transition_to(new_status):
            return False, f"Cannot transition from {current_status} to {new_status}"
        
        return True, None
    
    @staticmethod
    def is_suspicious_odds(odds: Odds) -> bool:
        """
        Check if odds are suspiciously high/low.
        
        Business rule: Flag odds < 1.10 or > 50.0 for review.
        """
        return odds.value < Decimal("1.10") or odds.value > Decimal("50.0")
    
    @staticmethod
    def is_high_stake(stake: Money) -> bool:
        """
        Check if stake is unusually high.
        
        Business rule: Flag stakes > 1000 EUR equivalent for review.
        """
        # Simplified: just check amount (in production, would convert currencies)
        return stake.amount > Decimal("1000")
    
    @staticmethod
    def calculate_risk_level(bet: Bet) -> str:
        """
        Calculate risk level based on bet characteristics.
        
        Returns:
            "LOW", "MEDIUM", or "HIGH"
        """
        if not bet.odds or not bet.stake:
            return "UNKNOWN"
        
        risk_score = 0
        
        # High odds = higher risk
        if bet.odds.value > Decimal("5.0"):
            risk_score += 2
        elif bet.odds.value > Decimal("3.0"):
            risk_score += 1
        
        # High stake = higher risk
        if BetValidator.is_high_stake(bet.stake):
            risk_score += 2
        elif bet.stake.amount > Decimal("500"):
            risk_score += 1
        
        # Suspicious odds = higher risk
        if BetValidator.is_suspicious_odds(bet.odds):
            risk_score += 1
        
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
