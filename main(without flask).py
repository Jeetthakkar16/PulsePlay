from flask import Flask, request, render_template
import requests
from yt_dlp import YoutubeDL

app = Flask(__name__)

API_KEY = "YOUR_API_KEY"

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
        'format': 'bestaudio/best',
        'quiet': True
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']


# 🏠 Home page
@app.route('/')
def home():
    return render_template("index.html")


# 🔍 Search route
@app.route('/search')
def search():
    query = request.args.get("q")

    result = search_youtube(query)
    audio_url = get_audio_url(result["video_id"])

    return render_template("player.html",
                           title=result["title"],
                           thumbnail=result["thumbnail"],
                           audio_url=audio_url)


if __name__ == '__main__':
    app.run(debug=True)
