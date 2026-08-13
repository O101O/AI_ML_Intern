import cv2 #for computer vision  accessweb cam
import mediapipe as mp #hand traking 
import time #for time countdown 
from datetime import datetime #for saving photo with timestamp naming photo

# MediaPipe hand tracking modules drawing utilities
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


TIP = [4, 8, 12, 16, 20]#indexes of fingertip landmarks
PIP = [2, 6, 10, 14, 18]#indexes of PIP joints pip(proximal interphalangeal joints) it checks if finger is up or down



def finger_state(landmarks): # 1 for up, 0 for down
    s = []
    for tip, pip in zip(TIP, PIP):
        s.append(1 if landmarks.landmark[tip].y < landmarks.landmark[pip].y else 0)
    return s


def main(): #turns on webcam and starts hand tracking
    cap = cv2.VideoCapture(0)

    if not cap.isOpened(): #if camera not opening stop program
        print("Camera not opening")
        return

    #variables for snapshot timing and countdown
    last_snap = 0
    countdown = False
    start_time = 0


        # Use MediaPipe Hands for hand tracking
    with mp_hands.Hands(max_num_hands=1) as hands:
        while True:
            ret, frame = cap.read() #gets the current webcam image
            if not ret:
                break

            frame = cv2.flip(frame, 1) #mirror effect
            h, w, _ = frame.shape

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)#medaipipe works on RGB format
            res = hands.process(rgb)

            if res.multi_hand_landmarks: #if hand detected  draws line 
                lm = res.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)#draw hand skeleton

                state = finger_state(lm)

                if state == [0,1,1,0,0] and not countdown:#peace sign detected
                    countdown = True
                    start_time = time.time()
                    print("Peace detected → starting countdown")

            # COUNTDOWN
            if countdown:
                elapsed = time.time() - start_time #time elapsed  how many sec passed
                remain = 3 - int(elapsed) #remaining seconds in countdown

                if remain > 0:#show countdown on screen
                    cv2.putText(frame, str(remain), (w//2 - 30, h//2),
                                cv2.FONT_HERSHEY_SIMPLEX, 3, (0,255,0), 5)
                else:
                    # TAKE SNAPSHOT after countdown
                    fname = f"snap_{datetime.now().strftime('%H%M%S')}.jpg"
                    cv2.imwrite(fname, frame)
                    print("Saved:", fname)

                    countdown = False
                    time.sleep(1)

                #shows camera window
            cv2.imshow("TEST WINDOW", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()