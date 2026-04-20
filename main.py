from flask import Flask, request, render_template
import requests
from yt_dlp import YoutubeDL
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

# 🔍 Search function
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

    print("DATA:", data)  # 🔥 debug

    # ✅ FIX: Prevent crash
    if "items" not in data or len(data["items"]) == 0:
        return None

    item = data["items"][0]

    return {
        "title": item["snippet"]["title"],
        "video_id": item["id"]["videoId"],
        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
    }


# 🎧 Extract audio
def get_audio_url(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'quiet': True,
        'noplaylist': True,
        'format': 'bestaudio/best',
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'web'],  # ios is more reliable than android
                'skip': ['dash', 'hls'],
            }
        },
        'http_headers': {
            'User-Agent': 'com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X)',
        },
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None

            formats = info.get("formats", [])

            # Best: audio-only stream
            for f in reversed(formats):  # reversed = best quality last
                if f.get("acodec") != "none" and f.get("vcodec") == "none":
                    audio_url = f.get("url")
                    if audio_url:
                        return audio_url

            # Fallback: any format with audio
            for f in reversed(formats):
                if f.get("acodec") != "none":
                    audio_url = f.get("url")
                    if audio_url:
                        return audio_url

            return None

    except Exception as e:
        print("yt-dlp error:", e)
        return None
# 🏠 Home page
@app.route('/')
def home():
    return render_template("index.html")


# 🔍 Search route
@app.route('/search')
def search():
    query = request.args.get("q", "").strip()

    print("QUERY:", query)

    if not query:
        return "❌ Please enter a song name"

    result = search_youtube(query)

    if not result:
        return "❌ YouTube API failed or no results"

    audio_url = get_audio_url(result["video_id"])

    if not audio_url:
        return "❌ Audio extraction failed"

    return render_template("player.html",
                           title=result["title"],
                           thumbnail=result["thumbnail"],
                           audio_url=audio_url)


if __name__ == '__main__':
    app.run(debug=True)
