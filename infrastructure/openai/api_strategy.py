"""
API Strategy Module

Detecta automáticamente el tipo de API (Responses vs Chat Completions)
basándose en la URL configurada y proporciona la estrategia correcta
para construir payloads y parsear respuestas.

Soporta:
    - Responses API: /v1/responses (Azure AI Services nuevo)
    - Chat Completions API: /chat/completions (Azure OpenAI clásico, OpenAI directo)
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class APIStrategy(ABC):
    """Interfaz base para estrategias de API."""

    @abstractmethod
    def build_url(self, base_url: str, api_version: str) -> str:
        """Construye la URL final del request."""
        ...

    @abstractmethod
    def build_text_payload(
        self, model: str, message: str, system_prompt: str
    ) -> Dict[str, Any]:
        """Construye el payload para mensajes de texto."""
        ...

    @abstractmethod
    def build_image_payload(
        self, model: str, image_url: str, prompt: str, system_prompt: str
    ) -> Dict[str, Any]:
        """Construye el payload para análisis de imagen."""
        ...

    @abstractmethod
    def extract_content(self, response_data: Dict[str, Any]) -> str:
        """Extrae el contenido de texto de la respuesta."""
        ...

    @abstractmethod
    def get_headers(self, api_key: str) -> Dict[str, str]:
        """Retorna los headers necesarios para la petición."""
        ...


class ResponsesAPIStrategy(APIStrategy):
    """
    Estrategia para Azure AI Services - Responses API.

    Endpoints: /v1/responses, /openai/v1/responses
    Formato: input/output
    Docs: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/responses
    """

    def build_url(self, base_url: str, api_version: str) -> str:
        return base_url

    def build_text_payload(
        self, model: str, message: str, system_prompt: str
    ) -> Dict[str, Any]:
        return {
            "model": model,
            "input": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        }

    def build_image_payload(
        self, model: str, image_url: str, prompt: str, system_prompt: str
    ) -> Dict[str, Any]:
        return {
            "model": model,
            "input": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url},
                    ],
                },
            ],
        }

    def extract_content(self, response_data: Dict[str, Any]) -> str:
        return response_data["output"][0]["content"][0]["text"]

    def get_headers(self, api_key: str) -> Dict[str, str]:
        return {"api-key": api_key, "Content-Type": "application/json"}


class ChatCompletionsStrategy(APIStrategy):
    """
    Estrategia para Azure OpenAI / OpenAI - Chat Completions API.

    Endpoints: /chat/completions, /openai/deployments/{model}/chat/completions
    Formato: messages/choices
    Docs: https://learn.microsoft.com/en-us/azure/ai-services/openai/reference
    """

    def build_url(self, base_url: str, api_version: str) -> str:
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}api-version={api_version}"

    def build_text_payload(
        self, model: str, message: str, system_prompt: str
    ) -> Dict[str, Any]:
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        }

    def build_image_payload(
        self, model: str, image_url: str, prompt: str, system_prompt: str
    ) -> Dict[str, Any]:
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        }

    def extract_content(self, response_data: Dict[str, Any]) -> str:
        return response_data["choices"][0]["message"]["content"]

    def get_headers(self, api_key: str) -> Dict[str, str]:
        # Soporta tanto api-key (Azure) como Bearer token (OpenAI directo)
        if api_key.startswith("sk-"):
            return {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        return {"api-key": api_key, "Content-Type": "application/json"}


def detect_api_strategy(base_url: str) -> APIStrategy:
    """
    Detecta automáticamente qué estrategia usar basándose en la URL.

    Rules:
        - URL contiene '/v1/responses' -> Responses API
        - URL contiene '/chat/completions' -> Chat Completions
        - URL termina en 'services.ai.azure.com' sin path específico -> Responses API
        - Default -> Chat Completions (compatibilidad)

    Args:
        base_url: La URL configurada en OPENAI_API_URL

    Returns:
        La estrategia apropiada para esa URL
    """
    url_lower = base_url.lower()

    if "/v1/responses" in url_lower or "/responses" in url_lower:
        logger.info("API detectada: Responses API (formato input/output)")
        return ResponsesAPIStrategy()

    if "/chat/completions" in url_lower:
        logger.info("API detectada: Chat Completions (formato messages/choices)")
        return ChatCompletionsStrategy()

    # Heurística: services.ai.azure.com usa Responses API por defecto
    if "services.ai.azure.com" in url_lower:
        logger.info("API detectada: Azure AI Services → Responses API")
        return ResponsesAPIStrategy()

    # Default: Chat Completions (mayor compatibilidad)
    logger.info("API detectada: Default → Chat Completions")
    return ChatCompletionsStrategy()
