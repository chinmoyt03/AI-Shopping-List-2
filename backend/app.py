from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import speech_recognition as sr
from pydub import AudioSegment
import os
import uuid
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1122'
app.config['MYSQL_DB'] = 'shopping_list'

mysql = MySQL(app)

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
                    print("Transcribed Text:", text)
                except sr.UnknownValueError:
                    return jsonify({"error": "Unable to understand audio"}), 400
                except sr.RequestError:
                    return jsonify({"error": "No results from audio"}), 500

            # Extract items, quantities, and units from text
            items = extract_items_from_text(text)

            # Save items to MySQL database
            save_items_to_db(items)
            
            return jsonify({"text": text, "items": items})

        finally:
            os.remove(audio_filename)
            os.remove(temp_wav_filename)

def extract_items_from_text(text):
    items = []
    
    # Split the text at the word "and" and extract items from each segment
    segments = text.split(" and ")
    pattern = re.compile(r'(\d+)\s*(kg|g|lbs|oz|liters|ml|units)\s*(\S+(?:\s+\S+)*)')  # Matches quantities, units, and nouns
    
    for segment in segments:
        matches = re.findall(pattern, segment)
        for match in matches:
            quantity = int(match[0])
            unit = match[1]
            item = match[2]
            items.append({"item": item, "quantity": quantity, "unit": unit})
    
    return items

def save_items_to_db(items):
    cur = mysql.connection.cursor()
    try:
        for item in items:
            # Check if the item already exists in the database
            cur.execute("SELECT * FROM shopping_items WHERE item = %s AND unit = %s", (item['item'], item['unit']))
            existing_item = cur.fetchone()

            if existing_item:
                # If the item exists, update the quantity
                new_quantity = existing_item[2] + item['quantity']
                cur.execute("UPDATE shopping_items SET quantity = %s WHERE id = %s", (new_quantity, existing_item[0]))
            else:
                # If the item does not exist, insert it into the database
                cur.execute("INSERT INTO shopping_items (item, quantity, unit) VALUES (%s, %s, %s)",
                            (item['item'], item['quantity'], item['unit']))

        mysql.connection.commit()
        return True
    except Exception as e:
        mysql.connection.rollback()
        print("Error saving items to database:", e)
        return False
    finally:
        cur.close()

def delete_item():
    try:
        data = request.json
        item_id = data.get('id')
        if not item_id:
            return jsonify({"error": "Invalid request, missing item ID"}), 400

        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM shopping_items WHERE id = %s", (item_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"message": "Item deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/shopping-list', methods=['GET'])
def get_shopping_list():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM shopping_items")
        shopping_items = cur.fetchall()
        cur.close()
        items = []
        for item in shopping_items:
            items.append({"item": item[1], "quantity": item[2], "unit": item[3]})
        return jsonify({"shopping_list": items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
