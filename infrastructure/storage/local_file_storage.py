"""
Local File Storage - Almacenamiento local de archivos

Error Handling Strategy:
- FileStorageError: Custom exception for storage operations
- Handles FileNotFoundError for missing files
- Handles PermissionError for access denied
- Handles OSError for disk/IO issues
- Comprehensive logging at debug, info, warning, and error levels
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FileStorageError(Exception):
    """Error específico del almacenamiento de archivos."""

    pass


class LocalFileStorage:
    """Almacenamiento local de archivos"""

    def __init__(self, base_path: str = "storage/images"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 LocalFileStorage inicializado: {self.base_path.absolute()}")

    async def save(
        self, file_data: bytes, filename: str, metadata: Optional[dict] = None
    ) -> str:
        """
        Guarda archivo localmente.

        Args:
            file_data: Datos binarios del archivo
            filename: Nombre del archivo
            metadata: Metadatos opcionales (no usado actualmente)

        Returns:
            Ruta completa del archivo guardado

        Raises:
            FileStorageError: Si falla el guardado
        """
        logger.debug(f"💾 Guardando archivo: {filename} ({len(file_data)} bytes)")

        try:
            file_path = self.base_path / filename

            with open(file_path, "wb") as f:
                f.write(file_data)

            logger.info(f"✅ Archivo guardado exitosamente: {filename} en {file_path}")
            return str(file_path)

        except PermissionError as e:
            logger.error(f"❌ Permiso denegado guardando archivo {filename}: {e}")
            raise FileStorageError(f"Sin permisos para guardar {filename}") from e

        except OSError as e:
            logger.error(f"❌ Error de IO guardando archivo {filename}: {e}")
            raise FileStorageError(
                f"Error de disco guardando {filename}: {str(e)}"
            ) from e

        except Exception as e:
            logger.error(
                f"❌ Error inesperado guardando archivo {filename}: {e}", exc_info=True
            )
            raise FileStorageError(f"Error guardando archivo: {str(e)}") from e

    async def load(self, filename: str) -> bytes:
        """
        Carga archivo desde disco.

        Args:
            filename: Nombre del archivo a cargar

        Returns:
            Datos binarios del archivo

        Raises:
            FileStorageError: Si falla la carga o el archivo no existe
        """
        logger.debug(f"📂 Cargando archivo: {filename}")

        try:
            file_path = self.base_path / filename

            with open(file_path, "rb") as f:
                data = f.read()

            logger.info(
                f"✅ Archivo cargado exitosamente: {filename} ({len(data)} bytes)"
            )
            return data

        except FileNotFoundError as e:
            logger.error(f"❌ Archivo no encontrado: {filename}")
            raise FileStorageError(f"Archivo no encontrado: {filename}") from e

        except PermissionError as e:
            logger.error(f"❌ Permiso denegado cargando archivo {filename}: {e}")
            raise FileStorageError(f"Sin permisos para leer {filename}") from e

        except OSError as e:
            logger.error(f"❌ Error de IO cargando archivo {filename}: {e}")
            raise FileStorageError(
                f"Error de disco cargando {filename}: {str(e)}"
            ) from e

        except Exception as e:
            logger.error(
                f"❌ Error inesperado cargando archivo {filename}: {e}", exc_info=True
            )
            raise FileStorageError(f"Error cargando archivo: {str(e)}") from e

    async def delete(self, filename: str) -> bool:
        """Elimina archivo del disco"""
        try:
            file_path = self.base_path / filename

            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️ Archivo eliminado: {filename}")
                return True
            else:
                logger.warning(f"⚠️ Archivo no encontrado para eliminar: {filename}")
                return False

        except Exception as e:
            logger.error(f"❌ Error eliminando archivo {filename}: {e}")
            return False

    async def exists(self, filename: str) -> bool:
        """Verifica si un archivo existe"""
        file_path = self.base_path / filename
        return file_path.exists()

    async def list_files(
        self, pattern: Optional[str] = None, limit: int = 100
    ) -> list[str]:
        """Lista archivos en el directorio"""
        try:
            if pattern:
                files = list(self.base_path.glob(pattern))
            else:
                files = list(self.base_path.iterdir())

            # Solo archivos, no directorios
            files = [f.name for f in files if f.is_file()]

            return files[:limit]

        except Exception as e:
            logger.error(f"❌ Error listando archivos: {e}")
            return []

    async def get_size(self, filename: str) -> int:
        """
        Obtiene tamaño del archivo en bytes.

        Args:
            filename: Nombre del archivo

        Returns:
            Tamaño en bytes

        Raises:
            FileStorageError: Si el archivo no existe o falla la operación
        """
        logger.debug(f"📏 Obteniendo tamaño de: {filename}")

        try:
            file_path = self.base_path / filename

            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {filename}")

            size = file_path.stat().st_size
            logger.info(f"✅ Tamaño obtenido: {filename} = {size} bytes")
            return size

        except FileNotFoundError as e:
            logger.error(f"❌ Archivo no encontrado: {filename}")
            raise FileStorageError(f"Archivo no encontrado: {filename}") from e

        except PermissionError as e:
            logger.error(f"❌ Permiso denegado accediendo a {filename}: {e}")
            raise FileStorageError(f"Sin permisos para acceder a {filename}") from e

        except Exception as e:
            logger.error(
                f"❌ Error inesperado obteniendo tamaño de {filename}: {e}",
                exc_info=True,
            )
            raise FileStorageError(f"Error obteniendo tamaño: {str(e)}") from e

    def get_path(self, filename: str) -> Path:
        """Obtiene la ruta completa de un archivo"""
        return self.base_path / filename
