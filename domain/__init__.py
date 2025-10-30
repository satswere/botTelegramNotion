"""
Domain Layer - Capa de Dominio

Contiene la lógica de negocio pura sin dependencias externas.
Esta capa define las reglas de negocio, entidades y contratos (interfaces).
"""

__version__ = "1.0.0"

from .repositories import (
    IBetRepository,
    IImageAnalyzer,
    IFileStorage,
    IMessageExtractor,
)
from .entities import Bet, BetImage, ForwardMetadata
from .value_objects import Money, Odds, BetStatus
from .services import BetValidator

__all__ = [
    # Repositories (Ports)
    "IBetRepository",
    "IImageAnalyzer",
    "IFileStorage",
    "IMessageExtractor",
    # Entities
    "Bet",
    "BetImage",
    "ForwardMetadata",
    # Value Objects
    "Money",
    "Odds",
    "BetStatus",
    # Services
    "BetValidator",
]
