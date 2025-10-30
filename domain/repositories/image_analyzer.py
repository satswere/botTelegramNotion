"""
IImageAnalyzer - Interfaz de Analizador de Imágenes

Define el contrato para análisis de imágenes con IA sin conocer el proveedor.
Permite cambiar de OpenAI a Claude, Google Vision, etc. sin afectar la lógica.
"""

from typing import Protocol, Dict, Any, Optional


class IImageAnalyzer(Protocol):
    """
    Puerto (Interface) para análisis de imágenes con IA.

    Esta interfaz define las operaciones de análisis de imágenes
    sin depender de un proveedor específico de IA.

    Implementaciones:
        - OpenAIImageAnalyzer (actual - GPT-4 Vision)
        - ClaudeImageAnalyzer (futuro - Claude 3)
        - GoogleVisionAnalyzer (futuro - Gemini)
        - MockImageAnalyzer (tests)

    Ejemplo de uso:
        >>> analyzer = OpenAIImageAnalyzer(openai_handler)
        >>> result = await analyzer.analyze(image_path, prompt)
        >>> print(result["event"])
    """

    async def analyze(
        self, image_path: str, prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza una imagen y extrae información estructurada.

        Args:
            image_path: Ruta al archivo de imagen o URL
            prompt: Prompt específico para el análisis (opcional)
                   Si no se proporciona, usa el prompt por defecto

        Returns:
            Dict con los datos extraídos de la imagen:
                - event: str - Evento identificado
                - market: str - Mercado de apuesta
                - selection: str - Selección realizada
                - odds: str - Cuota
                - amount: str - Monto apostado
                - potential_win: str - Ganancia potencial
                - status: str - Estado de la apuesta
                - confidence: float - Nivel de confianza (0-1)
                - raw_text: str - Texto crudo extraído

        Raises:
            AnalysisError: Si falla el análisis
            InvalidImageError: Si la imagen no es válida
            ProviderError: Si hay error con el proveedor de IA

        Example:
            >>> result = await analyzer.analyze(
            ...     "storage/images/bet_image.jpg",
            ...     prompt="Extrae información de esta apuesta"
            ... )
            >>> print(f"Evento: {result['event']}")
            >>> print(f"Cuota: {result['odds']}")
        """
        ...

    async def analyze_batch(
        self, image_paths: list[str], prompt: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Analiza múltiples imágenes en lote.

        Args:
            image_paths: Lista de rutas a imágenes
            prompt: Prompt común para todas las imágenes

        Returns:
            Lista de diccionarios con resultados de análisis

        Example:
            >>> images = ["img1.jpg", "img2.jpg", "img3.jpg"]
            >>> results = await analyzer.analyze_batch(images)
            >>> for result in results:
            ...     print(result["event"])
        """
        ...

    async def validate_image(self, image_path: str) -> bool:
        """
        Valida que una imagen sea procesable.

        Args:
            image_path: Ruta a la imagen

        Returns:
            bool: True si la imagen es válida, False en caso contrario

        Example:
            >>> is_valid = await analyzer.validate_image("bet.jpg")
            >>> if not is_valid:
            ...     print("Imagen no válida")
        """
        ...
