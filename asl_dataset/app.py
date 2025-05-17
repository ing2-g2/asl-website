from flask import Flask, render_template, Response
import cv2
import numpy as np
import mediapipe as mp
from tensorflow.keras.models import load_model
import time

app = Flask(__name__)

# Load model and mediapipe outside the loop
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

def generate_frames():
    global previous_letter, recognized_text, last_letter_time

    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

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

                    cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                    cv2.putText(frame, f'{asl_letter} ({confidence:.1f}%)', (x_min, y_min - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        current_time = time.time()
        if asl_letter != "" and asl_letter != previous_letter:
            last_letter_time = current_time
            previous_letter = asl_letter
        elif asl_letter == previous_letter and current_time - last_letter_time > 2.5:
            recognized_text += asl_letter
            last_letter_time = current_time
            previous_letter = ""

        cv2.putText(frame, f'Text: {recognized_text}', (10, 460),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

from flask import jsonify

@app.route('/recognized_text')
def get_recognized_text():
    global recognized_text
    return jsonify({'text': recognized_text})

if __name__ == '__main__':
    app.run(debug=True)
