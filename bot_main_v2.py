#!/usr/bin/env python3
"""
BOT DE TELEGRAM CON ARQUITECTURA HEXAGONAL
==========================================

Refactorizado usando:
- Domain Layer: Entidades, Value Objects, Services
- Application Layer: Use Cases, DTOs
- Infrastructure Layer: Adapters (Notion, Telegram, OpenAI, Storage)
- Presentation Layer: Handlers

Versión: 2.0 (Hexagonal Architecture)
"""

import logging
import os
import asyncio
from pathlib import Path

from telegram.ext import Application, CommandHandler, MessageHandler, filters
from notion_client import Client
from dotenv import load_dotenv

# Infrastructure
from infrastructure.notion import NotionBetRepository
from infrastructure.telegram import TelegramMessageExtractor
from infrastructure.storage import LocalFileStorage
from infrastructure.openai import OpenAIImageAnalyzer

# Application
from application.use_cases import ProcessBetImageUseCase

# Presentation
from presentation.handlers import (
    StartHandler,
    HelpHandler,
    StatusHandler,
    ImageHandler
)

# Load environment
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TelegramNotionBot:
    """
    Main bot application with Hexagonal Architecture.
    
    This class acts as the composition root, wiring up all dependencies.
    """
    
    def __init__(self):
        """Initialize bot with dependency injection."""
        logger.info("🚀 Inicializando bot...")
        
        # Load configuration
        self._load_configuration()
        
        # Initialize infrastructure
        self._initialize_infrastructure()
        
        # Initialize application layer
        self._initialize_application_layer()
        
        # Initialize presentation layer
        self._initialize_presentation_layer()
        
        # Processing queue
        self.processing_queue = asyncio.Queue()
        self.queue_task = None
        
        logger.info("✅ Bot inicializado correctamente")
    
    def _load_configuration(self):
        """Load environment configuration."""
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.notion_token = os.getenv('NOTION_TOKEN')
        self.database_id = os.getenv('NOTION_DATABASE_ID')
        
        if not self.telegram_token or self.telegram_token.startswith('your_'):
            raise ValueError("TELEGRAM_BOT_TOKEN no configurado")
        if not self.notion_token or self.notion_token.startswith('your_'):
            raise ValueError("NOTION_TOKEN no configurado")
        if not self.database_id:
            raise ValueError("NOTION_DATABASE_ID no configurado")
    
    def _initialize_infrastructure(self):
        """Initialize infrastructure adapters."""
        # Notion client
        self.notion_client = Client(auth=self.notion_token)
        
        # Images path
        self.images_path = Path("storage/images")
        self.images_path.mkdir(parents=True, exist_ok=True)
        
        # Adapters
        self.bet_repository = NotionBetRepository(
            self.notion_client,
            self.database_id
        )
        self.message_extractor = TelegramMessageExtractor()
        self.file_storage = LocalFileStorage(str(self.images_path))
        self.image_analyzer = OpenAIImageAnalyzer()
        
        logger.info(f"📁 Carpeta de imágenes: {self.images_path.absolute()}")
    
    def _initialize_application_layer(self):
        """Initialize application use cases."""
        self.process_bet_use_case = ProcessBetImageUseCase(
            image_analyzer=self.image_analyzer,
            file_storage=self.file_storage,
            bet_repository=self.bet_repository
        )
    
    def _initialize_presentation_layer(self):
        """Initialize presentation handlers."""
        # Command handlers (stateless)
        self.start_handler = StartHandler()
        self.help_handler = HelpHandler()
        self.status_handler = StatusHandler(
            notion_client=self.notion_client,
            database_id=self.database_id,
            images_path=self.images_path,
            processing_queue=self.processing_queue
        )
        
        # Image handler (with use case injection)
        self.image_handler = ImageHandler(
            process_bet_use_case=self.process_bet_use_case,
            message_extractor=self.message_extractor,
            images_path=self.images_path,
            processing_queue=self.processing_queue
        )
    
    async def queue_processor(self):
        """Process images from queue sequentially."""
        logger.info("🔄 Iniciando procesador de cola...")
        
        while True:
            try:
                task_data = await self.processing_queue.get()
                
                if task_data is None:  # Stop signal
                    break
                
                update, context = task_data
                queue_size = self.processing_queue.qsize()
                
                logger.info(f"📦 Procesando imagen desde cola (quedan {queue_size} en espera)")
                
                # Process using image handler
                await self.image_handler.process_from_queue(update, context)
                
                self.processing_queue.task_done()
                
                # Delay to avoid rate limiting
                if queue_size > 0:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"❌ Error en procesador de cola: {e}")
                self.processing_queue.task_done()
    
    async def post_init(self, application: Application):
        """Post initialization callback."""
        # Start queue processor
        self.queue_task = asyncio.create_task(self.queue_processor())
        logger.info("✅ Procesador de cola iniciado")
    
    async def post_shutdown(self, application: Application):
        """Post shutdown callback."""
        # Stop queue processor
        if self.queue_task:
            await self.processing_queue.put(None)
            await self.queue_task
        logger.info("✅ Procesador de cola detenido")
    
    def run(self):
        """Run the bot."""
        logger.info("🤖 Construyendo aplicación...")
        
        # Build application
        application = (
            Application.builder()
            .token(self.telegram_token)
            .post_init(self.post_init)
            .post_shutdown(self.post_shutdown)
            .build()
        )
        
        # Register command handlers
        application.add_handler(
            CommandHandler("start", self.start_handler.handle)
        )
        application.add_handler(
            CommandHandler("help", self.help_handler.handle)
        )
        application.add_handler(
            CommandHandler("status", self.status_handler.handle)
        )
        
        # Register message handlers
        application.add_handler(
            MessageHandler(filters.PHOTO, self.image_handler.handle)
        )
        
        # Start bot
        logger.info("🚀 Iniciando bot...")
        logger.info("✅ Bot funcionando. Presiona Ctrl+C para detener.")
        application.run_polling(allowed_updates=["message"])


def main():
    """Entry point."""
    try:
        bot = TelegramNotionBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
