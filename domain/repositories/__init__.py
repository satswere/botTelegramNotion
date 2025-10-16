"""
Repository Interfaces (Ports)

Define los contratos para acceso a datos sin especificar la implementación.
Permite que el dominio sea independiente de la infraestructura.
"""

from .bet_repository import IBetRepository
from .image_analyzer import IImageAnalyzer
from .file_storage import IFileStorage
from .message_extractor import IMessageExtractor

__all__ = [
    'IBetRepository',
    'IImageAnalyzer',
    'IFileStorage',
    'IMessageExtractor',
]
