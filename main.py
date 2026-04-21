from flask import Flask, request, render_template
import requests
import base64
import os
from Crypto.Cipher import DES
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


from flask import Flask, request, render_template
import requests
import base64
import os
from Crypto.Cipher import DES
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)


def decrypt_url(encrypted_url):
    try:
        key = b"38346591"
        enc_url = encrypted_url.strip()
        missing_padding = len(enc_url) % 4
        if missing_padding:
            enc_url += "=" * (4 - missing_padding)
        enc = base64.b64decode(enc_url)
        cipher = DES.new(key, DES.MODE_ECB)
        decrypted = cipher.decrypt(enc)
        pad_len = decrypted[-1]
        url = decrypted[:-pad_len].decode('utf-8').strip()
        url = url.replace("_96.", "_320.").replace("96.mp4", "320.mp4")
        return url
    except Exception as e:
        print(f"Decrypt error: {e}")
        return None


def search_saavn(query, limit=10):
    try:
        url = "https://www.jiosaavn.com/api.php"
        params = {
            "__call": "search.getResults",
            "_format": "json",
            "_marker": "0",
            "api_version": "4",
            "ctx": "web6dot0",
            "n": str(limit),
            "q": query
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, params=params, headers=headers, timeout=10)
        data = res.json()

        songs = []
        for song in data.get("results", []):
            try:
                encrypted_url = song["more_info"]["encrypted_media_url"]
                audio_url = decrypt_url(encrypted_url)
                if not audio_url:
                    continue
                songs.append({
                    "title": song["title"],
                    "artist": song.get("more_info", {}).get("singers", "Unknown"),
                    "thumbnail": song.get("image", "").replace("150x150", "500x500"),
                    "audio_url": audio_url,
                    "duration": song.get("more_info", {}).get("duration", "")
                })
            except Exception as e:
                print(f"Skipping song: {e}")
                continue

        return songs

    except Exception as e:
        print(f"JioSaavn error: {e}")
        return []


@app.route('/')
def home():
    return render_template("index.html")


@app.route('/search')
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return "❌ Please enter a song name"

    songs = search_saavn(query)
    if not songs:
        return "❌ No songs found"

    return render_template("results.html", songs=songs, query=query)


@app.route('/play')
def play():
    title = request.args.get("title", "")
    artist = request.args.get("artist", "")
    thumbnail = request.args.get("thumbnail", "")
    audio_url = request.args.get("audio_url", "")

    if not audio_url:
        return "❌ No audio URL"

    return render_template("player.html",
                           title=title,
                           artist=artist,
                           thumbnail=thumbnail,
                           audio_url=audio_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
def search_saavn(query):
    try:
        url = "https://www.jiosaavn.com/api.php"
        params = {
            "__call": "search.getResults",
            "_format": "json",
            "_marker": "0",
            "api_version": "4",
            "ctx": "web6dot0",
            "n": "1",
            "q": query
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"JioSaavn status: {res.status_code}")
        data = res.json()

        song = data["results"][0]
        title = song["title"]
        artist = song.get("more_info", {}).get("singers", "")
        image = song.get("image", "").replace("150x150", "500x500")
        encrypted_url = song["more_info"]["encrypted_media_url"]

        print(f"Encrypted URL: {encrypted_url}")
        audio_url = decrypt_url(encrypted_url)
        print(f"✅ Decrypted audio URL: {audio_url}")

        return {
            "title": title,
            "artist": artist,
            "thumbnail": image,
            "audio_url": audio_url
        }

    except Exception as e:
        print(f"JioSaavn error: {e}")
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
    print(f"Final result: {result}")

    if not result or not result["audio_url"]:
        return "❌ Song not found"

    return render_template("player.html",
                           title=result["title"],
                           artist=result["artist"],
                           thumbnail=result["thumbnail"],
                           audio_url=result["audio_url"])


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
