import cv2
import mediapipe as mp
from math import hypot
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np
import tkinter as tk
from tkinter import simpledialog

# Function to calculate distance between two points
def calculate_distance(x1, y1, x2, y2):
    return hypot(x2 - x1, y2 - y1)

def control_volume(length, volMin, volMax):
    global volume  # Make the volume variable global so it can be accessed within this function
    # Control volume based on hand gesture
    vol = np.interp(length, [30, 350], [volMin, volMax])
    volume.SetMasterVolumeLevel(vol, None)
    volbar = np.interp(length, [30, 350], [400, 150])
    volper = np.interp(length, [30, 350], [0, 100])
    return volbar, volper

def detect_gestures(lmList, img):
    # Hand gesture detection code
    if len(lmList) >= 5:
        x1, y1 = lmList[0][1], lmList[0][2]  # Palm landmark
        x5, y5 = lmList[4][1], lmList[4][2]  # Thumb tip

        # Calculate the distance between the thumb tip and palm
        palm_length = calculate_distance(x1, y1, x5, y5)

        # You can adjust this threshold value based on your preference
        # Smaller values will be more sensitive to detecting palms, larger values for fists.
        threshold_value = 50

        if palm_length > threshold_value:
            # If the palm_length is larger than the threshold, it's a palm gesture
            cv2.putText(img, "Palm Detected", (10, 80), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        else:
            # Otherwise, it's a fist gesture
            cv2.putText(img, "Fist Detected", (10, 80), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)

def detect_asl_a(lmList, img):
    # Sign language detection for letter 'A'
    if len(lmList) >= 5:
        x1, y1 = lmList[8][1], lmList[8][2]  # Index finger tip
        x2, y2 = lmList[4][1], lmList[4][2]  # Thumb tip

        # Calculate the distance between the index finger tip and thumb tip
        finger_length = calculate_distance(x1, y1, x2, y2)

        # You can adjust this threshold value based on your preference
        # Smaller values will be more sensitive to detecting the letter "A".
        threshold_value = 40

        if finger_length < threshold_value:
            # If the finger_length is smaller than the threshold, it's the letter "A" in ASL
            cv2.putText(img, "ASL 'A' Detected", (10, 80), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

# Interface for the user to choose control options using simpledialog
def choose_control_option():
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window

    option = simpledialog.askstring("Choose Control Option", "Select an option:\n1. Volume Control\n2. Gesture Detection\n3. Both (Volume Control + Gesture Detection)\n4. Sign Language Detection")
    root.destroy()

    if option == "1":
        return 1
    elif option == "2":
        return 2
    elif option == "3":
        return 3
    elif option == "4":
        return 4

# Main program
cap = cv2.VideoCapture(0)
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils

devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volMin, volMax = volume.GetVolumeRange()[:2]

control_option = choose_control_option()

while True:
    success, img = cap.read()
    imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    results = hands.process(imgRGB)
    lmList = []

    if results.multi_hand_landmarks:
        for handlandmark in results.multi_hand_landmarks:
            for id, lm in enumerate(handlandmark.landmark):
                h, w, _ = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmList.append([id, cx, cy])
            mpDraw.draw_landmarks(img, handlandmark, mpHands.HAND_CONNECTIONS)

        if control_option in (2, 3):
            detect_gestures(lmList, img)

        if control_option == 4:
            detect_asl_a(lmList, img)

    if control_option in (1, 3):
        if lmList:
            x1, y1 = lmList[4][1], lmList[4][2]  # Thumb tip
            x2, y2 = lmList[8][1], lmList[8][2]  # Index finger tip
            length = calculate_distance(x1, y1, x2, y2)
            volbar, volper = control_volume(length, volMin, volMax)
            volume_control_text = f"Volume: {int(volper)}%"
            cv2.rectangle(img, (50, 150), (85, 400), (0, 0, 255), 4)
            cv2.rectangle(img, (50, int(volbar)), (85, 400), (0, 0, 255), cv2.FILLED)
            cv2.putText(img, volume_control_text, (10, 40), cv2.FONT_ITALIC, 1, (0, 255, 98), 3)
            # Draw a line between index finger and thumb
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 3)

    cv2.imshow('Hand Gesture and Sign Language Detection', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()