"""
Command Orchestrator - Coordinador de Comandos

Coordina la ejecución de múltiples use cases según el comando recibido.
Actúa como mediador entre los handlers de presentación y los use cases de aplicación.

Responsabilidades:
- Mapear comandos a use cases
- Coordinar múltiples use cases si es necesario
- Gestionar el estado de la aplicación
- Proporcionar respuestas estructuradas
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from application.use_cases import (
    ProcessBetImageUseCase,
    UpdateBetStatusUseCase
)
from domain.repositories import IBetRepository
from domain.value_objects import BetStatus

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Tipos de comandos soportados."""
    START = "start"
    HELP = "help"
    STATUS = "status"
    UPDATE_BET = "update_bet"
    LIST_BETS = "list_bets"
    UNKNOWN = "unknown"


class CommandOrchestrator:
    """
    Orquesta la ejecución de comandos coordinando múltiples use cases.
    
    Esta clase implementa el patrón Command para desacoplar
    los handlers de presentación de la lógica de negocio.
    """
    
    def __init__(
        self,
        bet_repository: IBetRepository,
        update_bet_status_use_case: Optional[UpdateBetStatusUseCase] = None
    ):
        """
        Inicializa el orquestador de comandos.
        
        Args:
            bet_repository: Repositorio de apuestas
            update_bet_status_use_case: Use case para actualizar estado
        """
        self._bet_repository = bet_repository
        self._update_bet_status_use_case = update_bet_status_use_case or UpdateBetStatusUseCase(bet_repository)
        
        logger.info("🎯 CommandOrchestrator inicializado")
    
    async def execute_status_command(
        self,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Ejecuta el comando de estado/estadísticas.
        
        Coordina la obtención de estadísticas de apuestas.
        
        Args:
            user_id: ID del usuario (opcional, para filtrar)
            limit: Límite de resultados
            
        Returns:
            Diccionario con estadísticas y lista de apuestas
        """
        logger.info(f"📊 Ejecutando comando STATUS (limit={limit})")
        
        try:
            # Obtener todas las apuestas (o filtradas por usuario)
            bets = await self._bet_repository.find_all(limit=limit)
            
            # Calcular estadísticas
            stats = self._calculate_statistics(bets)
            
            # Obtener apuestas recientes
            recent_bets = bets[:5] if len(bets) > 5 else bets
            
            logger.info(f"✅ Estadísticas calculadas: {stats['total']} apuestas")
            
            return {
                "success": True,
                "statistics": stats,
                "recent_bets": recent_bets,
                "total_count": len(bets)
            }
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando comando STATUS: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "statistics": None,
                "recent_bets": []
            }
    
    async def execute_update_bet_command(
        self,
        bet_id: str,
        new_status: str
    ) -> Dict[str, Any]:
        """
        Ejecuta el comando para actualizar el estado de una apuesta.
        
        Args:
            bet_id: ID de la apuesta a actualizar
            new_status: Nuevo estado
            
        Returns:
            Diccionario con el resultado de la operación
        """
        logger.info(f"🔄 Ejecutando comando UPDATE_BET (bet_id={bet_id}, status={new_status})")
        
        try:
            # Validar que el estado sea válido
            status_enum = BetStatus.from_string(new_status)
            
            # from_string devuelve PENDING por defecto si no reconoce el estado
            # Verificamos que el string original coincida con algún estado válido
            valid_statuses = ["Pendiente", "Ganada", "Perdida", "Anulada", "Cashout",
                            "pending", "won", "lost", "void", "cashout"]
            if new_status not in valid_statuses:
                return {
                    "success": False,
                    "error": f"Estado inválido: {new_status}"
                }
            
            # Ejecutar use case
            success = await self._update_bet_status_use_case.execute(
                bet_id=bet_id,
                new_status=status_enum
            )
            
            if success:
                logger.info(f"✅ Apuesta {bet_id} actualizada a {new_status}")
                return {
                    "success": True,
                    "bet_id": bet_id,
                    "new_status": new_status
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo actualizar la apuesta"
                }
                
        except Exception as e:
            logger.error(f"❌ Error actualizando apuesta: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    async def execute_list_bets_command(
        self,
        status_filter: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Ejecuta el comando para listar apuestas.
        
        Args:
            status_filter: Filtro por estado (opcional)
            limit: Número máximo de resultados
            
        Returns:
            Diccionario con la lista de apuestas
        """
        logger.info(f"📋 Ejecutando comando LIST_BETS (status={status_filter}, limit={limit})")
        
        try:
            # Obtener apuestas
            bets = await self._bet_repository.find_all(
                limit=limit,
                status=status_filter
            )
            
            logger.info(f"✅ Obtenidas {len(bets)} apuestas")
            
            return {
                "success": True,
                "bets": bets,
                "count": len(bets),
                "filter": status_filter
            }
            
        except Exception as e:
            logger.error(f"❌ Error listando apuestas: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "bets": []
            }
    
    def _calculate_statistics(self, bets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estadísticas de las apuestas.
        
        Args:
            bets: Lista de apuestas
            
        Returns:
            Diccionario con estadísticas
        """
        if not bets:
            return {
                "total": 0,
                "pending": 0,
                "won": 0,
                "lost": 0,
                "void": 0
            }
        
        stats = {
            "total": len(bets),
            "pending": 0,
            "won": 0,
            "lost": 0,
            "void": 0
        }
        
        # Contar por estado
        for bet in bets:
            # El estado puede venir en diferentes formatos
            status = None
            
            # Intentar extraer el estado
            if isinstance(bet, dict):
                # Si es un dict directo
                status = bet.get("status") or bet.get("estado")
                
                # Si viene en properties de Notion
                if "properties" in bet:
                    props = bet["properties"]
                    if "Resultado" in props:
                        result_prop = props["Resultado"]
                        if "select" in result_prop and result_prop["select"]:
                            status = result_prop["select"].get("name")
                    elif "Estado" in props:
                        estado_prop = props["Estado"]
                        if "select" in estado_prop and estado_prop["select"]:
                            status = estado_prop["select"].get("name")
            
            # Clasificar
            if status:
                status_lower = status.lower()
                if "pendiente" in status_lower or "pending" in status_lower:
                    stats["pending"] += 1
                elif "ganada" in status_lower or "won" in status_lower or "ganado" in status_lower:
                    stats["won"] += 1
                elif "perdida" in status_lower or "lost" in status_lower or "perdido" in status_lower:
                    stats["lost"] += 1
                elif "anulada" in status_lower or "void" in status_lower:
                    stats["void"] += 1
        
        return stats
    
    def format_status_response(self, result: Dict[str, Any]) -> str:
        """
        Formatea la respuesta del comando STATUS.
        
        Args:
            result: Resultado del comando
            
        Returns:
            Texto formateado para mostrar al usuario
        """
        if not result["success"]:
            return f"❌ Error obteniendo estadísticas: {result.get('error', 'Error desconocido')}"
        
        stats = result["statistics"]
        recent = result["recent_bets"]
        
        response = "📊 **Estadísticas de Apuestas**\n\n"
        response += f"📈 Total: {stats['total']}\n"
        response += f"⏳ Pendientes: {stats['pending']}\n"
        response += f"✅ Ganadas: {stats['won']}\n"
        response += f"❌ Perdidas: {stats['lost']}\n"
        response += f"⚪ Anuladas: {stats['void']}\n"
        
        if recent:
            response += f"\n📝 **Últimas {len(recent)} apuestas**:\n"
            for i, bet in enumerate(recent, 1):
                # Extraer información básica
                event = self._extract_bet_event(bet)
                status = self._extract_bet_status(bet)
                response += f"{i}. {event} - {status}\n"
        
        return response
    
    def _extract_bet_event(self, bet: Dict[str, Any]) -> str:
        """Extrae el evento de una apuesta."""
        if "properties" in bet:
            props = bet["properties"]
            if "Evento" in props:
                title_prop = props["Evento"].get("title", [])
                if title_prop and len(title_prop) > 0:
                    return title_prop[0].get("text", {}).get("content", "Sin evento")
        
        return bet.get("event", bet.get("evento", "Sin evento"))
    
    def _extract_bet_status(self, bet: Dict[str, Any]) -> str:
        """Extrae el estado de una apuesta."""
        if "properties" in bet:
            props = bet["properties"]
            for status_key in ["Resultado", "Estado"]:
                if status_key in props:
                    select_prop = props[status_key].get("select")
                    if select_prop:
                        return select_prop.get("name", "Desconocido")
        
        return bet.get("status", bet.get("estado", "Desconocido"))
