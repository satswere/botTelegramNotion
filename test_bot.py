#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad del bot sin tokens reales.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from unittest.mock import Mock, patch
from datetime import datetime
from bot import NotionTelegramBot

def test_message_type_detection():
    """Test que verifica la detección de tipos de mensaje"""
    # Mock de un bot para pruebas
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'NOTION_TOKEN': 'test_notion_token', 
        'NOTION_DATABASE_ID': 'test_db_id'
    }):
        with patch('bot.Client') as mock_client:
            # Mock del cliente de Notion
            mock_notion = Mock()
            mock_notion.databases.retrieve.return_value = {"id": "test"}
            mock_client.return_value = mock_notion
            
            bot = NotionTelegramBot()
            
            # Test con mensaje de texto
            text_message = Mock()
            text_message.text = "Hola mundo"
            text_message.photo = None
            text_message.document = None
            assert bot._get_message_type(text_message) == "Texto"
            
            # Test con foto
            photo_message = Mock() 
            photo_message.text = None
            photo_message.photo = [Mock()]
            photo_message.document = None
            assert bot._get_message_type(photo_message) == "Foto"
            
            # Test con documento
            doc_message = Mock()
            doc_message.text = None
            doc_message.photo = None
            doc_message.document = Mock()
            assert bot._get_message_type(doc_message) == "Archivo"
            
            print("✅ Test de detección de tipos de mensaje: PASADO")

def test_title_generation():
    """Test que verifica la generación de títulos"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'NOTION_TOKEN': 'test_notion_token', 
        'NOTION_DATABASE_ID': 'test_db_id'
    }):
        with patch('bot.Client') as mock_client:
            mock_notion = Mock()
            mock_notion.databases.retrieve.return_value = {"id": "test"}
            mock_client.return_value = mock_notion
            
            bot = NotionTelegramBot()
            
            # Test con texto corto
            message = Mock()
            message.text = "Mensaje corto"
            message.caption = None
            message.photo = None
            message.document = None
            title = bot._get_title(message)
            assert title == "Mensaje corto"
            
            # Test con texto largo
            message.text = "Este es un mensaje muy largo que debería ser truncado en algún punto para no exceder los 50 caracteres"
            title = bot._get_title(message)
            assert len(title) <= 53  # 50 + "..."
            assert "..." in title
            
            print("✅ Test de generación de títulos: PASADO")

def test_additional_text():
    """Test que verifica la generación de texto adicional"""
    with patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'test_token',
        'NOTION_TOKEN': 'test_notion_token', 
        'NOTION_DATABASE_ID': 'test_db_id'
    }):
        with patch('bot.Client') as mock_client:
            mock_notion = Mock()
            mock_notion.databases.retrieve.return_value = {"id": "test"}
            mock_client.return_value = mock_notion
            
            bot = NotionTelegramBot()
            
            # Test con texto
            message = Mock()
            message.text = "Texto de prueba"
            message.caption = None
            message.document = None
            message.photo = None
            additional_text = bot._get_additional_text(message)
            assert additional_text == "Texto de prueba"
            
            # Test con documento
            message.text = None
            message.caption = "Caption del documento"
            document = Mock()
            document.file_name = "documento.pdf"
            document.file_size = 1024
            message.document = document
            additional_text = bot._get_additional_text(message)
            assert "Caption del documento" in additional_text
            assert "documento.pdf" in additional_text
            assert "1024" in additional_text
            
            print("✅ Test de texto adicional: PASADO")

def main():
    """Ejecutar todas las pruebas"""
    print("Ejecutando pruebas del bot...")
    print()
    
    try:
        test_message_type_detection()
        test_title_generation() 
        test_additional_text()
        print()
        print("🎉 Todas las pruebas pasaron exitosamente!")
        return True
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)