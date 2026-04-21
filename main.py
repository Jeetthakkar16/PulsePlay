from flask import Flask, request, render_template, send_file
import requests
from yt_dlp import YoutubeDL
import os
import glob
import imageio_ffmpeg
from dotenv import load_dotenv

load_dotenv()
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

app = Flask(__name__)
API_KEY = os.getenv("API_KEY")
YOUTUBE_COOKIES = os.getenv("YOUTUBE_COOKIES")

COOKIE_FILE = "/tmp/yt_cookies.txt"
if YOUTUBE_COOKIES:
    cookie_content = YOUTUBE_COOKIES.replace('\\n', '\n').strip()
    with open(COOKIE_FILE, "w") as f:
        f.write(cookie_content)
    print("✅ Cookies written successfully")
    print(f"✅ Cookie file size: {os.path.getsize(COOKIE_FILE)} bytes")
else:
    print("⚠️ No cookies found in environment")


def search_youtube(query):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 1,
        "key": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    print("DATA:", data)
    if "items" not in data or len(data["items"]) == 0:
        return None
    item = data["items"][0]
    return {
        "title": item["snippet"]["title"],
        "video_id": item["id"]["videoId"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
    }


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/search')
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return "❌ Please enter a song name"
    result = search_youtube(query)
    if not result:
        return "❌ YouTube API failed or no results"
    return render_template("player.html",
                           title=result["title"],
                           thumbnail=result["thumbnail"],
                           video_id=result["video_id"])


@app.route('/stream')
def stream():
    video_id = request.args.get("v")
    if not video_id:
        return "Missing video ID", 400

    existing = glob.glob(f"/tmp/{video_id}.*")
    if existing:
        print(f"✅ Serving cached: {existing[0]}")
        return send_file(existing[0], conditional=True)

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'quiet': False,
        'noplaylist': True,
        'format': 'bestaudio/best',
        'outtmpl': f'/tmp/{video_id}.%(ext)s',
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'extractor_args': {
            'youtube': {
                'player_client': ['web'],
                'skip': ['hls', 'dash'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = glob.glob(f"/tmp/{video_id}.*")
        print(f"✅ Files found after download: {files}")

        if not files:
            return "Download failed - file not found", 500

        return send_file(files[0], conditional=True)

    except Exception as e:
        print("❌ yt-dlp error:", e)
        return f"Audio extraction failed: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
