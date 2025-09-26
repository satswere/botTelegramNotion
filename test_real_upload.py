#!/usr/bin/env python3
"""
Test de subida REAL de archivos a Notion usando el proceso oficial de 3 pasos
Prueba la implementación completa según la documentación de Notion
"""

import os
import logging
import asyncio
import aiohttp
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

# Cargar variables de entorno
load_dotenv()

# Configuración del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotionRealUploadTester:
    """Tester para subida real de archivos a Notion"""
    
    def __init__(self):
        """Inicializa el tester"""
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = "27aa8baa-ff5a-808b-8cc4-d3cc8f010fa0"
        
        if not self.notion_token:
            raise ValueError("Falta NOTION_TOKEN en el archivo .env")
        
        # Crear cliente de Notion
        self.notion_client = Client(auth=self.notion_token)
        
        # Configuración para la API
        self.notion_api_base = "https://api.notion.com/v1"
        self.notion_headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28"
        }
        
        logger.info("Cliente de Notion inicializado para test de subida real")
    
    async def upload_file_real(self, file_path: Path) -> str:
        """
        Implementa el proceso completo de 3 pasos para subir archivo a Notion
        
        Returns:
            file_upload_id si es exitoso, None si falla
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            file_size = file_path.stat().st_size
            logger.info(f"🚀 Iniciando subida REAL: {file_path.name} ({file_size} bytes)")
            
            async with aiohttp.ClientSession() as session:
                # PASO 1: Crear File Upload Object
                logger.info("1️⃣ Creando File Upload Object...")
                
                create_url = f"{self.notion_api_base}/file_uploads"
                headers = {
                    **self.notion_headers,
                    "Content-Type": "application/json"
                }
                
                async with session.post(create_url, headers=headers, json={}) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Error creando file upload object: {response.status} - {error_text}")
                    
                    upload_data = await response.json()
                    file_upload_id = upload_data.get("id")
                    upload_url = upload_data.get("upload_url")
                    expiry_time = upload_data.get("expiry_time")
                    
                    if not file_upload_id or not upload_url:
                        raise Exception("No se obtuvo ID o URL de subida")
                    
                    logger.info(f"✅ File Upload Object creado:")
                    logger.info(f"   ID: {file_upload_id}")
                    logger.info(f"   Upload URL: {upload_url}")
                    logger.info(f"   Expira: {expiry_time}")
                
                # PASO 2: Subir el contenido del archivo
                logger.info("2️⃣ Subiendo contenido del archivo...")
                
                with open(file_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field('file', f, filename=file_path.name)
                    
                    # Headers para la subida (sin Content-Type explícito)
                    upload_headers = {
                        "Authorization": f"Bearer {self.notion_token}",
                        "Notion-Version": "2022-06-28"
                    }
                    
                    async with session.post(upload_url, headers=upload_headers, data=form_data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"Error subiendo archivo: {response.status} - {error_text}")
                        
                        upload_result = await response.json()
                        status = upload_result.get("status")
                        filename = upload_result.get("filename")
                        content_type = upload_result.get("content_type")
                        content_length = upload_result.get("content_length")
                        
                        if status != "uploaded":
                            raise Exception(f"Estado del archivo no es 'uploaded': {status}")
                        
                        logger.info(f"✅ Archivo subido exitosamente:")
                        logger.info(f"   Nombre: {filename}")
                        logger.info(f"   Tipo: {content_type}")
                        logger.info(f"   Tamaño: {content_length} bytes")
                        logger.info(f"   Estado: {status}")
                        
                        return file_upload_id
                        
        except Exception as e:
            logger.error(f"❌ Error en subida real: {e}")
            raise
    
    def create_record_with_real_file(self, title: str, file_upload_id: str, filename: str) -> str:
        """
        PASO 3: Crear registro con archivo real adjunto
        """
        try:
            logger.info("3️⃣ Creando registro con archivo real adjunto...")
            
            properties = {
                # Campo título - origin_chat_title
                "Evento / Selección": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                },
                # Fecha actual
                "Fecha": {
                    "date": {
                        "start": datetime.now().isoformat()[:10]
                    }
                },
                # Estado inicial
                "Resultado": {
                    "select": {
                        "name": "Pendiente"
                    }
                },
                # ARCHIVO REAL usando file_upload_id
                "Captura / Comprobante": {
                    "files": [
                        {
                            "type": "file_upload",
                            "file_upload": {
                                "id": file_upload_id
                            },
                            "name": filename
                        }
                    ]
                },
                # Información adicional
                "Mercado / Selección": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"Test de subida REAL - Archivo: {filename}"
                            }
                        }
                    ]
                }
            }
            
            # Crear el registro
            response = self.notion_client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            if isinstance(response, dict) and "id" in response:
                page_id = response["id"]
                page_url = response.get("url", "")
                
                logger.info(f"✅ Registro creado con archivo REAL:")
                logger.info(f"   Page ID: {page_id}")
                logger.info(f"   URL: {page_url}")
                logger.info(f"   File Upload ID: {file_upload_id}")
                
                return page_id
            else:
                raise Exception("Respuesta inesperada de Notion API")
                
        except Exception as e:
            logger.error(f"❌ Error creando registro: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Prueba la conexión con Notion"""
        try:
            response = self.notion_client.databases.retrieve(self.database_id)
            if isinstance(response, dict):
                title = "Base de datos de Apuestas"
                if "title" in response and response["title"]:
                    title = response["title"][0].get("plain_text", title)
                
                logger.info(f"✅ Conexión exitosa con: {title}")
                return True
        except Exception as e:
            logger.error(f"❌ Error conectando con Notion: {e}")
            return False
    
    async def run_complete_test(self):
        """Ejecuta el test completo de subida real"""
        logger.info("🧪 INICIANDO TEST DE SUBIDA REAL DE ARCHIVOS")
        print("="*80)
        
        try:
            # 1. Test de conexión
            logger.info("Paso 0: Probando conexión...")
            if not self.test_connection():
                raise Exception("No se pudo conectar con Notion")
            
            # 2. Buscar archivo de prueba
            logger.info("Buscando archivo de prueba...")
            images_folder = Path("imagenes_recibidas")
            test_file = None
            
            if images_folder.exists():
                for file_path in images_folder.glob("*"):
                    if file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                        test_file = file_path
                        break
            
            if not test_file:
                raise Exception("No hay archivos de prueba en 'imagenes_recibidas'")
            
            logger.info(f"📁 Usando archivo: {test_file.name}")
            
            # 3. Ejecutar subida real (3 pasos)
            file_upload_id = await self.upload_file_real(test_file)
            
            # 4. Crear registro con archivo real
            origin_chat_title = f"TEST REAL - {test_file.name}"
            page_id = self.create_record_with_real_file(
                title=origin_chat_title,
                file_upload_id=file_upload_id,
                filename=test_file.name
            )
            
            logger.info("🎉 TEST COMPLETADO EXITOSAMENTE")
            logger.info(f"Título: {origin_chat_title}")
            logger.info(f"Page ID: {page_id}")
            logger.info(f"File Upload ID: {file_upload_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ TEST FALLIDO: {e}")
            return False


async def main():
    """Función principal"""
    try:
        print("🧪 TEST DE SUBIDA REAL DE ARCHIVOS A NOTION")
        print("Implementación según documentación oficial de Notion")
        print("="*80)
        
        tester = NotionRealUploadTester()
        success = await tester.run_complete_test()
        
        print("\n" + "="*80)
        if success:
            print("✅ SUBIDA REAL EXITOSA")
            print("💡 Los archivos ahora se ven realmente en Notion")
            print("🔗 Revisa el registro creado en tu base de datos")
        else:
            print("❌ TEST FALLIDO")
            print("💡 Revisa los logs para más detalles")
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())