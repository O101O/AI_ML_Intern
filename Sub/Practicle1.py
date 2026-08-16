import cv2 # OpenCV for video capture and drawing
import mediapipe as mp # MediaPipe for hand tracking
from collections import deque # For storing motion trails
import time # For calculating FPS

# ------------ CONFIG -------------
MAX_TRAIL = 40          # length of finger movement trail
CAM_INDEX = 0           # change to 1 or 2 if external webcam
# ---------------------------------

#load medaipipe hand tracking modules

mp_hands = mp.solutions.hands # MediaPipe Hands solution
mp_draw = mp.solutions.drawing_utils # MediaPipe drawing utilities

# Fingertip landmark IDs for MediaPipe Hands
TIP_IDS = [4, 8, 12, 16, 20] # Thumb, Index, Middle, Ring, Pinky tips
TIP_NAMES = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

# For drawing motion trails
trails = {tip: deque(maxlen=MAX_TRAIL) for tip in TIP_IDS}


def to_pixel(norm_x, norm_y, width, height):
    """Convert normalized MediaPipe coords to pixel coords."""
    return int(norm_x * width), int(norm_y * height) #normal value convert


#main function start
#code run garna lai use  garna main
def main():
    cap = cv2.VideoCapture(CAM_INDEX)

    if not cap.isOpened():
        print("ERROR: Cannot access webcam. Try CAM_INDEX = 1 or 2.")
        return

    with mp_hands.Hands(
        static_image_mode=False, #live video mode
        max_num_hands=2, #detect both hands
        min_detection_confidence=0.6, #minimum confidence for detection 0 to 1
        min_tracking_confidence=0.6 #minimum confidence for tracking 0 to 1 smooth tracking
    ) as hands:

        prev_time = time.time()
            #main loop run unless press q to quit
        while True:
            ret, frame = cap.read() #read frame from webcam size define
            if not ret:
                print("ERROR: Cannot read frame.")
                break

            frame = cv2.flip(frame, 1)  #mirror effect flips horizontally
            h, w, _ = frame.shape

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #convert BGR to RGB color
            results = hands.process(rgb_frame) #process the frame to detect hands run ml model to detect hands 

            if results.multi_hand_landmarks: #hand detected if found
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks): #hand number 0 xaina or 1 xa  21 land marks detect garna

                    # Draw hand skeleton bone points
                    mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        mp_hands.HAND_CONNECTIONS
                    )

                    # Track each fingertip
                    for tip_id, name in zip(TIP_IDS, TIP_NAMES): #matches id and name of hand tips
                        lm = hand_landmarks.landmark[tip_id] #fingertip landmark
                        px, py = to_pixel(lm.x, lm.y, w, h) # convert to pixel

                        # Save position to trails
                        trails[tip_id].appendleft((px, py)) #new point 

                        # Draw fingertip dot
                        cv2.circle(frame, (px, py), 10, (0, 255, 120), -1) #draw circle on fingertip -1 coklor fill garna

                        # Label the fingertip
                        cv2.putText(frame, name, (px + 12, py + 5), #label the fingertip
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                                    (255, 255, 255), 1)

                        # Print coordinates to terminal
                        print(f"Hand {hand_idx+1} - {name}: ({px}, {py})") #print coordinates in terminal

                # Draw motion trails for each finger
                for tip_id in TIP_IDS:
                    points = list(trails[tip_id])
                    for i in range(1, len(points)): #convert in list 
                        cv2.line(frame, points[i - 1], points[i], (0, 180, 0), 2)

            # FPS counter show frame rate on screen
            now = time.time()
            fps = 1 / (now - prev_time)
            prev_time = now

            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25),  #fps fit top left corner
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (200, 200, 200), 2)

            cv2.imshow("Linux Five Finger Tracker", frame) #display window frame

            # Quit on 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'): #press q to quit 
                break

    cap.release()
    cv2.destroyAllWindows() #close all windows


if __name__ == "__main__":
    main() #run main function hold up program 