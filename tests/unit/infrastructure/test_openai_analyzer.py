"""
Unit Tests for OpenAIImageAnalyzer with Mocked OpenAI API

Tests the OpenAIImageAnalyzer adapter in isolation by mocking the OpenAIHandler
and verifying error handling for network errors, file errors, and JSON parsing.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp
import json

from infrastructure.openai.openai_image_analyzer import (
    OpenAIImageAnalyzer,
    OpenAIAnalyzerError
)


@pytest.fixture
def mock_openai_handler():
    """Mock del OpenAIHandler"""
    handler = Mock()
    handler.analyze_image = AsyncMock()
    return handler


@pytest.fixture
def analyzer(mock_openai_handler):
    """Analyzer con handler mockeado"""
    with patch('infrastructure.openai.openai_image_analyzer.OpenAIHandler', return_value=mock_openai_handler):
        analyzer = OpenAIImageAnalyzer()
        analyzer._handler = mock_openai_handler
        return analyzer


class TestOpenAIImageAnalyzerAnalyzeImage:
    """Tests para el método analyze_image()"""
    
    @pytest.mark.asyncio
    async def test_analyze_image_success(self, analyzer, mock_openai_handler):
        """Test análisis exitoso de imagen"""
        # Arrange
        mock_openai_handler.analyze_image.return_value = "Image contains a sports bet slip"
        
        # Act
        result = await analyzer.analyze_image(
            image_path="test.jpg",
            prompt="Analyze this image"
        )
        
        # Assert
        assert result == "Image contains a sports bet slip"
        mock_openai_handler.analyze_image.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_image_file_not_found(self, analyzer, mock_openai_handler):
        """Test manejo de archivo no encontrado"""
        # Arrange
        mock_openai_handler.analyze_image.side_effect = FileNotFoundError("File not found")
        
        # Act & Assert
        with pytest.raises(OpenAIAnalyzerError) as exc_info:
            await analyzer.analyze_image("nonexistent.jpg", "Analyze")
        
        assert "Imagen no encontrada" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, FileNotFoundError)
    
    @pytest.mark.asyncio
    async def test_analyze_image_network_error(self, analyzer, mock_openai_handler):
        """Test manejo de error de red"""
        # Arrange
        network_error = aiohttp.ClientError("Connection timeout")
        mock_openai_handler.analyze_image.side_effect = network_error
        
        # Act & Assert
        with pytest.raises(OpenAIAnalyzerError) as exc_info:
            await analyzer.analyze_image("test.jpg", "Analyze")
        
        assert "Error de conexión con OpenAI" in str(exc_info.value)
        assert exc_info.value.__cause__ == network_error
    
    @pytest.mark.asyncio
    async def test_analyze_image_malformed_response(self, analyzer, mock_openai_handler):
        """Test manejo de respuesta malformada"""
        # Arrange
        mock_openai_handler.analyze_image.side_effect = KeyError("choices")
        
        # Act & Assert
        with pytest.raises(OpenAIAnalyzerError) as exc_info:
            await analyzer.analyze_image("test.jpg", "Analyze")
        
        assert "Respuesta inválida de OpenAI API" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, KeyError)
    
    @pytest.mark.asyncio
    async def test_analyze_image_generic_error(self, analyzer, mock_openai_handler):
        """Test manejo de error genérico"""
        # Arrange
        mock_openai_handler.analyze_image.side_effect = Exception("Unexpected error")
        
        # Act & Assert
        with pytest.raises(OpenAIAnalyzerError) as exc_info:
            await analyzer.analyze_image("test.jpg", "Analyze")
        
        assert "Error analizando imagen" in str(exc_info.value)


class TestOpenAIImageAnalyzerExtractBetInfo:
    """Tests para el método extract_bet_info()"""
    
    @pytest.mark.asyncio
    async def test_extract_bet_info_success(self, analyzer, mock_openai_handler):
        """Test extracción exitosa de información"""
        # Arrange
        bet_info_json = {
            "evento": "Real Madrid vs Barcelona",
            "tipo_apuesta": "1X2",
            "cuota": "2.5",
            "monto": "10.00"
        }
        mock_openai_handler.analyze_image.return_value = json.dumps(bet_info_json)
        
        # Act
        result = await analyzer.extract_bet_info("bet.jpg")
        
        # Assert
        assert result == bet_info_json
        assert result["evento"] == "Real Madrid vs Barcelona"
    
    @pytest.mark.asyncio
    async def test_extract_bet_info_invalid_json(self, analyzer, mock_openai_handler):
        """Test manejo de JSON inválido con degradación graceful"""
        # Arrange
        mock_openai_handler.analyze_image.return_value = "This is not valid JSON"
        
        # Act
        result = await analyzer.extract_bet_info("bet.jpg")
        
        # Assert
        assert "raw_analysis" in result
        assert "error" in result
        assert result["raw_analysis"] == "This is not valid JSON"
    
    @pytest.mark.asyncio
    async def test_extract_bet_info_file_not_found(self, analyzer, mock_openai_handler):
        """Test manejo de archivo no encontrado"""
        # Arrange
        mock_openai_handler.analyze_image.side_effect = FileNotFoundError("File not found")
        
        # Act & Assert
        with pytest.raises(OpenAIAnalyzerError) as exc_info:
            await analyzer.extract_bet_info("nonexistent.jpg")
        
        assert "Imagen no encontrada" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_bet_info_network_error(self, analyzer, mock_openai_handler):
        """Test manejo de error de red durante extracción"""
        # Arrange
        network_error = aiohttp.ClientError("API timeout")
        mock_openai_handler.analyze_image.side_effect = network_error
        
        # Act & Assert
        with pytest.raises(OpenAIAnalyzerError) as exc_info:
            await analyzer.extract_bet_info("bet.jpg")
        
        assert "Error de conexión con OpenAI" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_bet_info_handles_null_values(self, analyzer, mock_openai_handler):
        """Test manejo de valores null en JSON"""
        # Arrange
        bet_info_json = {
            "evento": "Real Madrid vs Barcelona",
            "tipo_apuesta": None,
            "cuota": "2.5",
            "monto": None
        }
        mock_openai_handler.analyze_image.return_value = json.dumps(bet_info_json)
        
        # Act
        result = await analyzer.extract_bet_info("bet.jpg")
        
        # Assert
        assert result["evento"] == "Real Madrid vs Barcelona"
        assert result["tipo_apuesta"] is None
        assert result["monto"] is None
