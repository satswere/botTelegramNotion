#!/usr/bin/env python3
"""
Prueba de conexión a Notion con las propiedades correctas
"""

import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from notion_client import Client

# Cargar variables de entorno
load_dotenv()

def test_notion_connection():
    """Prueba la conexión con Notion usando las propiedades correctas."""
    
    # Verificar variables de entorno
    notion_token = os.getenv('NOTION_TOKEN')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    print("🔍 Verificando configuración...")
    print(f"Token: {'✅ Configurado' if notion_token else '❌ No encontrado'}")
    print(f"Database ID: {'✅ Configurado' if database_id else '❌ No encontrado'}")
    
    if not notion_token or not database_id:
        print("❌ Faltan variables de entorno")
        return False
    
    try:
        # Conectar con Notion
        print("\n🔌 Conectando con Notion...")
        notion = Client(auth=notion_token)
        
        # Verificar acceso a la base de datos
        print("📊 Verificando base de datos...")
        database = notion.databases.retrieve(database_id)
        print(f"✅ Base de datos encontrada: {database['title'][0]['plain_text']}")
        
        # Crear página de prueba
        print("\n📝 Creando página de prueba...")
        properties = {
            "Evento / Selección": {
                "title": [{"text": {"content": f"Prueba de conexión - {datetime.now().strftime('%H:%M:%S')}"}}]
            },
            "Fecha": {
                "date": {"start": datetime.now().isoformat()}
            },
            "Resultado": {
                "select": {"name": "Pendiente"}
            },
            "Tipo de apuesta": {
                "select": {"name": "Simple"}
            },
            "Mercado / Selección": {
                "rich_text": [{"text": {"content": "Esta es una prueba de conexión desde el bot"}}]
            }
        }
        
        page = notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        
        page_id = page['id']
        print(f"✅ Página creada exitosamente: {page_id}")
        
        # Leer la página creada
        print("📖 Verificando página creada...")
        created_page = notion.pages.retrieve(page_id)
        title = created_page['properties']['Evento / Selección']['title'][0]['plain_text']
        print(f"✅ Página verificada: '{title}'")
        
        print("\n🎉 ¡Conexión con Notion exitosa!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test de Conexión con Notion")
    print("=" * 40)
    
    success = test_notion_connection()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ RESULTADO: Conexión exitosa")
        print("📱 El bot debería poder subir a Notion correctamente")
    else:
        print("❌ RESULTADO: Error en la conexión")
        print("🔧 Revisar configuración antes de usar el bot")