#!/usr/bin/env python3
"""
Script Final - Inicializador del Bot Telegram + Notion
Versión más simple para ejecutar directamente
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    print("🤖 Bot Telegram + Notion - Extractor de Imágenes y Tipsters")
    print("=" * 60)
    
    # Cargar configuración
    load_dotenv()
    
    # Verificar configuración básica
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    notion_token = os.getenv('NOTION_TOKEN')
    notion_db_id = os.getenv('NOTION_DATABASE_ID')
    
    print("🔍 Verificando configuración...")
    
    # Telegram (obligatorio)
    if not telegram_token:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        print("💡 Configura el token del bot en el archivo .env")
        return False
    
    print("✅ Token de Telegram configurado")
    
    # Notion (opcional)
    notion_configured = (
        notion_token and 
        notion_token != 'tu_token_de_notion_aqui' and
        notion_db_id
    )
    
    if notion_configured:
        print("✅ Notion configurado correctamente")
        print(f"📊 Base de datos: {notion_db_id}")
    else:
        print("⚠️  Notion no configurado (modo solo Telegram)")
    
    # Verificar carpeta de imágenes
    images_folder = Path("imagenes_recibidas")
    images_folder.mkdir(exist_ok=True)
    print(f"📁 Carpeta de imágenes: {images_folder.absolute()}")
    
    print("\n" + "=" * 60)
    print("🚀 INICIANDO BOT...")
    print("=" * 60)
    
    # Importar y ejecutar el bot híbrido
    try:
        from bot_hybrid import TelegramBotHybrid
        bot = TelegramBotHybrid()
        bot.run()
    except ImportError as e:
        print(f"❌ Error importando bot: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 ¡Bot detenido!")
    except Exception as e:
        print(f"\n❌ Error: {e}")