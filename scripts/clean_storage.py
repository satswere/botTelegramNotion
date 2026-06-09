"""
Script de Limpieza de Almacenamiento Temporal

Limpia archivos antiguos de storage/ para mantener el sistema eficiente.
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def clean_images(days_old: int = 7) -> int:
    """
    Limpia imágenes procesadas más antiguas que X días.
    
    Args:
        days_old: Días de antigüedad para considerar archivo antiguo
        
    Returns:
        Número de archivos eliminados
    """
    images_path = Path("storage/images")
    if not images_path.exists():
        print(f"ℹ️  Carpeta {images_path} no existe")
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    
    for file in images_path.glob("*"):
        if file.is_file():
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            if file_time < cutoff_time:
                file.unlink()
                deleted_count += 1
                print(f"🗑️  Eliminado: {file.name} (antigüedad: {(datetime.now() - file_time).days} días)")
    
    return deleted_count


def clean_logs(days_old: int = 30) -> int:
    """
    Limpia logs antiguos.
    
    Args:
        days_old: Días de antigüedad para considerar log antiguo
        
    Returns:
        Número de archivos eliminados
    """
    logs_path = Path("storage/logs")
    if not logs_path.exists():
        print(f"ℹ️  Carpeta {logs_path} no existe")
        return 0
    
    cutoff_time = datetime.now() - timedelta(days=days_old)
    deleted_count = 0
    
    for file in logs_path.glob("*.log*"):
        if file.is_file() and file.name != "current.log":
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            if file_time < cutoff_time:
                file.unlink()
                deleted_count += 1
                print(f"🗑️  Eliminado: {file.name} (antigüedad: {(datetime.now() - file_time).days} días)")
    
    return deleted_count


def clean_pycache() -> int:
    """
    Elimina todos los __pycache__ del proyecto.
    
    Returns:
        Número de carpetas eliminadas
    """
    project_root = Path(".")
    deleted_count = 0
    
    for pycache in project_root.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)
            deleted_count += 1
            print(f"🗑️  Eliminado: {pycache}")
    
    return deleted_count


def get_storage_size() -> dict:
    """
    Calcula el tamaño de las carpetas de storage.
    
    Returns:
        Dict con tamaños en bytes
    """
    sizes = {}
    
    for folder in ["storage/images", "storage/logs", "__pycache__"]:
        path = Path(folder)
        if not path.exists():
            sizes[folder] = 0
            continue
        
        total_size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        sizes[folder] = total_size
    
    return sizes


def format_size(bytes_size: int) -> str:
    """Formatea bytes a formato legible"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def main():
    """Ejecuta la limpieza completa"""
    print("=" * 70)
    print("🧹 SCRIPT DE LIMPIEZA DE ALMACENAMIENTO")
    print("=" * 70)
    print()
    
    # Mostrar tamaño actual
    print("📊 Tamaño actual:")
    sizes = get_storage_size()
    for folder, size in sizes.items():
        print(f"   {folder}: {format_size(size)}")
    print()
    
    # Ejecutar limpieza
    print("🗑️  Ejecutando limpieza...")
    print()
    
    images_deleted = clean_images(days_old=7)
    logs_deleted = clean_logs(days_old=30)
    pycache_deleted = clean_pycache()
    
    print()
    print("=" * 70)
    print("✅ LIMPIEZA COMPLETADA")
    print("=" * 70)
    print(f"📸 Imágenes eliminadas: {images_deleted}")
    print(f"📝 Logs eliminados: {logs_deleted}")
    print(f"🐍 __pycache__ eliminados: {pycache_deleted}")
    print()
    
    # Mostrar tamaño final
    print("📊 Tamaño final:")
    sizes_final = get_storage_size()
    for folder, size in sizes_final.items():
        size_diff = sizes.get(folder, 0) - size
        print(f"   {folder}: {format_size(size)} (liberado: {format_size(size_diff)})")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Limpieza cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error durante la limpieza: {e}")
        sys.exit(1)
