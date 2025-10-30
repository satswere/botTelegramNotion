"""
Unit Tests for LocalFileStorage with Mocked Filesystem

Tests the LocalFileStorage adapter in isolation by mocking filesystem operations
and verifying error handling for permissions, IO errors, and file operations.
"""

import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock
from pathlib import Path

from infrastructure.storage.local_file_storage import LocalFileStorage, FileStorageError


@pytest.fixture
def storage(tmp_path):
    """Storage instance con directorio temporal"""
    return LocalFileStorage(base_path=str(tmp_path))


class TestLocalFileStorageSave:
    """Tests para el método save()"""

    @pytest.mark.asyncio
    async def test_save_success(self, storage):
        """Test guardado exitoso de archivo"""
        # Arrange
        file_data = b"Test file content"
        filename = "test.txt"

        # Act
        result = await storage.save(file_data, filename)

        # Assert
        assert filename in result
        saved_path = Path(result)
        assert saved_path.exists()
        assert saved_path.read_bytes() == file_data

    @pytest.mark.asyncio
    async def test_save_permission_error(self, storage):
        """Test manejo de error de permisos"""
        # Arrange
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            # Act & Assert
            with pytest.raises(FileStorageError) as exc_info:
                await storage.save(b"data", "test.txt")

            assert "Sin permisos para guardar" in str(exc_info.value)
            assert isinstance(exc_info.value.__cause__, PermissionError)

    @pytest.mark.asyncio
    async def test_save_os_error(self, storage):
        """Test manejo de error de IO"""
        # Arrange
        with patch("builtins.open", side_effect=OSError("Disk full")):
            # Act & Assert
            with pytest.raises(FileStorageError) as exc_info:
                await storage.save(b"data", "test.txt")

            assert "Error de disco guardando" in str(exc_info.value)
            assert isinstance(exc_info.value.__cause__, OSError)

    @pytest.mark.asyncio
    async def test_save_generic_error(self, storage):
        """Test manejo de error genérico"""
        # Arrange
        with patch("builtins.open", side_effect=Exception("Unexpected error")):
            # Act & Assert
            with pytest.raises(FileStorageError) as exc_info:
                await storage.save(b"data", "test.txt")

            assert "Error guardando archivo" in str(exc_info.value)


class TestLocalFileStorageLoad:
    """Tests para el método load()"""

    @pytest.mark.asyncio
    async def test_load_success(self, storage):
        """Test carga exitosa de archivo"""
        # Arrange
        file_data = b"Test content"
        filename = "test.txt"
        await storage.save(file_data, filename)

        # Act
        result = await storage.load(filename)

        # Assert
        assert result == file_data

    @pytest.mark.asyncio
    async def test_load_file_not_found(self, storage):
        """Test carga de archivo no existente"""
        # Act & Assert
        with pytest.raises(FileStorageError) as exc_info:
            await storage.load("nonexistent.txt")

        assert "Archivo no encontrado" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, FileNotFoundError)

    @pytest.mark.asyncio
    async def test_load_permission_error(self, storage):
        """Test manejo de error de permisos al cargar"""
        # Arrange
        filename = "test.txt"
        await storage.save(b"data", filename)

        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            # Act & Assert
            with pytest.raises(FileStorageError) as exc_info:
                await storage.load(filename)

            assert "Sin permisos para leer" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_load_os_error(self, storage):
        """Test manejo de error de IO al cargar"""
        # Arrange
        filename = "test.txt"
        await storage.save(b"data", filename)

        with patch("builtins.open", side_effect=OSError("IO error")):
            # Act & Assert
            with pytest.raises(FileStorageError) as exc_info:
                await storage.load(filename)

            assert "Error de disco cargando" in str(exc_info.value)


class TestLocalFileStorageDelete:
    """Tests para el método delete()"""

    @pytest.mark.asyncio
    async def test_delete_success(self, storage):
        """Test eliminación exitosa de archivo"""
        # Arrange
        filename = "test.txt"
        await storage.save(b"data", filename)

        # Act
        result = await storage.delete(filename)

        # Assert
        assert result is True
        assert not await storage.exists(filename)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_file(self, storage):
        """Test eliminación de archivo no existente"""
        # Act
        result = await storage.delete("nonexistent.txt")

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_error(self, storage):
        """Test manejo de error al eliminar"""
        # Arrange
        filename = "test.txt"
        await storage.save(b"data", filename)

        with patch.object(Path, "unlink", side_effect=OSError("Cannot delete")):
            # Act
            result = await storage.delete(filename)

            # Assert
            assert result is False


class TestLocalFileStorageExists:
    """Tests para el método exists()"""

    @pytest.mark.asyncio
    async def test_exists_true(self, storage):
        """Test archivo existente"""
        # Arrange
        filename = "test.txt"
        await storage.save(b"data", filename)

        # Act
        result = await storage.exists(filename)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, storage):
        """Test archivo no existente"""
        # Act
        result = await storage.exists("nonexistent.txt")

        # Assert
        assert result is False


class TestLocalFileStorageGetSize:
    """Tests para el método get_size()"""

    @pytest.mark.asyncio
    async def test_get_size_success(self, storage):
        """Test obtención exitosa de tamaño"""
        # Arrange
        file_data = b"12345"  # 5 bytes
        filename = "test.txt"
        await storage.save(file_data, filename)

        # Act
        size = await storage.get_size(filename)

        # Assert
        assert size == 5

    @pytest.mark.asyncio
    async def test_get_size_file_not_found(self, storage):
        """Test obtención de tamaño de archivo no existente"""
        # Act & Assert
        with pytest.raises(FileStorageError) as exc_info:
            await storage.get_size("nonexistent.txt")

        assert "Archivo no encontrado" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, FileNotFoundError)

    @pytest.mark.asyncio
    async def test_get_size_permission_error(self, storage):
        """Test manejo de error de permisos"""
        # Arrange
        filename = "test.txt"
        await storage.save(b"data", filename)

        with patch.object(Path, "stat", side_effect=PermissionError("Access denied")):
            # Act & Assert
            with pytest.raises(FileStorageError) as exc_info:
                await storage.get_size(filename)

            assert "Sin permisos para acceder" in str(exc_info.value)


class TestLocalFileStorageListFiles:
    """Tests para el método list_files()"""

    @pytest.mark.asyncio
    async def test_list_files_success(self, storage):
        """Test listado exitoso de archivos"""
        # Arrange
        await storage.save(b"data1", "file1.txt")
        await storage.save(b"data2", "file2.txt")
        await storage.save(b"data3", "file3.jpg")

        # Act
        files = await storage.list_files()

        # Assert
        assert len(files) == 3
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "file3.jpg" in files

    @pytest.mark.asyncio
    async def test_list_files_with_pattern(self, storage):
        """Test listado con patrón de filtro"""
        # Arrange
        await storage.save(b"data1", "file1.txt")
        await storage.save(b"data2", "file2.txt")
        await storage.save(b"data3", "file3.jpg")

        # Act
        files = await storage.list_files(pattern="*.txt")

        # Assert
        assert len(files) == 2
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "file3.jpg" not in files

    @pytest.mark.asyncio
    async def test_list_files_with_limit(self, storage):
        """Test listado con límite"""
        # Arrange
        for i in range(10):
            await storage.save(b"data", f"file{i}.txt")

        # Act
        files = await storage.list_files(limit=5)

        # Assert
        assert len(files) == 5

    @pytest.mark.asyncio
    async def test_list_files_error_returns_empty_list(self, storage):
        """Test que errores retornan lista vacía"""
        # Arrange
        with patch.object(Path, "iterdir", side_effect=OSError("Cannot list")):
            # Act
            files = await storage.list_files()

            # Assert
            assert files == []


class TestLocalFileStorageGetPath:
    """Tests para el método get_path()"""

    def test_get_path(self, storage):
        """Test obtención de ruta completa"""
        # Act
        path = storage.get_path("test.txt")

        # Assert
        assert isinstance(path, Path)
        assert path.name == "test.txt"
        assert str(storage.base_path) in str(path)
