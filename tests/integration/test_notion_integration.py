"""Test de integración para NotionBetRepository"""

import pytest
import os
from notion_client import Client
from dotenv import load_dotenv
from infrastructure.notion import NotionBetRepository

load_dotenv()


@pytest.fixture
def notion_repository():
    """Fixture que crea un repositorio real de Notion (solo si hay credenciales)"""
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_DATABASE_ID")

    if not notion_token or not database_id:
        pytest.skip("No hay credenciales de Notion configuradas")

    notion_client = Client(auth=notion_token)
    return NotionBetRepository(notion_client, database_id)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_bet_to_notion(notion_repository):
    """Test: Guardar una apuesta real en Notion"""

    bet_data = {
        "event": "Test - Barcelona vs Real Madrid",
        "market": "Ganador del partido",
        "selection": "Barcelona",
        "odds": 1.80,
        "amount": 50.0,
        "status": "Pendiente",
    }

    # Guardar apuesta
    bet_id = await notion_repository.save(bet_data)

    assert bet_id is not None
    assert isinstance(bet_id, str)
    assert len(bet_id) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_find_bet_by_id(notion_repository):
    """Test: Buscar una apuesta por ID"""

    # Primero guardar una apuesta
    bet_data = {"event": "Test - Find by ID", "odds": 2.0, "amount": 100.0}

    bet_id = await notion_repository.save(bet_data)

    # Luego buscarla
    found_bet = await notion_repository.find_by_id(bet_id)

    assert found_bet is not None
    assert found_bet["id"] == bet_id
    assert "Test - Find by ID" in found_bet["event"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_bet_status(notion_repository):
    """Test: Actualizar el estado de una apuesta"""

    # Crear apuesta
    bet_data = {"event": "Test - Update Status", "odds": 1.5}
    bet_id = await notion_repository.save(bet_data)

    # Actualizar estado
    updated = await notion_repository.update_status(bet_id, "Ganada")

    assert updated is True

    # Verificar actualización
    found_bet = await notion_repository.find_by_id(bet_id)
    assert found_bet["status"] == "Ganada"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
