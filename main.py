#!/usr/bin/env python3
"""
Telegram-Notion Betting Bot
============================

Main entry point for the application.

Architecture:
    - Hexagonal Architecture (Ports & Adapters)
    - Clean Architecture principles
    - Dependency Injection pattern

Layers:
    - Domain: Core business logic (Bet, Money, BetStatus)
    - Application: Use Cases and Orchestration
    - Infrastructure: External adapters (Notion, Telegram, OpenAI)
    - Presentation: Telegram handlers

Author: satswere
Version: 3.0.0
"""

import logging
import os
import sys
import asyncio
from pathlib import Path
from typing import Optional

import aiohttp
from telegram import Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from notion_client import Client
from dotenv import load_dotenv

# Infrastructure Layer
from infrastructure.notion import NotionBetRepository
from infrastructure.notion.notion_file_uploader import NotionFileUploader
from infrastructure.telegram import TelegramMessageExtractor
from infrastructure.storage import LocalFileStorage
from infrastructure.openai import OpenAIImageAnalyzer

# Application Layer
from application.use_cases import ProcessBetImageUseCase, UpdateBetStatusUseCase
from application.orchestration import MessageProcessor, CommandOrchestrator

# Presentation Layer
from presentation.handlers import StartHandler, HelpHandler, StatusHandler, ImageHandler


# ============================================================================
# CONFIGURATION
# ============================================================================


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def load_environment() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


# ============================================================================
# APPLICATION BOOTSTRAP
# ============================================================================


class BotApplication:
    """
    Main application class responsible for dependency injection and wiring.

    This class acts as the Composition Root, assembling all layers:
    - Infrastructure adapters
    - Application services (use cases and orchestrators)
    - Presentation handlers
    """

    def __init__(self):
        """Initialize application with all dependencies."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting bot...")

        # Configuration
        self.config = self._load_configuration()

        # Queue management (initialize before handlers need it)
        self.processing_queue = asyncio.Queue()
        self.queue_task: Optional[asyncio.Task] = None

        # Infrastructure
        self.infrastructure = self._setup_infrastructure()

        # Application Layer
        self.services = self._setup_application_services()

        # Presentation Layer
        self.handlers = self._setup_handlers()

        # Validate external connections
        self._validate_connections()

        self.logger.info("Bot initialized")

    def _load_configuration(self) -> dict:
        """
        Load and validate configuration from environment.

        Returns:
            Configuration dictionary

        Raises:
            ValueError: If required configuration is missing
        """
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        notion_token = os.getenv("NOTION_TOKEN")
        database_id = os.getenv("NOTION_DATABASE_ID")

        # Validation
        if not telegram_token or telegram_token.startswith("your_"):
            raise ValueError(
                "❌ TELEGRAM_BOT_TOKEN not configured. " "Please set it in .env file"
            )

        if not notion_token or notion_token.startswith("your_"):
            raise ValueError(
                "❌ NOTION_TOKEN not configured. " "Please set it in .env file"
            )

        if not database_id:
            raise ValueError(
                "❌ NOTION_DATABASE_ID not configured. " "Please set it in .env file"
            )

        return {
            "telegram_token": telegram_token,
            "notion_token": notion_token,
            "database_id": database_id,
            "tipster_database_id": os.getenv("TIPSTER_DATABASE_ID"),  # Opcional
            "images_path": Path("storage/images"),
        }

    def _validate_connections(self) -> None:
        """
        Validate connections to external services at startup.

        Checks:
            - Telegram Bot token validity
            - Notion API connection and database access
            - OpenAI API reachability

        Raises:
            ConnectionError: If any critical service is unreachable
        """
        errors = []

        # 1. Validate Telegram
        try:
            bot = Bot(token=self.config["telegram_token"])
            loop = asyncio.new_event_loop()
            bot_info = loop.run_until_complete(bot.get_me())
            loop.close()
            self.logger.info(f"Telegram: conectado como @{bot_info.username}")
        except Exception as e:
            errors.append(f"Telegram: {e}")
            self.logger.error(f"Telegram: {e}")

        # 2. Validate Notion
        try:
            notion_client = self.infrastructure["notion_client"]
            notion_client.databases.retrieve(self.config["database_id"])
            self.logger.info("Notion: conexión verificada")
        except Exception as e:
            errors.append(f"Notion: {e}")
            self.logger.error(f"Notion: {e}")

        # 3. Validate OpenAI
        try:
            api_url = os.getenv("OPENAI_API_URL")
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_url or not api_key:
                raise ValueError("OPENAI_API_URL o OPENAI_API_KEY no configuradas")

            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._check_openai(api_url, api_key))
            loop.close()
            self.logger.info("OpenAI: conexión verificada")
        except Exception as e:
            errors.append(f"OpenAI: {e}")
            self.logger.error(f"OpenAI: {e}")

        if errors:
            error_msg = "\n".join(f"  - {err}" for err in errors)
            raise ConnectionError(
                f"❌ Falló la validación de conexiones:\n{error_msg}"
            )

    @staticmethod
    async def _check_openai(api_url: str, api_key: str) -> None:
        """Send a minimal request to verify OpenAI API connectivity."""
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4.1",
            "input": "ping",
            "max_output_tokens": 1,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                if resp.status == 401:
                    raise ConnectionError("API key inválida (401 Unauthorized)")
                if resp.status == 404:
                    raise ConnectionError("URL de API no encontrada (404)")
                # 200 o 400 (bad request por payload mínimo) indica conectividad OK
                if resp.status >= 500:
                    raise ConnectionError(f"Servidor no disponible (HTTP {resp.status})")

    def _setup_infrastructure(self) -> dict:
        """
        Initialize infrastructure adapters (ports).

        Returns:
            Dictionary with infrastructure components
        """
        # Ensure images directory exists
        images_path = self.config["images_path"]
        images_path.mkdir(parents=True, exist_ok=True)

        # Notion client
        notion_client = Client(auth=self.config["notion_token"])

        # Repository (persistence port)
        # Si tienes una base de datos de Tipsters, agrega su ID aquí
        tipster_db_id = self.config.get("tipster_database_id")  # Opcional
        bet_repository = NotionBetRepository(notion_client, self.config["database_id"], tipster_db_id)

        # Message extractor (telegram port)
        message_extractor = TelegramMessageExtractor()

        # File storage (storage port)
        file_storage = LocalFileStorage(str(images_path))

        # Image analyzer (AI port)
        image_analyzer = OpenAIImageAnalyzer()

        # Notion file uploader
        notion_file_uploader = NotionFileUploader(notion_token=self.config["notion_token"])

        return {
            "notion_client": notion_client,
            "bet_repository": bet_repository,
            "message_extractor": message_extractor,
            "file_storage": file_storage,
            "image_analyzer": image_analyzer,
            "notion_file_uploader": notion_file_uploader,
        }

    def _setup_application_services(self) -> dict:
        """
        Initialize application layer (use cases and orchestrators).

        Returns:
            Dictionary with application services
        """
        # Use Cases
        process_bet_use_case = ProcessBetImageUseCase(
            image_analyzer=self.infrastructure["image_analyzer"],
            file_storage=self.infrastructure["file_storage"],
            bet_repository=self.infrastructure["bet_repository"],
        )

        update_bet_status_use_case = UpdateBetStatusUseCase(
            bet_repository=self.infrastructure["bet_repository"]
        )

        # Orchestrators
        message_processor = MessageProcessor(
            process_bet_use_case=process_bet_use_case,
            message_extractor=self.infrastructure["message_extractor"],
            notion_client=self.infrastructure["notion_client"],
            database_id=self.config["database_id"],
            images_path=self.config["images_path"],
            notion_file_uploader=self.infrastructure["notion_file_uploader"],
        )

        command_orchestrator = CommandOrchestrator(
            bet_repository=self.infrastructure["bet_repository"],
            update_bet_status_use_case=update_bet_status_use_case,
        )

        return {
            "process_bet_use_case": process_bet_use_case,
            "update_bet_status_use_case": update_bet_status_use_case,
            "message_processor": message_processor,
            "command_orchestrator": command_orchestrator,
        }

    def _setup_handlers(self) -> dict:
        """
        Initialize presentation layer (Telegram handlers).

        Returns:
            Dictionary with handlers
        """
        # Command handlers (stateless)
        start_handler = StartHandler()
        help_handler = HelpHandler()

        # Status handler (with orchestrator)
        status_handler = StatusHandler(
            command_orchestrator=self.services["command_orchestrator"],
            notion_client=self.infrastructure["notion_client"],
            database_id=self.config["database_id"],
            images_path=self.config["images_path"],
            processing_queue=self.processing_queue,
        )

        # Image handler (with message processor)
        image_handler = ImageHandler(
            message_processor=self.services["message_processor"],
            processing_queue=self.processing_queue,
        )

        return {
            "start": start_handler,
            "help": help_handler,
            "status": status_handler,
            "image": image_handler,
        }

    # ========================================================================
    # QUEUE PROCESSING
    # ========================================================================

    async def _process_queue(self) -> None:
        """
        Background task to process images from queue sequentially.

        This ensures images are processed one at a time to:
        - Avoid rate limiting from external APIs
        - Maintain order of processing
        - Control resource usage
        """
        self.logger.info("Queue processor started")

        while True:
            try:
                task_data = await self.processing_queue.get()

                # Stop signal
                if task_data is None:
                    break

                update, context = task_data
                queue_size = self.processing_queue.qsize()

                self.logger.info(
                    f"📦 Processing image ({queue_size} remaining)"
                )

                # Process using image handler
                await self.handlers["image"].process_from_queue(update, context)

                self.processing_queue.task_done()

                # Rate limiting: add delay if there are more items
                if queue_size > 0:
                    await asyncio.sleep(1.0)

            except Exception as e:
                self.logger.error(f"Error in queue processor: {e}", exc_info=True)
                self.processing_queue.task_done()

        self.logger.info("Queue processor stopped")

    async def _on_startup(self, application: Application) -> None:
        """Callback executed when bot starts."""
        self.queue_task = asyncio.create_task(self._process_queue())

    async def _on_shutdown(self, application: Application) -> None:
        """Callback executed when bot stops."""
        if self.queue_task:
            await self.processing_queue.put(None)
            await self.queue_task

    # ========================================================================
    # APPLICATION RUNNER
    # ========================================================================

    def run(self) -> None:
        """
        Build and run the Telegram bot application.

        This method:
        1. Creates the Telegram Application
        2. Registers all handlers
        3. Sets up lifecycle callbacks
        4. Starts polling for updates
        """
        # Build application with lifecycle callbacks
        application = (
            Application.builder()
            .token(self.config["telegram_token"])
            .post_init(self._on_startup)
            .post_shutdown(self._on_shutdown)
            .build()
        )

        # Register command handlers
        application.add_handler(CommandHandler("start", self.handlers["start"].handle))
        application.add_handler(CommandHandler("help", self.handlers["help"].handle))
        application.add_handler(
            CommandHandler("status", self.handlers["status"].handle)
        )

        # Register message handlers
        application.add_handler(
            MessageHandler(filters.PHOTO, self.handlers["image"].handle)
        )

        # Start bot
        self.logger.info("Bot is running. Press Ctrl+C to stop.")

        application.run_polling(allowed_updates=["message"])


# ============================================================================
# ENTRY POINT
# ============================================================================


def main() -> int:
    """
    Application entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    # Setup
    setup_logging()
    load_environment()

    logger = logging.getLogger(__name__)

    try:
        # Run application
        app = BotApplication()
        app.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
