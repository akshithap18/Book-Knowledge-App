from datetime import datetime
import logging
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
import threading
import os
import vertexai
import base64
from vertexai.generative_models import GenerativeModel, Part
import json
from google.cloud import texttospeech_v1
import os

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


UPLOAD_FOLDER = 'uploads'
RESPONSE_FOLDER = 'responses'
BOOK_FOLDER = 'books'
ALLOWED_EXTENSIONS = {'wav'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESPONSE_FOLDER, exist_ok=True)
os.makedirs(BOOK_FOLDER, exist_ok=True)

#project_id = "conversational-ai-448717"

client_texttospeech=texttospeech_v1.TextToSpeechClient()

prompt = """
Analyse the upload pdf book. 
Answer to audio question.
"""

#vertexai.init(project=project_id, location="us-central1")
vertexai.init()
model = GenerativeModel("gemini-1.5-flash-001")
voice = texttospeech_v1.VoiceSelectionParams(language_code = "en-US",ssml_gender = "FEMALE")
audio_config = texttospeech_v1.AudioConfig(audio_encoding = "LINEAR16",speaking_rate=0.9)

def vertexAI(audio_part,pdf_part, filename):
    try:
        logging.info(f"before AI")
        prompt_part = Part.from_text(prompt)
        response = model.generate_content([pdf_part, audio_part, prompt_part])
        logging.info(f"after ai")
        threading.Thread(target=text_to_speech, args=(response.text, filename,)).start()
        logging.info(f"after thread")
        return None
    except Exception as e:
        logging.error(f"An error occurred during audio-to-text processing: {e}")
        return None

def text_to_speech(text, filename):
    logging.info(f"Converting text to speech for file: {filename}")
    try:
        input = texttospeech_v1.SynthesisInput(text=text)
        request = texttospeech_v1.SynthesizeSpeechRequest(input=input, voice=voice, audio_config=audio_config)
        response = client_texttospeech.synthesize_speech(request=request)
        file_path = os.path.join(RESPONSE_FOLDER, filename)
        with open(file_path, 'wb') as f:
            f.write(response.audio_content)
        logging.info(f"Text-to-speech file saved: {filename}")
    except Exception as e:
        logging.error(f"Error during text-to-speech conversion: {e}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files(dir_path):
    files = []
    for filename in os.listdir(dir_path):
        if allowed_file(filename):
            files.append(filename)
    files.sort(reverse=True)
    return files

@app.route('/')
def index():
    files = get_files(UPLOAD_FOLDER)
    return render_template('index.html', files=files)

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    logging.info(f"Start api")
    pdf_filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.pdf'
    pdf_file_path = os.path.join(BOOK_FOLDER, pdf_filename)
    request.files['pdf_data'].save(pdf_file_path)

    with open(pdf_file_path, "rb") as pdf_data:
        pdf_part = Part.from_data(data=pdf_data.read(), mime_type="application/pdf")

    logging.info(f"pdf save")

    audio_filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    audio_file_path = os.path.join(UPLOAD_FOLDER, audio_filename)
    request.files['audio_data'].save(audio_file_path)

    with open(audio_file_path, "rb") as audio_file:
        audio_part = Part.from_data(data=audio_file.read(), mime_type="audio/wav")

    logging.info(f"audio save")

    vertexAI(pdf_part, audio_part, audio_filename)

    return redirect('/')


@app.route('/upload/<filename>')
def get_file(filename):
    return send_file(filename)


@app.route('/script.js',methods=['GET'])
def scripts_js():
    return send_file('./script.js')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/response/<filename>')
def response_file(filename):
    return send_from_directory(RESPONSE_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)

