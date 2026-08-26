import os
import threading
import uuid
import time
from flask import Flask, render_template_string, request, send_file, jsonify
import yt_dlp
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ----------------------------------------------------
# 1. إعداد التوكن وتطبيق Flask
# ----------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ضع_توكن_البوت_الحالي_هنا")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

user_urls = {}

# إنشاء مجلد التحميلات المؤقت إن لم يكن موجوداً
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ====================================================
# 2. واجهة الموقع الكاملة (HTML + CSS + JavaScript)
# ====================================================

HTML_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مُنزل الفيديوهات الذكي | كهلان زيد الاشول</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --bg: #07111f;
            --bg2: #0b1729;
            --card: rgba(17, 31, 52, 0.82);
            --card2: #111f34;
            --border: rgba(255,255,255,.09);
            --primary: #3b82f6;
            --primary2: #2563eb;
            --text: #f8fafc;
            --muted: #94a3b8;
            --success: #22c55e;
            --danger: #ef4444;
        }

        body {
            font-family: 'Tajawal', sans-serif;
            min-height: 100vh;
            color: var(--text);
            background:
                radial-gradient(circle at 20% 10%, rgba(59,130,246,.18), transparent 30%),
                radial-gradient(circle at 80% 80%, rgba(37,99,235,.13), transparent 30%),
                linear-gradient(145deg, var(--bg), var(--bg2));
        }

        .page {
            width: 100%;
            max-width: 850px;
            margin: auto;
            padding: 25px 16px 100px;
        }

        /* Header */
        header {
            text-align: center;
            padding: 35px 10px 25px;
        }

        .logo {
            width: 76px;
            height: 76px;
            margin: auto;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 34px;
            background: linear-gradient(135deg, #3b82f6, #7c3aed);
            box-shadow: 0 15px 40px rgba(37,99,235,.3);
        }

        header h1 {
            margin-top: 20px;
            font-size: 30px;
            font-weight: 800;
        }

        header p {
            color: var(--muted);
            margin-top: 10px;
            font-size: 15px;
        }

        /* Main Card */
        .main-card {
            background: var(--card);
            border: 1px solid var(--border);
            backdrop-filter: blur(18px);
            border-radius: 25px;
            padding: 25px;
            box-shadow: 0 25px 70px rgba(0,0,0,.35);
        }

        .input-label {
            display: block;
            margin-bottom: 10px;
            font-size: 15px;
            font-weight: 700;
        }

        .input-box {
            display: flex;
            gap: 10px;
            padding: 7px;
            background: #07111f;
            border: 1px solid var(--border);
            border-radius: 15px;
        }

        .input-box input {
            flex: 1;
            min-width: 0;
            border: 0;
            outline: 0;
            background: transparent;
            color: white;
            padding: 13px;
            font-family: inherit;
            font-size: 15px;
            direction: ltr;
            text-align: left;
        }

        .input-box input::placeholder {
            color: #64748b;
        }

        .analyze-btn {
            border: 0;
            border-radius: 11px;
            padding: 0 22px;
            background: linear-gradient(135deg, var(--primary), var(--primary2));
            color: white;
            font-family: inherit;
            font-weight: 700;
            cursor: pointer;
            transition: .2s;
        }

        .analyze-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 8px 25px rgba(59,130,246,.25);
        }

        .analyze-btn:disabled {
            opacity: .55;
            cursor: not-allowed;
            transform: none;
        }

        /* Loading */
        .loading {
            display: none;
            text-align: center;
            padding: 30px 10px;
        }

        .spinner {
            width: 42px;
            height: 42px;
            margin: auto;
            border: 4px solid rgba(255,255,255,.12);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin .8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .loading p {
            color: var(--muted);
            margin-top: 15px;
        }

        /* Video Information */
        .video-info {
            display: none;
            margin-top: 25px;
        }

        .video-preview {
            display: flex;
            gap: 18px;
            padding: 15px;
            border-radius: 18px;
            background: rgba(255,255,255,.035);
            border: 1px solid var(--border);
        }

        .thumbnail {
            width: 210px;
            height: 118px;
            object-fit: cover;
            border-radius: 13px;
            background: #020617;
        }

        .video-details {
            flex: 1;
            min-width: 0;
        }

        .video-title {
            font-size: 17px;
            font-weight: 800;
            line-height: 1.6;
        }

        .video-meta {
            color: var(--muted);
            font-size: 13px;
            margin-top: 9px;
        }

        /* Quality */
        .quality-section {
            margin-top: 25px;
        }

        .section-title {
            font-size: 17px;
            font-weight: 800;
            margin-bottom: 13px;
        }

        .qualities {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }

        .quality {
            position: relative;
            cursor: pointer;
        }

        .quality input {
            position: absolute;
            opacity: 0;
        }

        .quality-content {
            display: block;
            text-align: center;
            padding: 15px 8px;
            border-radius: 13px;
            border: 1px solid var(--border);
            background: rgba(255,255,255,.035);
            transition: .2s;
        }

        .quality-content strong {
            display: block;
            font-size: 17px;
        }

        .quality-content span {
            display: block;
            margin-top: 4px;
            font-size: 12px;
            color: var(--muted);
        }

        .quality input:checked + .quality-content {
            border-color: var(--primary);
            background: rgba(59,130,246,.13);
            box-shadow: 0 0 0 1px var(--primary);
        }

        /* Download Button */
        .download-btn {
            width: 100%;
            margin-top: 22px;
            padding: 16px;
            border: 0;
            border-radius: 14px;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            font-family: inherit;
            font-size: 17px;
            font-weight: 800;
            cursor: pointer;
            transition: .2s;
        }

        .download-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(34,197,94,.2);
        }

        .download-btn:disabled {
            opacity: .55;
            cursor: not-allowed;
            transform: none;
        }

        /* Error */
        .error {
            display: none;
            margin-top: 18px;
            padding: 14px;
            border-radius: 12px;
            background: rgba(239,68,68,.1);
            border: 1px solid rgba(239,68,68,.25);
            color: #fca5a5;
            text-align: center;
        }

        /* Footer */
        footer {
            text-align: center;
            margin-top: 35px;
            color: var(--muted);
            font-size: 13px;
        }

        .developer {
            color: white;
            font-weight: 800;
            margin-top: 6px;
        }

        /* WhatsApp */
        .whatsapp {
            position: fixed;
            bottom: 22px;
            left: 22px;
            width: 58px;
            height: 58px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #25D366;
            box-shadow: 0 10px 30px rgba(37,211,102,.35);
            transition: .2s;
            z-index: 100;
        }

        .whatsapp:hover {
            transform: scale(1.08);
        }

        .whatsapp svg {
            width: 31px;
            height: 31px;
            fill: white;
        }

        /* Mobile */
        @media (max-width: 650px) {
            .page {
                padding: 10px 12px 100px;
            }

            header {
                padding-top: 25px;
            }

            header h1 {
                font-size: 25px;
            }

            .main-card {
                padding: 18px;
                border-radius: 20px;
            }

            .input-box {
                flex-direction: column;
            }

            .analyze-btn {
                width: 100%;
                height: 48px;
            }

            .video-preview {
                flex-direction: column;
            }

            .thumbnail {
                width: 100%;
                height: auto;
                aspect-ratio: 16 / 9;
            }

            .qualities {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>

<div class="page">
    <header>
        <div class="logo">🎬</div>
        <h1>مُنزل الفيديوهات الذكي</h1>
        <p>حلّل الفيديو واختر الجودة التي تريدها قبل بدء التنزيل</p>
    </header>

    <main class="main-card">
        <label class="input-label">رابط الفيديو</label>

        <div class="input-box">
            <input id="videoUrl" type="url" placeholder="ألصق رابط الفيديو هنا..." autocomplete="off">
            <button id="analyzeBtn" class="analyze-btn" onclick="analyzeVideo()">تحليل الفيديو</button>
        </div>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p id="loadingText">جاري تحليل الفيديو واستخراج الدقات المتاحة...</p>
        </div>

        <div id="error" class="error"></div>

        <section id="videoInfo" class="video-info">
            <div class="video-preview">
                <img id="thumbnail" class="thumbnail" src="" alt="صورة الفيديو">
                <div class="video-details">
                    <div id="videoTitle" class="video-title"></div>
                    <div id="videoMeta" class="video-meta"></div>
                </div>
            </div>

            <div class="quality-section">
                <div class="section-title">اختر جودة الفيديو</div>
                <div id="qualities" class="qualities"></div>
            </div>

            <button id="downloadBtn" class="download-btn" onclick="downloadVideo()" disabled>
                ⬇️ تنزيل الفيديو
            </button>
        </section>
    </main>

    <footer>
        <div>تم التطوير بواسطة</div>
        <div class="developer">كهلان زيد الاشول</div>
    </footer>
</div>

<!-- WhatsApp -->
<a class="whatsapp" href="https://wa.me/967711014694" target="_blank" rel="noopener" aria-label="WhatsApp">
    <svg viewBox="0 0 32 32">
        <path d="M19.11 17.21c-.29-.15-1.72-.85-1.99-.95-.27-.1-.46-.15-.66.15-.19.29-.75.95-.92 1.14-.17.19-.34.22-.63.07-.29-.15-1.22-.45-2.33-1.44-.86-.77-1.44-1.72-1.61-2.01-.17-.29-.02-.45.13-.59.13-.13.29-.34.44-.51.15-.17.19-.29.29-.49.1-.19.05-.36-.02-.51-.07-.15-.66-1.58-.9-2.17-.24-.57-.48-.49-.66-.5h-.56c-.19 0-.49.07-.75.36-.26.29-1 .98-1 2.39s1.02 2.77 1.16 2.96c.15.19 2 3.05 4.84 4.28.68.29 1.21.46 1.62.59.68.22 1.3.19 1.79.12.55-.08 1.72-.7 1.96-1.38.24-.68.24-1.26.17-1.38-.07-.12-.27-.19-.56-.34z"/>
        <path d="M16.02 3C8.84 3 3 8.83 3 16c0 2.29.6 4.52 1.75 6.48L3 29l6.7-1.72A12.94 12.94 0 0 0 16.02 29C23.18 29 29 23.17 29 16S23.18 3 16.02 3zm0 23.68c-2.02 0-4-.54-5.72-1.56l-.41-.24-3.98 1.02 1.06-3.87-.27-.42A10.99 10.99 0 1 1 16.02 26.68z"/>
    </svg>
</a>

<script>
let selectedQuality = "best";

function showError(msg) {
    const errorBox = document.getElementById("error");
    errorBox.textContent = msg;
    errorBox.style.display = "block";
}

async function analyzeVideo() {
    const urlInput = document.getElementById("videoUrl");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const loading = document.getElementById("loading");
    const videoInfo = document.getElementById("videoInfo");
    const errorBox = document.getElementById("error");
    const loadingText = document.getElementById("loadingText");

    const url = urlInput.value.trim();

    errorBox.style.display = "none";
    videoInfo.style.display = "none";

    if (!url) {
        showError("⚠️ يرجى إدخال رابط الفيديو أولاً.");
        return;
    }

    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        showError("⚠️ يرجى إدخال رابط صحيح يبدأ بـ http أو https.");
        return;
    }

    analyzeBtn.disabled = true;
    loadingText.textContent = "جاري تحليل الفيديو واستخراج الدقات المتاحة...";
    loading.style.display = "block";

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "تعذر تحليل الرابط");
        }

        document.getElementById("thumbnail").src = data.thumbnail || "";
        document.getElementById("videoTitle").textContent = data.title || "فيديو بدون عنوان";
        document.getElementById("videoMeta").textContent = `المنصة: ${data.extractor || 'عام'} | المدة: ${data.duration || 'غير معروف'}`;

        const qualitiesContainer = document.getElementById("qualities");
        qualitiesContainer.innerHTML = "";

        if (data.qualities && data.qualities.length > 0) {
            data.qualities.forEach((q, index) => {
                const qDiv = document.createElement("label");
                qDiv.className = "quality";
                qDiv.innerHTML = `
                    <input type="radio" name="quality" value="${q.format_id}" ${index === 0 ? 'checked' : ''} onchange="selectedQuality='${q.format_id}'">
                    <div class="quality-content">
                        <strong>${q.height}p 🎥</strong>
                        <span>${q.ext || 'MP4'}</span>
                    </div>
                `;
                qualitiesContainer.appendChild(qDiv);
            });
            selectedQuality = data.qualities[0].format_id;
        } else {
            const bestDiv = document.createElement("label");
            bestDiv.className = "quality";
            bestDiv.innerHTML = `
                <input type="radio" name="quality" value="best" checked onchange="selectedQuality='best'">
                <div class="quality-content">
                    <strong>أفضل جودة 🌟</strong>
                    <span>تلقائي</span>
                </div>
            `;
            qualitiesContainer.appendChild(bestDiv);
            selectedQuality = "best";
        }

        videoInfo.style.display = "block";
        document.getElementById("downloadBtn").disabled = false;

    } catch (err) {
        showError("❌ حدث خطأ أثناء تحليل الفيديو: " + err.message);
    } finally {
        analyzeBtn.disabled = false;
        loading.style.display = "none";
    }
}

function downloadVideo() {
    const url = document.getElementById("videoUrl").value.trim();
    if (!url) return;

    window.location.href = `/download-web?url=${encodeURIComponent(url)}&format_id=${selectedQuality}`;
}
</script>

</body>
</html>
"""

# ====================================================
# 3. مسارات Flask (Back-End API)
# ====================================================

@app.route('/')
def index():
    return render_template_string(HTML_LAYOUT)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'يرجى تقديم رابط الفيديو.'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        title = info.get('title', 'فيديو بدون عنوان')
        thumbnail = info.get('thumbnail', '')
        extractor = info.get('extractor_key', 'عام')
        
        # تحويل مدة الفيديو إلى دقائق وثواني
        duration_sec = info.get('duration', 0)
        if duration_sec:
            minutes = duration_sec // 60
            seconds = duration_sec % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = 'غير معروف'

        # تجميع الدقات والجودات المتاحة
        qualities = []
        seen_heights = set()

        formats = info.get('formats', [])
        for f in formats:
            height = f.get('height')
            format_id = f.get('format_id')
            vcodec = f.get('vcodec', 'none')

            if height and height >= 144 and vcodec != 'none':
                if height not in seen_heights:
                    seen_heights.add(height)
                    qualities.append({
                        'height': height,
                        'format_id': format_id,
                        'ext': f.get('ext', 'mp4')
                    })

        # ترتيب الجودات من الأعلى إلى الأدنى
        qualities = sorted(qualities, key=lambda x: x['height'], reverse=True)

        return jsonify({
            'title': title,
            'thumbnail': thumbnail,
            'extractor': extractor,
            'duration': duration_str,
            'qualities': qualities
        })

    except Exception as e:
        return jsonify({'error': f"فشل في تحليل الفيديو: {str(e)}"}), 500

@app.route('/download-web')
def download_web():
    url = request.args.get('url', '').strip()
    format_id = request.args.get('format_id', 'best')

    if not url:
        return "الرابط غير صالح", 400

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    # تحديد معيار الجودة لـ yt-dlp
    if format_id == 'best':
        fmt = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        fmt = f"{format_id}+bestaudio/best"

    ydl_opts = {
        'format': fmt,
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # معالجة امتداد الملف في حال تم دمج الفيديو لـ mp4
            base, _ = os.path.splitext(filename)
            if os.path.exists(f"{base}.mp4"):
                final_file = f"{base}.mp4"
            elif os.path.exists(filename):
                final_file = filename
            else:
                return "حدث خطأ أثناء تنزيل الملف على السيرفر", 500

        title = info.get('title', 'video')
        download_name = f"{title}.mp4"

        # حذف الملف بعد تنزيله تلقائياً للحفاظ على مساحة السيرفر
        def remove_file():
            time.sleep(10)
            if os.path.exists(final_file):
                try:
                    os.remove(final_file)
                except Exception:
                    pass

        threading.Thread(target=remove_file, daemon=True).start()

        return send_file(
            final_file,
            as_attachment=True,
            download_name=download_name,
            mimetype='video/mp4'
        )

    except Exception as e:
        return f"حدث خطأ أثناء تحميل الفيديو: {str(e)}", 500

# ====================================================
# 4. بوت تليجرام (Telegram Bot Functionality)
# ====================================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "أهلاً بك في بوت وموقع مُنزل الفيديوهات الذكي! 🎬\n\n"
        "أرسل لي رابط الفيديو للتحميل المباشر عبر تليجرام."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    if url.startswith("http://") or url.startswith("https://"):
        msg = bot.reply_to(message, "⏳ جاري جلب دقات الفيديو المتاحة...")
        
        try:
            ydl_opts = {'quiet': True, 'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            req_id = str(uuid.uuid4())[:8]
            user_urls[req_id] = url

            markup = InlineKeyboardMarkup()
            markup.add(
                InlineKeyboardButton("🎥 أفضل جودة", callback_data=f"dl_{req_id}_best"),
                InlineKeyboardButton("🎵 صوتی فقط (MP3)", callback_data=f"dl_{req_id}_audio")
            )

            bot.edit_message_text(
                f"🎬 **{info.get('title', 'فيديو')}**\n\nاختر الصيغة أو الجودة المطلوبة:",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ أثناء تحليل الرابط: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)
    else:
        bot.reply_to(message, "⚠️ يرجى إرسال رابط صحيح يبدأ بـ http أو https.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def handle_download_callback(call):
    parts = call.data.split("_")
    req_id = parts[1]
    mode = parts[2]

    url = user_urls.get(req_id)
    if not url:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية هذا الرابط، أعد إرساله مجدداً.")
        return

    bot.answer_callback_query(call.id, "جاري بدء التحميل...")
    bot.edit_message_text("⏳ جاري تحميل الملف وإرساله لك...", chat_id=call.message.chat.id, message_id=call.message.message_id)

    def process_and_send():
        file_id = str(uuid.uuid4())
        out_tmpl = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
        
        if mode == "audio":
            opts = {
                'format': 'bestaudio/best',
                'outtmpl': out_tmpl,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
        else:
            opts = {'format': 'best[ext=mp4]/best', 'outtmpl': out_tmpl, 'quiet': True}

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            if mode == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

            with open(filename, 'rb') as f:
                if mode == "audio":
                    bot.send_audio(call.message.chat.id, f, caption="تم التحميل بنجاح 🎵")
                else:
                    bot.send_video(call.message.chat.id, f, caption="تم التحميل بنجاح 🎬")

            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            bot.send_message(call.message.chat.id, f"❌ حدث خطأ أثناء التحميل: {str(e)}")

    threading.Thread(target=process_and_send, daemon=True).start()

# ====================================================
# 5. تشغيل السيرفر والبوت معاً
# ====================================================

def run_bot():
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Telegram Bot Exception: {e}")

if __name__ == '__main__':
    # تشغيل بوت التليجرام في خلفية Thread مستقلة
    if BOT_TOKEN and BOT_TOKEN != "ضع_توكن_البوت_الحالي_هنا":
        threading.Thread(target=run_bot, daemon=True).start()
    
    # تشغيل تطبيق Web (Flask)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
