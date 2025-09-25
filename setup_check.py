#!/usr/bin/env python3
"""
Script para validar la configuración del bot y mostrar ejemplos.
"""

import os
import sys
from dotenv import load_dotenv

def check_configuration():
    """Verifica que la configuración esté completa"""
    print("🔍 Verificando configuración...")
    print()
    
    # Cargar variables de entorno
    load_dotenv()
    
    required_vars = [
        ('TELEGRAM_BOT_TOKEN', 'Token del bot de Telegram'),
        ('NOTION_TOKEN', 'Token de integración de Notion'),
        ('NOTION_DATABASE_ID', 'ID de la base de datos de Notion')
    ]
    
    missing_vars = []
    
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if not value or value.startswith('your_') or value.startswith('tu_'):
            missing_vars.append((var_name, description))
            print(f"❌ {var_name}: No configurado")
        else:
            # Mostrar valor parcialmente oculto para seguridad
            masked_value = value[:8] + '*' * (len(value) - 8) if len(value) > 8 else '*' * len(value)
            print(f"✅ {var_name}: {masked_value}")
    
    print()
    
    if missing_vars:
        print("⚠️  Variables faltantes:")
        for var_name, description in missing_vars:
            print(f"   • {var_name}: {description}")
        print()
        print("📝 Instrucciones:")
        print("1. Copia el archivo .env.example a .env")
        print("2. Edita el archivo .env con tus credenciales reales")
        print("3. Ejecuta este script nuevamente para verificar")
        return False
    else:
        print("🎉 ¡Configuración completa! El bot está listo para ejecutarse.")
        return True

def show_examples():
    """Muestra ejemplos de uso del bot"""
    print()
    print("📖 Ejemplos de uso:")
    print()
    print("1. Iniciar el bot:")
    print("   python bot.py")
    print()
    print("2. En Telegram, envía:")
    print("   • /start - Para ver el mensaje de bienvenida")
    print("   • /help - Para ver la ayuda")
    print("   • Cualquier texto - Se guarda como mensaje de texto")
    print("   • Una foto - Se guarda como imagen") 
    print("   • Un archivo - Se guarda como documento")
    print()
    print("3. Estructura de la base de datos de Notion:")
    print("   • Título: Título del mensaje (generado automáticamente)")
    print("   • Tipo: Select con opciones 'Texto', 'Foto', 'Archivo', 'Otro'")
    print("   • Fecha: Date (fecha de recepción)")
    print("   • Usuario: Text (nombre de usuario de Telegram)")
    print("   • URL: URL (enlace al archivo para fotos/documentos)")
    print("   • Texto adicional: Text (contenido completo y metadatos)")

def main():
    """Función principal"""
    print("🤖 Configurador del Bot Telegram + Notion")
    print("=" * 50)
    
    config_ok = check_configuration()
    
    show_examples()
    
    if config_ok:
        print()
        print("🚀 Todo listo. Ejecuta 'python bot.py' para iniciar el bot.")
    else:
        print()
        print("⚙️  Completa la configuración antes de ejecutar el bot.")
    
    return config_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)