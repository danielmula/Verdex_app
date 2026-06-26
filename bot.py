"""
Bot de Telegram. Configura el menu button que abre la Mini App y responde
a /start. Se ejecuta como proceso aparte (worker) en Render.

Variables de entorno necesarias:
  TELEGRAM_BOT_TOKEN  -> token de BotFather
  WEBAPP_URL          -> la URL que te da Render (https://tu-app.onrender.com)
"""

import os
import asyncio
from telegram import (
    Update, MenuButtonWebApp, WebAppInfo,
    InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
WEBAPP_URL = os.environ["WEBAPP_URL"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "⚽ Abrir App", web_app=WebAppInfo(url=WEBAPP_URL)
        )
    ]])
    await update.message.reply_text(
        "¡Bienvenido! Pulsa el botón para ver los partidos del día, "
        "estadísticas y análisis.",
        reply_markup=kb,
    )


async def post_init(application: Application):
    # Configura el menu button (el de abajo a la izquierda) para TODOS
    await application.bot.set_chat_menu_button(
        menu_button=MenuButtonWebApp(
            text="Abrir App",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    )


def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()


if __name__ == "__main__":
    main()
