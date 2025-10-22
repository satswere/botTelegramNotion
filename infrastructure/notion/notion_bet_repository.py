"""
Notion Bet Repository

Implementa IBetRepository para persistencia en Notion.
Maneja errores de API y proporciona logging detallado.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


class NotionRepositoryError(Exception):
    """Error específico del repositorio Notion."""

    pass


class NotionBetRepository:
    """Repositorio de apuestas usando Notion como backend"""

    def __init__(self, notion_client: Client, database_id: str):
        self.client = notion_client
        self.database_id = database_id

    async def save(self, bet_data) -> str:
        """
        Guarda una apuesta en Notion.

        Args:
            bet_data: Datos de la apuesta a guardar (puede ser Dict o Bet entity)

        Returns:
            ID de la página creada en Notion

        Raises:
            NotionRepositoryError: Si falla la creación
        """
        try:
            # Convertir objeto Bet a diccionario si es necesario
            if hasattr(bet_data, '__dict__') and not isinstance(bet_data, dict):
                bet_dict = self._bet_to_dict(bet_data)
            else:
                bet_dict = bet_data
            
            logger.debug(
                f"💾 Guardando apuesta en Notion: {bet_dict.get('title', 'Sin título')}"
            )
            properties = self._map_to_notion_properties(bet_dict)

            response = self.client.pages.create(
                parent={"database_id": self.database_id}, properties=properties
            )

            if isinstance(response, dict) and "id" in response:
                page_id = response["id"]
                logger.info(f"✅ Apuesta guardada exitosamente: {page_id}")
                return page_id
            else:
                error_msg = "Respuesta inesperada de Notion API"
                logger.error(f"❌ {error_msg}: {response}")
                raise NotionRepositoryError(error_msg)

        except APIResponseError as e:
            logger.error(f"❌ Error de API de Notion: {e.code} - {str(e)}")
            raise NotionRepositoryError(f"Error de Notion API: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ Error inesperado guardando apuesta: {e}", exc_info=True)
            raise NotionRepositoryError(f"Error guardando apuesta: {str(e)}") from e

    async def find_by_id(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca una apuesta por ID.

        Args:
            bet_id: ID de la página de Notion

        Returns:
            Datos de la apuesta o None si no existe
        """
        try:
            logger.debug(f"🔍 Buscando apuesta: {bet_id}")
            response = self.client.pages.retrieve(bet_id)
            if response:
                logger.info(f"✅ Apuesta encontrada: {bet_id}")
                return self._map_from_notion_page(response)
            return None
        except APIResponseError as e:
            if e.code == "object_not_found":
                logger.warning(f"⚠️ Apuesta no encontrada: {bet_id}")
                return None
            logger.error(f"❌ Error de API buscando apuesta {bet_id}: {str(e)}")
            raise NotionRepositoryError(f"Error buscando apuesta: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"❌ Error inesperado buscando apuesta {bet_id}: {e}", exc_info=True
            )
            raise NotionRepositoryError(f"Error buscando apuesta: {str(e)}") from e

    async def update_status(self, bet_id: str, new_status: str) -> bool:
        """
        Actualiza el estado de una apuesta.

        Args:
            bet_id: ID de la apuesta
            new_status: Nuevo estado

        Returns:
            True si se actualizó correctamente

        Raises:
            NotionRepositoryError: Si falla la actualización
        """
        try:
            logger.debug(f"🔄 Actualizando estado de {bet_id} a {new_status}")
            self.client.pages.update(
                page_id=bet_id,
                properties={"Resultado": {"select": {"name": new_status}}},
            )
            logger.info(f"✅ Estado actualizado: {bet_id} -> {new_status}")
            return True
        except APIResponseError as e:
            logger.error(f"❌ Error de API actualizando estado: {e.code} - {str(e)}")
            raise NotionRepositoryError(f"Error actualizando estado: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ Error inesperado actualizando estado: {e}", exc_info=True)
            raise NotionRepositoryError(f"Error actualizando estado: {str(e)}") from e

    async def find_all(
        self, limit: int = 10, offset: int = 0, status: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """Recupera múltiples apuestas con filtros"""
        try:
            query_params = {
                "database_id": self.database_id,
                "page_size": limit,
            }

            if status:
                query_params["filter"] = {
                    "property": "Resultado",
                    "select": {"equals": status},
                }

            response = self.client.databases.query(**query_params)

            results = []
            for page in response.get("results", []):
                bet = self._map_from_notion_page(page)
                if bet:
                    results.append(bet)

            return results

        except Exception as e:
            logger.error(f"❌ Error consultando apuestas: {e}")
            return []

    def _map_to_notion_properties(self, bet_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mapea datos de apuesta a propiedades de Notion"""

        # Parsear análisis si viene como string JSON
        analyzed_data = bet_data.get("analyzed_data", {})
        if isinstance(analyzed_data, str):
            import json

            try:
                analyzed_data = json.loads(
                    analyzed_data.replace("```json", "").replace("```", "").strip()
                )
            except (json.JSONDecodeError, ValueError, TypeError):
                analyzed_data = {}

        # Valores por defecto
        title = bet_data.get("event", bet_data.get("title", "Apuesta"))
        event = analyzed_data.get("Evento", title)
        
        # Buscar Mercado y Selección (en mayúsculas y minúsculas para compatibilidad)
        market = (
            analyzed_data.get("Mercado") 
            or analyzed_data.get("mercado") 
            or bet_data.get("market", "")
        )
        selection = (
            analyzed_data.get("Seleccion") 
            or analyzed_data.get("seleccion") 
            or bet_data.get("selection", "")
        )

        # Cuota y monto
        try:
            cuota_value = (
                analyzed_data.get("Cuota") 
                or analyzed_data.get("cuota") 
                or bet_data.get("odds", "0")
            )
            odds = float(str(cuota_value).replace(",", "."))
        except (ValueError, TypeError):
            odds = 0.0

        try:
            monto_value = (
                analyzed_data.get("Monto_Apostado") 
                or analyzed_data.get("monto") 
                or bet_data.get("amount", "0")
            )
            amount_str = str(monto_value)
            amount = float(amount_str.replace("€", "").replace(",", ".").strip())
        except (ValueError, TypeError, AttributeError):
            amount = 0.0

        properties = {
            "Evento / Selección": {
                "title": [{"text": {"content": event[:100]}}]  # Max 100 chars
            },
            "Fecha": {"date": {"start": datetime.now().isoformat()[:10]}},
            "Resultado": {"select": {"name": bet_data.get("status", "Pendiente")}},
            "Casa de apuestas": {
                "select": {"name": bet_data.get("bookmaker", "bet365")}
            },
            "Tipo de apuesta": {"select": {"name": bet_data.get("bet_type", "Simple")}},
            "Mercado": {"rich_text": [{"text": {"content": market[:2000]}}]},
            "Seleccion": {"rich_text": [{"text": {"content": selection[:2000]}}]},
            "Cuota": {"number": odds},
            "Importe apostado": {
                "number": amount if amount > 0 else 500  # Default 500 si no detecta
            },
        }

        # Agregar archivo en el campo "Captura / Comprobante"
        file_upload_id = bet_data.get("file_upload_id")
        filename = bet_data.get("filename", "image.jpg")
        
        if file_upload_id:
            # Usar file_upload_id (proceso de 3 pasos completado)
            properties["Captura / Comprobante"] = {
                "files": [
                    {
                        "type": "file_upload",
                        "file_upload": {"id": file_upload_id},
                        "name": filename,
                    }
                ]
            }
            logger.debug(f"✅ Archivo adjunto con file_upload_id: {file_upload_id}")
        elif filename:
            # Si no hay file_upload_id, agregar referencia en el mercado
            market_with_file = f"{market}\n📎 Archivo: {filename}" if market else f"📎 Archivo: {filename}"
            properties["Mercado"] = {"rich_text": [{"text": {"content": market_with_file[:2000]}}]}
            logger.debug(f"ℹ️ Archivo referenciado en Mercado: {filename}")

        return properties

    def _map_from_notion_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Mapea una página de Notion a diccionario de apuesta"""
        try:
            props = page.get("properties", {})

            # Extraer título
            title_prop = props.get("Evento / Selección", {})
            title = ""
            if title_prop.get("title"):
                title = title_prop["title"][0]["text"]["content"]

            # Extraer otros campos
            return {
                "id": page.get("id"),
                "event": title,
                "status": self._extract_select(props.get("Resultado")),
                "bookmaker": self._extract_select(props.get("Casa de apuestas")),
                "bet_type": self._extract_select(props.get("Tipo de apuesta")),
                "market": self._extract_rich_text(props.get("Mercado")),
                "selection": self._extract_rich_text(props.get("Seleccion")),
                "odds": props.get("Cuota", {}).get("number", 0),
                "amount": props.get("Importe apostado", {}).get("number", 0),
                "created_at": page.get("created_time"),
            }
        except Exception as e:
            logger.error(f"Error mapeando página de Notion: {e}")
            return None

    def _extract_select(self, prop: Optional[Dict]) -> str:
        """Extrae valor de propiedad select"""
        if prop and prop.get("select"):
            return prop["select"].get("name", "")
        return ""

    def _extract_rich_text(self, prop: Optional[Dict]) -> str:
        """Extrae valor de propiedad rich_text"""
        if prop and prop.get("rich_text") and len(prop["rich_text"]) > 0:
            return prop["rich_text"][0]["text"]["content"]
        return ""

    def _bet_to_dict(self, bet) -> Dict[str, Any]:
        """
        Convierte un objeto Bet a diccionario compatible con _map_to_notion_properties.
        
        Args:
            bet: Objeto Bet del dominio
            
        Returns:
            Diccionario con datos de la apuesta
        """
        # Obtener diccionario base del objeto Bet
        bet_dict = bet.to_dict()
        
        # Adaptar al formato esperado por _map_to_notion_properties
        result = {
            "title": bet_dict.get("event", "Apuesta"),
            "event": bet_dict.get("event", "No especificado"),
            "bet_type": bet_dict.get("bet_type", "Simple"),
            "status": bet_dict.get("status", {}).get("value", "Pendiente") if isinstance(bet_dict.get("status"), dict) else str(bet_dict.get("status", "Pendiente")),
            "bookmaker": "bet365",  # Default
        }
        
        # Agregar cuota si existe
        if bet_dict.get("odds"):
            odds_data = bet_dict["odds"]
            if isinstance(odds_data, dict):
                result["odds"] = odds_data.get("value", 0)
            else:
                result["odds"] = float(odds_data) if odds_data else 0
        
        # Agregar monto si existe
        if bet_dict.get("stake"):
            stake_data = bet_dict["stake"]
            if isinstance(stake_data, dict):
                result["amount"] = stake_data.get("amount", 0)
            else:
                result["amount"] = float(stake_data) if stake_data else 0
        
        # Agregar información de imágenes si existen
        if bet_dict.get("images") and len(bet_dict["images"]) > 0:
            first_image = bet_dict["images"][0]
            result["filename"] = first_image.get("filename", "image.jpg")
            
            # Buscar notion_file_id en la imagen
            if first_image.get("notion_file_id"):
                result["file_upload_id"] = first_image["notion_file_id"]
        
        # Agregar datos del análisis si existen
        if hasattr(bet, 'raw_analysis') and bet.raw_analysis:
            result["analyzed_data"] = bet.raw_analysis
        
        return result
