import os
import feedparser
from datetime import datetime
from weasyprint import HTML
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
import threading

# === CONFIG ===
TOKEN = "7395618332:AAFnBxVzUhmPkoquiO4CVV8rx4c8lQAS078"
PORT = int(os.environ.get('PORT', 8443))

# === FLASK SERVER FOR KEEP-ALIVE ON RENDER ===
app = Flask(__name__)

@app.route('/')
def home():
    return "InfoPulseBot is alive."

def run_flask():
    app.run(host='0.0.0.0', port=PORT)

# === RSS FEEDS ===
TECH_FEEDS = [
    "https://www.wired.it/feed/",
    "https://startupitalia.eu/feed",
    "https://techcrunch.com/feed/",
    "https://www.technologyreview.com/feed/"
]

WORLD_FEEDS = [
    "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
    "http://feeds.reuters.com/Reuters/worldNews",
    "https://www.aljazeera.com/xml/rss/all.xml"
]

ITALY_FEEDS = [
    "https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml",
    "https://www.ansa.it/sito/notizie/politica/politica_rss.xml",
    "https://www.ilpost.it/feed/",
    "https://tg24.sky.it/rss"
]

def get_rss_items(feed_urls, max_items=3):
    items = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items]:
            items.append(f"- <a href='{entry.link}'>{entry.title}</a>")
    return "<br>".join(items[:max_items]) if items else "Nessuna notizia trovata."

def get_tech_news():
    return get_rss_items(TECH_FEEDS)

def get_world_news():
    return get_rss_items(WORLD_FEEDS)

def get_italy_news():
    return get_rss_items(ITALY_FEEDS)

def generate_daily_pdf():
    today = datetime.today().strftime("%Y-%m-%d")
    tech = get_tech_news()
    world = get_world_news()
    italy = get_italy_news()

    html = f"""
    <h1>Rassegna Quotidiana – {today}</h1>
    <h2>🔬 Innovazioni e Tecnologie</h2>
    <p>{tech}</p>
    <h2>🌍 Politica Globale</h2>
    <p>{world}</p>
    <h2>🇮🇹 Notizie dall’Italia</h2>
    <p>{italy}</p>
    """

    pdf_path = f"rassegna-{today}.pdf"
    HTML(string=html).write_pdf(pdf_path)
    return pdf_path

# === TELEGRAM COMMANDS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono InfoPulseBot 🧠\n\nUsa /oggi per ricevere la rassegna completa in PDF oppure /info per tutti i comandi disponibili."
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/oggi → Rassegna completa\n/tech → Innovazioni e Tecnologie\n/mondo → Politica Globale\n/italia → Notizie dall’Italia"
    )

async def oggi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_path = generate_daily_pdf()
    with open(pdf_path, 'rb') as pdf:
        await update.message.reply_document(document=InputFile(pdf), filename=os.path.basename(pdf_path))

async def tech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tech = get_tech_news().replace('<a ', '[').replace('</a>', '').replace(" href=", "](").replace(">", ")")
    await update.message.reply_text(f"🔬 *Innovazioni e Tecnologie:*\n{tech}", parse_mode='Markdown')

async def mondo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    world = get_world_news().replace('<a ', '[').replace('</a>', '').replace(" href=", "](").replace(">", ")")
    await update.message.reply_text(f"🌍 *Politica Globale:*\n{world}", parse_mode='Markdown')

async def italia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    italy = get_italy_news().replace('<a ', '[').replace('</a>', '').replace(" href=", "](").replace(">", ")")
    await update.message.reply_text(f"🇮🇹 *Italia:*\n{italy}", parse_mode='Markdown')

# === MAIN ===
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    app_telegram = ApplicationBuilder().token(TOKEN).build()

    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(CommandHandler("info", info))
    app_telegram.add_handler(CommandHandler("oggi", oggi))
    app_telegram.add_handler(CommandHandler("tech", tech))
    app_telegram.add_handler(CommandHandler("mondo", mondo))
    app_telegram.add_handler(CommandHandler("italia", italia))

    app_telegram.run_polling()
