import os
from flask import Flask, request, jsonify
import google.generativeai as genai
import speech_recognition as sr
from moviepy import VideoFileClip

app = Flask(__name__)

# Define file paths
AUDIO_OUTPUT_PATH = 'output/audio.wav'

# Replace with your actual API key
API_KEY = os.getenv('api_key')
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

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

def extract_rating_from_response(response_text):
    """Extract the rating number from the AI response."""
    words = response_text.split()
    for word in words:
        if word.isdigit():
            return word  # Return the first number found as the rating
    return "N/A"  # Default if no rating found

def get_ai_response(user_message):
    """Get AI response to classify the text and assign a rating."""
    try:
        prompt = (
            f"Determine if the following text is educational. If educational, provide a rating from 1 to 10, "
            f"where 10 is highly educational. Otherwise, classify as 'Non-Educational'.\n\n"
            f"Text: {user_message}\n"
            f"Output: 'Educational' with a rating, or 'Non-Educational'."
        )
        response = model.generate_content(prompt)
        
        if response.text:
            output = response.text.strip().lower()
            
            if "non-educational" in output:
                return "Non-Educational", "N/A"
            else:
                # Extract rating if present
                rating = extract_rating_from_response(output)
                return "Educational", rating
        else:
            return 'Sorry, I could not understand that.', "N/A"
    
    except Exception as e:
        print(f"Error: {e}")
        return 'Error: Could not generate a response.', "N/A"

@app.route('/classify', methods=['POST'])
def classify_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    video = request.files['video']
    video_path = os.path.join('uploads', video.filename)
    os.makedirs('uploads', exist_ok=True)
    video.save(video_path)

    extract_audio(video_path, AUDIO_OUTPUT_PATH)
    transcription = transcribe_audio(AUDIO_OUTPUT_PATH)
    classification, rating = get_ai_response(transcription)

    return jsonify({
        'transcription': transcription,
        'classification': classification,
        'rating': rating
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
