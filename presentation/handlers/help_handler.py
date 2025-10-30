"""
Help Command Handler

Maneja el comando /help mostrando ayuda detallada.
"""

from telegram import Update
from telegram.ext import ContextTypes


class HelpHandler:
    """Handler for /help command."""

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle /help command.

        Args:
            update: Telegram update object
            context: Telegram context
        """
        if not update.message:
            return

        help_message = (
            "🆘 **Ayuda del Bot**\n\n"
            "📸 **Para usar el bot:**\n"
            "1️⃣ Envía una imagen (JPG, PNG, etc.)\n"
            "2️⃣ El bot la descargará automáticamente\n"
            "3️⃣ Subirá el archivo REAL a Notion\n"
            "4️⃣ Creará un registro en tu base de datos\n\n"
            "🔧 **Campos que se guardan:**\n"
            "• **Evento / Selección**: Título generado automáticamente\n"
            "• **Fecha**: Fecha y hora actuales\n"
            "• **Resultado**: 'Pendiente' (por defecto)\n"
            "• **Tipo de apuesta**: 'Simple' (por defecto)\n"
            "• **Captura / Comprobante**: Archivo real subido\n"
            "• **Mercado / Selección**: Texto adicional del mensaje\n\n"
            "⚠️ **Nota**: El bot solo procesa imágenes por ahora."
        )
        await update.message.reply_text(help_message, parse_mode="Markdown")
