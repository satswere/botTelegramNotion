import asyncio
import os
from dotenv import load_dotenv
from openai_handler import OpenAIHandler

# Cargar variables de entorno
load_dotenv()

async def test_openai_functions():
    try:
        # Inicializar el manejador de OpenAI
        openai_handler = OpenAIHandler()
        
        # Probar la función de texto
        text_response = await openai_handler.send_message_to_gpt(
            "¿Cuál es la capital de Francia?",
            "Eres un experto en geografía"
        )
        print("Respuesta a texto:", text_response)
        
        # Probar la función de análisis de imagen
        # Puedes usar una ruta local o una URL
        image_path = "storage/images/logo.png"  # Ajusta esta ruta según tu estructura
        image_response = await openai_handler.analyze_image(
            image_path,
            "Describe detalladamente qué ves en esta imagen"
        )
        print("Análisis de imagen:", image_response)
        
    except Exception as e:
        print(f"Error en las pruebas: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_openai_functions())