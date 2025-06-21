# backend/app.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from flask_cors import CORS
from google import genai
from bs4 import BeautifulSoup
import requests

# Load the key from environment variable
API_KEY = os.getenv("API_KEY")
client = genai.Client(api_key=API_KEY)



app = Flask(__name__)
CORS(app)  # Enable CORS globally

def extract_video_id(url):
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    if parsed.hostname in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed.query).get("v", [None])[0]
    return None

@app.route("/api/transcript", methods=["POST"])
def get_transcript():
    data = request.json
    link = data.get("link")
    video_id = extract_video_id(link)
    if not video_id:
        return jsonify({"error": "Invalid link"}), 400

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([t["text"] for t in transcript])
        return jsonify({"transcript": full_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route("/api/generate-script", methods=["POST"])
def generate_script():
    data = request.json
    transcript = data.get("transcript")

    if not transcript:
        return jsonify({"error": "Transcript not provided"}), 400

    try:
        

        response = client.models.generate_content(
          model="gemini-2.0-flash",
          contents= f"""
            You are a professional YouTube script writer. 
             The infromation given to you is extracted from variuos resources now you are required to write a script for a YouTube video.
             Don't ignore rely on only one link make sure to consider the content given to you from all resouurces . The authore name shouldn't
             be included in the script from any source whether the video or the website.
             Here is the gathered information:
           {transcript}

            Rewrite it as a video script:

        """,
)
        generated_script = response.text;

        return jsonify({"script": generated_script})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/web-analyze", methods=["POST"])
def web_analyze():

    data = request.json
    link = data.get("link")
    
    try:
        res = requests.get(link, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator=' ', strip=True)

        # ✅ Don't generate script here
        return jsonify({"website_text": text})  # Just return content

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/generate-prompts", methods=["POST"])
def generate_prompts():
    data = request.json
    content = data.get("text")

    if not content:
        return jsonify({"error": "No text provided"}), 400

    try:
        prompt_text = f"""
        You are a creative assistant. Based on the content below, suggest user with 3 bet prompts that can be used
        to genertare valuable content like a gpt model like you. The prompt should be best , use best pratices in prompt generation
         Content:
        {content}

        """
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_text,
        )

        suggestions = response.text.strip()
        return jsonify({"prompts": suggestions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/api/summarize", methods=["POST"])
def summarize_content():
    data = request.json
    content = data.get("text")

    if not content:
        return jsonify({"error": "No content provided to summarize"}), 400

    try:
        prompt_text = f"""
        Please summarize the following content in a way that preserves **all key points** and important information.
        Avoid omitting critical insights or facts.

        Content:
        {content}

        Summary:
        """

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_text,
        )

        summary = response.text.strip()
        return jsonify({"summary": summary})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
