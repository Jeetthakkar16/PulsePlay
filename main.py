from flask import Flask, request, render_template
import requests
from yt_dlp import YoutubeDL
import os
from dotenv import load_dotenv

load_dotenv()

import imageio_ffmpeg
os.environ["PATH"] += os.pathsep + os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())

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
    
    # Try multiple clients in order
    clients = ['ios', 'web_creator', 'tv_embedded']
    
    for client in clients:
        ydl_opts = {
            'quiet': False,
            'noplaylist': True,
            'format': 'bestaudio/best',
            'extractor_args': {
                'youtube': {
                    'player_client': [client],
                }
            },
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    continue

                formats = info.get("formats", [])

                for f in reversed(formats):
                    if f.get("acodec") != "none" and f.get("vcodec") == "none":
                        if f.get("url"):
                            print(f"✅ Got audio via client: {client}")
                            return f["url"]

                for f in reversed(formats):
                    if f.get("acodec") != "none":
                        if f.get("url"):
                            return f["url"]

        except Exception as e:
            print(f"❌ Client {client} failed: {e}")
            continue

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
