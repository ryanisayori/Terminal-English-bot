from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
import nltk, io, sys, textwrap
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder

# Setup NLTK
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# Hàm lấy thông tin từ vựng
def get_word_details(word: str) -> str:
    synsets = wn.synsets(word)
    if not synsets:
        return f"No definitions found for '{word}'"

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

    return "\n".join(out)

# Hàm xử lý tin nhắn từ người dùng
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    result = get_word_details(user_input)
    await update.message.reply_text(result)
    print("----------------------------------------")
    print("WORD: ", user_input)
    print(result)
    print("----------------------------------------")

# Run bot
if __name__ == '__main__':
    token = "6964609548:AAFIzEAB5ADVFEkiiJInKXLOfpJFmtNPeLk"  # thay token vào đây
    app = ApplicationBuilder().token(token).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
