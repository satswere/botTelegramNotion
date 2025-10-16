"""Notion Bet Repository - Implementa IBetRepository"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from notion_client import Client

logger = logging.getLogger(__name__)


class NotionBetRepository:
    """Repositorio de apuestas usando Notion como backend"""
    
    def __init__(self, notion_client: Client, database_id: str):
        self.client = notion_client
        self.database_id = database_id
    
    async def save(self, bet_data: Dict[str, Any]) -> str:
        """Guarda una apuesta en Notion"""
        try:
            properties = self._map_to_notion_properties(bet_data)
            
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            if isinstance(response, dict) and "id" in response:
                page_id = response["id"]
                logger.info(f"✅ Apuesta guardada: {page_id}")
                return page_id
            else:
                raise Exception("Respuesta inesperada de Notion API")
                
        except Exception as e:
            logger.error(f"❌ Error guardando apuesta: {e}")
            raise
    
    async def find_by_id(self, bet_id: str) -> Optional[Dict[str, Any]]:
        """Busca una apuesta por ID"""
        try:
            response = self.client.pages.retrieve(bet_id)
            if response:
                return self._map_from_notion_page(response)
            return None
        except Exception as e:
            logger.error(f"❌ Error buscando apuesta {bet_id}: {e}")
            return None
    
    async def update_status(self, bet_id: str, new_status: str) -> bool:
        """Actualiza el estado de una apuesta"""
        try:
            self.client.pages.update(
                page_id=bet_id,
                properties={
                    "Resultado": {
                        "select": {"name": new_status}
                    }
                }
            )
            logger.info(f"✅ Estado actualizado: {bet_id} -> {new_status}")
            return True
        except Exception as e:
            logger.error(f"❌ Error actualizando estado: {e}")
            return False
    
    async def find_all(
        self, 
        limit: int = 10, 
        offset: int = 0,
        status: Optional[str] = None
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
                    "select": {"equals": status}
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
                analyzed_data = json.loads(analyzed_data.replace('```json', '').replace('```', '').strip())
            except:
                analyzed_data = {}
        
        # Valores por defecto
        title = bet_data.get("event", bet_data.get("title", "Apuesta"))
        event = analyzed_data.get("Evento", title)
        market = analyzed_data.get("Mercado", bet_data.get("market", ""))
        selection = analyzed_data.get("Seleccion", bet_data.get("selection", ""))
        
        # Cuota y monto
        try:
            odds = float(str(analyzed_data.get("Cuota", bet_data.get("odds", "0"))).replace(",", "."))
        except:
            odds = 0.0
        
        try:
            amount_str = str(analyzed_data.get("Monto_Apostado", bet_data.get("amount", "0")))
            amount = float(amount_str.replace("€", "").replace(",", ".").strip())
        except:
            amount = 0.0
        
        properties = {
            "Evento / Selección": {
                "title": [{"text": {"content": event[:100]}}]  # Max 100 chars
            },
            "Fecha": {
                "date": {"start": datetime.now().isoformat()[:10]}
            },
            "Resultado": {
                "select": {"name": bet_data.get("status", "Pendiente")}
            },
            "Casa de apuestas": {
                "select": {"name": bet_data.get("bookmaker", "bet365")}
            },
            "Tipo de apuesta": {
                "select": {"name": bet_data.get("bet_type", "Simple")}
            },
            "Mercado": {
                "rich_text": [{"text": {"content": market[:2000]}}]
            },
            "Seleccion": {
                "rich_text": [{"text": {"content": selection[:2000]}}]
            },
            "Cuota": {
                "number": odds
            },
            "Importe apostado": {
                "number": amount if amount > 0 else 500  # Default 500 si no detecta
            }
        }
        
        # Agregar archivo si existe
        file_upload_id = bet_data.get("file_upload_id")
        filename = bet_data.get("filename", "image.jpg")
        if file_upload_id:
            properties["Captura / Comprobante"] = {
                "files": [{
                    "type": "file_upload",
                    "file_upload": {"id": file_upload_id},
                    "name": filename
                }]
            }
        
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
