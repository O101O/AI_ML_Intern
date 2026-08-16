import cv2
import time

def count_defects(cnt, hull):
    defects = cv2.convexityDefects(cnt, hull)
    if defects is None:
        return 0

    finger_count = 0
    for i in range(defects.shape[0]):
        s, e, f, d = defects[i, 0]
        start = tuple(cnt[s][0])
        end = tuple(cnt[e][0])
        far = tuple(cnt[f][0])

        # distance > 10000 gives nice accuracy for peace sign
        if d > 10000:
            finger_count += 1

    return finger_count

# ---- Open Camera ----
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not detected!")
    exit()

snap_taken = False

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera error!")
        break

    frame = cv2.flip(frame, 1)
    roi = frame[50:350, 50:350]  # region of interest for hand

    # Process image
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (35, 35), 0)
    _, thresh = cv2.threshold(blur, 80, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        cnt = max(contours, key=lambda x: cv2.contourArea(x))
        hull = cv2.convexHull(cnt, returnPoints=False)

        if hull is not None and len(hull) > 3:
            defects_count = count_defects(cnt, hull)

            # Peace sign = 2 fingers = 1 defect
            if defects_count == 1 and not snap_taken:
                print("Peace sign detected! Starting countdown...")

                # ---- Countdown ----
                for num in [3, 2, 1]:
                    countdown_frame = frame.copy()
                    cv2.putText(countdown_frame, str(num), (200, 200),
                                cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 5)
                    cv2.imshow("Peace Snap", countdown_frame)
                    cv2.waitKey(1000)

                # ---- Take snapshot ----
                filename = f"peace_snap_{int(time.time())}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Image saved as {filename}")

                snap_taken = True

    cv2.rectangle(frame, (50, 50), (350, 350), (0, 255, 0), 2)
    cv2.imshow("Peace Snap", frame)

    key = cv2.waitKey(1)
    if key == ord('r'):  
        snap_taken = False
        print("Ready for next snap...")
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()