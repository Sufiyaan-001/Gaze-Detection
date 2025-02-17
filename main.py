import cv2
import numpy as np
import dlib
import mediapipe as mp
import time
import textwrap
from math import hypot
from sklearn.metrics import accuracy_score, confusion_matrix
import pandas as pd

# Initialize webcam and dlib face detector with shape predictor
cap = cv2.VideoCapture(0)
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Virtual keyboard configuration
keyboard = np.zeros((600, 1200, 3), np.uint8)
key_width, key_height = 100, 100
cols = 12
keys_set_1 = {
    0: "1", 1: "2", 2: "3", 3: "4", 4: "5", 5: "6", 6: "7", 7: "8", 8: "9", 9: "0",
    10: "Q", 11: "W", 12: "E", 13: "R", 14: "T", 15: "Y", 16: "U", 17: "I", 18: "O", 19: "P",
    20: "A", 21: "S", 22: "D", 23: "F", 24: "G", 25: "H", 26: "J", 27: "K", 28: "L", 29: ";",
    30: "Z", 31: "X", 32: "C", 33: "V", 34: "B", 35: "N", 36: "M", 37: ",", 38: ".", 39: "/",
    40: "-", 41: "=", 42: "[", 43: "]", 44: "\\", 45: "'", 46: "`", 47: "!", 48: "@", 49: "#",
    50: "$", 51: "%", 52: "^", 53: "&", 54: "*", 55: "(", 56: ")", 57: "_", 58: "+", 59: "~"
}

# Text board configuration
board_width = 1000
board_height = 500
board = np.zeros((board_height, board_width), np.uint8)
board[:] = 255

# Function to draw a key on the virtual keyboard
def letter(letter_index, text, letter_light):
    x = (letter_index % cols) * key_width
    y = (letter_index // cols) * key_height
    th = 2

    if letter_light:
        cv2.rectangle(keyboard, (x + th, y + th), (x + key_width - th, y + key_height - th), (255, 255, 255), -1)  # White fill
    else:
        cv2.rectangle(keyboard, (x + th, y + th), (x + key_width - th, y + key_height - th), (255, 0, 0), th)  # Red border

    font_letter = cv2.FONT_HERSHEY_PLAIN
    font_scale = 3.5
    font_th = 2
    text_size = cv2.getTextSize(text, font_letter, font_scale, font_th)[0]

    text_x = x + (key_width - text_size[0]) // 2
    text_y = y + (key_height + text_size[1]) // 2

    cv2.putText(keyboard, text, (text_x, text_y), font_letter, font_scale, (255, 0, 0), font_th)


# Function to calculate the midpoint between two points
def midpoint(p1, p2):
    return (p1.x + p2.x) // 2, (p1.y + p2.y) // 2


# Function to calculate the blinking ratio
def get_blinking_ratio(eye_points, facial_landmarks):
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)

    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))

    hor_line_length = hypot(left_point[0] - right_point[0], left_point[1] - right_point[1])
    ver_line_length = hypot(center_top[0] - center_bottom[0], center_top[1] - center_bottom[1])

    ratio = hor_line_length / ver_line_length
    return ratio


# Variables to control text input
letter_index = 0
blinking_frames = 0
text = ""
blinking_threshold = 4.25  # Default blinking ratio threshold
frames_to_trigger = 5  # Frames required for a valid blink
key_switch_interval = 3  # Interval in seconds to switch keys

start_time = time.time()

while True:
    _, frame = cap.read()  # Capture webcam frame
    frame = cv2.resize(frame, None, fx=0.5, fy=0.5)  # Resize for performance
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
    
    # Reset keyboard and draw keys
    keyboard[:] = (0, 0, 0)
    
    # Switch keys every key_switch_interval seconds
    if time.time() - start_time >= key_switch_interval:
        letter_index += 1
        if letter_index >= len(keys_set_1):  # Wrap around if it exceeds total keys
            letter_index = 0
        start_time = time.time()  # Reset timer
    
    # Draw the keys and highlight the current one
    for i in range(len(keys_set_1)):
        letter(i, keys_set_1[i], i == letter_index)
    
    # Face detection and blink detection logic
    faces = detector(gray)  # Detect faces
    
    for face in faces:
        landmarks = predictor(gray, face)  # Get landmarks

        # Draw facial landmarks to verify
        for n in range(0, 68):  # Draw all 68 landmarks
            x = landmarks.part(n).x
            y = landmarks.part(n).y
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)  # Green dots to mark landmarks

        # Calculate blinking ratio for both eyes
        left_eye_ratio = get_blinking_ratio([36, 37, 38, 39, 40, 41], landmarks)
        right_eye_ratio = get_blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)

        blinking_ratio = (left_eye_ratio + right_eye_ratio) / 2
        
        # Display the calculated blinking ratio for debugging
        cv2.putText(frame, f"Blinking Ratio: {blinking_ratio:.2f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Blinking detection
        if blinking_ratio > blinking_threshold:
            cv2.putText(frame, "BLINKING", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 3)  # Display BLINKING
            blinking_frames += 1
            
            if blinking_frames >= frames_to_trigger:  # Validate a consistent blink
                text += keys_set_1[letter_index]  # Add letter to text
                blinking_frames = 0  # Reset blinking frames

        else:
            blinking_frames = 0  # Reset if not blinking

    # Display the text on the board
    max_chars_per_line = 40  # Maximum characters per line
    lines = textwrap.wrap(text, max_chars_per_line)  # Wrap text for multiple lines
    
    # Resize the board if needed
    new_board_height = len(lines) * 60
    if new_board_height > board_height:
        board_height = new_board_height
        board = np.zeros((board_height, board_width), np.uint8)  # Adjust board height
        board[:] = 255
    
    # Draw the text on the board
    for i, line in enumerate(lines):
        cv2.putText(board, line, (10, 60 * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

    # Display the frames
    cv2.imshow("Webcam Frame", frame)  # Main webcam frame
    cv2.imshow("Virtual Keyboard", keyboard)  # Virtual keyboard
    cv2.imshow("Text Board", board)  # Text board with input

    # Exit on ESC key
    if cv2.waitKey(10) & 0xFF == 27:  # ESC key
        break

# Release resources
cap.release()
cv2.destroyAllWindows()


import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Confusion Matrix
ground_truth_blinks = np.random.choice([0, 1], size=100, p=[0.7, 0.3])  # Example data
detected_blinks = np.random.choice([0, 1], size=100, p=[0.6, 0.4])  # Example data
conf_matrix = confusion_matrix(ground_truth_blinks, detected_blinks)

plt.figure(figsize=(6, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Not Blink', 'Blink'], yticklabels=['Not Blink', 'Blink'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix for Blink Detection')
plt.show()

# Blinking Ratio Distribution
blinking_ratios = np.random.normal(loc=5, scale=1, size=100)  # Example data
threshold = 4.25  # Example threshold
sns.histplot(blinking_ratios, kde=True, color='b', label='Blinking Ratios')
plt.axvline(threshold, color='r', linestyle='--', label='Blinking Threshold')
plt.xlabel('Blinking Ratio')
plt.ylabel('Frequency')
plt.title('Distribution of Blinking Ratios')
plt.legend()
plt.show()

# Typing Speed Over Time
time_points = np.linspace(0, 10, 10)  # Time intervals (in minutes)
typing_speed = np.random.randint(20, 60, size=10)  # Characters per minute
plt.plot(time_points, typing_speed, marker='o', linestyle='-', color='b', label='Typing Speed')
plt.xlabel('Time (minutes)')
plt.ylabel('Typing Speed (characters per minute)')
plt.title('Typing Speed Over Time')
plt.legend()
plt.show()

# Usability Metrics
user_feedback = {
    'blinking_comfort': np.random.randint(1, 10, size=10),  # Scale of 1 to 10
    'learning_curve': np.random.randint(5, 15, size=10),  # Time in minutes
    'typing_speed': np.random.randint(20, 60, size=10),  # Characters per minute
    'error_rate': np.random.randint(0, 5, size=10),  # Errors per minute
}

df = pd.DataFrame(user_feedback)
plt.figure(figsize=(12, 8))
sns.boxplot(data=df)
plt.xlabel('Metrics')
plt.ylabel('Values')
plt.title('Usability Metrics Box Plots')
plt.show()
