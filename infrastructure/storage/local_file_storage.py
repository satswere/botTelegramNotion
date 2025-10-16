"""Local File Storage - Almacenamiento local de archivos"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalFileStorage:
    """Almacenamiento local de archivos"""
    
    def __init__(self, base_path: str = "storage/images"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 LocalFileStorage inicializado: {self.base_path.absolute()}")
    
    async def save(
        self, 
        file_data: bytes, 
        filename: str,
        metadata: Optional[dict] = None
    ) -> str:
        """Guarda archivo localmente"""
        try:
            file_path = self.base_path / filename
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"✅ Archivo guardado: {filename} ({len(file_data)} bytes)")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Error guardando archivo {filename}: {e}")
            raise
    
    async def load(self, filename: str) -> bytes:
        """Carga archivo desde disco"""
        try:
            file_path = self.base_path / filename
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            logger.info(f"✅ Archivo cargado: {filename} ({len(data)} bytes)")
            return data
            
        except FileNotFoundError:
            logger.error(f"❌ Archivo no encontrado: {filename}")
            raise
        except Exception as e:
            logger.error(f"❌ Error cargando archivo {filename}: {e}")
            raise
    
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
        self, 
        pattern: Optional[str] = None,
        limit: int = 100
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
        """Obtiene tamaño del archivo en bytes"""
        file_path = self.base_path / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {filename}")
        
        return file_path.stat().st_size
    
    def get_path(self, filename: str) -> Path:
        """Obtiene la ruta completa de un archivo"""
        return self.base_path / filename
