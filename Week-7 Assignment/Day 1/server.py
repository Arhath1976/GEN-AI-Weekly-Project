import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, request
from livekit import api


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/token")
def get_token():
    room_name = request.args.get("room", "test-room")
    identity = request.args.get("identity", "user-1")

    livekit_api_key = os.getenv("LIVEKIT_API_KEY")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET")
    livekit_url = os.getenv("LIVEKIT_URL")

    if not livekit_api_key or not livekit_api_secret or not livekit_url:
        return jsonify({
            "error": "Missing LiveKit env variables"
        }), 500

    token = (
        api.AccessToken(livekit_api_key, livekit_api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .to_jwt()
    )

    return jsonify({
        "url": livekit_url,
        "token": token,
        "room": room_name,
        "identity": identity,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)