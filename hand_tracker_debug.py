import cv2
import numpy as np

print("Starting hand tracker...")
print(f"OpenCV version: {cv2.__version__}")

# Open webcam
print("Opening webcam...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Cannot open webcam!")
    exit(1)

print("Webcam opened successfully")
print(f"Camera properties: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}")

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("ERROR: Failed to read frame")
        break

    frame_count += 1
    if frame_count == 1:
        print(f"First frame received: {frame.shape}")
        print("Windows should appear now...")

    frame = cv2.flip(frame, 1)

    # Convert to HSV for skin detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Skin color range (works for most)
    lower = np.array([0, 30, 60])
    upper = np.array([20, 150, 255])

    mask = cv2.inRange(hsv, lower, upper)

    # Blur + threshold clean-up
    mask = cv2.GaussianBlur(mask, (7, 7), 0)

    # Find contours of hand
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Take biggest contour (hand)
        c = max(contours, key=cv2.contourArea)

        # Draw contour
        cv2.drawContours(frame, [c], -1, (0, 255, 0), 3)

        # Find center of hand
        M = cv2.moments(c)
        if M["m00"] != 0:
            x = int(M["m10"] / M["m00"])
            y = int(M["m01"] / M["m00"])

            # Draw center point
            cv2.circle(frame, (x, y), 10, (255, 0, 0), -1)
            cv2.putText(frame, f"Hand Center: {x}, {y}", (x + 20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Simple CV2 Hand Tracker", frame)
    cv2.imshow("Mask", mask)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        print("Quitting...")
        break

print(f"Total frames processed: {frame_count}")
cap.release()
cv2.destroyAllWindows()
print("Done!")
