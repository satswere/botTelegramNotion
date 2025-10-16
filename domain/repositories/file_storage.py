"""
IFileStorage - Interfaz de Almacenamiento de Archivos

Define el contrato para gestión de archivos sin conocer el backend.
Permite cambiar de almacenamiento local a S3, Azure Blob, etc.
"""

from typing import Protocol, Optional
from pathlib import Path


class IFileStorage(Protocol):
    """
    Puerto (Interface) para almacenamiento de archivos.

    Esta interfaz define las operaciones de almacenamiento
    sin depender de una implementación específica.

    Implementaciones:
        - LocalFileStorage (actual)
        - S3FileStorage (futuro - AWS S3)
        - AzureBlobStorage (futuro - Azure)
        - InMemoryFileStorage (tests)

    Ejemplo de uso:
        >>> storage = LocalFileStorage(base_path="storage/images")
        >>> file_path = await storage.save(file_data, "bet_image.jpg")
        >>> await storage.delete("bet_image.jpg")
    """

    async def save(
        self, file_data: bytes, filename: str, metadata: Optional[dict] = None
    ) -> str:
        """
        Guarda un archivo y retorna su ruta o identificador.

        Args:
            file_data: Contenido binario del archivo
            filename: Nombre del archivo (puede incluir extensión)
            metadata: Metadatos adicionales (opcional):
                - content_type: str - Tipo MIME
                - size: int - Tamaño en bytes
                - original_name: str - Nombre original

        Returns:
            str: Ruta completa o identificador del archivo guardado

        Raises:
            StorageError: Si falla el guardado
            InsufficientSpaceError: Si no hay espacio disponible

        Example:
            >>> with open("image.jpg", "rb") as f:
            ...     file_data = f.read()
            >>> path = await storage.save(
            ...     file_data,
            ...     "bet_20241016.jpg",
            ...     metadata={"content_type": "image/jpeg"}
            ... )
            >>> print(path)  # "storage/images/bet_20241016.jpg"
        """
        ...

    async def load(self, filename: str) -> bytes:
        """
        Carga el contenido de un archivo.

        Args:
            filename: Nombre o ruta del archivo

        Returns:
            bytes: Contenido binario del archivo

        Raises:
            FileNotFoundError: Si el archivo no existe
            StorageError: Si hay error al leer

        Example:
            >>> file_data = await storage.load("bet_20241016.jpg")
            >>> print(len(file_data))  # Tamaño en bytes
        """
        ...

    async def delete(self, filename: str) -> bool:
        """
        Elimina un archivo del almacenamiento.

        Args:
            filename: Nombre o ruta del archivo a eliminar

        Returns:
            bool: True si se eliminó, False si no existía

        Raises:
            StorageError: Si hay error al eliminar

        Example:
            >>> deleted = await storage.delete("bet_20241016.jpg")
            >>> if deleted:
            ...     print("Archivo eliminado")
        """
        ...

    async def exists(self, filename: str) -> bool:
        """
        Verifica si un archivo existe.

        Args:
            filename: Nombre o ruta del archivo

        Returns:
            bool: True si existe, False en caso contrario

        Example:
            >>> if await storage.exists("bet_20241016.jpg"):
            ...     print("El archivo existe")
        """
        ...

    async def list_files(
        self, pattern: Optional[str] = None, limit: int = 100
    ) -> list[str]:
        """
        Lista archivos en el almacenamiento.

        Args:
            pattern: Patrón para filtrar (ej: "*.jpg")
            limit: Número máximo de resultados

        Returns:
            Lista de nombres/rutas de archivos

        Example:
            >>> files = await storage.list_files(pattern="*.jpg", limit=10)
            >>> for file in files:
            ...     print(file)
        """
        ...

    async def get_size(self, filename: str) -> int:
        """
        Obtiene el tamaño de un archivo en bytes.

        Args:
            filename: Nombre del archivo

        Returns:
            int: Tamaño en bytes

        Raises:
            FileNotFoundError: Si el archivo no existe
        """
        ...
