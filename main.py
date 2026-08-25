import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import yt_dlp

BOT_TOKEN = "8294576614:AAHWGU7AQntnN9eZX_8aTyTo7oDwMOhYJWU"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من (TikTok, Instagram, YouTube...) لتحميله فوراً.")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not (url.startswith("http://") or url.startswith("https://")):
        return

    msg = await update.message.reply_text("⏳ جاري تحميل الفيديو، يرجى الانتظار...")
    file_path = f"video_{update.message.message_id}.mp4"

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': file_path,
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024, # 50MB
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(file_path):
            await update.message.reply_video(video=open(file_path, 'rb'), caption="✅ تم التحميل بنجاح!")
        else:
            await update.message.reply_text("❌ لم يتم العثور على الملف بعد التحميل.")
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")
        
    finally:
        await msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("🚀 البوت يعمل الآن...")
    app.run_polling()
