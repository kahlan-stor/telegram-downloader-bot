import os
import re
import uuid
import time
import threading
from pathlib import Path

from flask import Flask, render_template_string, request, send_file
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")

MAX_FILE_SIZE = 49 * 1024 * 1024
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

DEVELOPER_NAME = "كهلان زيد الاشول"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_sessions = {}


# =========================================================
# واجهة الموقع
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">

<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>KM Downloader</title>

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
    font-family: "Tajawal", sans-serif;
    min-height: 100vh;
    background:
        radial-gradient(circle at top, #243b67 0%, transparent 35%),
        linear-gradient(135deg, #070b16, #10182c 55%, #070b16);
    color: white;
    overflow-x: hidden;
}


/* =====================================================
   شاشة البداية
   ===================================================== */

#splash {
    position: fixed;
    inset: 0;
    z-index: 9999;

    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;

    background:
        radial-gradient(circle, #172a52 0%, #070b16 65%);
}

.logo-heart {
    width: 330px;
    height: 280px;

    display: flex;
    align-items: center;
    justify-content: center;

    position: relative;

    font-family: monospace;
    font-weight: bold;
    font-size: 15px;
    line-height: 14px;

    white-space: pre;

    color: #fff;

    text-shadow:
        0 0 5px #fff,
        0 0 15px #5d8cff,
        0 0 30px #5d8cff;

    animation: heartGlow 1.5s infinite alternate;
}

@keyframes heartGlow {
    from {
        filter: drop-shadow(0 0 5px #477cff);
    }

    to {
        filter: drop-shadow(0 0 25px #6d94ff);
    }
}

.splash-title {
    margin-top: 25px;
    font-size: 26px;
    font-weight: 800;
}

.splash-subtitle {
    margin-top: 8px;
    color: #aebbd8;
    font-size: 14px;
}


/* =====================================================
   التطبيق
   ===================================================== */

#app {
    display: none;
    min-height: 100vh;
}

.container {
    width: min(920px, 92%);
    margin: auto;
    padding: 35px 0;
}


/* Header */

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: 18px 20px;

    border: 1px solid rgba(255,255,255,.08);
    border-radius: 22px;

    background: rgba(255,255,255,.05);
    backdrop-filter: blur(20px);

    box-shadow: 0 20px 50px rgba(0,0,0,.25);
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-logo {
    width: 48px;
    height: 48px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 15px;

    background: linear-gradient(135deg,#4d7cff,#795cff);

    font-size: 18px;
    font-weight: 900;

    box-shadow: 0 8px 30px rgba(76,110,255,.35);
}

.brand-text h1 {
    font-size: 19px;
}

.brand-text p {
    font-size: 12px;
    color: #9aa8c4;
}


/* Main */

.hero {
    text-align: center;
    padding: 60px 10px 35px;
}

.hero h2 {
    font-size: clamp(28px, 7vw, 48px);
    font-weight: 800;

    background: linear-gradient(90deg,#fff,#9db9ff);
    -webkit-background-clip: text;
    color: transparent;
}

.hero p {
    margin-top: 14px;
    color: #aab5ca;
    font-size: 15px;
}


/* Card */

.download-card {
    padding: 28px;

    border-radius: 28px;

    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.09);

    backdrop-filter: blur(25px);

    box-shadow:
        0 25px 80px rgba(0,0,0,.35);
}

.input-title {
    font-weight: 700;
    margin-bottom: 10px;
}

.url-box {
    display: flex;
    gap: 10px;

    padding: 8px;

    border-radius: 18px;

    background: rgba(0,0,0,.25);

    border: 1px solid rgba(255,255,255,.08);
}

.url-box input {
    flex: 1;

    min-width: 0;

    border: 0;
    outline: 0;

    padding: 15px;

    color: white;

    background: transparent;

    font-family: inherit;
    font-size: 15px;
}

.url-box input::placeholder {
    color: #69758d;
}

.download-btn {
    border: 0;

    padding: 0 25px;

    border-radius: 14px;

    color: white;

    font-family: inherit;
    font-weight: 700;

    background: linear-gradient(135deg,#557fff,#7658ff);

    cursor: pointer;

    transition: .25s;
}

.download-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(82,110,255,.35);
}


/* Options */

.options {
    display: grid;

    grid-template-columns: repeat(2,1fr);

    gap: 14px;

    margin-top: 18px;
}

.option {
    padding: 20px;

    border-radius: 20px;

    background: rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.07);

    cursor: pointer;

    transition: .25s;
}

.option:hover {
    background: rgba(255,255,255,.08);
    transform: translateY(-3px);
}

.option-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

.option-title {
    font-weight: 700;
}

.option-desc {
    color: #8996b0;
    font-size: 12px;
    margin-top: 4px;
}


/* Loading */

#loading {
    display: none;

    text-align: center;

    margin-top: 25px;

    padding: 22px;

    border-radius: 18px;

    background: rgba(79,111,255,.08);
}

.spinner {
    width: 38px;
    height: 38px;

    margin: 0 auto 12px;

    border: 3px solid rgba(255,255,255,.15);
    border-top-color: #6d8fff;

    border-radius: 50%;

    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}


/* Footer */

.footer {
    text-align: center;

    margin-top: 30px;

    color: #69758d;

    font-size: 12px;
}

.footer strong {
    color: #aebeff;
}


/* Mobile */

@media(max-width:650px) {

    .container {
        width: 94%;
        padding-top: 18px;
    }

    .url-box {
        flex-direction: column;
    }

    .download-btn {
        min-height: 52px;
    }

    .options {
        grid-template-columns: 1fr;
    }

    .download-card {
        padding: 20px;
    }

    .hero {
        padding-top: 40px;
    }

    .logo-heart {
        transform: scale(.8);
    }
}

</style>
</head>


<body>


<!-- =====================================================
     SPLASH
     ===================================================== -->

<div id="splash">

    <div id="heart" class="logo-heart"></div>

    <div class="splash-title">
        KM Downloader
    </div>

    <div class="splash-subtitle">
        جاري تجهيز أداة التحميل...
    </div>

</div>


<!-- =====================================================
     APP
     ===================================================== -->

<div id="app">

<div class="container">


    <header class="header">

        <div class="brand">

            <div class="brand-logo">
                KM
            </div>

            <div class="brand-text">

                <h1>KM Downloader</h1>

                <p>
                    أداة تحميل الوسائط
                </p>

            </div>

        </div>

    </header>


    <section class="hero">

        <h2>
            حمّل ما تريد بسهولة
        </h2>

        <p>
            فيديو أو صوت بجودة عالية من الرابط مباشرة
        </p>

    </section>


    <section class="download-card">

        <div class="input-title">
            🔗 رابط الفيديو
        </div>


        <div class="url-box">

            <input
                id="url"
                type="url"
                placeholder="ألصق رابط الفيديو هنا..."
                autocomplete="off"
            >

            <button
                class="download-btn"
                onclick="downloadMedia()"
            >
                تحميل
            </button>

        </div>


        <div class="options">

            <div
                class="option"
                onclick="downloadMedia('video')"
            >

                <div class="option-icon">
                    🎬
                </div>

                <div class="option-title">
                    تحميل فيديو
                </div>

                <div class="option-desc">
                    أفضل جودة فيديو متاحة
                </div>

            </div>


            <div
                class="option"
                onclick="downloadMedia('audio')"
            >

                <div class="option-icon">
                    🎵
                </div>

                <div class="option-title">
                    تحميل كصوت
                </div>

                <div class="option-desc">
                    استخراج الصوت بصيغة MP3
                </div>

            </div>

        </div>


        <div id="loading">

            <div class="spinner"></div>

            <div>
                جاري تجهيز الملف...
            </div>

        </div>

    </section>


    <footer class="footer">

        المطور
        <strong>
            كهلان زيد الاشول
        </strong>

    </footer>


</div>

</div>


<script>

/* =====================================================
   قلب KM
   ===================================================== */

const heartPattern = [
"      KM KM       ",
"    KM     KM     ",
"   KM       KM    ",
"  KM         KM   ",
" KM           KM  ",
"KM             KM ",
"KM             KM ",
" KM           KM  ",
"  KM         KM   ",
"   KM       KM    ",
"    KM     KM     ",
"      KM KM       ",
"        KM        "
];

const heart = document.getElementById("heart");

let row = 0;
let col = 0;

function drawHeart() {

    if (row >= heartPattern.length) {

        setTimeout(() => {

            document.getElementById("splash").style.opacity = "0";
            document.getElementById("splash").style.transition = "opacity .7s";

            setTimeout(() => {

                document.getElementById("splash").style.display = "none";
                document.getElementById("app").style.display = "block";

            }, 700);

        }, 700);

        return;
    }


    const current = heartPattern[row];

    if (col >= current.length) {

        row++;
        col = 0;

        heart.innerHTML += "<br>";

        setTimeout(drawHeart, 30);

        return;
    }


    const char = current[col];

    if (char === "K" || char === "M") {

        heart.innerHTML += char;

    } else {

        heart.innerHTML += "&nbsp;";

    }

    col++;

    setTimeout(drawHeart, 12);
}

drawHeart();


/* =====================================================
   تحميل
   ===================================================== */

function downloadMedia(type) {

    const url = document.getElementById("url").value.trim();

    if (!url) {

        alert("ضع رابط الفيديو أولاً");

        return;
    }


    document.getElementById("loading").style.display = "block";


    const form = document.createElement("form");

    form.method = "POST";
    form.action = "/download-web";

    const urlInput = document.createElement("input");

    urlInput.type = "hidden";
    urlInput.name = "url";
    urlInput.value = url;

    form.appendChild(urlInput);


    const typeInput = document.createElement("input");

    typeInput.type = "hidden";
    typeInput.name = "type";
    typeInput.value = type || "video";

    form.appendChild(typeInput);


    document.body.appendChild(form);

    form.submit();
}

</script>

</body>
</html>
"""


# =========================================================
# أدوات مساعدة
# =========================================================

def is_valid_url(url):
    return bool(
        re.match(
            r"^https?://",
            url,
            re.IGNORECASE
        )
    )


def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:150]


def find_downloaded_file(stem):
    files = list(
        DOWNLOAD_DIR.glob(f"{stem}.*")
    )

    if not files:
        return None

    files.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    return files[0]


# =========================================================
# إعدادات yt-dlp
# =========================================================

def base_ydl_options():

    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,

        # لا نستخدم صيغة ثابتة تسبب الخطأ
        # ونترك yt-dlp يختار أفضل صيغة متاحة.
        "retries": 3,
        "fragment_retries": 3,

        "socket_timeout": 30,

        "http_headers": {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
        }
    }


# =========================================================
# تنزيل الفيديو
# =========================================================

def download_video(url, output_path):

    options = base_ydl_options()

    options.update({

        # الأولوية:
        # فيديو + صوت
        # ثم أفضل ملف منفرد إذا لم تتوفر المسارات المنفصلة
        #
        # علامة ? تجعل الاختيار أكثر مرونة مع الصيغ التي
        # تكون بعض خصائصها غير معروفة.
        "format":
            "bv*+ba/b[ext=mp4]/b*",

        "merge_output_format": "mp4",

        "outtmpl": str(output_path),

        "overwrites": True,

        "restrictfilenames": False,

        "postprocessors": []
    })


    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        return info


# =========================================================
# تنزيل الصوت MP3
# =========================================================

def download_audio(url, output_path):

    options = base_ydl_options()

    options.update({

        "format":
            "ba/b[acodec!=none]/b*",

        "outtmpl":
            str(output_path),

        "postprocessors": [

            {
                "key":
                    "FFmpegExtractAudio",

                "preferredcodec":
                    "mp3",

                "preferredquality":
                    "192"
            }

        ]
    })


    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        return info


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def index():

    return render_template_string(HTML)


# =========================================================
# تحميل من الموقع
# =========================================================

@app.route(
    "/download-web",
    methods=["POST"]
)
def download_web():

    url = request.form.get(
        "url",
        ""
    ).strip()

    media_type = request.form.get(
        "type",
        "video"
    )


    if not is_valid_url(url):

        return """
        <script>
        alert("الرابط غير صحيح");
        history.back();
        </script>
        """


    job_id = uuid.uuid4().hex

    safe_name = f"download_{job_id}"

    output = DOWNLOAD_DIR / safe_name


    try:

        if media_type == "audio":

            output = output.with_suffix(".%(ext)s")

            info = download_audio(
                url,
                output
            )

            downloaded = find_downloaded_file(
                safe_name
            )

            if not downloaded:

                raise Exception(
                    "لم يتم العثور على ملف الصوت"
                )


        else:

            output = output.with_suffix(".%(ext)s")

            info = download_video(
                url,
                output
            )

            downloaded = find_downloaded_file(
                safe_name
            )

            if not downloaded:

                raise Exception(
                    "لم يتم العثور على ملف الفيديو"
                )


        if downloaded.stat().st_size > MAX_FILE_SIZE:

            downloaded.unlink(
                missing_ok=True
            )

            return """
            <script>
            alert("الملف أكبر من الحد المسموح به للإرسال");
            history.back();
            </script>
            """


        if media_type == "audio":

            mimetype = "audio/mpeg"

        else:

            mimetype = "video/mp4"


        return send_file(
            downloaded,
            as_attachment=True,
            download_name=(
                clean_filename(
                    info.get("title", "download")
                )
                + (
                    ".mp3"
                    if media_type == "audio"
                    else ".mp4"
                )
            ),
            mimetype=mimetype
        )


    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            repr(e)
        )

        return f"""
        <!DOCTYPE html>

        <html lang="ar" dir="rtl">

        <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width,initial-scale=1">

        <style>

        body {{
            background:#090d18;
            color:white;
            font-family:Arial;
            text-align:center;
            padding:60px 20px;
        }}

        .box {{
            max-width:600px;
            margin:auto;
            padding:30px;
            border-radius:25px;
            background:#151d31;
        }}

        h2 {{
            color:#ff6b7a;
        }}

        p {{
            color:#aeb8cb;
            line-height:1.8;
        }}

        button {{
            padding:14px 25px;
            border:0;
            border-radius:12px;
            background:#557cff;
            color:white;
            font-weight:bold;
            cursor:pointer;
        }}

        </style>

        </head>

        <body>

        <div class="box">

        <h2>❌ حدث خطأ أثناء التحميل</h2>

        <p>
        تعذر تحميل هذا الرابط حاليًا.
        </p>

        <p>
        قد يكون الموقع المصدر قد طلب تسجيل الدخول
        أو وضع حدًا مؤقتًا للطلبات.
        </p>

        <button onclick="history.back()">
        ↩ العودة
        </button>

        </div>

        </body>

        </html>
        """


# =========================================================
# Telegram
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    text = f"""
👋 أهلاً بك في KM Downloader

🎬 تحميل فيديو
🎵 تحميل صوت MP3
⚡ اختيار أفضل جودة متاحة تلقائيًا

👨‍💻 المطور:
{DEVELOPER_NAME}

أرسل رابط الفيديو الآن.
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# رابط Telegram
# =========================================================

@bot.message_handler(
    func=lambda message:
        bool(
            message.text
            and is_valid_url(
                message.text.strip()
            )
        )
)
def receive_url(message):

    url = message.text.strip()

    try:

        bot.send_chat_action(
            message.chat.id,
            "typing"
        )

        options = base_ydl_options()

        options["skip_download"] = True

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )


        title = info.get(
            "title",
            "فيديو"
        )

        user_sessions[
            message.chat.id
        ] = {

            "url": url,

            "title": title
        }


        keyboard = InlineKeyboardMarkup(
            row_width=2
        )


        keyboard.add(

            InlineKeyboardButton(
                "🎬 أفضل جودة",
                callback_data="download_best"
            ),

            InlineKeyboardButton(
                "🎵 صوت MP3",
                callback_data="download_audio"
            )
        )


        # استخراج الجودات الموجودة فعليًا
        heights = set()

        for fmt in info.get(
            "formats",
            []
        ):

            height = fmt.get("height")

            vcodec = fmt.get(
                "vcodec"
            )

            if (
                height
                and height >= 144
                and vcodec
                and vcodec != "none"
            ):

                heights.add(
                    int(height)
                )


        selected = sorted(
            heights,
            reverse=True
        )[:8]


        for height in selected:

            keyboard.add(

                InlineKeyboardButton(
                    f"🎥 {height}p",
                    callback_data=
                        f"download_{height}"
                )
            )


        bot.send_message(

            message.chat.id,

            f"🎬 {title}\n\n"
            "اختر نوع التحميل:",

            reply_markup=keyboard
        )


    except Exception as e:

        print(
            "INFO ERROR:",
            repr(e)
        )

        bot.send_message(

            message.chat.id,

            "❌ تعذر قراءة الرابط حاليًا.\n"
            "تأكد من أن الرابط عام ويمكن الوصول إليه."
        )


# =========================================================
# أزرار Telegram
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("download_")
)
def callback_download(call):

    chat_id = call.message.chat.id

    session = user_sessions.get(
        chat_id
    )


    if not session:

        bot.answer_callback_query(
            call.id,
            "انتهت جلسة التحميل، أرسل الرابط مرة أخرى."
        )

        return


    url = session["url"]

    action = call.data.replace(
        "download_",
        ""
    )


    bot.answer_callback_query(
        call.id,
        "جاري التحميل..."
    )


    status = bot.send_message(
        chat_id,
        "⏳ جاري تجهيز الملف..."
    )


    job_id = uuid.uuid4().hex

    stem = DOWNLOAD_DIR / job_id


    try:

        if action == "audio":

            output = stem.with_suffix(
                ".%(ext)s"
            )

            info = download_audio(
                url,
                output
            )

            downloaded = find_downloaded_file(
                job_id
            )

            if not downloaded:

                raise Exception(
                    "ملف الصوت غير موجود"
                )


            if downloaded.stat().st_size > MAX_FILE_SIZE:

                raise Exception(
                    "حجم ملف الصوت أكبر من الحد المسموح"
                )


            bot.delete_message(
                chat_id,
                status.message_id
            )


            with open(
                downloaded,
                "rb"
            ) as audio:

                bot.send_audio(
                    chat_id,
                    audio,
                    title=info.get(
                        "title",
                        "Audio"
                    ),
                    performer=DEVELOPER_NAME
                )


        else:

            output = stem.with_suffix(
                ".%(ext)s"
            )


            if action == "best":

                format_selector = (
                    "bv*+ba/b[ext=mp4]/b*"
                )

            else:

                try:
                    height = int(action)

                    # ? يسمح بتعامل أكثر مرونة مع
                    # الخصائص غير المعروفة.
                    format_selector = (
                        f"import os
import re
import uuid
import time
import threading
from pathlib import Path

from flask import Flask, render_template_string, request, send_file
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# إعدادات البوت
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")

MAX_FILE_SIZE = 49 * 1024 * 1024
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

DEVELOPER_NAME = "كهلان زيد الاشول"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_sessions = {}


# =========================================================
# واجهة الموقع
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">

<head>
<meta charset="UTF-8">
<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>KM Downloader</title>

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
    font-family: "Tajawal", sans-serif;
    min-height: 100vh;
    background:
        radial-gradient(circle at top, #243b67 0%, transparent 35%),
        linear-gradient(135deg, #070b16, #10182c 55%, #070b16);
    color: white;
    overflow-x: hidden;
}


/* =====================================================
   شاشة البداية
   ===================================================== */

#splash {
    position: fixed;
    inset: 0;
    z-index: 9999;

    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;

    background:
        radial-gradient(circle, #172a52 0%, #070b16 65%);
}

.logo-heart {
    width: 330px;
    height: 280px;

    display: flex;
    align-items: center;
    justify-content: center;

    position: relative;

    font-family: monospace;
    font-weight: bold;
    font-size: 15px;
    line-height: 14px;

    white-space: pre;

    color: #fff;

    text-shadow:
        0 0 5px #fff,
        0 0 15px #5d8cff,
        0 0 30px #5d8cff;

    animation: heartGlow 1.5s infinite alternate;
}

@keyframes heartGlow {
    from {
        filter: drop-shadow(0 0 5px #477cff);
    }

    to {
        filter: drop-shadow(0 0 25px #6d94ff);
    }
}

.splash-title {
    margin-top: 25px;
    font-size: 26px;
    font-weight: 800;
}

.splash-subtitle {
    margin-top: 8px;
    color: #aebbd8;
    font-size: 14px;
}


/* =====================================================
   التطبيق
   ===================================================== */

#app {
    display: none;
    min-height: 100vh;
}

.container {
    width: min(920px, 92%);
    margin: auto;
    padding: 35px 0;
}


/* Header */

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    padding: 18px 20px;

    border: 1px solid rgba(255,255,255,.08);
    border-radius: 22px;

    background: rgba(255,255,255,.05);
    backdrop-filter: blur(20px);

    box-shadow: 0 20px 50px rgba(0,0,0,.25);
}

.brand {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-logo {
    width: 48px;
    height: 48px;

    display: flex;
    align-items: center;
    justify-content: center;

    border-radius: 15px;

    background: linear-gradient(135deg,#4d7cff,#795cff);

    font-size: 18px;
    font-weight: 900;

    box-shadow: 0 8px 30px rgba(76,110,255,.35);
}

.brand-text h1 {
    font-size: 19px;
}

.brand-text p {
    font-size: 12px;
    color: #9aa8c4;
}


/* Main */

.hero {
    text-align: center;
    padding: 60px 10px 35px;
}

.hero h2 {
    font-size: clamp(28px, 7vw, 48px);
    font-weight: 800;

    background: linear-gradient(90deg,#fff,#9db9ff);
    -webkit-background-clip: text;
    color: transparent;
}

.hero p {
    margin-top: 14px;
    color: #aab5ca;
    font-size: 15px;
}


/* Card */

.download-card {
    padding: 28px;

    border-radius: 28px;

    background: rgba(255,255,255,.055);
    border: 1px solid rgba(255,255,255,.09);

    backdrop-filter: blur(25px);

    box-shadow:
        0 25px 80px rgba(0,0,0,.35);
}

.input-title {
    font-weight: 700;
    margin-bottom: 10px;
}

.url-box {
    display: flex;
    gap: 10px;

    padding: 8px;

    border-radius: 18px;

    background: rgba(0,0,0,.25);

    border: 1px solid rgba(255,255,255,.08);
}

.url-box input {
    flex: 1;

    min-width: 0;

    border: 0;
    outline: 0;

    padding: 15px;

    color: white;

    background: transparent;

    font-family: inherit;
    font-size: 15px;
}

.url-box input::placeholder {
    color: #69758d;
}

.download-btn {
    border: 0;

    padding: 0 25px;

    border-radius: 14px;

    color: white;

    font-family: inherit;
    font-weight: 700;

    background: linear-gradient(135deg,#557fff,#7658ff);

    cursor: pointer;

    transition: .25s;
}

.download-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(82,110,255,.35);
}


/* Options */

.options {
    display: grid;

    grid-template-columns: repeat(2,1fr);

    gap: 14px;

    margin-top: 18px;
}

.option {
    padding: 20px;

    border-radius: 20px;

    background: rgba(255,255,255,.035);

    border: 1px solid rgba(255,255,255,.07);

    cursor: pointer;

    transition: .25s;
}

.option:hover {
    background: rgba(255,255,255,.08);
    transform: translateY(-3px);
}

.option-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

.option-title {
    font-weight: 700;
}

.option-desc {
    color: #8996b0;
    font-size: 12px;
    margin-top: 4px;
}


/* Loading */

#loading {
    display: none;

    text-align: center;

    margin-top: 25px;

    padding: 22px;

    border-radius: 18px;

    background: rgba(79,111,255,.08);
}

.spinner {
    width: 38px;
    height: 38px;

    margin: 0 auto 12px;

    border: 3px solid rgba(255,255,255,.15);
    border-top-color: #6d8fff;

    border-radius: 50%;

    animation: spin 1s linear infinite;
}

@keyframes spin {
    to {
        transform: rotate(360deg);
    }
}


/* Footer */

.footer {
    text-align: center;

    margin-top: 30px;

    color: #69758d;

    font-size: 12px;
}

.footer strong {
    color: #aebeff;
}


/* Mobile */

@media(max-width:650px) {

    .container {
        width: 94%;
        padding-top: 18px;
    }

    .url-box {
        flex-direction: column;
    }

    .download-btn {
        min-height: 52px;
    }

    .options {
        grid-template-columns: 1fr;
    }

    .download-card {
        padding: 20px;
    }

    .hero {
        padding-top: 40px;
    }

    .logo-heart {
        transform: scale(.8);
    }
}

</style>
</head>


<body>


<!-- =====================================================
     SPLASH
     ===================================================== -->

<div id="splash">

    <div id="heart" class="logo-heart"></div>

    <div class="splash-title">
        KM Downloader
    </div>

    <div class="splash-subtitle">
        جاري تجهيز أداة التحميل...
    </div>

</div>


<!-- =====================================================
     APP
     ===================================================== -->

<div id="app">

<div class="container">


    <header class="header">

        <div class="brand">

            <div class="brand-logo">
                KM
            </div>

            <div class="brand-text">

                <h1>KM Downloader</h1>

                <p>
                    أداة تحميل الوسائط
                </p>

            </div>

        </div>

    </header>


    <section class="hero">

        <h2>
            حمّل ما تريد بسهولة
        </h2>

        <p>
            فيديو أو صوت بجودة عالية من الرابط مباشرة
        </p>

    </section>


    <section class="download-card">

        <div class="input-title">
            🔗 رابط الفيديو
        </div>


        <div class="url-box">

            <input
                id="url"
                type="url"
                placeholder="ألصق رابط الفيديو هنا..."
                autocomplete="off"
            >

            <button
                class="download-btn"
                onclick="downloadMedia()"
            >
                تحميل
            </button>

        </div>


        <div class="options">

            <div
                class="option"
                onclick="downloadMedia('video')"
            >

                <div class="option-icon">
                    🎬
                </div>

                <div class="option-title">
                    تحميل فيديو
                </div>

                <div class="option-desc">
                    أفضل جودة فيديو متاحة
                </div>

            </div>


            <div
                class="option"
                onclick="downloadMedia('audio')"
            >

                <div class="option-icon">
                    🎵
                </div>

                <div class="option-title">
                    تحميل كصوت
                </div>

                <div class="option-desc">
                    استخراج الصوت بصيغة MP3
                </div>

            </div>

        </div>


        <div id="loading">

            <div class="spinner"></div>

            <div>
                جاري تجهيز الملف...
            </div>

        </div>

    </section>


    <footer class="footer">

        المطور
        <strong>
            كهلان زيد الاشول
        </strong>

    </footer>


</div>

</div>


<script>

/* =====================================================
   قلب KM
   ===================================================== */

const heartPattern = [
"      KM KM       ",
"    KM     KM     ",
"   KM       KM    ",
"  KM         KM   ",
" KM           KM  ",
"KM             KM ",
"KM             KM ",
" KM           KM  ",
"  KM         KM   ",
"   KM       KM    ",
"    KM     KM     ",
"      KM KM       ",
"        KM        "
];

const heart = document.getElementById("heart");

let row = 0;
let col = 0;

function drawHeart() {

    if (row >= heartPattern.length) {

        setTimeout(() => {

            document.getElementById("splash").style.opacity = "0";
            document.getElementById("splash").style.transition = "opacity .7s";

            setTimeout(() => {

                document.getElementById("splash").style.display = "none";
                document.getElementById("app").style.display = "block";

            }, 700);

        }, 700);

        return;
    }


    const current = heartPattern[row];

    if (col >= current.length) {

        row++;
        col = 0;

        heart.innerHTML += "<br>";

        setTimeout(drawHeart, 30);

        return;
    }


    const char = current[col];

    if (char === "K" || char === "M") {

        heart.innerHTML += char;

    } else {

        heart.innerHTML += "&nbsp;";

    }

    col++;

    setTimeout(drawHeart, 12);
}

drawHeart();


/* =====================================================
   تحميل
   ===================================================== */

function downloadMedia(type) {

    const url = document.getElementById("url").value.trim();

    if (!url) {

        alert("ضع رابط الفيديو أولاً");

        return;
    }


    document.getElementById("loading").style.display = "block";


    const form = document.createElement("form");

    form.method = "POST";
    form.action = "/download-web";

    const urlInput = document.createElement("input");

    urlInput.type = "hidden";
    urlInput.name = "url";
    urlInput.value = url;

    form.appendChild(urlInput);


    const typeInput = document.createElement("input");

    typeInput.type = "hidden";
    typeInput.name = "type";
    typeInput.value = type || "video";

    form.appendChild(typeInput);


    document.body.appendChild(form);

    form.submit();
}

</script>

</body>
</html>
"""


# =========================================================
# أدوات مساعدة
# =========================================================

def is_valid_url(url):
    return bool(
        re.match(
            r"^https?://",
            url,
            re.IGNORECASE
        )
    )


def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:150]


def find_downloaded_file(stem):
    files = list(
        DOWNLOAD_DIR.glob(f"{stem}.*")
    )

    if not files:
        return None

    files.sort(
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    return files[0]


# =========================================================
# إعدادات yt-dlp
# =========================================================

def base_ydl_options():

    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,

        # لا نستخدم صيغة ثابتة تسبب الخطأ
        # ونترك yt-dlp يختار أفضل صيغة متاحة.
        "retries": 3,
        "fragment_retries": 3,

        "socket_timeout": 30,

        "http_headers": {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
        }
    }


# =========================================================
# تنزيل الفيديو
# =========================================================

def download_video(url, output_path):

    options = base_ydl_options()

    options.update({

        # الأولوية:
        # فيديو + صوت
        # ثم أفضل ملف منفرد إذا لم تتوفر المسارات المنفصلة
        #
        # علامة ? تجعل الاختيار أكثر مرونة مع الصيغ التي
        # تكون بعض خصائصها غير معروفة.
        "format":
            "bv*+ba/b[ext=mp4]/b*",

        "merge_output_format": "mp4",

        "outtmpl": str(output_path),

        "overwrites": True,

        "restrictfilenames": False,

        "postprocessors": []
    })


    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        return info


# =========================================================
# تنزيل الصوت MP3
# =========================================================

def download_audio(url, output_path):

    options = base_ydl_options()

    options.update({

        "format":
            "ba/b[acodec!=none]/b*",

        "outtmpl":
            str(output_path),

        "postprocessors": [

            {
                "key":
                    "FFmpegExtractAudio",

                "preferredcodec":
                    "mp3",

                "preferredquality":
                    "192"
            }

        ]
    })


    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True
        )

        return info


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def index():

    return render_template_string(HTML)


# =========================================================
# تحميل من الموقع
# =========================================================

@app.route(
    "/download-web",
    methods=["POST"]
)
def download_web():

    url = request.form.get(
        "url",
        ""
    ).strip()

    media_type = request.form.get(
        "type",
        "video"
    )


    if not is_valid_url(url):

        return """
        <script>
        alert("الرابط غير صحيح");
        history.back();
        </script>
        """


    job_id = uuid.uuid4().hex

    safe_name = f"download_{job_id}"

    output = DOWNLOAD_DIR / safe_name


    try:

        if media_type == "audio":

            output = output.with_suffix(".%(ext)s")

            info = download_audio(
                url,
                output
            )

            downloaded = find_downloaded_file(
                safe_name
            )

            if not downloaded:

                raise Exception(
                    "لم يتم العثور على ملف الصوت"
                )


        else:

            output = output.with_suffix(".%(ext)s")

            info = download_video(
                url,
                output
            )

            downloaded = find_downloaded_file(
                safe_name
            )

            if not downloaded:

                raise Exception(
                    "لم يتم العثور على ملف الفيديو"
                )


        if downloaded.stat().st_size > MAX_FILE_SIZE:

            downloaded.unlink(
                missing_ok=True
            )

            return """
            <script>
            alert("الملف أكبر من الحد المسموح به للإرسال");
            history.back();
            </script>
            """


        if media_type == "audio":

            mimetype = "audio/mpeg"

        else:

            mimetype = "video/mp4"


        return send_file(
            downloaded,
            as_attachment=True,
            download_name=(
                clean_filename(
                    info.get("title", "download")
                )
                + (
                    ".mp3"
                    if media_type == "audio"
                    else ".mp4"
                )
            ),
            mimetype=mimetype
        )


    except Exception as e:

        print(
            "DOWNLOAD ERROR:",
            repr(e)
        )

        return f"""
        <!DOCTYPE html>

        <html lang="ar" dir="rtl">

        <head>

        <meta charset="UTF-8">

        <meta name="viewport"
              content="width=device-width,initial-scale=1">

        <style>

        body {{
            background:#090d18;
            color:white;
            font-family:Arial;
            text-align:center;
            padding:60px 20px;
        }}

        .box {{
            max-width:600px;
            margin:auto;
            padding:30px;
            border-radius:25px;
            background:#151d31;
        }}

        h2 {{
            color:#ff6b7a;
        }}

        p {{
            color:#aeb8cb;
            line-height:1.8;
        }}

        button {{
            padding:14px 25px;
            border:0;
            border-radius:12px;
            background:#557cff;
            color:white;
            font-weight:bold;
            cursor:pointer;
        }}

        </style>

        </head>

        <body>

        <div class="box">

        <h2>❌ حدث خطأ أثناء التحميل</h2>

        <p>
        تعذر تحميل هذا الرابط حاليًا.
        </p>

        <p>
        قد يكون الموقع المصدر قد طلب تسجيل الدخول
        أو وضع حدًا مؤقتًا للطلبات.
        </p>

        <button onclick="history.back()">
        ↩ العودة
        </button>

        </div>

        </body>

        </html>
        """


# =========================================================
# Telegram
# =========================================================

@bot.message_handler(commands=["start"])
def start(message):

    text = f"""
👋 أهلاً بك في KM Downloader

🎬 تحميل فيديو
🎵 تحميل صوت MP3
⚡ اختيار أفضل جودة متاحة تلقائيًا

👨‍💻 المطور:
{DEVELOPER_NAME}

أرسل رابط الفيديو الآن.
"""

    bot.send_message(
        message.chat.id,
        text
    )


# =========================================================
# رابط Telegram
# =========================================================

@bot.message_handler(
    func=lambda message:
        bool(
            message.text
            and is_valid_url(
                message.text.strip()
            )
        )
)
def receive_url(message):

    url = message.text.strip()

    try:

        bot.send_chat_action(
            message.chat.id,
            "typing"
        )

        options = base_ydl_options()

        options["skip_download"] = True

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )


        title = info.get(
            "title",
            "فيديو"
        )

        user_sessions[
            message.chat.id
        ] = {

            "url": url,

            "title": title
        }


        keyboard = InlineKeyboardMarkup(
            row_width=2
        )


        keyboard.add(

            InlineKeyboardButton(
                "🎬 أفضل جودة",
                callback_data="download_best"
            ),

            InlineKeyboardButton(
                "🎵 صوت MP3",
                callback_data="download_audio"
            )
        )


        # استخراج الجودات الموجودة فعليًا
        heights = set()

        for fmt in info.get(
            "formats",
            []
        ):

            height = fmt.get("height")

            vcodec = fmt.get(
                "vcodec"
            )

            if (
                height
                and height >= 144
                and vcodec
                and vcodec != "none"
            ):

                heights.add(
                    int(height)
                )


        selected = sorted(
            heights,
            reverse=True
        )[:8]


        for height in selected:

            keyboard.add(

                InlineKeyboardButton(
                    f"🎥 {height}p",
                    callback_data=
                        f"download_{height}"
                )
            )


        bot.send_message(

            message.chat.id,

            f"🎬 {title}\n\n"
            "اختر نوع التحميل:",

            reply_markup=keyboard
        )


    except Exception as e:

        print(
            "INFO ERROR:",
            repr(e)
        )

        bot.send_message(

            message.chat.id,

            "❌ تعذر قراءة الرابط حاليًا.\n"
            "تأكد من أن الرابط عام ويمكن الوصول إليه."
        )


# =========================================================
# أزرار Telegram
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith("download_")
)
def callback_download(call):

    chat_id = call.message.chat.id

    session = user_sessions.get(
        chat_id
    )


    if not session:

        bot.answer_callback_query(
            call.id,
            "انتهت جلسة التحميل، أرسل الرابط مرة أخرى."
        )

        return


    url = session["url"]

    action = call.data.replace(
        "download_",
        ""
    )


    bot.answer_callback_query(
        call.id,
        "جاري التحميل..."
    )


    status = bot.send_message(
        chat_id,
        "⏳ جاري تجهيز الملف..."
    )


    job_id = uuid.uuid4().hex

    stem = DOWNLOAD_DIR / job_id


    try:

        if action == "audio":

            output = stem.with_suffix(
                ".%(ext)s"
            )

            info = download_audio(
                url,
                output
            )

            downloaded = find_downloaded_file(
                job_id
            )

            if not downloaded:

                raise Exception(
                    "ملف الصوت غير موجود"
                )


            if downloaded.stat().st_size > MAX_FILE_SIZE:

                raise Exception(
                    "حجم ملف الصوت أكبر من الحد المسموح"
                )


            bot.delete_message(
                chat_id,
                status.message_id
            )


            with open(
                downloaded,
                "rb"
            ) as audio:

                bot.send_audio(
                    chat_id,
                    audio,
                    title=info.get(
                        "title",
                        "Audio"
                    ),
                    performer=DEVELOPER_NAME
                )


        else:

            output = stem.with_suffix(
                ".%(ext)s"
            )


            if action == "best":

                format_selector = (
                    "bv*+ba/b[ext=mp4]/b*"
                )

            else:

                try:
                    height = int(action)

                    # ? يسمح بتعامل أكثر مرونة مع
                    # الخصائص غير المعروفة.
                    format_selector = (
                        f"
