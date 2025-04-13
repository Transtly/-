from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from deep_translator import GoogleTranslator
import fitz
import os

BOT_TOKEN = '7906120916:AAEYEKS6ZhBQPEEy0gyQOGcUCEuHImB2rL0'
INSTAGRAM_LINK = 'https://instagram.com/o8.ne'
user_verified = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_verified:
        await update.message.reply_text("مرحبًا بك مجددًا! أرسل لي ملف PDF أو نص.")
    else:
        keyboard = [
            [InlineKeyboardButton("تابعتك", callback_data="verified")],
            [InlineKeyboardButton("متابعة على إنستغرام", url=INSTAGRAM_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("قبل الاستخدام، تابع حسابي على إنستغرام ثم اضغط 'تابعتك'.", reply_markup=reply_markup)

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_verified.add(user_id)
    await query.edit_message_text("شكراً لمتابعتك! الآن يمكنك إرسال الملفات أو النصوص.")

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_verified:
        await start(update, context)
        return

    original_text = update.message.text
    translated = GoogleTranslator(source='en', target='ar').translate(original_text)
    await update.message.reply_text(translated)

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_verified:
        await start(update, context)
        return

    await update.message.reply_text("تم استلام الملف. يرجى الانتظار ريثما تتم معالجته...")

    file = await update.message.document.get_file()
    file_path = f"{file.file_id}.pdf"
    await file.download_to_drive(file_path)

    try:
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()
        os.remove(file_path)

        if full_text.strip():
            translated = GoogleTranslator(source='en', target='ar').translate(full_text)
            chunks = [translated[i:i+4000] for i in range(0, len(translated), 4000)]
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            await update.message.reply_text("الملف لا يحتوي على نص قابل للقراءة.")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء معالجة الملف: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(verify_callback))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), translate_text))
app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))

app.run_polling()
