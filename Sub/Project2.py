import cv2
import mediapipe as mp
from collections import deque
import time
from datetime import datetime   # NEW for saving photos

MAX_TRAIL = 40
CAM_INDEX = 0

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Fingertip IDs
TIP_IDS = [4, 8, 12, 16, 20] 
PIP_IDS = [2, 6, 10, 14, 18]  # PIP joints for comparison

TIP_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

trails = {tip: deque(maxlen=MAX_TRAIL) for tip in TIP_IDS}

def to_pixel(norm_x, norm_y, width, height):
    return int(norm_x * width), int(norm_y * height)


def finger_state(hand_landmarks):
    """Return list of finger states [Thumb, Index, Middle, Ring, Pinky] (1=up, 0=down)."""
    states = []

    for tip, pip in zip(TIP_IDS, PIP_IDS):
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
            states.append(1)  # finger is up
        else:
            states.append(0)  # finger is down

    return states


def main():
    cap = cv2.VideoCapture(CAM_INDEX)

    if not cap.isOpened():
        print("ERROR: Cannot access webcam.")
        return

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    ) as hands:

        prev_time = time.time()
        last_snap_time = 0  # NEW to prevent rapid snapping

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            peace_detected = False  # NEW

            if results.multi_hand_landmarks:
                for hand_idx, hand in enumerate(results.multi_hand_landmarks):

                    mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                    states = finger_state(hand)  # NEW
                    # states example: [0,1,1,0,0] → index & middle up

                    if states == [0,1,1,0,0]:    # NEW peace sign rule
                        peace_detected = True
                        cv2.putText(frame, "PEACE SIGN DETECTED!", (50, 80),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 3)

                    # Trail logic
                    for tip_id, name in zip(TIP_IDS, TIP_NAMES):
                        lm = hand.landmark[tip_id]
                        px, py = to_pixel(lm.x, lm.y, w, h)
                        trails[tip_id].appendleft((px, py))
                        cv2.circle(frame, (px, py), 10, (0,255,120), -1)
                        cv2.putText(frame, name, (px+12, py+5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

                # Draw trails
                for tip_id in TIP_IDS:
                    pts = list(trails[tip_id])
                    for i in range(1, len(pts)):
                        cv2.line(frame, pts[i-1], pts[i], (0,180,0), 2)

            # NEW --- SNAP WHEN PEACE SIGN IS SHOWN
            if peace_detected and time.time() - last_snap_time > 2:
                last_snap_time = time.time()

                # flash
                flash = frame.copy()
                cv2.rectangle(flash, (0,0), (w,h), (255,255,255), -1)
                cv2.addWeighted(flash, 0.4, frame, 0.6, 0, frame)

                filename = f"peace_snap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(filename, frame)
                print(f"SNAPPED & SAVED → {filename}")

            # FPS
            now = time.time()
            fps = 1 / (now - prev_time)
            prev_time = now

            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

            cv2.imshow("Five Finger Tracker + Peace Snap", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()