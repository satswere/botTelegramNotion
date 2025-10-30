"""
Unit Tests for MessageProcessor

Tests the MessageProcessor orchestrator with mocked dependencies.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from telegram import Update, Message, User, Chat, PhotoSize

from application.orchestration import MessageProcessor, MessageProcessingError
from application.dtos import BetDTO


@pytest.fixture
def mock_process_bet_use_case():
    """Mock del ProcessBetImageUseCase"""
    use_case = Mock()
    use_case.execute = AsyncMock()
    return use_case


@pytest.fixture
def mock_message_extractor():
    """Mock del MessageExtractor"""
    extractor = Mock()
    extractor.extract_metadata = Mock(
        return_value={
            "message_id": 123,
            "timestamp": "2024-01-01T12:00:00",
            "forwarding": {"is_forwarded": False},
        }
    )
    return extractor


@pytest.fixture
def mock_notion_client():
    """Mock del cliente de Notion"""
    client = Mock()
    client.pages = Mock()
    client.pages.create = Mock(return_value={"id": "notion-page-123"})
    return client


@pytest.fixture
def tmp_images_path(tmp_path):
    """Directorio temporal para imágenes"""
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    return images_dir


@pytest.fixture
def message_processor(
    mock_process_bet_use_case,
    mock_message_extractor,
    mock_notion_client,
    tmp_images_path,
):
    """Instancia de MessageProcessor con mocks"""
    return MessageProcessor(
        process_bet_use_case=mock_process_bet_use_case,
        message_extractor=mock_message_extractor,
        notion_client=mock_notion_client,
        database_id="test-database-id",
        images_path=tmp_images_path,
    )


@pytest.fixture
def mock_telegram_update():
    """Mock de un Update de Telegram con imagen"""
    update = Mock(spec=Update)
    message = Mock(spec=Message)

    # User
    user = Mock(spec=User)
    user.id = 12345
    user.first_name = "John"
    user.last_name = "Doe"
    user.username = "johndoe"
    message.from_user = user

    # Chat
    chat = Mock(spec=Chat)
    chat.id = 67890
    message.chat = chat

    # Photo
    photo = Mock(spec=PhotoSize)
    photo.file_id = "photo-file-id-123"
    photo.file_size = 50000
    message.photo = [photo]

    # Message metadata
    message.message_id = 999
    message.date = MagicMock()
    message.date.isoformat = Mock(return_value="2024-01-01T12:00:00")

    update.message = message
    return update


@pytest.fixture
def mock_context():
    """Mock del contexto de Telegram"""
    context = Mock()
    bot = Mock()

    # Mock get_file
    file_mock = AsyncMock()
    file_mock.download_to_drive = AsyncMock()
    bot.get_file = AsyncMock(return_value=file_mock)

    context.bot = bot
    return context


class TestMessageProcessorImageProcessing:
    """Tests para procesamiento de mensajes con imagen"""

    @pytest.mark.asyncio
    async def test_process_image_message_success(
        self,
        message_processor,
        mock_telegram_update,
        mock_context,
        mock_process_bet_use_case,
        tmp_images_path,
    ):
        """Test procesamiento exitoso de mensaje con imagen"""
        # Arrange
        bet_dto = BetDTO(
            id="bet-123",
            event="Test Event",
            bet_type="1X2",
            stake_amount=10.0,
            stake_currency="USD",
            odds_value=2.5,
            potential_profit_amount=15.0,
            potential_profit_currency="USD",
            status="pending",
            telegram_user_id=12345,
            telegram_username="testuser",
            created_at="2024-01-01T10:00:00",
            updated_at="2024-01-01T10:00:00",
            has_images=True,
            is_forwarded=False,
        )
        mock_process_bet_use_case.execute.return_value = bet_dto

        # Mock de métodos internos para evitar I/O real
        with patch.object(
            message_processor, "_download_image", return_value="bet_12345_999.jpg"
        ) as mock_download, patch.object(
            message_processor, "_upload_to_notion", return_value="notion-file-123"
        ) as mock_upload:

            # Act
            result = await message_processor.process_image_message(
                mock_telegram_update, mock_context
            )

            # Assert
            assert result["success"] is True
            assert result["bet_dto"] == bet_dto
            assert "filename" in result
            assert mock_process_bet_use_case.execute.called
            mock_download.assert_called_once()
            mock_upload.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_image_message_no_message(
        self, message_processor, mock_context
    ):
        """Test error cuando no hay mensaje en el update"""
        # Arrange
        update = Mock(spec=Update)
        update.message = None

        # Act & Assert
        with pytest.raises(MessageProcessingError) as exc_info:
            await message_processor.process_image_message(update, mock_context)

        assert "Mensaje no disponible" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_image_message_no_photo(
        self, message_processor, mock_telegram_update, mock_context
    ):
        """Test error cuando el mensaje no tiene foto"""
        # Arrange
        mock_telegram_update.message.photo = None

        # Act & Assert
        with pytest.raises(MessageProcessingError) as exc_info:
            await message_processor.process_image_message(
                mock_telegram_update, mock_context
            )

        assert "no contiene foto" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_download_image_creates_file(
        self, message_processor, mock_telegram_update, mock_context, tmp_images_path
    ):
        """Test que la descarga crea el archivo en el path correcto"""
        # Act
        filename = await message_processor._download_image(
            mock_telegram_update.message, mock_context
        )

        # Assert
        assert filename.startswith("bet_")
        assert filename.endswith(".jpg")
        assert mock_context.bot.get_file.called


class TestMessageProcessorMetadataExtraction:
    """Tests para extracción de metadatos"""

    def test_extract_message_metadata_success(
        self, message_processor, mock_telegram_update, mock_message_extractor
    ):
        """Test extracción exitosa de metadatos"""
        # Act
        metadata = message_processor._extract_message_metadata(
            mock_telegram_update.message
        )

        # Assert
        assert metadata["message_id"] == 123
        assert mock_message_extractor.extract_metadata.called

    def test_extract_message_metadata_fallback_on_error(
        self, message_processor, mock_telegram_update, mock_message_extractor
    ):
        """Test que retorna metadatos mínimos si falla la extracción"""
        # Arrange
        mock_message_extractor.extract_metadata.side_effect = Exception("Error")

        # Act
        metadata = message_processor._extract_message_metadata(
            mock_telegram_update.message
        )

        # Assert
        assert "message_id" in metadata
        assert metadata["forwarding"]["is_forwarded"] is False


class TestMessageProcessorResponseFormatting:
    """Tests para formateo de respuestas"""

    def test_format_success_response_basic(
        self, message_processor, mock_telegram_update
    ):
        """Test formateo básico de respuesta exitosa"""
        # Arrange
        bet_dto = BetDTO(
            id="bet-123",
            event="Real Madrid vs Barcelona",
            bet_type="1X2",
            stake_amount=10.0,
            stake_currency="USD",
            odds_value=2.5,
            potential_profit_amount=15.0,
            potential_profit_currency="USD",
            status="pending",
            telegram_user_id=12345,
            telegram_username="testuser",
            created_at="2024-01-01T10:00:00",
            updated_at="2024-01-01T10:00:00",
            has_images=True,
            is_forwarded=False,
        )
        message_data = {"forwarding": {"is_forwarded": False}}

        # Act
        response = message_processor.format_success_response(
            bet_dto, mock_telegram_update.message, message_data
        )

        # Assert
        assert "✅" in response
        assert "Apuesta procesada" in response
        assert "Real Madrid vs Barcelona" in response
        assert "2.5" in response

    def test_format_success_response_with_forwarding(
        self, message_processor, mock_telegram_update
    ):
        """Test formateo con información de reenvío"""
        # Arrange
        bet_dto = BetDTO(
            id="bet-123",
            event="Test Event",
            bet_type="1X2",
            stake_amount=10.0,
            stake_currency="USD",
            odds_value=2.5,
            potential_profit_amount=15.0,
            potential_profit_currency="USD",
            status="pending",
            telegram_user_id=12345,
            telegram_username="testuser",
            created_at="2024-01-01T10:00:00",
            updated_at="2024-01-01T10:00:00",
            has_images=True,
            is_forwarded=True,
        )
        message_data = {
            "forwarding": {
                "is_forwarded": True,
                "origin_info": {"origin_sender_name": "Original Sender"},
            }
        }

        # Act
        response = message_processor.format_success_response(
            bet_dto, mock_telegram_update.message, message_data
        )

        # Assert
        assert "Reenviado de: Original Sender" in response

    def test_get_user_name_with_full_name(
        self, message_processor, mock_telegram_update
    ):
        """Test obtención de nombre completo del usuario"""
        # Act
        user_name = message_processor._get_user_name(mock_telegram_update.message)

        # Assert
        assert user_name == "John Doe"

    def test_get_user_name_with_username_only(self, message_processor):
        """Test obtención de nombre cuando solo hay username"""
        # Arrange
        message = Mock()
        user = Mock()
        user.first_name = None
        user.last_name = None
        user.username = "testuser"
        user.id = 123
        message.from_user = user

        # Act
        user_name = message_processor._get_user_name(message)

        # Assert
        assert user_name == "@testuser"
