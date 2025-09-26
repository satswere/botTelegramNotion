#!/usr/bin/env python3
"""
Script de prueba para verificar la integración con Notion
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Configurar path y cargar variables
sys.path.append(str(Path(__file__).parent / "src"))
load_dotenv()

def test_notion_connection():
    """Prueba la conexión con Notion"""
    try:
        from services.notion_service import get_notion_service
        
        # Verificar variables de entorno
        print("🔍 Verificando configuración...")
        notion_token = os.getenv('NOTION_TOKEN')
        notion_db_id = os.getenv('NOTION_DATABASE_ID')
        
        if not notion_token or notion_token == 'tu_token_de_notion_aqui':
            print("❌ NOTION_TOKEN no configurado en .env")
            print("💡 Ve a https://www.notion.so/my-integrations para crear una integración")
            return False
        
        if not notion_db_id:
            print("❌ NOTION_DATABASE_ID no configurado")
            return False
        
        print(f"✅ Token configurado: {notion_token[:20]}...")
        print(f"✅ Database ID: {notion_db_id}")
        
        # Probar conexión
        print("\n🔗 Probando conexión con Notion...")
        notion_service = get_notion_service()
        
        if notion_service.test_connection():
            print("✅ Conexión exitosa con Notion!")
            
            # Obtener información de la base de datos
            db_info = notion_service.get_database_info()
            if db_info and isinstance(db_info, dict):
                title = "Base de datos de apuestas"
                if "title" in db_info and db_info["title"]:
                    title = db_info["title"][0].get("plain_text", title)
                print(f"📊 Base de datos: {title}")
                
                # Mostrar propiedades disponibles
                if "properties" in db_info:
                    print("📝 Propiedades disponibles:")
                    for prop_name, prop_info in db_info["properties"].items():
                        prop_type = prop_info.get("type", "unknown")
                        print(f"   • {prop_name} ({prop_type})")
            
            # Probar creación de entrada de prueba
            print("\n📝 Probando creación de entrada...")
            page_id = notion_service.create_bet_entry(
                event_title="🧪 PRUEBA - Real Madrid vs Barcelona",
                tipster_name="@TipsterPrueba",
                image_path=None,
                additional_data={"test": True}
            )
            
            if page_id:
                print(f"✅ Entrada de prueba creada: {page_id}")
                print("🎉 ¡Notion funcionando perfectamente!")
                return True
            else:
                print("❌ Error creando entrada de prueba")
                return False
        else:
            print("❌ Error conectando con Notion")
            return False
            
    except ImportError as e:
        print(f"❌ Error importando: {e}")
        print("💡 Ejecuta: pip install notion-client")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Función principal"""
    print("🤖 Probando integración Bot Telegram + Notion")
    print("=" * 50)
    
    success = test_notion_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 ¡Todo funcionando! Puedes ejecutar el bot con:")
        print("   python bot_notion.py")
    else:
        print("❌ Hay problemas que resolver antes de usar el bot")
        print("\n💡 Pasos para configurar Notion:")
        print("1. Ve a https://www.notion.so/my-integrations")
        print("2. Crea una nueva integración")
        print("3. Copia el token de integración")
        print("4. Actualiza NOTION_TOKEN en el archivo .env")
        print("5. Comparte la base de datos con la integración")

if __name__ == "__main__":
    main()