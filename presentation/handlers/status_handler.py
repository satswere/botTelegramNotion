"""
Status Command Handler - Refactorizado

Maneja el comando /status usando el CommandOrchestrator.
Delega la lógica de negocio al orquestador.
"""
import logging
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from notion_client import Client

from application.orchestration import CommandOrchestrator

logger = logging.getLogger(__name__)


class StatusHandler:
    """Handler para el comando /status (refactorizado)."""
    
    def __init__(
        self,
        command_orchestrator: CommandOrchestrator,
        notion_client: Client,
        database_id: str,
        images_path: Path,
        processing_queue
    ):
        """
        Inicializa el handler de status.
        
        Args:
            command_orchestrator: Orquestador de comandos
            notion_client: Cliente de Notion API
            database_id: ID de la base de datos de Notion
            images_path: Ruta al directorio de imágenes
            processing_queue: Cola de procesamiento de imágenes
        """
        self._orchestrator = command_orchestrator
        self._notion_client = notion_client
        self._database_id = database_id
        self._images_path = images_path
        self._processing_queue = processing_queue
        
        logger.info("📊 StatusHandler inicializado (refactorizado con CommandOrchestrator)")
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja el comando /status.
        
        Args:
            update: Update de Telegram
            context: Contexto de Telegram
        """
        if not update.message:
            return
        
        logger.info(f"📊 Comando /status recibido de usuario {update.message.from_user.id}")
        
        try:
            # Ejecutar comando a través del orquestador
            result = await self._orchestrator.execute_status_command(limit=10)
            
            # Obtener información del sistema
            notion_status = await self._check_notion_connection()
            queue_status = self._get_queue_status()
            image_count = self._count_images()
            
            # Formatear respuesta combinando estadísticas de apuestas y sistema
            if result["success"]:
                stats_text = self._orchestrator.format_status_response(result)
                
                system_text = (
                    f"\n\n🔧 **Estado del Sistema**\n\n"
                    f"🤖 **Bot**: ✅ Activo\n"
                    f"📝 **Notion**: {notion_status}\n"
                    f"📁 **Imágenes guardadas**: {image_count}\n"
                    f"⏳ **Cola de procesamiento**: {queue_status}"
                )
                
                full_response = stats_text + system_text
            else:
                full_response = (
                    f"📊 **Estado del Sistema**\n\n"
                    f"🤖 **Bot**: ✅ Activo\n"
                    f"📝 **Notion**: {notion_status}\n"
                    f"� **Imágenes guardadas**: {image_count}\n"
                    f"⏳ **Cola de procesamiento**: {queue_status}\n\n"
                    f"⚠️ No se pudieron obtener estadísticas de apuestas"
                )
            
            await update.message.reply_text(full_response, parse_mode='Markdown')
            logger.info("✅ Comando /status completado")
            
        except Exception as e:
            logger.error(f"❌ Error en comando /status: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Error obteniendo estado: {str(e)[:100]}",
                parse_mode='Markdown'
            )
    
    async def _check_notion_connection(self) -> str:
        """Verifica la conexión con Notion."""
        try:
            database = self._notion_client.databases.retrieve(self._database_id)
            return "✅ Conectado"
        except Exception as e:
            return f"❌ Error: {str(e)[:30]}..."
    
    def _get_queue_status(self) -> str:
        """Obtiene el estado de la cola."""
        queue_size = self._processing_queue.qsize()
        if queue_size == 0:
            return "✅ Vacía"
        else:
            return f"⏳ {queue_size} imagen(es) en espera"
    
    def _count_images(self) -> int:
        """Cuenta las imágenes guardadas."""
        try:
            return len(list(self._images_path.glob('*')))
        except Exception:
            return 0
