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

    tmp_path = f"/tmp/{video_id}.webm"

    # Use cached file if already downloaded
    if not os.path.exists(tmp_path):
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': False,
            'noplaylist': True,
            'format': 'bestaudio[ext=webm]/bestaudio/best',
            'outtmpl': tmp_path,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios']
                }
            },
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            print("❌ yt-dlp download error:", e)
            return "Audio extraction failed", 500

    # send_file handles Range requests → duration + seeking works
    return send_file(tmp_path, mimetype='audio/webm', conditional=True)


if __name__ == '__main__':
    app.run(debug=True)
