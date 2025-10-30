"""
Unit Tests for CommandOrchestrator

Tests the CommandOrchestrator with mocked repositories and use cases.
"""

import pytest
from unittest.mock import Mock, AsyncMock

from application.orchestration import CommandOrchestrator, CommandType
from domain.value_objects import BetStatus


@pytest.fixture
def mock_bet_repository():
    """Mock del repositorio de apuestas"""
    repo = Mock()
    repo.find_all = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.update_status = AsyncMock()
    return repo


@pytest.fixture
def mock_update_bet_use_case():
    """Mock del use case de actualización"""
    use_case = Mock()
    use_case.execute = AsyncMock()
    return use_case


@pytest.fixture
def orchestrator(mock_bet_repository, mock_update_bet_use_case):
    """Instancia de CommandOrchestrator"""
    return CommandOrchestrator(
        bet_repository=mock_bet_repository,
        update_bet_status_use_case=mock_update_bet_use_case,
    )


class TestCommandOrchestratorStatusCommand:
    """Tests para el comando STATUS"""

    @pytest.mark.asyncio
    async def test_execute_status_command_success(
        self, orchestrator, mock_bet_repository
    ):
        """Test ejecución exitosa del comando STATUS"""
        # Arrange
        mock_bets = [
            {
                "id": "bet-1",
                "properties": {
                    "Evento": {"title": [{"text": {"content": "Event 1"}}]},
                    "Resultado": {"select": {"name": "Pendiente"}},
                },
            },
            {
                "id": "bet-2",
                "properties": {
                    "Evento": {"title": [{"text": {"content": "Event 2"}}]},
                    "Resultado": {"select": {"name": "Ganada"}},
                },
            },
            {
                "id": "bet-3",
                "properties": {
                    "Evento": {"title": [{"text": {"content": "Event 3"}}]},
                    "Resultado": {"select": {"name": "Perdida"}},
                },
            },
        ]
        mock_bet_repository.find_all.return_value = mock_bets

        # Act
        result = await orchestrator.execute_status_command(limit=10)

        # Assert
        assert result["success"] is True
        assert result["statistics"]["total"] == 3
        assert result["statistics"]["pending"] == 1
        assert result["statistics"]["won"] == 1
        assert result["statistics"]["lost"] == 1
        assert len(result["recent_bets"]) == 3

    @pytest.mark.asyncio
    async def test_execute_status_command_empty_database(
        self, orchestrator, mock_bet_repository
    ):
        """Test comando STATUS con base de datos vacía"""
        # Arrange
        mock_bet_repository.find_all.return_value = []

        # Act
        result = await orchestrator.execute_status_command()

        # Assert
        assert result["success"] is True
        assert result["statistics"]["total"] == 0
        assert len(result["recent_bets"]) == 0

    @pytest.mark.asyncio
    async def test_execute_status_command_error(
        self, orchestrator, mock_bet_repository
    ):
        """Test manejo de errores en comando STATUS"""
        # Arrange
        mock_bet_repository.find_all.side_effect = Exception("Database error")

        # Act
        result = await orchestrator.execute_status_command()

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["statistics"] is None


class TestCommandOrchestratorUpdateBetCommand:
    """Tests para el comando UPDATE_BET"""

    @pytest.mark.asyncio
    async def test_execute_update_bet_command_success(
        self, orchestrator, mock_update_bet_use_case
    ):
        """Test actualización exitosa de apuesta"""
        # Arrange
        mock_update_bet_use_case.execute.return_value = True

        # Act
        result = await orchestrator.execute_update_bet_command(
            bet_id="bet-123", new_status="Ganada"
        )

        # Assert
        assert result["success"] is True
        assert result["bet_id"] == "bet-123"
        assert result["new_status"] == "Ganada"
        mock_update_bet_use_case.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_update_bet_command_invalid_status(self, orchestrator):
        """Test actualización con estado inválido"""
        # Act
        result = await orchestrator.execute_update_bet_command(
            bet_id="bet-123", new_status="InvalidStatus"
        )

        # Assert
        assert result["success"] is False
        assert "Estado inválido" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_update_bet_command_use_case_fails(
        self, orchestrator, mock_update_bet_use_case
    ):
        """Test cuando el use case retorna False"""
        # Arrange
        mock_update_bet_use_case.execute.return_value = False

        # Act
        result = await orchestrator.execute_update_bet_command(
            bet_id="bet-123", new_status="Ganada"
        )

        # Assert
        assert result["success"] is False
        assert "No se pudo actualizar" in result["error"]


class TestCommandOrchestratorListBetsCommand:
    """Tests para el comando LIST_BETS"""

    @pytest.mark.asyncio
    async def test_execute_list_bets_command_success(
        self, orchestrator, mock_bet_repository
    ):
        """Test listado exitoso de apuestas"""
        # Arrange
        mock_bets = [
            {"id": "bet-1", "event": "Event 1"},
            {"id": "bet-2", "event": "Event 2"},
        ]
        mock_bet_repository.find_all.return_value = mock_bets

        # Act
        result = await orchestrator.execute_list_bets_command(limit=20)

        # Assert
        assert result["success"] is True
        assert len(result["bets"]) == 2
        assert result["count"] == 2

    @pytest.mark.asyncio
    async def test_execute_list_bets_command_with_filter(
        self, orchestrator, mock_bet_repository
    ):
        """Test listado con filtro por estado"""
        # Arrange
        mock_bets = [{"id": "bet-1", "status": "Pendiente"}]
        mock_bet_repository.find_all.return_value = mock_bets

        # Act
        result = await orchestrator.execute_list_bets_command(
            status_filter="Pendiente", limit=10
        )

        # Assert
        assert result["success"] is True
        assert result["filter"] == "Pendiente"
        mock_bet_repository.find_all.assert_called_with(limit=10, status="Pendiente")


class TestCommandOrchestratorStatistics:
    """Tests para cálculo de estadísticas"""

    def test_calculate_statistics_empty_list(self, orchestrator):
        """Test estadísticas con lista vacía"""
        # Act
        stats = orchestrator._calculate_statistics([])

        # Assert
        assert stats["total"] == 0
        assert stats["pending"] == 0
        assert stats["won"] == 0
        assert stats["lost"] == 0

    def test_calculate_statistics_mixed_statuses(self, orchestrator):
        """Test estadísticas con diferentes estados"""
        # Arrange
        bets = [
            {"properties": {"Resultado": {"select": {"name": "Pendiente"}}}},
            {"properties": {"Resultado": {"select": {"name": "Ganada"}}}},
            {"properties": {"Resultado": {"select": {"name": "Perdida"}}}},
            {"properties": {"Resultado": {"select": {"name": "Pendiente"}}}},
        ]

        # Act
        stats = orchestrator._calculate_statistics(bets)

        # Assert
        assert stats["total"] == 4
        assert stats["pending"] == 2
        assert stats["won"] == 1
        assert stats["lost"] == 1

    def test_calculate_statistics_with_dict_format(self, orchestrator):
        """Test estadísticas con formato directo de dict"""
        # Arrange
        bets = [{"status": "Pendiente"}, {"status": "won"}, {"estado": "perdida"}]

        # Act
        stats = orchestrator._calculate_statistics(bets)

        # Assert
        assert stats["total"] == 3
        assert stats["pending"] == 1
        assert stats["won"] == 1
        assert stats["lost"] == 1


class TestCommandOrchestratorResponseFormatting:
    """Tests para formateo de respuestas"""

    def test_format_status_response_success(self, orchestrator):
        """Test formateo de respuesta STATUS exitosa"""
        # Arrange
        result = {
            "success": True,
            "statistics": {"total": 10, "pending": 3, "won": 5, "lost": 2, "void": 0},
            "recent_bets": [
                {
                    "properties": {
                        "Evento": {"title": [{"text": {"content": "Event 1"}}]},
                        "Resultado": {"select": {"name": "Pendiente"}},
                    }
                }
            ],
        }

        # Act
        response = orchestrator.format_status_response(result)

        # Assert
        assert "📊" in response
        assert "Total: 10" in response
        assert "Pendientes: 3" in response
        assert "Ganadas: 5" in response
        assert "Event 1" in response

    def test_format_status_response_error(self, orchestrator):
        """Test formateo de respuesta con error"""
        # Arrange
        result = {"success": False, "error": "Database connection failed"}

        # Act
        response = orchestrator.format_status_response(result)

        # Assert
        assert "❌" in response
        assert "Error" in response

    def test_extract_bet_event(self, orchestrator):
        """Test extracción de evento desde bet"""
        # Arrange
        bet = {
            "properties": {
                "Evento": {"title": [{"text": {"content": "Real Madrid vs Barcelona"}}]}
            }
        }

        # Act
        event = orchestrator._extract_bet_event(bet)

        # Assert
        assert event == "Real Madrid vs Barcelona"

    def test_extract_bet_status(self, orchestrator):
        """Test extracción de estado desde bet"""
        # Arrange
        bet = {"properties": {"Resultado": {"select": {"name": "Ganada"}}}}

        # Act
        status = orchestrator._extract_bet_status(bet)

        # Assert
        assert status == "Ganada"
