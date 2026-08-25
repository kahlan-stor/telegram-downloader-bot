import os
import threading
import asyncio
from flask import Flask, render_template_string, request, send_file
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ----------------------------------------------------
# 1. الإعدادات وتطبيق Flask
# ----------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8294576614:AAHZDyHZ5mtC3rU6RpsSfvB9lX0oiGKZ9bY")
app = Flask(__name__)

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مُنزّل الفيديوهات الذكي</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --bg-color: #0f172a; --card-bg: #1e293b; --accent: #3b82f6; --text: #f8fafc; --border: #334155; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
        body { background: var(--bg-color); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .container { width: 100%; max-width: 600px; display: flex; flex-direction: column; gap: 20px; margin-top: 40px; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .input-group { position: relative; margin-top: 15px; }
        .input-group input { width: 100%; padding: 14px 45px 14px 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; outline: none; font-size: 15px; }
        .input-group i { position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: #94a3b8; }
        .btn-main { width: 100%; padding: 14px; border-radius: 10px; border: none; background: var(--accent); color: white; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 15px; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h2 style="text-align:center;">مُنزّل الفيديوهات الذكي</h2>
        <form action="/download-web" method="post">
            <div class="input-group">
                <i class="fa-solid fa-link"></i>
                <input type="url" name="url" placeholder="ألصق رابط الفيديو هنا..." required>
            </div>
            <button type="submit" class="btn-main">تنزيل الفيديو (أعلى جودة)</button>
        </form>
    </div>
</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/download-web', methods=['POST'])
def web_download():
    url = request.form.get('url', '').strip()
    file_path = "web_download.mp4"
    try:
        # استخدام صيغة جاهزة مدموجة لتفادي الحاجة لـ ffmpeg
        opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': file_path,
            'quiet': True
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return f"❌ حدث خطأ: {str(e)}"
    finally:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

# ----------------------------------------------------
# 2. منطق بوت التليجرام (اختيار الدقة + بدون ffmpeg)
# ----------------------------------------------------
user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط الفيديو، وسأعرض عليك الدقات المتاحة لتختار منها.")

async def process_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("⚠️ يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    msg = await update.message.reply_text("🔍 جاري جلب الدقات المتاحة...")
    
    try:
        loop = asyncio.get_event_loop()
        def extract_info():
            ydl_opts = {'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, extract_info)
        formats = info.get('formats', [])
        
        # استخراج الدقات المتاحة (فيديو يحتوي على صوت وصورة معاً لتجنب الحاجة لـ ffmpeg)
        available_qualities = []
        seen_heights = set()

        for f in formats:
            height = f.get('height')
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')
            
            # التأكد من أن الصيغة تحتوي على فيديو وصوت مدمجين
            if height and vcodec != 'none' and acodec != 'none':
                if height not in seen_heights:
                    seen_heights.add(height)
                    available_qualities.append((height, f.get('format_id')))

        # ترتيب الدقات من الأعلى للأقل
        available_qualities.sort(key=lambda x: x[0], reverse=True)

        if not available_qualities:
            # في حال لم تجد صيغ مدموجة جاهزة، خذ الدقة الافتراضية الجاهزة
            keyboard = [[InlineKeyboardButton("تنزيل بأفضل جودة متاحة 🎬", callback_data="best")]]
        else:
            keyboard = []
            row = []
            for q_height, fmt_id in available_qualities:
                row.append(InlineKeyboardButton(f"{q_height}p 🎥", callback_data=f"fmt_{fmt_id}"))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton("أفضل جودة تلقائية 🌟", callback_data="best")])

        # حفظ الرابط الخاص بالمستخدم
        user_urls[update.message.chat_id] = url
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text(" اختر الدقة المطلوبة للتنزيل:", reply_markup=reply_markup)

    except Exception as e:
        await msg.edit_text(f"❌ تعذر استخراج معلومات الفيديو: {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    url = user_urls.get(chat_id)
    if not url:
        await query.edit_message_text("❌ انتهت الجلسة، يرجى إرسال الرابط من جديد.")
        return

    data = query.data
    await query.edit_message_text("⏳ جاري تنزيل الفيديو بالدقة المختارة وإرساله...")

    file_path = f"tg_{chat_id}.mp4"
    
    if data == "best":
        fmt_str = "best[ext=mp4]/best"
    else:
        fmt_id = data.replace("fmt_", "")
        fmt_str = f"{fmt_id}/best[ext=mp4]/best"

    opts = {
        'format': fmt_str,
        'outtmpl': file_path,
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024  # حد أقصى 50 ميجابايت للتلجرام
    }

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([url]))

        if os.path.exists(file_path):
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(chat_id=chat_id, video=video_file)
            await query.delete_message()
        else:
            await context.bot.send_message(chat_id=chat_id, text="❌ لم يتم العثور على الملف بعد التنزيل.")

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ تعذر التحميل: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

def run_telegram_bot():
    asyncio.set_event_loop(asyncio.new_event_loop())
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_url))
    tg_app.add_handler(CallbackQueryHandler(button_callback))
    tg_app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
