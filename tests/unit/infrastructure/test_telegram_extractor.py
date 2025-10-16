"""
Unit Tests for TelegramMessageExtractor with Mocked Telegram Objects

Tests the TelegramMessageExtractor in isolation by mocking Telegram Message objects
and verifying error handling for missing attributes and malformed messages.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from infrastructure.telegram.telegram_message_extractor import (
    TelegramMessageExtractor,
    TelegramExtractorError
)


@pytest.fixture
def extractor():
    """Extractor instance"""
    return TelegramMessageExtractor()


@pytest.fixture
def mock_telegram_message():
    """Mock completo de un mensaje de Telegram"""
    message = Mock()
    message.message_id = 12345
    message.date = datetime(2024, 1, 15, 10, 30, 0)
    message.text = "Test message"
    message.caption = None
    message.photo = None
    message.document = None
    
    # Mock user
    user = Mock()
    user.id = 98765
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.is_bot = False
    user.language_code = "es"
    message.from_user = user
    
    # Mock chat
    chat = Mock()
    chat.id = 55555
    chat.type = "private"
    chat.title = None
    chat.username = "testuser"
    message.chat = chat
    
    # No forwarding
    message.forward_from = None
    message.forward_from_chat = None
    message.forward_sender_name = None
    message.forward_date = None
    message.is_automatic_forward = False
    message.forward_origin = None
    
    return message


class TestTelegramMessageExtractorExtractMetadata:
    """Tests para el método extract_metadata()"""
    
    def test_extract_metadata_success(self, extractor, mock_telegram_message):
        """Test extracción exitosa de metadatos"""
        # Act
        result = extractor.extract_metadata(mock_telegram_message)
        
        # Assert
        assert result["message_id"] == 12345
        assert result["sender"]["user_id"] == 98765
        assert result["sender"]["username"] == "testuser"
        assert result["sender"]["full_name"] == "Test User"
        assert result["chat"]["chat_id"] == 55555
        assert result["text"] == "Test message"
        assert result["has_media"] is False
    
    def test_extract_metadata_with_caption(self, extractor, mock_telegram_message):
        """Test extracción con caption en lugar de texto"""
        # Arrange
        mock_telegram_message.text = None
        mock_telegram_message.caption = "Image caption"
        
        # Act
        result = extractor.extract_metadata(mock_telegram_message)
        
        # Assert
        assert result["text"] == "Image caption"
    
    def test_extract_metadata_missing_user_attribute(self, extractor):
        """Test manejo de atributo faltante en usuario"""
        # Arrange
        message = Mock()
        message.message_id = 12345
        message.date = datetime.now()
        
        # User sin algunos atributos
        user = Mock()
        user.id = 123
        # username no existe
        del user.username
        user.first_name = "John"
        message.from_user = user
        
        chat = Mock()
        chat.id = 456
        chat.type = "private"
        message.chat = chat
        
        message.text = "Test"
        message.caption = None
        message.photo = None
        message.document = None
        message.forward_from = None
        message.forward_from_chat = None
        message.forward_sender_name = None
        message.forward_date = None
        message.is_automatic_forward = False
        message.forward_origin = None
        
        # Act - debería usar getattr con default None
        result = extractor.extract_metadata(message)
        
        # Assert
        assert result["sender"]["username"] is None
    
    def test_extract_metadata_missing_required_attribute(self, extractor):
        """Test manejo de atributo requerido faltante"""
        # Arrange
        message = Mock()
        # message_id faltante causa AttributeError
        del message.message_id
        
        # Act & Assert
        with pytest.raises(TelegramExtractorError) as exc_info:
            extractor.extract_metadata(message)
        
        assert "estructura inválida" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, AttributeError)
    
    def test_extract_metadata_with_photo(self, extractor, mock_telegram_message):
        """Test detección de foto adjunta"""
        # Arrange
        photo = Mock()
        mock_telegram_message.photo = [photo]
        
        # Act
        result = extractor.extract_metadata(mock_telegram_message)
        
        # Assert
        assert result["has_media"] is True
    
    def test_extract_metadata_with_document(self, extractor, mock_telegram_message):
        """Test detección de documento adjunto"""
        # Arrange
        doc = Mock()
        mock_telegram_message.document = doc
        
        # Act
        result = extractor.extract_metadata(mock_telegram_message)
        
        # Assert
        assert result["has_media"] is True


class TestTelegramMessageExtractorExtractFile:
    """Tests para el método extract_file()"""
    
    @pytest.mark.asyncio
    async def test_extract_file_photo_success(self, extractor, mock_telegram_message):
        """Test extracción exitosa de foto"""
        # Arrange
        photo = Mock()
        photo.file_id = "PHOTO_123"
        photo.file_size = 50000
        photo.width = 1920
        photo.height = 1080
        mock_telegram_message.photo = [photo]
        
        # Act
        result = await extractor.extract_file(mock_telegram_message)
        
        # Assert
        assert result["file_id"] == "PHOTO_123"
        assert result["file_type"] == "photo"
        assert result["file_size"] == 50000
        assert result["width"] == 1920
    
    @pytest.mark.asyncio
    async def test_extract_file_document_success(self, extractor, mock_telegram_message):
        """Test extracción exitosa de documento"""
        # Arrange
        doc = Mock()
        doc.file_id = "DOC_456"
        doc.file_name = "apuesta.pdf"
        doc.file_size = 100000
        doc.mime_type = "application/pdf"
        mock_telegram_message.document = doc
        
        # Act
        result = await extractor.extract_file(mock_telegram_message)
        
        # Assert
        assert result["file_id"] == "DOC_456"
        assert result["file_type"] == "document"
        assert result["file_name"] == "apuesta.pdf"
        assert result["mime_type"] == "application/pdf"
    
    @pytest.mark.asyncio
    async def test_extract_file_no_attachment(self, extractor, mock_telegram_message):
        """Test sin archivo adjunto"""
        # Act
        result = await extractor.extract_file(mock_telegram_message)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_extract_file_missing_photo_attribute(self, extractor):
        """Test manejo de atributo faltante en foto"""
        # Arrange
        message = Mock()
        photo = Mock()
        # file_id faltante
        del photo.file_id
        message.photo = [photo]
        message.document = None
        
        # Act & Assert
        with pytest.raises(TelegramExtractorError) as exc_info:
            await extractor.extract_file(message)
        
        assert "estructura inválida" in str(exc_info.value)


class TestTelegramMessageExtractorForwardInfo:
    """Tests para el método extract_forward_info()"""
    
    def test_extract_forward_info_not_forwarded(self, extractor, mock_telegram_message):
        """Test mensaje no reenviado"""
        # Act
        result = extractor.extract_forward_info(mock_telegram_message)
        
        # Assert
        assert result["is_forwarded"] is False
        assert result["origin_info"] == {}
    
    def test_extract_forward_info_with_forward_origin(self, extractor):
        """Test mensaje reenviado con forward_origin"""
        # Arrange
        message = Mock()
        
        # Mock forward_origin moderno
        forward_origin = Mock()
        sender_user = Mock()
        sender_user.id = 99999
        sender_user.first_name = "Forwarded"
        sender_user.last_name = "User"
        sender_user.username = "forwardeduser"
        forward_origin.sender_user = sender_user
        forward_origin.date = datetime(2024, 1, 10, 8, 0, 0)
        
        message.forward_origin = forward_origin
        message.forward_date = datetime(2024, 1, 10, 8, 0, 0)
        message.forward_from = None
        message.forward_from_chat = None
        message.forward_sender_name = None
        message.is_automatic_forward = False
        
        # Act
        result = extractor.extract_forward_info(message)
        
        # Assert
        assert result["is_forwarded"] is True
        assert result["origin_info"]["origin_sender_user_id"] == 99999
        assert result["origin_info"]["origin_sender_username"] == "forwardeduser"


class TestTelegramMessageExtractorValidation:
    """Tests para el método is_valid_message()"""
    
    def test_is_valid_message_success(self, extractor, mock_telegram_message):
        """Test validación de mensaje válido"""
        # Act
        result = extractor.is_valid_message(mock_telegram_message)
        
        # Assert
        assert result is True
    
    def test_is_valid_message_no_user(self, extractor):
        """Test mensaje sin usuario es inválido"""
        # Arrange
        message = Mock()
        message.from_user = None
        
        # Act
        result = extractor.is_valid_message(message)
        
        # Assert
        assert result is False
    
    def test_is_valid_message_none(self, extractor):
        """Test mensaje None es inválido"""
        # Act
        result = extractor.is_valid_message(None)
        
        # Assert
        assert result is False
