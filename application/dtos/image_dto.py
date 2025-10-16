"""
Image DTO

Data Transfer Object for image file information.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageDTO:
    """DTO for image file data."""
    
    filename: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: str = "image/jpeg"
    
    # Telegram specific
    telegram_file_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate DTO."""
        if not self.filename:
            raise ValueError("Filename is required")
        if not self.file_path:
            raise ValueError("File path is required")
