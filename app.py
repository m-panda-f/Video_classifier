import os
from flask import Flask, request, jsonify
import speech_recognition as sr
from moviepy import VideoFileClip

app = Flask(__name__)

# Define file paths
AUDIO_OUTPUT_PATH = 'output/audio.wav'
os.makedirs('output', exist_ok=True)

def extract_audio(video_path, output_audio_path):
    """Extract audio from the video."""
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = video_clip.audio
        audio_clip.write_audiofile(output_audio_path)
        audio_clip.close()
        video_clip.close()
        print(f"Audio extracted and saved to {output_audio_path}")
    except Exception as e:
        print(f"Error in extract_audio: {e}")

def transcribe_audio(audio_path):
    """Transcribe the audio to text."""
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)
            return text
    except sr.UnknownValueError:
        return "Google Speech Recognition could not understand the audio"
    except sr.RequestError as e:
        return f"Could not request results from Google Speech Recognition service; {e}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@app.route('/transcribe', methods=['POST'])
def transcribe_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video = request.files['video']
    video_path = os.path.join('uploads', video.filename)
    os.makedirs('uploads', exist_ok=True)
    video.save(video_path)

    # Extract audio and transcribe
    extract_audio(video_path, AUDIO_OUTPUT_PATH)
    transcription = transcribe_audio(AUDIO_OUTPUT_PATH)

    return jsonify({'transcription': transcription})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
