"""
OpenAI Handler

Cliente para la API de OpenAI/Azure AI Services.
Detecta automáticamente el formato de API (Responses vs Chat Completions)
basándose en la URL configurada.
"""

import aiohttp
import json
import os
from typing import Optional
from base64 import b64encode
from dotenv import load_dotenv
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

from infrastructure.openai.api_strategy import detect_api_strategy, APIStrategy

# Cargar variables de entorno desde el archivo .env
load_dotenv()

logger = logging.getLogger(__name__)


class OpenAIHandler:
    def __init__(self):
        # Cargar configuración desde variables de entorno
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no está configurada en el archivo .env")

        self.base_url = os.getenv("OPENAI_API_URL")
        if not self.base_url:
            raise ValueError("OPENAI_API_URL no está configurada en el archivo .env")

        self.api_version = os.getenv("API_VERSION")
        if not self.api_version:
            raise ValueError("API_VERSION no está configurada en el archivo .env")

        # Detectar estrategia de API automáticamente
        self.strategy: APIStrategy = detect_api_strategy(self.base_url)
        logger.info(f"OpenAI Handler inicializado - Modelo: {self.api_version}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, aiohttp.ClientResponseError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def send_message_to_gpt(
        self, message: str, system_prompt: str = "Eres un asistente útil"
    ) -> str:
        """
        Envía un mensaje al modelo GPT y obtiene una respuesta.

        Args:
            message: El mensaje del usuario
            system_prompt: El prompt del sistema

        Returns:
            La respuesta del modelo
        """
        try:
            url = self.strategy.build_url(self.base_url, self.api_version)
            payload = self.strategy.build_text_payload(
                self.api_version, message, system_prompt
            )
            headers = self.strategy.get_headers(self.api_key)

            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error_msg = response_data.get("error", {}).get("message", str(response_data))
                        raise RuntimeError(f"API error ({response.status}): {error_msg}")

                    return self.strategy.extract_content(response_data)
        except Exception as e:
            logger.error(f"Error al enviar mensaje a OpenAI: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, aiohttp.ClientResponseError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "¿Qué hay en esta imagen?",
        system_prompt: str = "Eres un asistente útil para analizar imágenes",
    ) -> str:
        """
        Analiza una imagen usando el modelo GPT-4 Vision.

        Args:
            image_path: Ruta al archivo de imagen o URL
            prompt: Instrucciones específicas para analizar la imagen
            system_prompt: Mensaje del sistema para el asistente

        Returns:
            Descripción o análisis de la imagen
        """
        try:
            # Si es una ruta local, convertir a base64
            if os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    image_data = b64encode(image_file.read()).decode("utf-8")
                image_url = f"data:image/jpeg;base64,{image_data}"
            else:
                # Si es una URL, usarla directamente
                image_url = image_path

            url = self.strategy.build_url(self.base_url, self.api_version)
            payload = self.strategy.build_image_payload(
                self.api_version, image_url, prompt, system_prompt
            )
            headers = self.strategy.get_headers(self.api_key)

            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error_msg = response_data.get("error", {}).get("message", str(response_data))
                        raise RuntimeError(f"API error ({response.status}): {error_msg}")

                    content = self.strategy.extract_content(response_data)

                    # Limpiar marcadores de código JSON si están presentes
                    cleaned_content = (
                        content.replace("```json", "").replace("```", "").strip()
                    )

                    # Validar que sea un JSON válido
                    try:
                        json.loads(cleaned_content)
                        return cleaned_content
                    except json.JSONDecodeError:
                        # Si no es JSON válido, devolver el contenido original
                        return content
        except Exception as e:
            logger.error(f"Error al analizar la imagen con OpenAI: {str(e)}")
            raise
