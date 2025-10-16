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
        return """
        Analiza esta captura de apuesta deportiva y extrae la siguiente información en formato JSON:
        {
            "evento": "descripción del evento deportivo",
            "tipo_apuesta": "tipo de apuesta realizada",
            "cuota": "valor de la cuota (ej: 1.90, 2.50)",
            "monto": "monto apostado con símbolo de moneda (ej: €50, €100)",
            "ganancia_potencial": "ganancia potencial con símbolo de moneda",
            "fecha": "fecha del evento si está visible",
            "estado": "estado de la apuesta (Ganada, Perdida, Pendiente)"
        }

Reglas importantes:
1. SIEMPRE devuelve un objeto JSON con TODOS los campos.
2. Si no puedes identificar un campo, usa EXACTAMENTE "No especificado" como valor.
3. Mantén los nombres de los campos EXACTAMENTE como se muestran.
4. Las cuotas deben ser strings con formato decimal (ej: "1.90", "2.10").
5. Los montos deben incluir el símbolo de la moneda (ej: "€50", "€100").
6. El estado debe ser "Ganada", "Perdida" o "Pendiente".
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
            # Try to parse as JSON
            return json.loads(analysis_result)
        except json.JSONDecodeError:
            # If not valid JSON, return raw result wrapped
            return {
                "raw_analysis": analysis_result,
                "evento": "No especificado",
                "tipo_apuesta": "No especificado",
                "cuota": "No especificado",
                "monto": "No especificado",
                "ganancia_potencial": "No especificado",
                "estado": "Pendiente",
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
