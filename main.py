import os
import threading
from flask import Flask, render_template_string, request, send_file
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ----------------------------------------------------
# 1. إعداد التوكن وتطبيق Flask
# ----------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8294576614:AAHZDyHZ5mtC3rU6RpsSfvB9lX0oiGKZ9bY")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_urls = {}

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مُنزّل الفيديوهات الذكي</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        :root { --bg-color: #0f172a; --card-bg: #1e293b; --accent: #3b82f6; --text: #f8fafc; --border: #334155; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
        body { background: var(--bg-color); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .container { width: 100%; max-width: 600px; margin-top: 40px; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 25px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .input-group { position: relative; margin-top: 15px; }
        .input-group input { width: 100%; padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; font-size: 15px; }
        .btn-main { width: 100%; padding: 14px; border-radius: 10px; border: none; background: var(--accent); color: white; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 15px; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <h2 style="text-align:center;">مُنزّل الفيديوهات الذكي</h2>
        <form action="/download-web" method="post">
            <div class="input-group">
                <input type="url" name="url" placeholder="ألصق رابط الفيديو هنا..." required>
            </div>
            <button type="submit" class="btn-main">تنزيل الفيديو</button>
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
        opts = {'format': 'best[ext=mp4]/best', 'outtmpl': file_path, 'quiet': True}
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
# 2. منطق بوت التليجرام
# ----------------------------------------------------
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! 🎬 أرسل لي رابط الفيديو لتحديد الدقة المطلوب تنزيلها.")

@bot.message_handler(func=lambda message: True)
def process_video_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "⚠️ يرجى إرسال رابط صحيح يبدأ بـ http أو https.")
        return

    msg = bot.reply_to(message, "🔍 جاري تحليل الرابط واستخراج الدقات المتاحة...")

    try:
        ydl_opts = {'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = info.get('formats', [])
        available_qualities = []
        seen_heights = set()

        for f in formats:
            height = f.get('height')
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')

            if height and vcodec != 'none' and acodec != 'none':
                if height not in seen_heights:
                    seen_heights.add(height)
                    available_qualities.append((height, f.get('format_id')))

        available_qualities.sort(key=lambda x: x[0], reverse=True)

        markup = InlineKeyboardMarkup()
        if available_qualities:
            row = []
            for q_height, fmt_id in available_qualities:
                row.append(InlineKeyboardButton(f"{q_height}p 🎥", callback_data=f"fmt_{fmt_id}"))
                if len(row) == 2:
                    markup.add(*row)
                    row = []
            if row:
                markup.add(*row)
        
        markup.add(InlineKeyboardButton("أفضل جودة تلقائية 🌟", callback_data="best"))

        user_urls[message.chat.id] = url
        bot.edit_message_text("اختر الدقة المطلوبة للتنزيل:", chat_id=message.chat.id, message_id=msg.message_id, reply_markup=markup)

    except Exception as e:
        bot.edit_message_text(f"❌ تعذر جلب معلومات الفيديو: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

@bot.callback_query_handler(func=lambda call: True)
def callback_download(call):
    chat_id = call.message.chat.id
    url = user_urls.get(chat_id)

    if not url:
        bot.answer_callback_query(call.id, "انتهت الجلسة، يرجى إرسال الرابط مجدداً.")
        return

    bot.edit_message_text("⏳ جاري تنزيل الفيديو بالدقة المختارة والإرسال...", chat_id=chat_id, message_id=call.message.message_id)

    data = call.data
    if data == "best":
        fmt_str = "best[ext=mp4]/bestvideo+bestaudio/best"
    else:
        fmt_id = data.replace("fmt_", "")
        fmt_str = f"{fmt_id}/best[ext=mp4]/best"

    file_path = f"tg_{chat_id}.mp4"
    opts = {
        'format': fmt_str,
        'outtmpl': file_path,
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        if os.path.exists(file_path):
            with open(file_path, 'rb') as video:
                bot.send_video(chat_id, video)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.send_message(chat_id, "❌ لم يتم العثور على الملف بعد التنزيل.")

    except Exception as e:
        bot.send_message(chat_id, f"❌ تعذر التنزيل: {str(e)}")
    finally:
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass

# ----------------------------------------------------
# 3. تشغيل البوت (تم إصلاح المعامل هنا)
# ----------------------------------------------------
def start_bot():
    try:
        print("🤖 جاري تشغيل بوت التليجرام...")
        bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")

bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
