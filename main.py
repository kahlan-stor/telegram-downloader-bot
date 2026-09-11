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

BOT_TOKEN = os.getenv("BOT_TOKEN", "ضع_توكن_البوت_هنا")
MAX_FILE_SIZE = 49 * 1024 * 1024
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
DEVELOPER_NAME = "كهلان زيد الاشول"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)
user_sessions = {}

HTML = r"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>KM Downloader</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
font-family:"Tajawal",sans-serif;min-height:100vh;color:white;overflow-x:hidden;
background:radial-gradient(circle at 50% -10%,rgba(76,108,255,.35),transparent 35%),
radial-gradient(circle at 90% 90%,rgba(124,78,255,.18),transparent 30%),
linear-gradient(135deg,#050812 0%,#0b1224 50%,#050812 100%)
}
#splash{position:fixed;inset:0;z-index:99999;display:flex;align-items:center;justify-content:center;flex-direction:column;
background:radial-gradient(circle at center,#182b55 0%,#0a1020 42%,#04060d 100%);opacity:1;transition:opacity .8s ease}
#heart{min-width:330px;min-height:230px;display:flex;align-items:center;justify-content:center;text-align:center;white-space:pre;
font-family:monospace;font-size:16px;line-height:15px;font-weight:900;color:white;
text-shadow:0 0 5px white,0 0 12px #6488ff,0 0 25px #557cff,0 0 45px #557cff;
animation:heartPulse 1.4s ease-in-out infinite alternate}
@keyframes heartPulse{from{transform:scale(.98);filter:brightness(.9)}to{transform:scale(1.04);filter:brightness(1.3)}}
.splash-title{margin-top:18px;font-size:28px;font-weight:800;letter-spacing:.5px}
.splash-subtitle{margin-top:8px;color:#9caac7;font-size:14px}
#app{display:none;min-height:100vh}
.container{width:min(920px,92%);margin:auto;padding:25px 0 40px}
.header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-radius:23px;
border:1px solid rgba(255,255,255,.09);background:rgba(255,255,255,.055);backdrop-filter:blur(20px);
box-shadow:0 20px 60px rgba(0,0,0,.28)}
.brand{display:flex;align-items:center;gap:12px}
.brand-logo{width:50px;height:50px;display:flex;align-items:center;justify-content:center;border-radius:16px;font-size:17px;font-weight:900;
background:linear-gradient(135deg,#557cff,#795cff);box-shadow:0 10px 35px rgba(82,110,255,.35)}
.brand-text h1{font-size:19px;font-weight:800}
.brand-text p{margin-top:3px;color:#8997b4;font-size:11px}
.hero{text-align:center;padding:65px 10px 38px}
.hero-badge{display:inline-flex;align-items:center;gap:7px;padding:8px 13px;margin-bottom:18px;border-radius:50px;
background:rgba(85,124,255,.09);border:1px solid rgba(100,135,255,.15);color:#9db4ff;font-size:12px}
.hero h2{font-size:clamp(30px,7vw,52px);line-height:1.2;font-weight:800;background:linear-gradient(90deg,#fff,#b7c7ff,#fff);
-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{max-width:600px;margin:16px auto 0;color:#9aa7c0;font-size:15px;line-height:1.8}
.download-card{padding:28px;border-radius:30px;border:1px solid rgba(255,255,255,.09);
background:linear-gradient(145deg,rgba(255,255,255,.065),rgba(255,255,255,.025));backdrop-filter:blur(25px);
box-shadow:0 30px 90px rgba(0,0,0,.35)}
.input-title{display:flex;align-items:center;gap:8px;margin-bottom:11px;font-size:14px;font-weight:700}
.url-box{display:flex;gap:10px;padding:7px;border-radius:19px;background:rgba(0,0,0,.24);border:1px solid rgba(255,255,255,.07)}
.url-box input{flex:1;min-width:0;padding:15px 14px;outline:none;border:none;background:transparent;color:white;font-family:inherit;font-size:14px}
.url-box input::placeholder{color:#66728a}
.download-btn{border:none;padding:0 25px;min-height:50px;border-radius:14px;color:white;font-family:inherit;font-size:14px;font-weight:700;
background:linear-gradient(135deg,#557cff,#755cff);cursor:pointer;transition:transform .2s,box-shadow .2s}
.download-btn:hover{transform:translateY(-2px);box-shadow:0 12px 30px rgba(85,124,255,.35)}
.download-btn:active{transform:translateY(0)}
.options{display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-top:18px}
.option{position:relative;overflow:hidden;padding:22px;border-radius:21px;border:1px solid rgba(255,255,255,.07);
background:rgba(255,255,255,.035);cursor:pointer;transition:transform .25s,background .25s,border .25s}
.option::before{content:"";position:absolute;width:100px;height:100px;top:-50px;left:-50px;border-radius:50%;background:rgba(90,120,255,.12)}
.option:hover{transform:translateY(-4px);background:rgba(255,255,255,.075);border-color:rgba(110,140,255,.25)}
.option-icon{position:relative;font-size:31px;margin-bottom:10px}
.option-title{position:relative;font-size:15px;font-weight:700}
.option-desc{position:relative;margin-top:5px;color:#818da6;font-size:12px;line-height:1.6}
#loading{display:none;margin-top:20px;padding:20px;text-align:center;border-radius:18px;background:rgba(85,124,255,.07);border:1px solid rgba(85,124,255,.12)}
.spinner{width:38px;height:38px;margin:0 auto 12px;border-radius:50%;border:3px solid rgba(255,255,255,.12);border-top-color:#6e8fff;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.footer{margin-top:28px;text-align:center;color:#65718a;font-size:12px}
.footer strong{color:#aebeff;font-weight:700}
@media(max-width:650px){
.container{width:94%;padding-top:15px}.header{padding:13px}.brand-logo{width:44px;height:44px}.brand-text h1{font-size:17px}
.hero{padding:45px 5px 28px}.hero h2{font-size:31px}.hero p{font-size:13px}.download-card{padding:18px;border-radius:24px}
.url-box{flex-direction:column;padding:7px}.url-box input{min-height:50px}.download-btn{width:100%}.options{grid-template-columns:1fr}#heart{transform:scale(.78)}
}
</style>
</head>
<body>
<div id="splash">
<div id="heart"></div>
<div class="splash-title">KM Downloader</div>
<div class="splash-subtitle">جاري تجهيز أداة التحميل...</div>
</div>

<div id="app">
<div class="container">
<header class="header">
<div class="brand">
<div class="brand-logo">KM</div>
<div class="brand-text"><h1>KM Downloader</h1><p>أداة تحميل الوسائط</p></div>
</div>
</header>

<section class="hero">
<div class="hero-badge">⚡ سريع • بسيط • للجوال</div>
<h2>حمّل ما تريد بسهولة</h2>
<p>ألصق رابط الفيديو واختر تحميل الفيديو أو استخراج الصوت بصيغة MP3.</p>
</section>

<section class="download-card">
<div class="input-title">🔗 رابط الفيديو</div>
<div class="url-box">
<input id="url" type="url" placeholder="ألصق رابط الفيديو هنا..." autocomplete="off">
<button class="download-btn" onclick="downloadMedia()">تحميل</button>
</div>

<div class="options">
<div class="option" onclick="downloadMedia('video')">
<div class="option-icon">🎬</div>
<div class="option-title">تحميل فيديو</div>
<div class="option-desc">أفضل جودة فيديو متاحة تلقائيًا</div>
</div>
<div class="option" onclick="downloadMedia('audio')">
<div class="option-icon">🎵</div>
<div class="option-title">تحميل كصوت</div>
<div class="option-desc">استخراج الصوت وتحويله إلى MP3</div>
</div>
</div>

<div id="loading"><div class="spinner"></div><div>جاري تجهيز الملف...</div></div>
</section>

<footer class="footer">المطور: <strong>كهلان زيد الاشول</strong></footer>
</div>
</div>

<script>
const heartPattern=[
"        KM KM        ",
"      KM     KM      ",
"    KM         KM    ",
"   KM           KM   ",
"  KM             KM  ",
" KM               KM ",
"KM                 KM",
"KM                 KM",
" KM               KM ",
"  KM             KM  ",
"   KM           KM   ",
"    KM         KM    ",
"      KM     KM      ",
"        KM KM        ",
"          KM         "
];

const heart=document.getElementById("heart");
let row=0,col=0;

function drawHeart(){
if(row>=heartPattern.length){setTimeout(finishSplash,700);return}
const current=heartPattern[row];
if(col>=current.length){row++;col=0;heart.innerHTML+="<br>";setTimeout(drawHeart,25);return}
const character=current[col];
heart.innerHTML+=(character==="K"||character==="M")?character:"&nbsp;";
col++;
setTimeout(drawHeart,13);
}

function finishSplash(){
const splash=document.getElementById("splash");
splash.style.opacity="0";
setTimeout(function(){
splash.style.display="none";
document.getElementById("app").style.display="block";
},800);
}

drawHeart();

function downloadMedia(type){
const input=document.getElementById("url");
const url=input.value.trim();

if(!url){alert("⚠️ ألصق رابط الفيديو أولاً");input.focus();return}
if(!/^https?:\/\//i.test(url)){alert("❌ الرابط غير صحيح");input.focus();return}

document.getElementById("loading").style.display="block";

const form=document.createElement("form");
form.method="POST";
form.action="/download-web";

const urlInput=document.createElement("input");
urlInput.type="hidden";urlInput.name="url";urlInput.value=url;
form.appendChild(urlInput);

const typeInput=document.createElement("input");
typeInput.type="hidden";typeInput.name="type";typeInput.value=type||"video";
form.appendChild(typeInput);

document.body.appendChild(form);
form.submit();
}

document.getElementById("url").addEventListener("keydown",function(event){
if(event.key==="Enter")downloadMedia("video");
});
</script>
</body>
</html>
"""

def is_valid_url(url):
    return bool(re.match(r"^https?://", url, re.IGNORECASE))

def clean_filename(name):
    name=re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:150]

def find_downloaded_file(stem):
    files=list(DOWNLOAD_DIR.glob(f"{stem}.*"))
    if not files:
        return None
    files.sort(key=lambda file:file.stat().st_mtime, reverse=True)
    return files[0]

def base_ydl_options():
    return {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "retries": 3,
        "fragment_retries": 3,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 3,
        "http_headers": {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
        }
    }

def download_video(url, output_path, format_selector=None):
    options=base_ydl_options()
    if not format_selector:
        format_selector="bv*+ba/b[ext=mp4]/b*"
    options.update({
        "format":format_selector,
        "merge_output_format":"mp4",
        "outtmpl":str(output_path),
        "overwrites":True
    })
    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=True)

def download_audio(url, output_path):
    options=base_ydl_options()
    options.update({
        "format":"ba/b[acodec!=none]/b*",
        "outtmpl":str(output_path),
        "postprocessors":[{
            "key":"FFmpegExtractAudio",
            "preferredcodec":"mp3",
            "preferredquality":"192"
        }]
    })
    with yt_dlp.YoutubeDL(options) as ydl:
        return ydl.extract_info(url, download=True)

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/download-web", methods=["POST"])
def download_web():
    url=request.form.get("url","").strip()
    media_type=request.form.get("type","video")

    if not is_valid_url(url):
        return '<script>alert("الرابط غير صحيح");history.back();</script>'

    if media_type not in ("video","audio"):
        media_type="video"

    job_id=uuid.uuid4().hex
    safe_name="web_"+job_id
    output=DOWNLOAD_DIR/safe_name
    downloaded=None

    try:
        if media_type=="audio":
            info=download_audio(url, output.with_suffix(".%(ext)s"))
            downloaded=find_downloaded_file(safe_name)
            if not downloaded:
                raise Exception("لم يتم العثور على ملف الصوت")
            extension=".mp3"
            mimetype="audio/mpeg"
        else:
            info=download_video(url, output.with_suffix(".%(ext)s"))
            downloaded=find_downloaded_file(safe_name)
            if not downloaded:
                raise Exception("لم يتم العثور على ملف الفيديو")
            extension=".mp4"
            mimetype="video/mp4"

        if downloaded.stat().st_size>MAX_FILE_SIZE:
            downloaded.unlink(missing_ok=True)
            return '<script>alert("❌ الملف أكبر من الحد المسموح");history.back();</script>'

        title=info.get("title","download")
        filename=clean_filename(title)+extension

        return send_file(downloaded, as_attachment=True, download_name=filename, mimetype=mimetype)

    except Exception as e:
        print("WEB DOWNLOAD ERROR:",repr(e))
        return """
        <!DOCTYPE html><html lang="ar" dir="rtl"><head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
        body{background:#070b16;color:white;font-family:Arial,sans-serif;text-align:center;padding:60px 20px}
        .box{max-width:600px;margin:auto;padding:30px;border-radius:25px;background:#121a2d;border:1px solid rgba(255,255,255,.08)}
        h2{color:#ff7181}p{color:#aeb8cb;line-height:1.9}
        button{margin-top:15px;padding:14px 28px;border:0;border-radius:13px;background:#557cff;color:white;font-weight:bold;cursor:pointer}
        </style></head><body><div class="box">
        <h2>❌ حدث خطأ أثناء التحميل</h2>
        <p>تعذر تحميل هذا الرابط حاليًا.</p>
        <p>قد يكون الموقع المصدر وضع حدًا مؤقتًا للطلبات أو أن الرابط يحتاج إلى وصول مختلف.</p>
        <button onclick="history.back()">↩ العودة</button>
        </div></body></html>
        """
    finally:
        pass

@bot.message_handler(commands=["start"])
def start(message):
    text=(
        "👋 أهلاً بك في KM Downloader\n\n"
        "🎬 تحميل فيديو\n"
        "🎵 تحميل صوت MP3\n"
        "⚡ أفضل جودة متاحة تلقائيًا\n\n"
        "👨‍💻 المطور:\n"
        f"{DEVELOPER_NAME}\n\n"
        "أرسل رابط الفيديو الآن."
    )
    bot.send_message(message.chat.id,text)

@bot.message_handler(
    func=lambda message: bool(
        message.text and is_valid_url(message.text.strip())
    )
)
def receive_url(message):
    url=message.text.strip()
    try:
        bot.send_chat_action(message.chat.id,"typing")
        options=base_ydl_options()
        options["skip_download"]=True

        with yt_dlp.YoutubeDL(options) as ydl:
            info=ydl.extract_info(url,download=False)

        title=info.get("title","فيديو")
        user_sessions[message.chat.id]={"url":url,"title":title}

        keyboard=InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            InlineKeyboardButton("🎬 أفضل جودة",callback_data="download_best"),
            InlineKeyboardButton("🎵 صوت MP3",callback_data="download_audio")
        )

        heights=set()
        for fmt in info.get("formats",[]):
            height=fmt.get("height")
            vcodec=fmt.get("vcodec")
            if height and isinstance(height,(int,float)) and height>=144 and vcodec and vcodec!="none":
                heights.add(int(height))

        selected_heights=sorted(heights,reverse=True)[:8]

        for height in selected_heights:
            keyboard.add(
                InlineKeyboardButton(
                    f"🎥 {height}p",
                    callback_data=f"download_{height}"
                )
            )

        bot.send_message(
            message.chat.id,
            "🎬 "+title+"\n\nاختر نوع التحميل:",
            reply_markup=keyboard
        )

    except Exception as e:
        print("INFO ERROR:",repr(e))
        bot.send_message(
            message.chat.id,
            "❌ تعذر قراءة الرابط حاليًا.\n\nتأكد أن الرابط صحيح ويمكن الوصول إليه."
        )

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("download_")
)
def callback_download(call):
    chat_id=call.message.chat.id
    session=user_sessions.get(chat_id)

    if not session:
        bot.answer_callback_query(
            call.id,
            "انتهت جلسة التحميل، أرسل الرابط مرة أخرى."
        )
        return

    url=session["url"]
    action=call.data.replace("download_","",1)

    bot.answer_callback_query(call.id,"⏳ جاري التحميل...")
    status=bot.send_message(chat_id,"⏳ جاري تجهيز الملف...")

    job_id=uuid.uuid4().hex
    stem=DOWNLOAD_DIR/job_id

    try:
        if action=="audio":
            output=stem.with_suffix(".%(ext)s")
            info=download_audio(url,output)
            downloaded=find_downloaded_file(job_id)

            if not downloaded:
                raise Exception("ملف الصوت غير موجود")

            if downloaded.stat().st_size>MAX_FILE_SIZE:
                raise Exception("حجم ملف الصوت أكبر من الحد المسموح")

            try:
                bot.delete_message(chat_id,status.message_id)
            except Exception:
                pass

            with open(downloaded,"rb") as audio:
                bot.send_audio(
                    chat_id,
                    audio,
                    title=info.get("title","Audio"),
                    performer=DEVELOPER_NAME
                )

        else:
            output=stem.with_suffix(".%(ext)s")

            if action=="best":
                format_selector="bv*+ba/b[ext=mp4]/b*"
            else:
                try:
                    height=int(action)
                    format_selector=(
                        f"bv*[height<={height}]+ba/"
                        f"b[height<={height}]/"
                        "bv*+ba/"
                        "b[ext=mp4]/"
                        "b*"
                    )
                except (ValueError,TypeError):
                    format_selector="bv*+ba/b[ext=mp4]/b*"

            info=download_video(url,output,format_selector)
            downloaded=find_downloaded_file(job_id)

            if not downloaded:
                raise Exception("لم يتم العثور على ملف الفيديو")

            if downloaded.stat().st_size>MAX_FILE_SIZE:
                raise Exception("حجم الفيديو أكبر من الحد المسموح")

            try:
                bot.delete_message(chat_id,status.message_id)
            except Exception:
                pass

            with open(downloaded,"rb") as video:
                bot.send_video(
                    chat_id,
                    video,
                    caption=(
                        "🎬 تم تحميل الفيديو بنجاح\n\n"
                        "👨‍💻 المطور: "+DEVELOPER_NAME
                    ),
                    supports_streaming=True
                )

    except Exception as e:
        print("TELEGRAM DOWNLOAD ERROR:",repr(e))
        error_text=str(e)

        if "Requested format is not available" in error_text:
            user_message="❌ هذه الجودة غير متوفرة لهذا الفيديو.\n\nجرب 🎬 أفضل جودة."
        elif "login" in error_text.lower() or "sign in" in error_text.lower():
            user_message="❌ الموقع المصدر يطلب تسجيل الدخول أو يمنع الوصول لهذا الرابط حاليًا."
        elif "rate-limit" in error_text.lower() or "rate limit" in error_text.lower():
            user_message="⚠️ الموقع المصدر وضع حدًا مؤقتًا للطلبات من الخادم.\n\nحاول لاحقًا أو جرب رابطًا آخر."
        elif "أكبر من الحد" in error_text:
            user_message="❌ حجم الملف أكبر من الحد المسموح."
        else:
            user_message="❌ حدث خطأ أثناء التحميل.\n\nجرب «🎬 أفضل جودة» أو أرسل رابطًا آخر."

        try:
            bot.edit_message_text(user_message,chat_id,status.message_id)
        except Exception:
            try:
                bot.send_message(chat_id,user_message)
            except Exception:
                pass

    finally:
        for file in DOWNLOAD_DIR.glob(f"{job_id}.*"):
            try:
                file.unlink(missing_ok=True)
            except Exception:
                pass

@bot.message_handler(func=lambda message: True)
def other_message(message):
    bot.send_message(
        message.chat.id,
        "🔗 أرسل رابط فيديو أو صوت للبدء بالتحميل.\n\n🎬 فيديو\n🎵 MP3"
    )

def cleanup_files():
    while True:
        try:
            now=time.time()
            for file in DOWNLOAD_DIR.iterdir():
                try:
                    age=now-file.stat().st_mtime
                    if age>3600:
                        file.unlink(missing_ok=True)
                except Exception:
                    pass
        except Exception:
            pass
        time.sleep(600)

def run_bot():
    print("Telegram bot started")
    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )

if __name__=="__main__":
    cleanup_thread=threading.Thread(target=cleanup_files,daemon=True)
    cleanup_thread.start()

    bot_thread=threading.Thread(target=run_bot,daemon=True)
    bot_thread.start()

    port=int(os.getenv("PORT","8080"))
    print(f"Web server running on port {port}")

    app.run(
        host="0.0.0.0",
        port=port,
        threaded=True
    )
