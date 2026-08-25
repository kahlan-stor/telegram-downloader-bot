import os
import threading
import json
import urllib.request
import asyncio
from flask import Flask, render_template_string, request, send_file
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import yt_dlp

# ----------------------------------------------------
# 1. إعدادات السيرفر والبوت (جلب التوكين بأمان)
# ----------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8294576614:AAHZDyHZ5mtC3rU6RpsSfvB9lX0oiGKZ9bY")
app = Flask(__name__)

# تصميم واجهة الموقع بـ HTML & CSS (مع معلومات المطور وزر الواتساب وتحديد الجودة)
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مُنزّل الفيديوهات الذكي | كهلان زيد الأشول</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --accent: #3b82f6;
            --text: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --whatsapp: #25d366;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }
        body { background: var(--bg-color); color: var(--text); min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .container { width: 100%; max-width: 650px; display: flex; flex-direction: column; gap: 20px; }
        .card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
        .dev-card { display: flex; align-items: center; justify-content: space-between; }
        .dev-info { display: flex; align-items: center; gap: 12px; }
        .avatar { width: 50px; height: 50px; border-radius: 50%; background: linear-gradient(135deg, #3b82f6, #8b5cf6); display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px; color: white; }
        .wa-btn { background: rgba(37, 211, 102, 0.15); color: var(--whatsapp); border: 1px solid var(--whatsapp); padding: 8px 14px; border-radius: 10px; text-decoration: none; font-weight: bold; display: flex; align-items: center; gap: 6px; transition: all 0.3s; }
        .wa-btn:hover { background: var(--whatsapp); color: white; }
        .input-group { position: relative; margin-top: 15px; }
        .input-group input { width: 100%; padding: 14px 45px 14px 14px; border-radius: 10px; border: 1px solid var(--border); background: #0f172a; color: white; outline: none; font-size: 15px; }
        .input-group i { position: absolute; right: 15px; top: 50%; transform: translateY(-50%); color: var(--text-muted); font-size: 18px; }
        .select-box { width: 100%; margin-top: 12px; padding: 12px; border-radius: 10px; background: #0f172a; color: white; border: 1px solid var(--border); outline: none; font-size: 14px; }
        .btn-main { width: 100%; padding: 14px; border-radius: 10px; border: none; background: var(--accent); color: white; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 15px; transition: background 0.3s; display: flex; align-items: center; justify-content: center; gap: 8px; }
        .btn-main:hover { background: #2563eb; }
    </style>
</head>
<body>
<div class="container">
    <!-- بطاقة المطور -->
    <div class="card dev-card">
        <div class="dev-info">
            <div class="avatar">ك</div>
            <div>
                <h3>كهلان زيد الأشول</h3>
                <p style="font-size:12px; color:var(--text-muted);">مطور تطبيقات ومواقع إلكترونية</p>
            </div>
        </div>
        <a href="https://wa.me/967711014694" target="_blank" class="wa-btn">
            <i class="fa-brands fa-whatsapp"></i> واتساب
        </a>
    </div>

    <!-- بطاقة التنزيل -->
    <div class="card">
        <h2 style="text-align:center; font-size:20px;">مُنزّل الفيديوهات والأصوات الذكي</h2>
        <p style="text-align:center; color:var(--text-muted); font-size:13px; margin-bottom:15px;">يدعم TikTok, YouTube, Instagram, Facebook...</p>
        
        <form action="/download-web" method="post">
            <div class="input-group">
                <i class="fa-solid fa-link"></i>
                <input type="url" name="url" placeholder="ألصق رابط الفيديو هنا..." required>
            </div>
            
            <select name="format_type" class="select-box">
                <option value="video_high">🎬 فيديو - أعلى دقة متاحة (1080p/720p)</option>
                <option value="video_mid">📹 فيديو - دقة متوسطة (480p)</option>
                <option value="audio">🎵 صوت فقط (MP3)</option>
            </select>
            
            <button type="submit" class="btn-main">
                <i class="fa-solid fa-download"></i> تنزيل الآن
            </button>
        </form>
    </div>
</div>
</body>
</html>
"""

# ----------------------------------------------------
# 2. خدمات ومسارات الموقع (Web Server Routes)
# ----------------------------------------------------
@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/download-web', methods=['POST'])
def web_download():
    url = request.form.get('url', '').strip()
    fmt = request.form.get('format_type', 'video_high')
    file_path = "web_download.mp3" if fmt == 'audio' else "web_download.mp4"

    try:
        if "tiktok.com" in url:
            api_url = f"https://api.tiklydown.eu.org/api/download?url={url}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                video_url = data.get('video', {}).get('noWatermark') or data.get('video', {}).get('watermark')
            
            v_req = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(v_req, timeout=30) as v_resp, open(file_path, 'wb') as f:
                f.write(v_resp.read())
        else:
            if fmt == 'audio':
                opts = {'format': 'bestaudio/best', 'outtmpl': file_path, 'quiet': True}
            elif fmt == 'video_mid':
                opts = {'format': 'best[height<=480]', 'outtmpl': file_path, 'quiet': True}
            else:
                opts = {'format': 'bestvideo+bestaudio/best', 'outtmpl': file_path, 'quiet': True}

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return f"<h3 style='color:red; text-align:center; font-family:sans-serif;'>❌ حدث خطأ أثناء التنزيل: {str(e)}</h3>"

    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass

# ----------------------------------------------------
# 3. خدمات بوت التليجرام (Telegram Bot Logic)
# ----------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط فيديو من (TikTok, YouTube, Instagram...) وسأقوم بتحميله لك فوراً.")

async def download_telegram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return
    
    msg = await update.message.reply_text("⏳ جاري التحميل، يرجى الانتظار...")
    file_path = f"tg_{update.message.message_id}.mp4"

    try:
        loop = asyncio.get_event_loop()
        
        if "tiktok.com" in url:
            api_url = f"https://api.tiklydown.eu.org/api/download?url={url}"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                v_url = data.get('video', {}).get('noWatermark') or data.get('video', {}).get('watermark')
            
            v_req = urllib.request.Request(v_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(v_req, timeout=30) as v_resp, open(file_path, 'wb') as f:
                f.write(v_resp.read())
        else:
            ydl_opts = {'format': 'best', 'outtmpl': file_path, 'quiet': True, 'max_filesize': 50 * 1024 * 1024}
            await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))

        if os.path.exists(file_path):
            await update.message.reply_video(
                video=open(file_path, 'rb'),
                caption="✅ تم التحميل بنجاح عبر بوت المطور كهلان زيد الأشول"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ أثناء التحميل: {str(e)}")
    finally:
        await msg.delete()
        if os.path.exists(file_path):
            os.remove(file_path)

def start_bot():
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).request(request).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_telegram))
    telegram_app.run_polling()

# ----------------------------------------------------
# 4. تشغيل الموقع والبوت معاً
# ----------------------------------------------------
if __name__ == '__main__':
    # 1. تشغيل البوت في الخلفية (Thread)
    threading.Thread(target=start_bot, daemon=True).start()
    
    # 2. تشغيل خادم الموقع الرئيسي
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

