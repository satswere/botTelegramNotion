"""
Notion File Uploader

Servicio para subir archivos a Notion usando el proceso de 3 pasos oficial.
"""

import logging
from pathlib import Path
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)


class NotionFileUploaderError(Exception):
    """Error durante la subida de archivos a Notion."""
    pass


class NotionFileUploader:
    """
    Servicio para subir archivos a Notion.
    
    Implementa el proceso oficial de 3 pasos:
    1. Crear File Upload Object
    2. Subir contenido del archivo
    3. Usar el file_upload_id en propiedades de página
    """

    def __init__(self, notion_token: str, notion_version: str = "2022-06-28"):
        """
        Inicializa el uploader.

        Args:
            notion_token: Token de autenticación de Notion
            notion_version: Versión de la API de Notion
        """
        self._notion_token = notion_token
        self._notion_version = notion_version
        self._api_base = "https://api.notion.com/v1"
        
        self._headers = {
            "Authorization": f"Bearer {self._notion_token}",
            "Notion-Version": self._notion_version,
        }

    async def upload_file(self, file_path: str | Path) -> Optional[str]:
        """
        Sube un archivo a Notion usando el proceso de 3 pasos.

        Args:
            file_path: Ruta al archivo a subir

        Returns:
            file_upload_id si es exitoso, None si falla

        Raises:
            NotionFileUploaderError: Si falla la subida
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise NotionFileUploaderError(f"Archivo no encontrado: {file_path}")
        
        filename = file_path.name
        file_size = file_path.stat().st_size
        
        logger.info(f"🚀 Iniciando subida de archivo: {filename} ({file_size} bytes)")
        
        try:
            async with aiohttp.ClientSession() as session:
                # PASO 1: Crear File Upload Object
                file_upload_id = await self._create_file_upload_object(session)
                
                # PASO 2: Obtener URL de subida
                upload_url = await self._get_upload_url(session, file_upload_id)
                
                # PASO 3: Subir contenido del archivo
                await self._upload_file_content(
                    session, upload_url, file_path, filename
                )
                
                logger.info(f"✅ Archivo subido exitosamente: {filename}")
                return file_upload_id
                
        except aiohttp.ClientError as e:
            logger.error(f"❌ Error de red subiendo archivo: {e}")
            raise NotionFileUploaderError(f"Error de conexión: {str(e)}") from e
        except Exception as e:
            logger.error(f"❌ Error inesperado subiendo archivo: {e}", exc_info=True)
            raise NotionFileUploaderError(f"Error subiendo archivo: {str(e)}") from e

    async def _create_file_upload_object(self, session: aiohttp.ClientSession) -> str:
        """
        Paso 1: Crear File Upload Object en Notion.

        Args:
            session: Sesión HTTP activa

        Returns:
            file_upload_id

        Raises:
            NotionFileUploaderError: Si falla la creación
        """
        logger.debug("1️⃣ Creando File Upload Object...")
        
        create_url = f"{self._api_base}/file_uploads"
        headers = {
            **self._headers,
            "Content-Type": "application/json"
        }
        
        async with session.post(create_url, headers=headers, json={}) as response:
            if response.status != 200:
                error_text = await response.text()
                raise NotionFileUploaderError(
                    f"Error creando file upload object: {response.status} - {error_text}"
                )
            
            upload_data = await response.json()
            file_upload_id = upload_data.get("id")
            
            if not file_upload_id:
                raise NotionFileUploaderError("No se obtuvo file_upload_id")
            
            logger.debug(f"✅ File Upload Object creado: {file_upload_id}")
            return file_upload_id

    async def _get_upload_url(
        self, session: aiohttp.ClientSession, file_upload_id: str
    ) -> str:
        """
        Obtiene la URL de subida del File Upload Object.

        Args:
            session: Sesión HTTP activa
            file_upload_id: ID del file upload object

        Returns:
            URL de subida

        Raises:
            NotionFileUploaderError: Si falla la obtención
        """
        logger.debug("📡 Obteniendo URL de subida...")
        
        get_url = f"{self._api_base}/file_uploads/{file_upload_id}"
        
        async with session.get(get_url, headers=self._headers) as response:
            if response.status != 200:
                error_text = await response.text()
                raise NotionFileUploaderError(
                    f"Error obteniendo upload URL: {response.status} - {error_text}"
                )
            
            upload_data = await response.json()
            upload_url = upload_data.get("upload_url")
            
            if not upload_url:
                raise NotionFileUploaderError("No se obtuvo upload_url")
            
            logger.debug(f"✅ URL de subida obtenida")
            return upload_url

    async def _upload_file_content(
        self,
        session: aiohttp.ClientSession,
        upload_url: str,
        file_path: Path,
        filename: str,
    ) -> None:
        """
        Paso 2: Sube el contenido del archivo a la URL proporcionada.

        Args:
            session: Sesión HTTP activa
            upload_url: URL para subir el archivo
            file_path: Ruta del archivo
            filename: Nombre del archivo

        Raises:
            NotionFileUploaderError: Si falla la subida
        """
        logger.debug("2️⃣ Subiendo contenido del archivo...")
        
        with open(file_path, 'rb') as f:
            form_data = aiohttp.FormData()
            form_data.add_field('file', f, filename=filename)
            
            upload_headers = {
                "Authorization": f"Bearer {self._notion_token}",
                "Notion-Version": self._notion_version
            }
            
            async with session.post(
                upload_url, headers=upload_headers, data=form_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise NotionFileUploaderError(
                        f"Error subiendo archivo: {response.status} - {error_text}"
                    )
                
                upload_result = await response.json()
                status = upload_result.get("status")
                
                if status != "uploaded":
                    raise NotionFileUploaderError(
                        f"Estado del archivo no es 'uploaded': {status}"
                    )
                
                logger.debug(f"✅ Contenido subido exitosamente")
