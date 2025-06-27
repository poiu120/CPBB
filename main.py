import sys
print(f"Python version: {sys.version}")

import os
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

# ===== CONFIGURAZIONE TOKEN =====
TOKEN = os.environ["TOKEN"]

# ===== FILE E COSTANTI =====
UTENTI_FILE = "utenti.json"
INSERISCI_NOME, INSERISCI_COGNOME, MENU = range(3)

# ===== DATABASE =====
def carica_utenti():
    if os.path.exists(UTENTI_FILE):
        with open(UTENTI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def salva_utenti():
    with open(UTENTI_FILE, "w", encoding="utf-8") as f:
        json.dump(utenti, f, indent=2, ensure_ascii=False)

utenti = carica_utenti()
stato_utente = {}  # Temporaneo per nome parziale

# ===== HANDLER PRINCIPALE =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in utenti:
        await mostra_menu(update)
        return MENU
    else:
        await update.message.reply_text("Benvenuto! Sei un nuovo utente? Scrivi il tuo *nome*.", parse_mode="Markdown")
        return INSERISCI_NOME

# ===== REGISTRAZIONE UTENTE =====
async def ricevi_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    nome = update.message.text.strip()
    stato_utente[user_id] = {"nome": nome}
    await update.message.reply_text("Perfetto! Ora scrivi il tuo *cognome*.", parse_mode="Markdown")
    return INSERISCI_COGNOME

async def ricevi_cognome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    cognome = update.message.text.strip()
    nome = stato_utente[user_id]["nome"]
    utenti[user_id] = {"nome": nome, "cognome": cognome}
    salva_utenti()
    await update.message.reply_text(f"Registrazione completata ✅: {nome} {cognome}")
    await mostra_menu(update)
    return MENU

# ===== MENU PRINCIPALE =====
async def mostra_menu(update: Update):
    keyboard = [
        [KeyboardButton("➕ Inserisci nuovo risultato")],
        [KeyboardButton("📜 Vedi storico partite")],
        [KeyboardButton("🏆 Vedi classifica generale")],
        [KeyboardButton("🚧 Altre opzioni (in arrivo)")]
    ]
    markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Cosa vuoi fare?", reply_markup=markup)

async def gestione_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scelta = update.message.text
    if scelta.startswith("➕"):
        await update.message.reply_text("👉 Funzione 'Inserisci risultato' in arrivo!")
    elif scelta.startswith("📜"):
        await update.message.reply_text("👉 Funzione 'Storico partite' in arrivo!")
    elif scelta.startswith("🏆"):
        await update.message.reply_text("👉 Funzione 'Classifica generale' in arrivo!")
    elif scelta.startswith("🚧"):
        await update.message.reply_text("Nuove funzionalità in arrivo!")
    else:
        await update.message.reply_text("❗ Comando non riconosciuto. Usa i pulsanti del menu.")

# ===== CANCELLO =====
async def annulla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operazione annullata.")
    return ConversationHandler.END

# ===== CONVERSATION HANDLER =====
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        INSERISCI_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_nome)],
        INSERISCI_COGNOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ricevi_cognome)],
        MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, gestione_menu)],
    },
    fallbacks=[CommandHandler("cancel", annulla)],
)

# ===== AVVIO BOT =====
if __name__ == "__main__":
    print("🤖 CesarePaveseBiliardinoBot è attivo.")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(conv_handler)
    app.run_polling()

