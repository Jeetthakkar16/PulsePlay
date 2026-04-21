from flask import Flask, request, render_template
import requests
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


def search_saavn(query):
    apis = [
        "https://jiosaavn-api-privatecoder.vercel.app/search/songs",
        "https://jiosaavn-api-sigma.vercel.app/api/search/songs",
        "https://jiosaavn-api-ts.vercel.app/search/songs",
    ]

    for api_url in apis:
        try:
            params = {"query": query, "page": 1, "limit": 1}
            res = requests.get(api_url, params=params, timeout=8)
            print(f"Trying {api_url} → status {res.status_code}")

            if res.status_code != 200 or not res.text.strip():
                print(f"Empty or bad response from {api_url}")
                continue

            data = res.json()
            print("Saavn response:", data)

            results = data.get("data", {}).get("results", [])
            if not results:
                continue

            song = results[0]

            download_url = None
            for quality in ["320kbps", "160kbps", "96kbps"]:
                for item in song.get("downloadUrl", []):
                    if item["quality"] == quality and item["url"]:
                        download_url = item["url"]
                        break
                if download_url:
                    break

            if not download_url:
                continue

            return {
                "title": song["name"],
                "artist": song["artists"]["primary"][0]["name"] if song["artists"]["primary"] else "",
                "thumbnail": song["image"][-1]["url"],
                "audio_url": download_url
            }

        except Exception as e:
            print(f"Error with {api_url}: {e}")
            continue

    return None


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/search')
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return "❌ Please enter a song name"

    result = search_saavn(query)
    if not result or not result["audio_url"]:
        return "❌ Song not found"

    return render_template("player.html",
                           title=result["title"],
                           artist=result["artist"],
                           thumbnail=result["thumbnail"],
                           audio_url=result["audio_url"])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
