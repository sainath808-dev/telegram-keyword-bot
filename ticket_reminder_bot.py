import os
import logging
from datetime import datetime

from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# ============= LOGGING SETUP =============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ============= KEYWORDS =============
KEYWORDS = [
    "bancolombia",
    "latam",
    "netflix",
    "bancodebogota",
    "vencen",
    "nacionales",
    "multas",
    "prejuridico",
    "suscripcion",
    "suspension",
    "suspendida",
    "nvoadades",
    "mastercard",
    "poliza",
    "llave",
    "bre b",
    "nequi",
    "simit",
    "facturas",
    "factura",
    "comparendos",
    "seguro",
    "%",
    "claro",
    "movistar",
    "impuestos",
    "valor",
    "caducarán",
    "medianoche",
    "word – hasta",
    "hasta",
    "paga",
    "hoy",
    "paga hoy",
    "apuestale a tu",
    "betplay",
    "b a n c olo m bia",
    "postpago",
    "pago",
]

# Normalize keywords (lowercase for matching)
KEYWORDS_LOWER = [k.lower() for k in KEYWORDS]

# ============= SIMPLE IN-MEMORY LOG =============
# If you want to keep a small tail of matches in memory
last_matches = []  # list of dicts: {time, user, chat, text, matched_keywords}


def start(update: Update, context: CallbackContext):
    """Start command."""
    update.message.reply_text(
        "👋 Hola! Soy el Keyword Checker Bot.\n"
        "En este chat revisaré mensajes que contengan palabras clave.\n"
        "Usa /keywords para ver las palabras configuradas\n"
        "Usa /lastmatches para ver las últimas coincidencias detectadas."
    )


def keywords_command(update: Update, context: CallbackContext):
    """Show configured keywords."""
    text = "📌 Palabras clave actuales:\n\n" + "\n".join(f"- {k}" for k in KEYWORDS)
    update.message.reply_text(text)


def last_matches_command(update: Update, context: CallbackContext):
    """Show last detected matches."""
    if not last_matches:
        update.message.reply_text("Aún no se han detectado coincidencias.")
        return

    lines = []
    for item in last_matches[-10:]:  # show last 10
        time_str = item["time"]
        user = item["user"]
        chat = item["chat"]
        kws = ", ".join(item["matched_keywords"])
        lines.append(
            f"[{time_str}] Chat: {chat}, User: {user}\n"
            f"  Keywords: {kws}\n"
            f"  Text: {item['text']}\n"
        )

    update.message.reply_text("🕒 Últimas coincidencias:\n\n" + "\n".join(lines))


def check_keywords_in_text(text: str):
    """Return list of matched keywords in given text."""
    if not text:
        return []

    lower = text.lower()
    matched = []
    for kw in KEYWORDS_LOWER:
        if kw in lower:
            matched.append(kw)
    return list(set(matched))  # unique


def message_handler(update: Update, context: CallbackContext):
    """Handle all text messages and check for keywords."""
    message = update.message
    if not message or not message.text:
        return

    text = message.text
    matched = check_keywords_in_text(text)

    if not matched:
        return

    user = message.from_user
    chat = message.chat

    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to in-memory log
    last_matches.append({
        "time": time_str,
        "user": f"{user.id} ({user.first_name})",
        "chat": f"{chat.id} ({chat.title or chat.first_name})",
        "text": text,
        "matched_keywords": matched,
    })

    # Log in server logs
    logger.info(
        f"Keyword match at {time_str} | chat={chat.id} user={user.id} | "
        f"kws={matched} | text={text}"
    )

    # Optional: reply in chat (you can customize this)
    reply_text = (
        f"🔎 Detecté palabras clave: {', '.join(matched)}\n"
        f"Mensaje: {text}"
    )
    try:
        message.reply_text(reply_text)
    except Exception as e:
        logger.error(f"Error replying to message: {e}")


def main():
    """Main entry point."""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("BOT_TOKEN environment variable not set")

    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("keywords", keywords_command))
    dp.add_handler(CommandHandler("lastmatches", last_matches_command))

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))

    logger.info("Keyword checker bot starting with long polling...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
