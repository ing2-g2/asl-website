from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
import time
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)

# Load model and mediapipe
model = load_model('asl_cnn_model.h5')
image_size = 32
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

previous_letter = None
recognized_text = ""
last_letter_time = 0

def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (15, 15), 0)
    _, thresholded = cv2.threshold(gray, 161, 255, cv2.THRESH_BINARY)
    resized = cv2.resize(thresholded, (image_size, image_size))
    normalized = resized / 255.0
    reshaped = np.reshape(normalized, (1, image_size, image_size, 1))
    return reshaped

def predict_asl_letter(prediction):
    asl_letters = 'ABCDEFGHIKLMNOPQRSTUVWXY'  # No J, Z
    return asl_letters[prediction]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict_frame', methods=['POST'])
def predict_frame():
    global previous_letter, recognized_text, last_letter_time

    data = request.get_json()
    if 'image' not in data:
        return jsonify({'error': 'No image provided'}), 400

    try:
        # Decode base64 image
        image_data = data['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        frame = np.array(image)

        # Preprocess frame for hand detection
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.flip(frame, 1)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(frame_rgb)

        asl_letter = ""

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                h, w, c = frame.shape
                x_min, y_min = w, h
                x_max, y_max = 0, 0

                for landmark in hand_landmarks.landmark:
                    x, y = int(landmark.x * w), int(landmark.y * h)
                    x_min, y_min = min(x_min, x), min(y_min, y)
                    x_max, y_max = max(x_max, x), max(y_max, y)

                margin = 30
                x_min = max(0, x_min - margin)
                y_min = max(0, y_min - margin)
                x_max = min(w, x_max + margin)
                y_max = min(h, y_max + margin)

                hand_image = frame[y_min:y_max, x_min:x_max]

                if hand_image.size > 0:
                    preprocessed = preprocess_image(hand_image)
                    prediction = model.predict(preprocessed)
                    predicted_label = np.argmax(prediction)
                    confidence = np.max(prediction) * 100
                    asl_letter = predict_asl_letter(predicted_label)

        # Update recognized text logic
        current_time = time.time()
        if asl_letter != "" and asl_letter != previous_letter:
            last_letter_time = current_time
            previous_letter = asl_letter
        elif asl_letter == previous_letter and current_time - last_letter_time > 1.5:
            recognized_text += asl_letter
            last_letter_time = current_time
            previous_letter = ""

        return jsonify({'letter': asl_letter})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_text', methods=['POST'])
def update_text():
    global recognized_text

    key = request.json.get('key')

    if key == 'c':
        recognized_text = ''
    elif key == 's':
        recognized_text += " "
    elif key == 'b':
        recognized_text = recognized_text[:-1]

    return {'status': 'success', 'recognized_text': recognized_text}

@app.route('/recognized_text')
def get_recognized_text():
    global recognized_text
    return jsonify({'text': recognized_text})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
