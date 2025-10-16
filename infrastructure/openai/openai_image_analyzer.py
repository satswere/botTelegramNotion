"""
OpenAI Image Analyzer Adapter

Implements IImageAnalyzer interface wrapping the existing OpenAIHandler.
This adapter follows the Dependency Inversion Principle by depending on the
domain interface rather than concrete implementation details.

Error Handling Strategy:
- OpenAIAnalyzerError: Custom exception for this adapter
- Handles aiohttp.ClientError for network issues
- Handles KeyError for malformed API responses
- Handles FileNotFoundError for missing image files
- Comprehensive logging at debug, info, warning, and error levels
"""
from typing import Dict, Any
import logging
import json
import aiohttp
from domain.repositories.image_analyzer import IImageAnalyzer
from testingApi.openai_handler import OpenAIHandler

logger = logging.getLogger(__name__)


class OpenAIAnalyzerError(Exception):
    """Error específico del analizador de imágenes OpenAI."""
    pass


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
            OpenAIAnalyzerError: If analysis fails due to API, network, or file issues
        """
        logger.debug(f"🔍 Analizando imagen: {image_path[:50]}...")
        
        try:
            result = await self._handler.analyze_image(
                image_path=image_path,
                prompt=prompt,
                system_prompt=system_prompt
            )
            logger.info(f"✅ Imagen analizada exitosamente (longitud: {len(result)} chars)")
            return result
            
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo de imagen no encontrado: {image_path}")
            raise OpenAIAnalyzerError(f"Imagen no encontrada: {image_path}") from e
            
        except aiohttp.ClientError as e:
            logger.error(f"❌ Error de red al conectar con OpenAI API: {e}")
            raise OpenAIAnalyzerError(f"Error de conexión con OpenAI: {str(e)}") from e
            
        except KeyError as e:
            logger.error(f"❌ Respuesta malformada de OpenAI API - clave faltante: {e}")
            raise OpenAIAnalyzerError(f"Respuesta inválida de OpenAI API") from e
            
        except Exception as e:
            logger.error(f"❌ Error inesperado analizando imagen: {e}", exc_info=True)
            raise OpenAIAnalyzerError(f"Error analizando imagen: {str(e)}") from e
    
    async def extract_bet_info(self, image_path: str) -> Dict[str, Any]:
        """
        Extract structured bet information from image.
        
        Args:
            image_path: Path to image containing bet information
            
        Returns:
            Dictionary with bet details extracted from image
            
        Raises:
            OpenAIAnalyzerError: If extraction or JSON parsing fails
        """
        logger.debug(f"📊 Extrayendo información de apuesta desde imagen: {image_path[:50]}...")
        
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
        
        try:
            result = await self._handler.analyze_image(
                image_path=image_path,
                prompt=prompt,
                system_prompt=system_prompt
            )
            
            logger.debug(f"🔄 Parseando respuesta JSON de OpenAI...")
            
            # OpenAIHandler already handles JSON cleaning and validation
            try:
                parsed_data = json.loads(result)
                logger.info(f"✅ Información de apuesta extraída exitosamente: {list(parsed_data.keys())}")
                return parsed_data
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Respuesta no es JSON válido - envolviendo en formato estructurado")
                # If result is not valid JSON, wrap it in a structured format
                return {
                    "raw_analysis": result,
                    "error": "Could not parse structured data from response"
                }
                
        except FileNotFoundError as e:
            logger.error(f"❌ Archivo de imagen no encontrado: {image_path}")
            raise OpenAIAnalyzerError(f"Imagen no encontrada: {image_path}") from e
            
        except aiohttp.ClientError as e:
            logger.error(f"❌ Error de red extrayendo información de apuesta: {e}")
            raise OpenAIAnalyzerError(f"Error de conexión con OpenAI: {str(e)}") from e
            
        except Exception as e:
            logger.error(f"❌ Error inesperado extrayendo información de apuesta: {e}", exc_info=True)
            raise OpenAIAnalyzerError(f"Error extrayendo información: {str(e)}") from e
