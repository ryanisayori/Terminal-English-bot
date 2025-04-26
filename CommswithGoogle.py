import asyncio
import io
import sys
import textwrap
import nltk
from termcolor import colored
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters, CommandHandler
from nltk.corpus import wordnet as wn
from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
from nltk.tokenize import word_tokenize
import requests
# Replace googletrans with deep_translator
from deep_translator import GoogleTranslator

# Telegram config
TOKEN = "6964609548:AAFIzEAB5ADVFEkiiJInKXLOfpJFmtNPeLk"  # Replace with your bot token
CHAT_ID = "5283761841"  # Replace with your Telegram user ID

# Setup NLTK
def setup_nltk():
    resources = {
        'tokenizers/punkt': 'punkt',
        'corpora/wordnet': 'wordnet',
        'corpora/stopwords': 'stopwords'
    }
    for path, package in resources.items():
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(package)

setup_nltk()

# Initialize translator
# We don't need to set up multiple service URLs with deep_translator
translator = GoogleTranslator(source='auto', target='en')

# Send message to Telegram
def send_to_telegram(message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

# Format output
def format_output(title, content, title_color, content_color="white", width=80):
    wrapped = textwrap.fill(content, width=width - len(title) - 3)
    return f"{colored(title, title_color)} {colored(wrapped, content_color)}"

# Get collocations
def get_collocations(word, top_n=5):
    sample_text = """
    Happy birthday! Happy anniversary! Happy days.
    Run fast. Run free. Run smoothly.
    Light room. Light reading. Light colors.
    Beautiful day. Beautiful life. Beautiful person.
    """
    tokens = word_tokenize(sample_text.lower())
    stopwords = set(nltk.corpus.stopwords.words('english'))
    filtered = [w for w in tokens if w.isalpha() and w not in stopwords]
    finder = BigramCollocationFinder.from_words(filtered)
    return [" ".join(c) for c in finder.nbest(BigramAssocMeasures().pmi, 20) if word in c][:top_n]

# Get word info
def get_word_details(word):
    synsets = wn.synsets(word)
    if not synsets:
        return f"\n🔍 No definitions found for '{word}'"
    out = []
    first_syn = synsets[0]
    out.append(f"📖 Definition: {first_syn.definition()}")
    pos_map = {'n': 'Noun', 'v': 'Verb', 'a': 'Adjective', 's': 'Adjective (satellite)', 'r': 'Adverb'}
    pos = pos_map.get(first_syn.pos(), first_syn.pos())
    out.append(f"🗣️ Part of Speech: {pos}")
    examples = first_syn.examples()
    if examples:
        out.append("📝 Examples: " + "; ".join(examples))
    synonyms = set(lemma.name().replace('_', ' ') for syn in synsets for lemma in syn.lemmas())
    if synonyms:
        out.append("🔄 Synonyms: " + ", ".join(list(synonyms)[:10]))
    antonyms = set(ant.name().replace('_', ' ') for syn in synsets for lemma in syn.lemmas() for ant in lemma.antonyms())
    if antonyms:
        out.append("⚡ Antonyms: " + ", ".join(antonyms))
    collocations = get_collocations(word.lower())
    if collocations:
        out.append("🤝 Collocations: " + ", ".join(collocations))
    return "\n".join(out)

# Function to translate text using deep_translator
def translate_text(text, target_language='en', source_language='auto'):
    try:
        # Create a translator instance with the desired languages
        translator = GoogleTranslator(source=source_language, target=target_language)
        # Translate the text
        result = translator.translate(text)
        return result
    except Exception as e:
        return f"Translation error: {str(e)}"

# Handle Telegram messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.strip()
    
    # Check if message starts with "translate:"
    if message_text.lower().startswith("translate:"):
        # Parse the translation request
        parts = message_text[10:].strip().split(':', 1)
        if len(parts) == 2:
            lang, text = parts
            translated = translate_text(text, lang)
            await update.message.reply_text(f"Original: {text}\nTranslated ({lang}): {translated}")
        else:
            await update.message.reply_text("Format: translate:language_code:text\nExample: translate:es:Hello world")
    else:
        # Treat as word lookup
        word = message_text
        result = get_word_details(word)
        print(f"\n{colored('► Analyzing from Telegram:', 'green')} {colored(word.upper(), 'white', attrs=['bold', 'underline'])}")
        print(result)
        await update.message.reply_text(result)

# Handle translate command
async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if there are any arguments
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("Usage: /translate [language_code] [text]\nExample: /translate es Hello world")
        return
        
    # Extract language and text
    target_lang = context.args[0].lower()
    text = ' '.join(context.args[1:])
    
    # Perform translation
    translated = translate_text(text, target_lang)
    
    # Reply with the translation
    await update.message.reply_text(f"Original: {text}\nTranslated ({target_lang}): {translated}")

# Run bot async
async def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("translate", translate_command))
    await app.run_polling()

# Terminal input loop (send to Telegram)
def terminal_loop():
    while True:
        user_input = input("\nEnter a word (or 'translate:lang:text' or 'q' to quit): ").strip()
        if user_input.lower() == 'q':
            break
            
        if user_input.lower().startswith('translate:'):
            # Handle translation request
            parts = user_input[10:].split(':', 1)
            if len(parts) == 2:
                lang, text = parts
                translated = translate_text(text, lang)
                print(f"\n{colored('► Translation:', 'magenta')}")
                print(f"Original: {text}")
                print(f"Translated ({lang}): {translated}")
                send_to_telegram(f"Original: {text}")
                send_to_telegram(f"Translated ({lang}): {translated}")
            else:
                print("Format: translate:language_code:text\nExample: translate:es:Hello world")
        else:
            # Handle word lookup
            word = user_input
            print(f"\n{colored('► Analyzing from Terminal:', 'cyan')} {colored(word.upper(), 'white', attrs=['bold', 'underline'])}")
            result = get_word_details(word)
            print(result)
            send_to_telegram(f"Analyzing from Terminal: {word}")
            send_to_telegram(result)

# Run both terminal and bot loop
if __name__ == '__main__':
    try:
        asyncio.get_event_loop().create_task(run_bot())
        terminal_loop()
    except (KeyboardInterrupt, SystemExit):
        print("\nBot stopped.")