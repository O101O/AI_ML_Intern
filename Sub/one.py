import cv2
import mediapipe as mp

hnads = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret: break
    cv2.imshow('Camera', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break



cap.release()
cv2.destroyAllWindows()

