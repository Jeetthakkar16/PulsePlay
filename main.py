from flask import Flask, request, render_template, Response, send_file
import requests
from yt_dlp import YoutubeDL
import os
import imageio_ffmpeg
from dotenv import load_dotenv

load_dotenv()
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

app = Flask(__name__)
API_KEY = os.getenv("API_KEY")
YOUTUBE_COOKIES = os.getenv("YOUTUBE_COOKIES")  # ← NEW

# Write cookies to /tmp at startup ← NEW
COOKIE_FILE = "/tmp/yt_cookies.txt"
if YOUTUBE_COOKIES:
    with open(COOKIE_FILE, "w") as f:
        f.write(YOUTUBE_COOKIES)
    print("✅ Cookies written successfully")
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


import glob

@app.route('/stream')
def stream():
    video_id = request.args.get("v")
    if not video_id:
        return "Missing video ID", 400

    # Find any already cached file for this video
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
                'player_client': ['ios']
            }
        },
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find what yt-dlp actually saved
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
