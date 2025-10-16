"""
IBetRepository - Interfaz de Repositorio de Apuestas

Define el contrato para persistencia de apuestas sin conocer la implementación.
Permite cambiar el backend (Notion, PostgreSQL, MongoDB) sin afectar la lógica.
"""

from typing import Protocol, Optional, Dict, Any


class IBetRepository(Protocol):
    """
    Puerto (Interface) para persistencia de apuestas.

    Esta interfaz define las operaciones de persistencia que necesita
    el dominio sin depender de una implementación específica.

    Implementaciones:
        - NotionBetRepository (actual)
        - PostgreSQLBetRepository (futuro)
        - InMemoryBetRepository (tests)

    Ejemplo de uso:
        >>> repository = NotionBetRepository(notion_client, database_id)
        >>> bet_id = await repository.save(bet_data)
        >>> bet = await repository.find_by_id(bet_id)
    """

    async def save(self, bet_data: Dict[str, Any]) -> str:
        """
        Guarda una apuesta y retorna su ID único.

        Args:
            bet_data: Diccionario con los datos de la apuesta:
                - event: str - Nombre del evento (ej: "Barcelona vs Real Madrid")
                - market: str - Tipo de mercado (ej: "Ganador del partido")
                - selection: str - Selección realizada (ej: "Barcelona")
                - odds: float - Cuota de la apuesta (ej: 1.80)
                - amount: float - Monto apostado (ej: 50.0)
                - currency: str - Moneda (ej: "EUR")
                - status: str - Estado (ej: "Pendiente")
                - image_file_id: Optional[str] - ID del archivo adjunto
                - metadata: Optional[Dict] - Información adicional

        Returns:
            str: ID único de la apuesta guardada

        Raises:
            SaveError: Si falla la operación de guardado
            ValidationError: Si los datos no son válidos

        Example:
            >>> bet_data = {
            ...     "event": "Barcelona vs Real Madrid",
            ...     "odds": 1.80,
            ...     "amount": 50.0
            ... }
            >>> bet_id = await repository.save(bet_data)
            >>> print(bet_id)  # "page_abc123..."
        """
        ...

    async def find_by_id(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca una apuesta por su ID único.

        Args:
            bet_id: ID único de la apuesta

        Returns:
            Dict con los datos de la apuesta o None si no existe

        Raises:
            RepositoryError: Si hay error en la consulta

        Example:
            >>> bet = await repository.find_by_id("page_abc123")
            >>> if bet:
            ...     print(bet["event"])
        """
        ...

    async def update_status(self, bet_id: str, new_status: str) -> bool:
        """
        Actualiza el estado de una apuesta.

        Args:
            bet_id: ID de la apuesta
            new_status: Nuevo estado ("Ganada", "Perdida", "Pendiente")

        Returns:
            bool: True si se actualizó, False si no existe

        Raises:
            UpdateError: Si falla la actualización
        """
        ...

    async def find_all(
        self, limit: int = 10, offset: int = 0, status: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Recupera múltiples apuestas con paginación.

        Args:
            limit: Número máximo de resultados
            offset: Desplazamiento para paginación
            status: Filtrar por estado (opcional)

        Returns:
            Lista de diccionarios con datos de apuestas

        Example:
            >>> pending_bets = await repository.find_all(
            ...     limit=20,
            ...     status="Pendiente"
            ... )
        """
        ...
