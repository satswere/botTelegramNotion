"""
Start Command Handler

Maneja el comando /start mostrando mensaje de bienvenida.
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)


class StartHandler:
    """Handler for /start command."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /start command.
        
        Args:
            update: Telegram update object
            context: Telegram context
        """
        if not update.message:
            return
        
        welcome_message = (
            "🤖 **Bot de Telegram con Notion** 🤖\n\n"
            "✨ **Funcionalidades:**\n"
            "📸 Recibe y procesa imágenes\n"
            "📝 Crea registros automáticos en Notion\n"
            "🔗 Sube archivos REALES (no solo referencias)\n"
            "🔍 Extrae información de mensajes reenviados\n\n"
            "📋 **Comandos:**\n"
            "• `/start` - Este mensaje\n"
            "• `/help` - Ayuda detallada\n"
            "• `/status` - Estado del sistema\n\n"
            "🚀 **¡Envía una imagen para comenzar!**"
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
        user_name = "Usuario"
        if update.effective_user and update.effective_user.first_name:
            user_name = update.effective_user.first_name
        logger.info(f"👋 Usuario {user_name} inició el bot")
