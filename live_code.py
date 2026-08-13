import cv2  # for web camera
import mediapipe as mp
import time
from datetime import datetime

hands = mp.solutions.hands.Hands(max_num_hands=1)
draw = mp.solutions.drawing_utils

TIP = [4, 8, 12, 16, 20]
PIP = [2, 6, 10, 14, 18]


def fingers_up(lm):
    return [lm.landmark[t].y < lm.landmark[p].y for t, p in zip(TIP, PIP)]


cap = cv2.VideoCapture(0)
count, start = False, 0

while True:
    ok, frame = cap.read()
    if not ok:
        break
    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]

    res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0]

        draw.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)

        if fingers_up(lm) == [0, 1, 1, 0, 0] and not count:
            count, start = True, time.time()
            print("Peace -> countdown")

        if count:
            r = 3 - int(time.time() - start)
            if r > 0:
                cv2.putText(frame, str(r), (w // 2 - 40, h // 2), 1, 3, (0, 255, 0), 3)
            else:
                name = f"snap_{datetime.now().strftime("%H%M%S")}.jpg"
                cv2.imwrite(name, frame)
                print("saved:", name)
                time.sleep(1)
                count = False

    cv2.imshow("CAM", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
