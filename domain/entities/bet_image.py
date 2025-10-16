"""
BetImage Entity

Represents an image associated with a bet.
Contains file information and analysis results.
"""
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class BetImage:
    """Represents an image file related to a bet."""
    
    # File information
    filename: str
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    
    # Notion integration
    notion_file_id: Optional[str] = None
    
    # Analysis results
    analysis_result: Optional[str] = None
    analyzed_at: Optional[datetime] = None
    
    # Metadata
    uploaded_at: datetime = field(default_factory=datetime.now)
    mime_type: str = "image/jpeg"
    
    @property
    def is_uploaded(self) -> bool:
        """Check if image has been uploaded to Notion."""
        return bool(self.notion_file_id)
    
    @property
    def is_analyzed(self) -> bool:
        """Check if image has been analyzed."""
        return bool(self.analysis_result)
    
    @property
    def file_extension(self) -> str:
        """Get file extension."""
        return Path(self.filename).suffix.lower()
    
    @property
    def is_valid_image(self) -> bool:
        """Check if file extension is valid for images."""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        return self.file_extension in valid_extensions
    
    def mark_as_uploaded(self, notion_file_id: str) -> None:
        """Mark image as uploaded to Notion."""
        self.notion_file_id = notion_file_id
    
    def mark_as_analyzed(self, analysis_result: str) -> None:
        """Mark image as analyzed and store result."""
        self.analysis_result = analysis_result
        self.analyzed_at = datetime.now()
    
    @classmethod
    def from_telegram_file(
        cls,
        filename: str,
        file_path: Optional[str] = None,
        file_size: Optional[int] = None
    ) -> 'BetImage':
        """
        Create BetImage from Telegram file information.
        
        Args:
            filename: Name of the file
            file_path: Local path to the file
            file_size: Size in bytes
            
        Returns:
            BetImage instance
        """
        return cls(
            filename=filename,
            file_path=Path(file_path) if file_path else None,
            file_size=file_size,
            uploaded_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "filename": self.filename,
            "file_path": str(self.file_path) if self.file_path else None,
            "file_size": self.file_size,
            "notion_file_id": self.notion_file_id,
            "analysis_result": self.analysis_result,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "uploaded_at": self.uploaded_at.isoformat(),
            "mime_type": self.mime_type,
            "is_uploaded": self.is_uploaded,
            "is_analyzed": self.is_analyzed,
            "file_extension": self.file_extension,
            "is_valid_image": self.is_valid_image
        }
