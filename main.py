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
ASK_NICKNAME, ASK_NAME, MAIN_MENU = range(3)
SELECT_COMPAGNO, SELECT_AVV1, SELECT_AVV2, SELECT_ESITO = range(3, 7)

# Tastiere
main_menu_keyboard = [
    ["1. Inserisci nuovo risultato"],
    ["2. Vedi storico partite"],
    ["3. Vedi Classifica Generale"],
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, one_time_keyboard=False, resize_keyboard=True)

# Database in memoria
user_db = {
    111111: {"nickname": "mario_r", "nome": "Mario", "cognome": "Rossi", "punteggio": 1000, "K": 60},
    222222: {"nickname": "luigi_v", "nome": "Luigi", "cognome": "Verdi", "punteggio": 1000, "K": 60},
    333333: {"nickname": "anna_b", "nome": "Anna", "cognome": "Bianchi", "punteggio": 1000, "K": 60},
    444444: {"nickname": "carla_m", "nome": "Carla", "cognome": "Marini", "punteggio": 1000, "K": 60},
    555555: {"nickname": "luca_n", "nome": "Luca", "cognome": "Neri", "punteggio": 1000, "K": 60},
    666666: {"nickname": "paolo_d", "nome": "Paolo", "cognome": "De Luca", "punteggio": 1000, "K": 60},
    777777: {"nickname": "sara_f", "nome": "Sara", "cognome": "Ferrari", "punteggio": 1000, "K": 60},
    888888: {"nickname": "giulia_s", "nome": "Giulia", "cognome": "Seri", "punteggio": 1000, "K": 60},
    999999: {"nickname": "marco_g", "nome": "Marco", "cognome": "Gallo", "punteggio": 1000, "K": 60},
    101010: {"nickname": "elena_p", "nome": "Elena", "cognome": "Pini", "punteggio": 1000, "K": 60}
}

storico_partite = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id in user_db:
        await update.message.reply_text(
            f"Bentornato {user_db[user_id]['nickname']}! Scegli un'opzione dal menu qui sotto:",
            reply_markup=main_menu_markup,
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Benvenuto! Inserisci un nickname (sarà visibile agli altri giocatori):",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_NICKNAME

async def ask_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nickname"] = update.message.text.strip()
    await update.message.reply_text("Perfetto! Ora inserisci il tuo Nome e Cognome:")
    return ASK_NAME

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
    user_id = update.effective_user.id
    user_db[user_id] = {
        "nickname": context.user_data["nickname"],
        "name": update.message.text.strip(),
        "username": update.effective_user.username or "",
        "punteggio": 1000,
        "K": 60
    }
    await update.message.reply_text(
        f"Grazie {context.user_data['nickname']}! Ora puoi scegliere un'opzione dal menu.",
        reply_markup=main_menu_markup,
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    if text.startswith("1"):
        return await nuova_partita(update, context)
    elif text.startswith("2"):
        await update.message.reply_text("Hai scelto: Vedi storico partite. (funzionalità da implementare)")
    elif text.startswith("3"):
        await mostra_classifica(update, context)
    else:
        await update.message.reply_text("Selezione non valida, riprova.")

    return MAIN_MENU

async def mostra_classifica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_db:
        await update.message.reply_text("⚠️ Nessun utente registrato.")
        return

    testo = "📊 *Classifica Generale*\n\n"
    testo += f"{'Giocatore':<25} {'Punteggio'}\n"
    testo += "-" * 40 + "\n"

    for user in sorted(user_db.values(), key=lambda u: u["punteggio"], reverse=True):
        testo += f"{user['nickname']:<25} {user['punteggio']}\n"

    await update.message.reply_text(f"```\n{testo}\n```", parse_mode="Markdown")



# ========== Funzioni nuova partita ==========

async def nuova_partita(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    giocatori = [v["nickname"] for k, v in user_db.items() if k != user_id]
    context.user_data["giocatore"] = user_db[user_id]

    if not giocatori or len(giocatori) < 3:
        await update.message.reply_text("Servono almeno altri 3 utenti registrati per inserire un risultato.")
        return MAIN_MENU

    markup = ReplyKeyboardMarkup([[n] for n in giocatori], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Ho giocato insieme a", reply_markup=markup)
    return SELECT_COMPAGNO

async def select_compagno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    compagno = update.message.text
    context.user_data["compagno"] = compagno
    user = context.user_data["giocatore"]
    
    # Escludiamo gli utenti con nickname uguale a user['nickname'] o compagno
    avversari_possibili = [v["nickname"] for v in user_db.values() if v["nickname"] not in [user["nickname"], compagno]]
    
    markup = ReplyKeyboardMarkup([[n] for n in avversari_possibili], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Abbiamo giocato contro", reply_markup=markup)
    return SELECT_AVV1


async def select_avversario1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    avv1 = update.message.text
    context.user_data["avv1"] = avv1
    
    # Prepara lista di nickname da escludere
    esclusi = [
        context.user_data["giocatore"]["nickname"],
        context.user_data["compagno"],
        avv1
    ]
    
    avversari_restanti = [v["nickname"] for v in user_db.values() if v["nickname"] not in esclusi]
    
    markup = ReplyKeyboardMarkup([[n] for n in avversari_restanti], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("e", reply_markup=markup)
    return SELECT_AVV2


async def select_avversario2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    avv2 = update.message.text
    context.user_data["avv2"] = avv2
    markup = ReplyKeyboardMarkup([["Vinto", "Perso"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("E abbiamo...", reply_markup=markup)
    return SELECT_ESITO

import math

async def select_esito(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    esito = update.message.text  # "Vinto" o "Perso"
    dati = context.user_data

    squadra_1 = [dati["giocatore"]["nickname"], dati["compagno"]]
    squadra_2 = [dati["avv1"], dati["avv2"]]

    # Prendi punteggi e K dei giocatori
    R = {}
    K = {}
    for nick in squadra_1 + squadra_2:
        # Cerca l'utente nel db (per nickname)
        for user in user_db.values():
            if user["nickname"] == nick:
                R[nick] = user["punteggio"]
                K[nick] = user["K"]
                break

    k = 0.45
    R_std = 600

    # Calcola R_1 e R_2
    RA = R[squadra_1[0]]
    RB = R[squadra_1[1]]
    RC = R[squadra_2[0]]
    RD = R[squadra_2[1]]

    R_1 = 0.5 * math.sqrt(RA * RB) + 0.5 * (k * max(RA, RB) + (1 - k) * min(RA, RB))
    R_2 = 0.5 * math.sqrt(RC * RD) + 0.5 * (k * max(RC, RD) + (1 - k) * min(RC, RD))

    # Calcola valori attesi
    E_1 = 1 / (1 + 10 ** ((R_2 - R_1) / R_std))
    E_2 = 1 - E_1

    # Assegna S in base all'esito
    if esito == "Vinto":
        S_1 = 1
        S_2 = 0
    else:
        S_1 = 0
        S_2 = 1

    # Aggiorna i punteggi
    RA_nuovo = RA + K[squadra_1[0]] * (S_1 - E_1)
    RB_nuovo = RB + K[squadra_1[1]] * (S_1 - E_1)
    RC_nuovo = RC + K[squadra_2[0]] * (S_2 - E_2)
    RD_nuovo = RD + K[squadra_2[1]] * (S_2 - E_2)

    # Salva i nuovi punteggi nel db
    for user in user_db.values():
        if user["nickname"] == squadra_1[0]:
            user["punteggio"] = round(RA_nuovo)
        elif user["nickname"] == squadra_1[1]:
            user["punteggio"] = round(RB_nuovo)
        elif user["nickname"] == squadra_2[0]:
            user["punteggio"] = round(RC_nuovo)
        elif user["nickname"] == squadra_2[1]:
            user["punteggio"] = round(RD_nuovo)

    # Salva risultato in storico
    risultato = {
        "squadra": squadra_1,
        "avversari": squadra_2,
        "esito": esito
    }
    storico_partite.append(risultato)

    await update.message.reply_text(
        f"✅ Risultato salvato!\n"
        f"Punteggi aggiornati:\n"
        f"{squadra_1[0]}: {round(RA_nuovo)}\n"
        f"{squadra_1[1]}: {round(RB_nuovo)}\n"
        f"{squadra_2[0]}: {round(RC_nuovo)}\n"
        f"{squadra_2[1]}: {round(RD_nuovo)}",
        reply_markup=main_menu_markup
    )
    return MAIN_MENU

# ========== Cancel ==========

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operazione annullata.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ========== Avvio Bot ==========

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_nickname)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            SELECT_COMPAGNO: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_compagno)],
            SELECT_AVV1: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_avversario1)],
            SELECT_AVV2: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_avversario2)],
            SELECT_ESITO: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_esito)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True,
    )

    app.add_handler(conv_handler)

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", "8443")),
        url_path=TOKEN,
        webhook_url=f"https://cpbb.onrender.com/{TOKEN}"
    )

if __name__ == "__main__":
    print("🤖 CesarePaveseBiliardinoBot è attivo.")
    main()
