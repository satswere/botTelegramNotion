"""
Status Command Handler

Maneja el comando /status mostrando el estado del sistema.
"""
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from notion_client import Client


class StatusHandler:
    """Handler for /status command."""
    
    def __init__(
        self,
        notion_client: Client,
        database_id: str,
        images_path: Path,
        processing_queue
    ):
        """
        Initialize status handler.
        
        Args:
            notion_client: Notion API client
            database_id: Notion database ID
            images_path: Path to images directory
            processing_queue: Processing queue for images
        """
        self._notion_client = notion_client
        self._database_id = database_id
        self._images_path = images_path
        self._processing_queue = processing_queue
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /status command.
        
        Args:
            update: Telegram update object
            context: Telegram context
        """
        if not update.message:
            return
        
        try:
            # Check Notion connection
            if self._notion_client:
                database = self._notion_client.databases.retrieve(self._database_id)
                if isinstance(database, dict):
                    database_name = database.get('title', [{}])[0].get('plain_text', 'Base de datos') if database.get('title') else 'Base de datos'
                else:
                    database_name = "Base de datos"
                notion_status = "✅ Conectado"
            else:
                database_name = "Error"
                notion_status = "❌ Cliente no inicializado"
        except Exception as e:
            database_name = "Error"
            notion_status = f"❌ Error: {str(e)[:50]}..."
        
        # Queue status
        queue_size = self._processing_queue.qsize()
        queue_status = f"{queue_size} imagen(es) en espera" if queue_size > 0 else "✅ Vacía"
        
        # Count images
        image_count = len(list(self._images_path.glob('*')))
        
        status_message = (
            f"📊 **Estado del Sistema**\n\n"
            f"🤖 **Bot**: ✅ Activo\n"
            f"📝 **Notion**: {notion_status}\n"
            f"🗃️ **Base de datos**: {database_name}\n"
            f"📁 **Carpeta**: {self._images_path.name}/\n"
            f"📸 **Imágenes guardadas**: {image_count}\n"
            f"⏳ **Cola de procesamiento**: {queue_status}\n\n"
            f"🔧 **ID Base de datos**: `{self._database_id}`"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
