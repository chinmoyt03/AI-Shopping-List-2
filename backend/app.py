from flask import Flask, request, jsonify
from flask_cors import CORS
import speech_recognition as sr
from pydub import AudioSegment
import os
import uuid
from transformers import pipeline

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize NLP model for item extraction
item_extraction_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")


@app.route('/ab', methods=['POST', 'GET'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        file_extension = file.filename.split('.')[-1]
        audio_filename = f"{uuid.uuid4()}.{file_extension}"
        temp_wav_filename = "converted.wav"
        
        try:
            file.save(audio_filename)

            # Convert audio to text
            recognizer = sr.Recognizer()
            audio = AudioSegment.from_file(audio_filename)
            audio.export(temp_wav_filename, format="wav")

            with sr.AudioFile(temp_wav_filename) as source:
                audio_data = recognizer.record(source)
                try:
                    text = recognizer.recognize_google(audio_data)
                except sr.UnknownValueError:
                    return jsonify({"error": "unable to understand audio"}), 400
                except sr.RequestError:
                    return jsonify({"error": "No results from audio"}), 500

            # Extract items and quantities from text
            items = extract_items_from_text(text)
            return jsonify({"text": text, "items": items})
        
        finally:
            os.remove(audio_filename)
            os.remove(temp_wav_filename)

def extract_items_from_text(text):
    # Extract entities using NLP model
    entities = item_extraction_pipeline(text)

    # Extract item names and quantities
    items = []
    for entity in entities:
        if entity['entity_group'] == 'MISC':
            items.append(entity['word'])

    return [{"item": item, "quantity": 1} for item in items]

if __name__ == '__main__':
    app.run(debug=True)
