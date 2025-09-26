"""
Servicio para integración con Notion API
Permite crear entradas en la base de datos de apuestas con imágenes
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from notion_client import Client

logger = logging.getLogger(__name__)


class NotionService:
    """Servicio para interactuar con Notion API"""
    
    def __init__(self):
        """Inicializa el cliente de Notion"""
        self.token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.token:
            raise ValueError("Falta NOTION_TOKEN en el archivo .env")
        
        if not self.database_id:
            raise ValueError("Falta NOTION_DATABASE_ID en el archivo .env")
        
        self.client = Client(auth=self.token)
        logger.info("Cliente de Notion inicializado")
    
    def upload_image_to_notion(self, image_path: Path) -> Optional[str]:
        """
        Sube una imagen a Notion y retorna la URL
        Nota: Notion no permite subir archivos directamente via API,
        pero podemos usar el archivo local como referencia
        """
        try:
            if not image_path.exists():
                logger.error(f"Imagen no encontrada: {image_path}")
                return None
            
            # Por ahora retornamos la ruta local, ya que Notion API no permite
            # subir archivos directamente. Una alternativa sería subirlo a un
            # servicio de almacenamiento en la nube y usar esa URL
            return str(image_path.absolute())
            
        except Exception as e:
            logger.error(f"Error procesando imagen para Notion: {e}")
            return None
    
    def create_bet_entry(self, 
                        event_title: str,
                        tipster_name: str,
                        image_path: Optional[Path] = None,
                        additional_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Crea una nueva entrada en la base de datos de apuestas de Notion
        
        Args:
            event_title: Título del evento/selección (campo principal)
            tipster_name: Nombre del tipster (origen del mensaje)
            image_path: Ruta a la imagen de la apuesta
            additional_data: Datos adicionales del mensaje de Telegram
            
        Returns:
            ID de la página creada en Notion o None si hay error
        """
        try:
            # Preparar propiedades base
            properties = {
                # Título principal (obligatorio)
                "Evento / Selección": {
                    "title": [
                        {
                            "text": {
                                "content": event_title
                            }
                        }
                    ]
                },
                # Fecha actual
                "Fecha": {
                    "date": {
                        "start": datetime.now().isoformat()[:10]  # Solo la fecha
                    }
                },
                # Estado inicial pendiente
                "Resultado": {
                    "select": {
                        "name": "Pendiente"
                    }
                }
            }
            
            # Agregar información del tipster si está disponible
            if tipster_name:
                # Crear o buscar relación con tipster
                # Por simplicidad, guardamos el nombre en el mercado/selección
                properties["Mercado / Selección"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"Tipster: {tipster_name}"
                            }
                        }
                    ]
                }
            
            # Agregar imagen si está disponible
            if image_path and image_path.exists():
                # Nota: Notion API no permite subir archivos directamente
                # Necesitaríamos usar un servicio externo como AWS S3, Google Drive, etc.
                # Por ahora, indicamos que hay una imagen disponible
                current_text = properties.get("Mercado / Selección", {}).get("rich_text", [{}])[0].get("text", {}).get("content", "")
                new_content = f"{current_text}\nImagen: {image_path.name}" if current_text else f"Imagen: {image_path.name}"
                
                properties["Mercado / Selección"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": new_content
                            }
                        }
                    ]
                }
                
                # TODO: Para subir la imagen realmente, necesitaríamos:
                # 1. Subirla a un servicio de almacenamiento en la nube
                # 2. Usar la URL pública en el campo "Captura / Comprobante"
            
            # Crear la página en Notion
            try:
                response = self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties=properties
                )
                
                if isinstance(response, dict):
                    page_id = response.get("id")
                    page_url = response.get("url")
                    
                    logger.info(f"Entrada creada en Notion: {page_url}")
                    return page_id
                else:
                    logger.error("Respuesta inesperada de Notion API")
                    return None
            except Exception as api_error:
                logger.error(f"Error en API de Notion: {api_error}")
                return None
            
        except Exception as e:
            logger.error(f"Error creando entrada en Notion: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Prueba la conexión con Notion"""
        try:
            # Intentar obtener información de la base de datos
            if not self.database_id:
                logger.error("Database ID no configurado")
                return False
                
            response = self.client.databases.retrieve(self.database_id)
            if isinstance(response, dict) and "title" in response:
                title = response["title"][0]["plain_text"] if response["title"] else "Base de datos"
                logger.info(f"Conexión exitosa con base de datos: {title}")
                return True
            else:
                logger.info("Conexión exitosa con Notion")
                return True
        except Exception as e:
            logger.error(f"Error conectando con Notion: {e}")
            return False
    
    def get_database_info(self) -> Optional[Dict[str, Any]]:
        """Obtiene información de la base de datos"""
        try:
            if not self.database_id:
                return None
            response = self.client.databases.retrieve(self.database_id)
            if isinstance(response, dict):
                return response
            else:
                logger.warning("Respuesta no es un diccionario")
                return None
        except Exception as e:
            logger.error(f"Error obteniendo información de la base de datos: {e}")
            return None


# Función de utilidad para crear instancia singleton
_notion_service = None

def get_notion_service() -> NotionService:
    """Obtiene instancia singleton del servicio de Notion"""
    global _notion_service
    if _notion_service is None:
        _notion_service = NotionService()
    return _notion_service