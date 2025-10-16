"""
OpenAI Image Analyzer Adapter

Implements IImageAnalyzer interface wrapping the existing OpenAIHandler.
This adapter follows the Dependency Inversion Principle by depending on the
domain interface rather than concrete implementation details.
"""
from typing import Dict, Any
from domain.repositories.image_analyzer import IImageAnalyzer
from testingApi.openai_handler import OpenAIHandler


class OpenAIImageAnalyzer(IImageAnalyzer):
    """Adapter that wraps OpenAIHandler to implement IImageAnalyzer interface."""
    
    def __init__(self):
        """Initialize the OpenAI handler."""
        self._handler = OpenAIHandler()
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system_prompt: str = "Eres un asistente útil para analizar imágenes"
    ) -> str:
        """
        Analyze an image using GPT-4 Vision.
        
        Args:
            image_path: Path to local image file or URL
            prompt: Instructions for image analysis
            system_prompt: System message for the assistant
            
        Returns:
            Analysis result as string (may be JSON formatted)
            
        Raises:
            Exception: If analysis fails
        """
        return await self._handler.analyze_image(
            image_path=image_path,
            prompt=prompt,
            system_prompt=system_prompt
        )
    
    async def extract_bet_info(self, image_path: str) -> Dict[str, Any]:
        """
        Extract structured bet information from image.
        
        Args:
            image_path: Path to image containing bet information
            
        Returns:
            Dictionary with bet details extracted from image
            
        Raises:
            Exception: If extraction fails
        """
        system_prompt = (
            "Eres un asistente especializado en analizar capturas de apuestas deportivas. "
            "Debes extraer información estructurada de las imágenes."
        )
        
        prompt = """
        Analiza esta captura de apuesta deportiva y extrae la siguiente información en formato JSON:
        {
            "evento": "descripción del evento deportivo",
            "tipo_apuesta": "tipo de apuesta realizada",
            "cuota": "valor de la cuota",
            "monto": "monto apostado",
            "ganancia_potencial": "ganancia potencial",
            "fecha": "fecha del evento si está visible",
            "estado": "estado de la apuesta si está visible"
        }
        
        Si algún campo no es visible en la imagen, usa null como valor.
        """
        
        result = await self._handler.analyze_image(
            image_path=image_path,
            prompt=prompt,
            system_prompt=system_prompt
        )
        
        # OpenAIHandler already handles JSON cleaning and validation
        import json
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            # If result is not valid JSON, wrap it in a structured format
            return {
                "raw_analysis": result,
                "error": "Could not parse structured data from response"
            }
