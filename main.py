import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler,
    MessageHandler, filters
)
import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TOKEN"]

# Stati della conversazione
ASK_NEW_USER, ASK_NAME, MAIN_MENU = range(3)

# Tastiere
main_menu_keyboard = [
    ["1. Inserisci nuovo risultato"],
    ["2. Vedi storico partite"],
    ["3. Vedi Classifica Generale"],
    # spazio per nuove opzioni
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, one_time_keyboard=False, resize_keyboard=True)

# Memorizzazione utenti semplice (in memoria)
user_db = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id in user_db:
        await update.message.reply_text(
            "Bentornato! Scegli un'opzione dal menu qui sotto:",
            reply_markup=main_menu_markup,
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Sei un nuovo utente? (si/no)",
            reply_markup=ReplyKeyboardMarkup([["si", "no"]], one_time_keyboard=True, resize_keyboard=True),
        )
        return ASK_NEW_USER

async def ask_new_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.lower()
    if text == "si":
        await update.message.reply_text("Inserisci il tuo Nome e Cognome:", reply_markup=ReplyKeyboardRemove())
        return ASK_NAME
    elif text == "no":
        await update.message.reply_text("Ok, bentornato! Scegli un'opzione:", reply_markup=main_menu_markup)
        user_db[update.effective_user.id] = "utente_sconosciuto"
        return MAIN_MENU
    else:
        await update.message.reply_text("Per favore rispondi con 'si' o 'no'.")
        return ASK_NEW_USER

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_db[update.effective_user.id] = update.message.text
    await update.message.reply_text(
        f"Grazie {update.message.text}! Ora puoi scegliere un'opzione dal menu.",
        reply_markup=main_menu_markup,
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text.startswith("1"):
        await update.message.reply_text("Hai scelto: Inserisci nuovo risultato. (funzionalità da implementare)")
    elif text.startswith("2"):
        await update.message.reply_text("Hai scelto: Vedi storico partite. (funzionalità da implementare)")
    elif text.startswith("3"):
        await update.message.reply_text("Hai scelto: Vedi Classifica Generale. (funzionalità da implementare)")
    else:
        await update.message.reply_text("Selezione non valida, riprova.")

    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operazione annullata.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NEW_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_new_user)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)

    # Configuro webhook con il tuo URL
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TOKEN,
        webhook_url=f"https://cpbb.onrender.com/{TOKEN}"
    )

if __name__ == "__main__":
    print("🤖 CesarePaveseBiliardinoBot è attivo.")
    main()


