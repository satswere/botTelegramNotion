"""
Unit Tests for NotionBetRepository with Mocked Notion API

Tests the NotionBetRepository adapter in isolation by mocking the Notion client
and verifying error handling, logging, and exception chaining.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from notion_client.errors import APIResponseError

from infrastructure.notion.notion_bet_repository import (
    NotionBetRepository,
    NotionRepositoryError
)


@pytest.fixture
def mock_notion_client():
    """Mock del cliente de Notion"""
    client = Mock()
    client.pages = Mock()
    client.databases = Mock()
    return client


@pytest.fixture
def repository(mock_notion_client):
    """Repository con cliente mockeado"""
    repo = NotionBetRepository(
        notion_client=mock_notion_client,
        database_id="mock-database-id"
    )
    return repo


class TestNotionBetRepositorySave:
    """Tests para el método save()"""
    
    @pytest.mark.asyncio
    async def test_save_success(self, repository, mock_notion_client):
        """Test guardado exitoso de apuesta"""
        # Arrange
        mock_notion_client.pages.create.return_value = {
            "id": "page-123",
            "properties": {}
        }
        
        bet_data = {
            "evento": "Real Madrid vs Barcelona",
            "cuota": "2.5",
            "monto": "10.00"
        }
        
        # Act
        page_id = await repository.save(bet_data)
        
        # Assert
        assert page_id == "page-123"
        mock_notion_client.pages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_handles_api_response_error(self, repository, mock_notion_client):
        """Test manejo de APIResponseError al guardar"""
        # Arrange
        api_error = APIResponseError(
            response=Mock(status=400),
            message="Invalid properties",
            code="validation_error"
        )
        mock_notion_client.pages.create.side_effect = api_error
        
        # Act & Assert
        with pytest.raises(NotionRepositoryError) as exc_info:
            await repository.save({"evento": "Test"})
        
        assert "Error de Notion API" in str(exc_info.value)
        assert exc_info.value.__cause__ == api_error
    
    @pytest.mark.asyncio
    async def test_save_handles_generic_exception(self, repository, mock_notion_client):
        """Test manejo de excepciones genéricas"""
        # Arrange
        mock_notion_client.pages.create.side_effect = Exception("Network timeout")
        
        # Act & Assert
        with pytest.raises(NotionRepositoryError) as exc_info:
            await repository.save({"evento": "Test"})
        
        assert "Error guardando apuesta" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, Exception)


class TestNotionBetRepositoryFindById:
    """Tests para el método find_by_id()"""
    
    @pytest.mark.asyncio
    async def test_find_by_id_success(self, repository, mock_notion_client):
        """Test búsqueda exitosa de apuesta"""
        # Arrange
        mock_notion_client.pages.retrieve.return_value = {
            "id": "page-123",
            "properties": {
                "Evento": {"title": [{"text": {"content": "Test Event"}}]}
            }
        }
        
        # Act
        result = await repository.find_by_id("page-123")
        
        # Assert
        assert result is not None
        assert result["id"] == "page-123"
        mock_notion_client.pages.retrieve.assert_called_once_with("page-123")
    
    @pytest.mark.asyncio
    async def test_find_by_id_not_found(self, repository, mock_notion_client):
        """Test búsqueda de apuesta no existente"""
        # Arrange
        api_error = APIResponseError(
            response=Mock(status=404),
            message="Page not found",
            code="object_not_found"
        )
        mock_notion_client.pages.retrieve.side_effect = api_error
        
        # Act
        result = await repository.find_by_id("nonexistent-id")
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_find_by_id_handles_api_error(self, repository, mock_notion_client):
        """Test manejo de otros errores de API"""
        # Arrange
        api_error = APIResponseError(
            response=Mock(status=500),
            message="Internal server error",
            code="internal_error"
        )
        mock_notion_client.pages.retrieve.side_effect = api_error
        
        # Act & Assert
        with pytest.raises(NotionRepositoryError) as exc_info:
            await repository.find_by_id("page-123")
        
        assert "Error buscando apuesta" in str(exc_info.value)


class TestNotionBetRepositoryUpdateStatus:
    """Tests para el método update_status()"""
    
    @pytest.mark.asyncio
    async def test_update_status_success(self, repository, mock_notion_client):
        """Test actualización exitosa de estado"""
        # Arrange
        mock_notion_client.pages.update.return_value = {
            "id": "page-123",
            "properties": {}
        }
        
        # Act
        result = await repository.update_status("page-123", "Ganada")
        
        # Assert
        assert result is True
        mock_notion_client.pages.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_status_handles_api_error(self, repository, mock_notion_client):
        """Test manejo de error al actualizar estado"""
        # Arrange
        api_error = APIResponseError(
            response=Mock(status=400),
            message="Invalid status",
            code="validation_error"
        )
        mock_notion_client.pages.update.side_effect = api_error
        
        # Act & Assert
        with pytest.raises(NotionRepositoryError) as exc_info:
            await repository.update_status("page-123", "InvalidStatus")
        
        assert "Error actualizando estado" in str(exc_info.value)
        assert exc_info.value.__cause__ == api_error


class TestNotionBetRepositoryFindAll:
    """Tests para el método find_all()"""
    
    @pytest.mark.asyncio
    async def test_find_all_success(self, repository, mock_notion_client):
        """Test listado exitoso de apuestas"""
        # Arrange
        mock_notion_client.databases.query.return_value = {
            "results": [
                {"id": "page-1", "properties": {}},
                {"id": "page-2", "properties": {}}
            ]
        }
        
        # Act
        results = await repository.find_all(limit=10)
        
        # Assert
        assert len(results) == 2
        assert results[0]["id"] == "page-1"
    
    @pytest.mark.asyncio
    async def test_find_all_with_status_filter(self, repository, mock_notion_client):
        """Test filtrado por estado"""
        # Arrange
        mock_notion_client.databases.query.return_value = {
            "results": [{"id": "page-1", "properties": {}}]
        }
        
        # Act
        results = await repository.find_all(status="Pendiente")
        
        # Assert
        call_args = mock_notion_client.databases.query.call_args
        assert call_args is not None
        assert "filter" in call_args[1]
