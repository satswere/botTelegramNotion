import aiohttp
import json
import os
from typing import Optional
from base64 import b64encode
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class OpenAIHandler:
    def __init__(self):
        # Cargar configuración desde variables de entorno
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en el archivo .env")
            
        self.base_url = os.getenv('OPENAI_API_URL')
        if not self.base_url:
            raise ValueError("OPENAI_API_URL no está configurada en el archivo .env")
            
        self.api_version = os.getenv('API_VERSION')
        if not self.api_version:
            raise ValueError("API_VERSION no está configurada en el archivo .env")

    async def send_message_to_gpt(self, message: str, system_prompt: str = "Eres un asistente útil") -> str:
        """
        Envía un mensaje al modelo GPT y obtiene una respuesta
        
        Args:
            message (str): El mensaje del usuario
            system_prompt (str, optional): El prompt del sistema. Por defecto es "Eres un asistente útil"
            
        Returns:
            str: La respuesta del modelo
        """
        try:
            url = f"{self.base_url}?api-version={self.api_version}"
            
            payload = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ]
            }
            
            headers = {
                'api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_data = await response.json()
                    return response_data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error al enviar mensaje a OpenAI: {str(e)}")
            raise

    async def analyze_image(self, image_path: str, prompt: str = "¿Qué hay en esta imagen?", system_prompt: str = "Eres un asistente útil para analizar imágenes") -> str:
        """
        Analiza una imagen usando el modelo GPT-4 Vision
        
        Args:
            image_path (str): Ruta al archivo de imagen o URL
            prompt (str, optional): Instrucciones específicas para analizar la imagen
            system_prompt (str, optional): Mensaje del sistema para el asistente
            
        Returns:
            str: Descripción o análisis de la imagen
        """
        try:
            # Si es una ruta local, convertir a base64
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    image_data = b64encode(image_file.read()).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{image_data}"
            else:
                # Si es una URL, usarla directamente
                image_url = image_path

            url = f"{self.base_url}?api-version={self.api_version}"
            
            # Construir el payload según el formato requerido
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url
                                }
                            }
                        ]
                    }
                ]
            }
            
            headers = {
                'api-key': self.api_key,
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_data = await response.json()
                    content = response_data['choices'][0]['message']['content']
                    
                    # Limpiar marcadores de código JSON si están presentes
                    cleaned_content = content.replace('```json', '').replace('```', '').strip()
                    
                    # Validar que sea un JSON válido
                    try:
                        json.loads(cleaned_content)
                        return cleaned_content
                    except json.JSONDecodeError:
                        # Si no es JSON válido, devolver el contenido original
                        return content
        except Exception as e:
            print(f"Error al analizar la imagen con OpenAI: {str(e)}")
            raise