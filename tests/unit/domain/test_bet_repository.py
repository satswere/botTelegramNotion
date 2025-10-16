"""
Tests para IBetRepository

Valida que las implementaciones cumplan con el contrato definido.
"""

import pytest
from typing import Dict, Any
from domain.repositories import IBetRepository


class MockBetRepository:
    """Mock implementation para testing"""
    
    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    async def save(self, bet_data: Dict[str, Any]) -> str:
        bet_id = f"bet_{self.next_id}"
        self.next_id += 1
        self.storage[bet_id] = bet_data.copy()
        return bet_id
    
    async def find_by_id(self, bet_id: str) -> Dict[str, Any] | None:
        return self.storage.get(bet_id)
    
    async def update_status(self, bet_id: str, new_status: str) -> bool:
        if bet_id in self.storage:
            self.storage[bet_id]["status"] = new_status
            return True
        return False
    
    async def find_all(
        self, 
        limit: int = 10, 
        offset: int = 0,
        status: str | None = None
    ) -> list[Dict[str, Any]]:
        bets = list(self.storage.values())
        if status:
            bets = [b for b in bets if b.get("status") == status]
        return bets[offset:offset + limit]


@pytest.fixture
def bet_repository():
    """Fixture que proporciona un repositorio mock"""
    return MockBetRepository()


@pytest.fixture
def sample_bet_data():
    """Fixture con datos de apuesta de ejemplo"""
    return {
        "event": "Barcelona vs Real Madrid",
        "market": "Ganador del partido",
        "selection": "Barcelona",
        "odds": 1.80,
        "amount": 50.0,
        "currency": "EUR",
        "status": "Pendiente"
    }


class TestIBetRepository:
    """Tests para el contrato IBetRepository"""
    
    @pytest.mark.asyncio
    async def test_save_bet_returns_id(self, bet_repository: IBetRepository, sample_bet_data):
        """Test: save() debe retornar un ID único"""
        bet_id = await bet_repository.save(sample_bet_data)
        
        assert bet_id is not None
        assert isinstance(bet_id, str)
        assert len(bet_id) > 0
    
    @pytest.mark.asyncio
    async def test_find_by_id_existing_bet(self, bet_repository: IBetRepository, sample_bet_data):
        """Test: find_by_id() debe retornar la apuesta guardada"""
        bet_id = await bet_repository.save(sample_bet_data)
        found_bet = await bet_repository.find_by_id(bet_id)
        
        assert found_bet is not None
        assert found_bet["event"] == sample_bet_data["event"]
        assert found_bet["odds"] == sample_bet_data["odds"]
        assert found_bet["amount"] == sample_bet_data["amount"]
    
    @pytest.mark.asyncio
    async def test_find_by_id_non_existing_bet(self, bet_repository: IBetRepository):
        """Test: find_by_id() debe retornar None si no existe"""
        found_bet = await bet_repository.find_by_id("non_existing_id")
        
        assert found_bet is None
    
    @pytest.mark.asyncio
    async def test_update_status_existing_bet(self, bet_repository: IBetRepository, sample_bet_data):
        """Test: update_status() debe actualizar el estado"""
        bet_id = await bet_repository.save(sample_bet_data)
        updated = await bet_repository.update_status(bet_id, "Ganada")
        
        assert updated is True
        
        found_bet = await bet_repository.find_by_id(bet_id)
        assert found_bet["status"] == "Ganada"
    
    @pytest.mark.asyncio
    async def test_update_status_non_existing_bet(self, bet_repository: IBetRepository):
        """Test: update_status() debe retornar False si no existe"""
        updated = await bet_repository.update_status("non_existing_id", "Ganada")
        
        assert updated is False
    
    @pytest.mark.asyncio
    async def test_find_all_returns_list(self, bet_repository: IBetRepository, sample_bet_data):
        """Test: find_all() debe retornar lista de apuestas"""
        # Guardar varias apuestas
        await bet_repository.save(sample_bet_data)
        await bet_repository.save({**sample_bet_data, "event": "Otro evento"})
        
        bets = await bet_repository.find_all()
        
        assert isinstance(bets, list)
        assert len(bets) >= 2
    
    @pytest.mark.asyncio
    async def test_find_all_with_limit(self, bet_repository: IBetRepository, sample_bet_data):
        """Test: find_all() debe respetar el límite"""
        # Guardar 5 apuestas
        for i in range(5):
            await bet_repository.save({**sample_bet_data, "event": f"Evento {i}"})
        
        bets = await bet_repository.find_all(limit=3)
        
        assert len(bets) == 3
    
    @pytest.mark.asyncio
    async def test_find_all_with_status_filter(self, bet_repository: IBetRepository, sample_bet_data):
        """Test: find_all() debe filtrar por estado"""
        # Guardar apuestas con diferentes estados
        bet_id_1 = await bet_repository.save({**sample_bet_data, "status": "Pendiente"})
        bet_id_2 = await bet_repository.save({**sample_bet_data, "status": "Ganada"})
        bet_id_3 = await bet_repository.save({**sample_bet_data, "status": "Pendiente"})
        
        pending_bets = await bet_repository.find_all(status="Pendiente")
        
        assert len(pending_bets) == 2
        assert all(bet["status"] == "Pendiente" for bet in pending_bets)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
