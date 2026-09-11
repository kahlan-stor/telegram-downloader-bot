import os
import re
import uuid
import threading
import shutil
from pathlib import Path

from flask import Flask, render_template_string, request, send_file
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# 🔑 توكن البوت
# =========================================================
# احذف كلمة "توكن" وضع التوكن الحقيقي مكانها
BOT_TOKEN = "توكن"


# =========================================================
# ⚙️ الإعدادات
# =========================================================
MAX_FILE_SIZE = 49 * 1024 * 1024
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# حفظ الرابط لكل مستخدم
user_sessions = {}


# =========================================================
# 🌐 واجهة الويب
# =========================================================
HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>مُنزّل الفيديوهات الذكي</title>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">

<style>

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Tajawal', sans-serif;
    min-height: 100vh;
    background:
        radial-gradient(circle at top right, #243b73 0, transparent 35%),
        radial-gradient(circle at bottom left, #172554 0, transparent 35%),
        #070b16;
    color: #fff;
    padding: 20px;
}

.container {
    width: 100%;
    max-width: 680px;
    margin: 45px auto;
}

.logo {
    width: 80px;
    height: 80px;
    margin: 0 auto 18px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    box-shadow: 0 15px 45px rgba(37,99,235,.35);
}

h1 {
    text-align: center;
    font-size: 28px;
    margin-bottom: 8px;
}

.subtitle {
    text-align: center;
    color: #94a3b8;
    margin-bottom: 25px;
}

.card {
    background: rgba(15, 23, 42, .82);
    border: 1px solid rgba(148,163,184,.15);
    border-radius: 24px;
    padding: 25px;
    backdrop-filter: blur(20px);
    box-shadow: 0 25px 70px rgba(0,0,0,.35);
}

label {
    display: block;
    margin-bottom: 9px;
    color: #cbd5e1;
    font-weight: 700;
}

input {
    width: 100%;
    height: 56px;
    padding: 0 17px;
    border-radius: 15px;
    border: 1px solid #334155;
    outline: none;
    background: #080d19;
    color: white;
    font-size: 15px;
    direction: ltr;
}

input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59,130,246,.12);
}

button {
    width: 100%;
    height: 56px;
    margin-top: 15px;
    border: 0;
    border-radius: 15px;
    color: white;
    font-family: inherit;
    font-size: 16px;
    font-weight: 800;
    cursor: pointer;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    transition: .2s;
}

button:hover {
    transform: translateY(-2px);
}

.features {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 20px;
}

.feature {
    padding: 15px;
    border-radius: 16px;
    background: rgba(30,41,59,.65);
    border: 1px solid rgba(148,163,184,.1);
    text-align: center;
    color: #cbd5e1;
}

.feature strong {
    display: block;
    color: white;
    margin-bottom: 5px;
}

.footer {
    text-align: center;
    color: #64748b;
    margin-top: 20px;
    font-size: 13px;
}

@media(max-width:500px) {
    .container {
        margin-top: 20px;
    }

    .card {
        padding: 18px;
    }

    h1 {
        font-size: 24px;
    }
}

</style>
</head>

<body>

<div class="container">

    <div class="logo">🎬</div>

    <h1>مُنزّل الفيديوهات الذكي</h1>

    <p class="subtitle">
        حمّل الفيديو أو الصوت بسهولة وبأفضل جودة متاحة
    </p>

    <div class="card">

        <form action="/download-web" method="post">

            <label>🔗 رابط الفيديو</label>

            <input
                type="url"
                name="url"
                placeholder="https://..."
                required
            >

            <button type="submit">
                ⬇️ تنزيل الفيديو
            </button>

        </form>

        <div class="features">

            <div class="feature">
                <strong>🎬 فيديو</strong>
                جودة متعددة
            </div>

            <div class="feature">
                <strong>🎵 صوت</strong>
                MP3
            </div>

            <div class="feature">
                <strong>⚡ سريع</strong>
                تحميل مباشر
            </div>

            <div class="feature">
                <strong>📱 جوال</strong>
                تصميم متجاوب
            </div>

        </div>

    </div>

    <div class="footer">
        يعمل بواسطة yt-dlp
    </div>

</div>

</body>
</html>
"""


# =========================================================
# 🌐 الصفحة الرئيسية
# =========================================================
@app.route("/")
def index():
    return render_template_string(HTML_LAYOUT)


# =========================================================
# 🌐 تحميل من الموقع
# =========================================================
@app.route("/download-web", methods=["POST"])
def web_download():

    url = request.form.get("url", "").strip()

    if not url.startswith(("http://", "https://")):
        return "❌ الرابط غير صحيح"

    file_id = uuid.uuid4().hex
    output = DOWNLOAD_DIR / f"{file_id}.%(ext)s"

    try:

        options = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": str(output),
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            final_path = Path(
                ydl.prepare_filename(info)
            )

            if not final_path.exists():

                candidates = list(
                    DOWNLOAD_DIR.glob(f"{file_id}.*")
                )

                if not candidates:
                    return "❌ لم يتم إنشاء الملف"

                final_path = candidates[0]

        return send_file(
            final_path,
            as_attachment=True,
            download_name=final_path.name
        )

    except Exception as e:
        return f"❌ حدث خطأ أثناء التحميل:<br><br>{str(e)}"

    finally:

        for file in DOWNLOAD_DIR.glob(f"{file_id}.*"):
            try:
                file.unlink()
            except Exception:
                pass


# =========================================================
# 🧹 تنظيف اسم الملف
# =========================================================
def safe_filename(name):

    name = re.sub(r'[\\\\/:*?"<>|]+', "_", name)
    name = name.strip()

    if not name:
        name = "video"

    return name[:80]


# =========================================================
# 📦 الحصول على الحجم
# =========================================================
def get_file_size(path):

    try:
        return os.path.getsize(path)
    except:
        return 0


# =========================================================
# 🤖 /start
# =========================================================
@bot.message_handler(commands=["start"])
def send_welcome(message):

    text = (
        "🎬 أهلاً بك في *مُنزّل الفيديوهات الذكي*\\n\\n"
        "أرسل رابط الفيديو وسأعرض لك الخيارات المتاحة:\\n\\n"
        "🎥 فيديو مع صوت\\n"
        "🎵 صوت فقط MP3\\n"
        "📺 جودات مختلفة"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown"
    )


# =========================================================
# 🔗 استقبال الرابط
# =========================================================
@bot.message_handler(
    func=lambda message:
    message.text and
    message.text.startswith(("http://", "https://"))
)
def process_video_link(message):

    chat_id = message.chat.id
    url = message.text.strip()

    loading = bot.reply_to(
        message,
        "🔍 جاري تحليل الرابط...\\n"
        "⏳ لحظات من فضلك"
    )

    try:

        options = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        user_sessions[chat_id] = {
            "url": url,
            "title": info.get("title", "فيديو"),
            "thumbnail": info.get("thumbnail"),
        }

        title = info.get("title", "فيديو")
        duration = info.get("duration")

        duration_text = ""

        if duration:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"\\n⏱ المدة: {minutes}:{seconds:02d}"

        qualities = []

        seen = set()

        for f in info.get("formats", []):

            height = f.get("height")
            vcodec = f.get("vcodec")

            if (
                height and
                vcodec and
                vcodec != "none" and
                height not in seen
            ):

                seen.add(height)
                qualities.append(height)

        qualities = sorted(
            qualities,
            reverse=True
        )

        markup = InlineKeyboardMarkup()

        row = []

        for height in qualities:

            if height > 2160:
                continue

            row.append(
                InlineKeyboardButton(
                    f"🎥 {height}p",
                    callback_data=f"video_{height}"
                )
            )

            if len(row) == 2:
                markup.add(*row)
                row = []

        if row:
            markup.add(*row)

        markup.add(
            InlineKeyboardButton(
                "🌟 أفضل جودة",
                callback_data="video_best"
            )
        )

        markup.add(
            InlineKeyboardButton(
                "🎵 صوت فقط MP3",
                callback_data="audio"
            )
        )

        text = (
            f"🎬 *{title[:100]}*"
            f"{duration_text}\\n\\n"
            "اختر نوع التحميل:"
        )

        bot.edit_message_text(
            text,
            chat_id,
            loading.message_id,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:

        bot.edit_message_text(
            f"❌ تعذر تحليل الرابط:\\n\\n{str(e)[:1000]}",
            chat_id,
            loading.message_id
        )


# =========================================================
# ❌ الروابط غير الصحيحة
# =========================================================
@bot.message_handler(func=lambda message: True)
def invalid_message(message):

    bot.reply_to(
        message,
        "⚠️ أرسل رابط فيديو يبدأ بـ http أو https."
    )


# =========================================================
# 🎛️ أزرار التحميل
# =========================================================
@bot.callback_query_handler(
    func=lambda call: True
)
def callback_download(call):

    chat_id = call.message.chat.id
    session = user_sessions.get(chat_id)

    if not session:

        bot.answer_callback_query(
            call.id,
            "❌ انتهت الجلسة، أرسل الرابط مرة أخرى."
        )
        return

    url = session["url"]
    data = call.data

    bot.answer_callback_query(
        call.id,
        "⏳ جاري التحميل..."
    )

    try:

        bot.edit_message_text(
            "⏳ *جاري تجهيز الملف...*\\n\\n"
            "📥 يتم تنزيل الفيديو الآن...",
            chat_id,
            call.message.message_id,
            parse_mode="Markdown"
        )

        file_id = uuid.uuid4().hex

        # =================================================
        # 🎵 تحميل الصوت
        # =================================================
        if data == "audio":

            output = DOWNLOAD_DIR / f"{file_id}.%(ext)s"

            options = {
                "format": "bestaudio/best",
                "outtmpl": str(output),
                "quiet": True,
                "noplaylist": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(
                    url,
                    download=True
                )

            files = list(
                DOWNLOAD_DIR.glob(f"{file_id}.*")
            )

            if not files:
                raise Exception(
                    "لم يتم إنشاء ملف الصوت."
                )

            file_path = files[0]

            if get_file_size(file_path) > MAX_FILE_SIZE:
                raise Exception(
                    "حجم الملف أكبر من الحد المسموح به في البوت."
                )

            title = safe_filename(
                info.get("title", "audio")
            )

            final_name = f"{title}.mp3"

            with open(file_path, "rb") as audio:

                bot.send_audio(
                    chat_id,
                    audio,
                    caption="🎵 تم تحميل الصوت بنجاح",
                    title=title[:64]
                )

        # =================================================
        # 🎥 تحميل الفيديو
        # =================================================
        else:

            output = DOWNLOAD_DIR / f"{file_id}.%(ext)s"

            if data == "video_best":

                fmt = (
                    "bestvideo[ext=mp4]+"
                    "bestaudio[ext=m4a]/"
                    "best[ext=mp4]/best"
                )

            else:

                height = data.replace(
                    "video_",
                    ""
                )

                fmt = (
                    f"bestvideo[height<={height}]"
                    f"[ext=mp4]+"
                    f"bestaudio[ext=m4a]/"
                    f"best[height<={height}]"
                    f"[ext=mp4]/best"
                )

            options = {
                "format": fmt,
                "merge_output_format": "mp4",
                "outtmpl": str(output),
                "quiet": True,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(options) as ydl:

                info = ydl.extract_info(
                    url,
                    download=True
                )

                prepared = Path(
                    ydl.prepare_filename(info)
                )

            files = list(
                DOWNLOAD_DIR.glob(f"{file_id}.*")
            )

            if prepared.exists():
                file_path = prepared
            elif files:
                file_path = files[0]
            else:
                raise Exception(
                    "لم يتم إنشاء ملف الفيديو."
                )

            # محاولة إيجاد MP4 بعد الدمج
            mp4_files = list(
                DOWNLOAD_DIR.glob(
                    f"{file_id}*.mp4"
                )
            )

            if mp4_files:
                file_path = mp4_files[0]

            if get_file_size(file_path) > MAX_FILE_SIZE:

                bot.send_message(
                    chat_id,
                    "❌ الفيديو أكبر من الحد المسموح به للإرسال عبر البوت.\\n"
                    "جرّب اختيار جودة أقل."
                )

                return

            with open(file_path, "rb") as video:

                bot.send_video(
                    chat_id,
                    video,
                    supports_streaming=True,
                    caption="🎬 تم تحميل الفيديو بنجاح"
                )

        try:
            bot.delete_message(
                chat_id,
                call.message.message_id
            )
        except:
            pass

    except Exception as e:

        bot.send_message(
            chat_id,
            "❌ *تعذر تحميل الملف*\\n\\n"
            f"`{str(e)[:1500]}`",
            parse_mode="Markdown"
        )

    finally:

        # تنظيف الملفات المؤقتة
        for file in DOWNLOAD_DIR.glob(
            f"{file_id}.*"
        ):
            try:
                file.unlink()
            except:
                pass


# =========================================================
# 🧹 تنظيف الملفات القديمة
# =========================================================
def cleanup_old_files():

    for file in DOWNLOAD_DIR.iterdir():

        try:

            if file.is_file():

                age = (
                    __import__("time").time()
                    - file.stat().st_mtime
                )

                if age > 3600:
                    file.unlink()

        except:
            pass


# =========================================================
# 🤖 تشغيل البوت
# =========================================================
def start_bot():

    print("🤖 تشغيل بوت Telegram...")

    while True:

        try:

            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )

        except Exception as e:

            print(
                f"❌ خطأ في البوت: {e}"
            )

            import time
            time.sleep(5)


# =========================================================
# 🚀 تشغيل
# =========================================================
if __name__ == "__main__":

    if BOT_TOKEN == "8294576614:AAFQeLslZLrYyM4TRoP0kyQ_9qwBk0ztrj0":

        print(
            "⚠️ ضع توكن البوت في المتغير BOT_TOKEN أولاً."
        )

    else:

        bot_thread = threading.Thread(
            target=start_bot,
            daemon=True
        )

        bot_thread.start()

    port = int(
        os.environ.get(
            "PORT",
            8080
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
                                         )
