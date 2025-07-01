import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, ConversationHandler,
    MessageHandler, filters
)

ASK_NICKNAME, ASK_NAME, MAIN_MENU, SELECT_COMPAGNO, SELECT_AVV1, SELECT_AVV2, SELECT_ESITO, PROFILE_MENU = range(8)

import os

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TOKEN"]

# Stati conversazione
ASK_NICKNAME, ASK_NAME, MAIN_MENU, PROFILE_MENU = range(4)
SELECT_COMPAGNO, SELECT_AVV1, SELECT_AVV2, SELECT_ESITO = range(4, 8)

main_menu_keyboard = [
    ["Inserisci nuovo risultato"],
    ["Il mio profilo"],
    ["Visualizza classifica"],
    ["Informazioni"]
]
main_menu_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True, one_time_keyboard=True)


# Database in memoria
import json

with open("archivio_utenti.json", "r", encoding="utf-8") as f:
    user_db = json.load(f)

import time

DB_UTENTI_FILE = "archivio_utenti.json"

if os.path.exists("storico_partite.json"):
    with open("storico_partite.json", "r") as f:
        storico_partite = json.load(f)

def carica_db_utenti():
    try:
        with open(DB_UTENTI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def salva_db_utenti(db):
    with open(DB_UTENTI_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

user_db = carica_db_utenti()

async def info_app(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    testo_info = (
        "🏓 *App Biliardino*\n\n"
        "Questa app ti permette di inserire risultati, "
        "vedere la classifica aggiornata e visualizzare il tuo profilo.\n"
        "Sistema di punteggi Elo personalizzato.\n"
        "Buon divertimento!"
    )
    keyboard = ReplyKeyboardMarkup([["Indietro"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_markdown(testo_info, reply_markup=keyboard)
    return MAIN_MENU  # Torni a MAIN_MENU ma non chiami main_menu() subito

async def mostra_profilo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Leggi il database esterno degli utenti
    try:
        with open("archivio_utenti.json", "r") as f:
            user_db = json.load(f)
    except FileNotFoundError:
        user_db = {}

    user = user_db.get(str(user_id))
    if not user:
        await update.message.reply_text("Utente non trovato nel database.")
        return MAIN_MENU

    nickname = user["nickname"]

    # Leggi lo storico partite dal file
    try:
        with open("storico.json", "r") as f:
            storico_partite = json.load(f)
    except FileNotFoundError:
        storico_partite = []

    # Calcola statistiche
    partite_utente = [p for p in storico_partite if nickname in p["squadra"] or nickname in p["avversari"]]
    vinte = sum(1 for p in partite_utente if
                (nickname in p["squadra"] and p["esito"] == "Vinto") or
                (nickname in p["avversari"] and p["esito"] == "Perso"))
    perse = len(partite_utente) - vinte

    testo_profilo = (
        f"👤 Profilo di *{nickname}*\n\n"
        f"Punteggio: {user['punteggio']}\n"
        f"Partite giocate: {len(partite_utente)}\n"
        f"Vittorie: {vinte}\n"
        f"Sconfitte: {perse}\n"
    )

    keyboard = ReplyKeyboardMarkup([["Vedi storico partite"], ["Indietro"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_markdown(text=testo_profilo, reply_markup=keyboard)
    return PROFILE_MENU



# start(): prima funzione chiamata
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)
    context.user_data.clear()

    if user_id in user_db:
        nickname = user_db[user_id]['nickname']
        await update.message.reply_text(
            f"Bentornato {nickname}! Scegli un'opzione dal menu qui sotto:",
            reply_markup=main_menu_markup,
        )
        return MAIN_MENU
    else:
        await update.message.reply_text(
            "Benvenuto! Inserisci un nickname (sarà visibile agli altri giocatori):",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_NICKNAME

# ask_nickname(): riceve il nickname, lo salva temporaneamente in user_data
async def ask_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    nickname = update.message.text.strip()

    # puoi anche aggiungere validazioni qui, tipo lunghezza, caratteri, unicità...
    context.user_data["nickname"] = nickname

    await update.message.reply_text("Perfetto! Ora inserisci il tuo *nome reale*.", parse_mode="Markdown")
    return ASK_NAME

# ask_name(): riceve il nome e completa la registrazione
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = str(update.effective_user.id)

    user_db[user_id] = {
        "nickname": context.user_data["nickname"],
        "name": update.message.text.strip(),
        "username": update.effective_user.username or "",
        "punteggio": 1000,
        "K": 60,
        "timestamp": int(time.time())
    }

    salva_db_utenti(user_db)

    await update.message.reply_text(
        f"Grazie {context.user_data['nickname']}! Ora puoi scegliere un'opzione dal menu.",
        reply_markup=main_menu_markup,
    )
    return MAIN_MENU


async def mostra_storico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id

    # Leggi il db utenti da file
    try:
        with open("utenti.json", "r") as f:
            user_db = json.load(f)
    except FileNotFoundError:
        user_db = {}

    user = user_db.get(str(user_id))
    if not user:
        await update.message.reply_text("Utente non trovato nel database.")
        return MAIN_MENU

    nickname = user["nickname"]

    # Leggi lo storico partite da file
    try:
        with open("storico.json", "r") as f:
            storico_partite = json.load(f)
    except FileNotFoundError:
        storico_partite = []

    # Filtra le partite dell'utente
    partite_utente = [p for p in storico_partite if nickname in p["squadra"] or nickname in p["avversari"]]

    if not partite_utente:
        testo = "Non hai ancora partite registrate."
    else:
        righe = []
        # Mostra massimo le ultime 10 partite
        for p in partite_utente[-10:]:
            squadra_1 = " & ".join(p["squadra"])
            squadra_2 = " & ".join(p["avversari"])
            risultato = ("Vittoria" if
                         (nickname in p["squadra"] and p["esito"] == "Vinto") or
                         (nickname in p["avversari"] and p["esito"] == "Perso")
                         else "Sconfitta")
            righe.append(f"{squadra_1} vs {squadra_2} -> {risultato}")

        testo = "Ultime partite:\n" + "\n".join(righe)

    keyboard = ReplyKeyboardMarkup([["Indietro"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(testo, reply_markup=keyboard)
    return PROFILE_MENU


async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scelta = update.message.text
    if scelta == "Inserisci nuovo risultato":
        return await nuova_partita(update, context)
    elif scelta == "Il mio profilo":
        return await mostra_profilo(update, context)
    elif scelta == "Visualizza classifica":
        return await mostra_classifica(update, context)
    elif scelta == "Informazioni":
        return await info_app(update, context)
    elif scelta == "Indietro":
        # Se sei già nel main_menu e premi indietro, semplicemente rispondi con menu
        await update.message.reply_text("Seleziona un'opzione:", reply_markup=main_menu_markup)
        return MAIN_MENU
    else:
        await update.message.reply_text("Seleziona una voce valida.", reply_markup=main_menu_markup)
        return MAIN_MENU


async def profilo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scelta = update.message.text
    if scelta == "Vedi storico partite":
        return await mostra_storico(update, context)
    elif scelta == "Indietro":
        # Torna al main menu mostrando la tastiera
        await update.message.reply_text("Seleziona un'opzione:", reply_markup=main_menu_markup)
        return MAIN_MENU
    else:
        await update.message.reply_text("Seleziona una voce valida.")
        return PROFILE_MENU


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
    user_id = str(update.effective_user.id)  # Cast a stringa per accedere al JSON
    context.user_data["giocatore"] = user_db[user_id]

    # Escludi il giocatore corrente dalla lista dei possibili compagni
    giocatori = [v["nickname"] for k, v in user_db.items() if k != user_id]

    if len(giocatori) < 3:
        await update.message.reply_text("Servono almeno altri 3 utenti registrati per inserire un risultato.")
        return MAIN_MENU

    markup = ReplyKeyboardMarkup([[n] for n in giocatori], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Ho giocato insieme a", reply_markup=markup)
    return SELECT_COMPAGNO


async def select_compagno(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    compagno = update.message.text
    user = context.user_data["giocatore"]
    nickname_utente = user["nickname"]

    # Lista dei nickname validi (tutti tranne sé stessi)
    compagni_validi = [v["nickname"] for v in user_db.values() if v["nickname"] != nickname_utente]

    if compagno not in compagni_validi:
        await update.message.reply_text(
            "⚠️ Scelta non valida. Seleziona il compagno dalla lista usando i pulsanti."
        )
        return SELECT_COMPAGNO

    context.user_data["compagno"] = compagno

    # Avversari = tutti tranne giocatore e compagno
    avversari_possibili = [v["nickname"] for v in user_db.values() if v["nickname"] not in [nickname_utente, compagno]]
    markup = ReplyKeyboardMarkup([[n] for n in avversari_possibili], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text("Abbiamo giocato contro", reply_markup=markup)
    return SELECT_AVV1

async def select_avversario1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    avv1 = update.message.text

    esclusi = [
        context.user_data["giocatore"]["nickname"],
        context.user_data["compagno"],
    ]

    validi = [v["nickname"] for v in user_db.values() if v["nickname"] not in esclusi]

    if avv1 not in validi:
        markup = ReplyKeyboardMarkup([[n] for n in validi], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("⚠️ Scegli un avversario valido tra quelli nel menu.", reply_markup=markup)
        return SELECT_AVV1

    context.user_data["avv1"] = avv1

    # Aggiorna la lista degli esclusi e genera la lista rimanente
    esclusi.append(avv1)
    avversari_restanti = [v["nickname"] for v in user_db.values() if v["nickname"] not in esclusi]

    markup = ReplyKeyboardMarkup([[n] for n in avversari_restanti], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("e", reply_markup=markup)
    return SELECT_AVV2

async def select_avversario2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    avv2 = update.message.text

    esclusi = [
        context.user_data["giocatore"]["nickname"],
        context.user_data["compagno"],
        context.user_data["avv1"]
    ]

    validi = [v["nickname"] for v in user_db.values() if v["nickname"] not in esclusi]

    if avv2 not in validi:
        markup = ReplyKeyboardMarkup([[n] for n in validi], one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("⚠️ Scegli un avversario valido tra quelli nel menu.", reply_markup=markup)
        return SELECT_AVV2

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
        for user in user_db.values():
            if user["nickname"] == nick:
                R[nick] = user["punteggio"]
                K[nick] = user["K"]
                break

    k = 0.45
    R_std = 600

    # Calcola R_1 e R_2
    RA, RB = R[squadra_1[0]], R[squadra_1[1]]
    RC, RD = R[squadra_2[0]], R[squadra_2[1]]

    R_1 = 0.5 * math.sqrt(RA * RB) + 0.5 * (k * max(RA, RB) + (1 - k) * min(RA, RB))
    R_2 = 0.5 * math.sqrt(RC * RD) + 0.5 * (k * max(RC, RD) + (1 - k) * min(RC, RD))

    # Valori attesi
    E_1 = 1 / (1 + 10 ** ((R_2 - R_1) / R_std))
    E_2 = 1 - E_1

    # Risultato
    S_1 = 1 if esito == "Vinto" else 0
    S_2 = 1 - S_1

    # Nuovi punteggi
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

    # Salva risultato nello storico
    try:
        with open("storico.json", "r") as f:
            storico = json.load(f)
    except FileNotFoundError:
        storico = []
    
    storico.append(risultato)
    
    with open("storico.json", "w") as f:
        json.dump(storico, f, indent=2)


    # Notifica ai giocatori coinvolti (escludendo l'autore)
    autore = dati["giocatore"]["nickname"]
    coinvolti = set(squadra_1 + squadra_2)
    coinvolti.discard(autore)

    for user_id_str, user in user_db.items():
        if user["nickname"] in coinvolti:
            try:
                await context.bot.send_message(
                    chat_id=int(user_id_str),
                    text=(
                        f"⚠️ Ciao {user['nickname']}, {autore} ha inserito una partita in cui sei coinvolto!\n"
                        f"Controlla la classifica aggiornata o il tuo storico partite."
                    )
                )
            except Exception as e:
                print(f"Errore inviando notifica a {user['nickname']}: {e}")

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
    import os

    TOKEN = os.getenv("TOKEN")  # Assicurati di esportare la variabile d'ambiente TOKEN

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_nickname)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            PROFILE_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, profilo_handler)],
            SELECT_COMPAGNO: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_compagno)],
            SELECT_AVV1: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_avversario1)],
            SELECT_AVV2: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_avversario2)],
            SELECT_ESITO: [MessageHandler(filters.Regex("^(Vinto|Perso)$"), select_esito)],
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('cancel', cancel)],
        allow_reentry=True,
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

