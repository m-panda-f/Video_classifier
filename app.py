import os
from flask import Flask, request, render_template_string
import google.generativeai as genai
import speech_recognition as sr
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Define file paths
AUDIO_OUTPUT_PATH = 'output/audio.wav'
os.makedirs('output', exist_ok=True)

# Replace with your actual API key
API_KEY = 'YOUR_API_KEY'
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def extract_audio(video_path, output_audio_path):
    """Extract audio from the video."""
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_audio_path)
    audio_clip.close()
    video_clip.close()

def transcribe_audio(audio_path):
    """Transcribe the audio to text."""
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Google Speech Recognition could not understand the audio"
    except sr.RequestError as e:
        return f"Could not request results; {e}"

def get_ai_response(user_message):
    """Classify text and provide an educational rating."""
    prompt = f"""
    Determine if the following text is educational and provide a rating from 1 to 10 if it is educational.
    Otherwise, classify as "Non-Educational".
    Text: {user_message}
    """
    response = model.generate_content(prompt)
    output = response.text.strip().lower()
    if "non-educational" in output:
        return "Non-Educational", "N/A"
    else:
        rating = [word for word in output.split() if word.isdigit()]
        return "Educational", rating[0] if rating else "N/A"

@app.route('/classify', methods=['POST'])
def classify_video():
    if 'video' not in request.files:
        return {'error': 'No video file provided'}, 400
    video = request.files['video']
    video_path = os.path.join('uploads', video.filename)
    os.makedirs('uploads', exist_ok=True)
    video.save(video_path)

    extract_audio(video_path, AUDIO_OUTPUT_PATH)
    transcription = transcribe_audio(AUDIO_OUTPUT_PATH)
    classification, rating = get_ai_response(transcription)

    return {
        'transcription': transcription,
        'classification': classification,
        'rating': rating
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
