"""
Process Bet Image Use Case

Orchestrates the complete workflow of processing a bet image:
1. Download image from Telegram
2. Analyze image with AI
3. Upload to Notion
4. Create bet record
5. Clean up temporary files
"""

from typing import Optional, Dict, Any
import json

from domain.repositories import IImageAnalyzer, IFileStorage, IBetRepository
from application.dtos import CreateBetDTO, ImageDTO, MessageDTO, BetDTO
from .create_bet import CreateBetUseCase


class ProcessBetImageUseCase:
    """
    Use case for processing a bet image end-to-end.

    This is the main orchestration use case that coordinates
    all the steps needed to process a betting image from Telegram.
    """

    def __init__(
        self,
        image_analyzer: IImageAnalyzer,
        file_storage: IFileStorage,
        bet_repository: IBetRepository,
    ):
        """
        Initialize use case with required dependencies.

        Args:
            image_analyzer: Service for AI image analysis
            file_storage: Service for file operations
            bet_repository: Repository for bet persistence
        """
        self._image_analyzer = image_analyzer
        self._file_storage = file_storage
        self._create_bet_use_case = CreateBetUseCase(bet_repository)

    async def execute(
        self, image_dto: ImageDTO, message_dto: MessageDTO, notion_file_id: str
    ) -> BetDTO:
        """
        Process bet image through complete workflow.

        Args:
            image_dto: Image file information
            message_dto: Telegram message information
            notion_file_id: ID of file uploaded to Notion

        Returns:
            BetDTO with created bet information

        Raises:
            Exception: If any step fails
        """
        analysis_data = None

        try:
            # Step 1: Analyze image with AI
            analysis_result = await self._analyze_image(image_dto.file_path)

            # Step 2: Parse analysis result
            analysis_data = self._parse_analysis_result(analysis_result)
            # Step 3: Create bet with analysis data
            create_dto = CreateBetDTO(
                telegram_user_id=message_dto.user_id,
                telegram_username=message_dto.username,
                telegram_message_id=message_dto.message_id,
                image_filename=image_dto.filename,
                image_file_path=image_dto.file_path,
                analysis_data=analysis_data,
                message_metadata=message_dto.forward_metadata,
                notion_file_id=notion_file_id,
            )

            bet_dto = await self._create_bet_use_case.execute(create_dto)

            return bet_dto

        finally:
            # Step 4: Clean up temporary image file
            await self._cleanup_temp_file(image_dto.filename)

    async def _analyze_image(self, image_path: str) -> str:
        """
        Analyze image using AI service.

        Args:
            image_path: Path to image file

        Returns:
            Analysis result as string
        """
        prompt = self._build_analysis_prompt()
        return await self._image_analyzer.analyze_image(
            image_path=image_path, prompt=prompt
        )

    def _build_analysis_prompt(self) -> str:
        """Build the prompt for image analysis."""
        return """Eres un sistema de extracción de campos para tickets de apuesta. Tu tarea es identificar y extraer información clave a partir de la imagen de un ticket. La información debe estructurarse en campos específicos según el formato definido.

# Campos que debes identificar y extraer:

1. **ID_Ticket:** El número identificador único del ticket (ej: "123456")
2. **Deporte:** El deporte relacionado con el evento (ej: "Baloncesto", "Fútbol", "Tenis", "Béisbol"). Si no se identifica, pon "No identificado"
3. **Evento:** Nombre específico del evento o partido (ej: "Barcelona vs Real Madrid")
4. **Mercado:** El tipo de apuesta realizada (ej: "Ganador del partido", "Over/Under 2.5", "Ambos equipos marcan")
5. **Seleccion:** La elección del apostador (ej: "Barcelona", "Más de 2.5 goles", "Sí")
6. **Cuota:** La cuota asociada a la apuesta (ej: "1.75", "2.10")
7. **Monto_Apostado:** Cantidad en la moneda definida (ej: "€20", "€50"). IMPORTANTE: Extrae este valor de la imagen, no uses un valor por defecto
8. **Ganancia_Potencial:** Cantidad que se puede ganar (ej: "€35", "€105")
9. **Estado_Apuesta:** Estado actual del ticket. USA SOLO: "Ganada", "Perdida" o "Pendiente" (no uses otros estados)
10. **Numero_Apuestas:** El número total de apuestas en el ticket. Si es una sola apuesta, pon 1. Si hay múltiples apuestas combinadas, pon el número total (ej: 2, 3, 4, etc.)
11. **Fecha_Evento:** Fecha del evento deportivo si es visible (formato: "YYYY-MM-DD" o "DD/MM/YYYY")
12. **Casa_Apuestas:** Nombre de la casa de apuestas visible en la imagen (ej: "bet365", "Codere", "Betway", "Sportium")

# Formato de salida esperado:
Debes devolver SIEMPRE un objeto JSON con esta estructura exacta:

```json
{
  "ID_Ticket": "123456",
  "Deporte": "Baloncesto",
  "Evento": "Lakers vs Celtics",
  "Mercado": "Ganador del partido",
  "Seleccion": "Lakers",
  "Cuota": "1.80",
  "Monto_Apostado": "€50",
  "Ganancia_Potencial": "€90",
  "Estado_Apuesta": "Pendiente",
  "Numero_Apuestas": 1,
  "Fecha_Evento": "2024-12-20",
  "Casa_Apuestas": "bet365"
}
```

# Reglas importantes:
1. SIEMPRE devuelve un objeto JSON con TODOS los campos.
2. Si no puedes identificar un campo, usa EXACTAMENTE "No especificado" como valor.
3. Mantén los nombres de los campos EXACTAMENTE como se muestran (con mayúsculas y guiones bajos).
4. Las cuotas deben ser strings con formato decimal (ej: "1.90", "2.10").
5. Los montos deben incluir el símbolo de la moneda (ej: "€50", "€100") y deben ser extraídos de la imagen.
6. El estado de la apuesta SOLO puede ser: "Ganada", "Perdida" o "Pendiente".
7. El Mercado y la Selección son CAMPOS DIFERENTES: Mercado es el tipo de apuesta, Selección es la opción elegida.
8. Deporte: Identificar el deporte específico (ej: "Baloncesto", "Fútbol", "Tenis"). Si no se puede identificar, usar "No identificado".
9. Numero_Apuestas debe ser un número entero (1 para simple, 2+ para combinada).
10. Fecha_Evento: Extraer la fecha del evento si está visible en formato ISO o europeo. Si no está visible, usar "No especificado".
11. Casa_Apuestas: Buscar logos, nombres o marcas de agua en la imagen. Casas comunes: bet365, Codere, Betway, Sportium, William Hill.
"""

    def _parse_analysis_result(self, analysis_result: str) -> Dict[str, Any]:
        """
        Parse analysis result into structured data.

        Args:
            analysis_result: Raw analysis string

        Returns:
            Parsed dictionary
        """
        try:
            # Limpiar resultado si viene con marcadores de código
            cleaned_result = analysis_result.strip()
            if cleaned_result.startswith("```json"):
                cleaned_result = cleaned_result.replace("```json", "").replace("```", "").strip()
            elif cleaned_result.startswith("```"):
                cleaned_result = cleaned_result.replace("```", "").strip()
            
            # Try to parse as JSON
            parsed_data = json.loads(cleaned_result)
            
            # Normalizar nombres de campos a los esperados por el repositorio
            normalized = {}
            field_mapping = {
                "ID_Ticket": "ID_Ticket",
                "Deporte": "Deporte",
                "Evento": "Evento",
                "Mercado": "Mercado",
                "Seleccion": "Seleccion",
                "Cuota": "Cuota",
                "Monto_Apostado": "Monto_Apostado",
                "Ganancia_Potencial": "Ganancia_Potencial",
                "Estado_Apuesta": "Estado_Apuesta",
                "Numero_Apuestas": "Numero_Apuestas",
                "Fecha_Evento": "Fecha_Evento",
                "Casa_Apuestas": "Casa_Apuestas",
            }
            
            for key, normalized_key in field_mapping.items():
                if key in parsed_data:
                    normalized[normalized_key] = parsed_data[key]
            
            return normalized if normalized else parsed_data
            
        except json.JSONDecodeError:
            # If not valid JSON, return raw result wrapped
            return {
                "raw_analysis": analysis_result,
                "Evento": "No especificado",
                "Mercado": "No especificado",
                "Seleccion": "No especificado",
                "Cuota": "No especificado",
                "Monto_Apostado": "No especificado",
                "Ganancia_Potencial": "No especificado",
                "Estado_Apuesta": "Pendiente",
            }

    async def _cleanup_temp_file(self, filename: str) -> None:
        """
        Clean up temporary image file.

        Args:
            filename: Name of file to delete
        """
        try:
            await self._file_storage.delete(filename)
        except Exception as e:
            # Log but don't fail if cleanup fails
            print(f"Warning: Failed to cleanup temp file {filename}: {e}")
