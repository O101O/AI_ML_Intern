import cv2
from ultralytics import YOLO

# --- 1. Load the Model ---
# Load a pre-trained YOLO model. 'yolov8n.pt' is the nano version of YOLOv8, 
# which is fast and small. Replace this with your preferred model file.
model = YOLO('yolov8n.pt')
# Use CPU to avoid GPU compatibility issues with older NVIDIA cards
model.to('cpu')

# --- 2. Load the Image/Video (We'll use an image for simplicity) ---
# Specify the path to the image you want to process.
image_path = '/home/ps/Pictures/Webcam/2025-11-10-081043.jpg'  # Replace with your image file path
img = cv2.imread(image_path)

if img is None:
    print(f"Error: Could not load image at {image_path}")
    exit()

# --- 3. Perform Detection ---
# Run the YOLO model on the image. 'conf' sets the minimum confidence score 
# for a detection to be considered valid (e.g., 0.25 = 25%).
results = model(img, conf=0.25, device='cpu')

# --- 4. Process and Draw Results ---
# The results object contains all detected objects.
# We'll loop through the detected boxes (bboxes) and draw them.
for r in results:
    # 'boxes' contains bounding box coordinates, confidence scores, and class IDs
    boxes = r.boxes
    
    for box in boxes:
        # Get integer coordinates (x1, y1, x2, y2) for the bounding box
        # .xyxy returns [x1, y1, x2, y2] format
        x1, y1, x2, y2 = [int(val) for val in box.xyxy[0]]
        
        # Get the confidence score (a float between 0 and 1)
        conf = box.conf[0].item()
        
        # Get the class ID (an integer)
        cls = int(box.cls[0].item())
        
        # Look up the class name from the model's names dictionary
        class_name = model.names[cls]
        
        # Draw the bounding box (Green color, 2 pixel thickness)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Create the label text (e.g., 'person 0.95')
        label = f'{class_name} {conf:.2f}'
        
        # Put the text label above the box (White text, Black background)
        # Ensure label doesn't go off the top of the image
        label_y = max(y1 - 10, 20)
        cv2.putText(img, label, (x1, label_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        print(f"Detected: {label} at coordinates ({x1}, {y1})")

# --- 5. Display the Output Image ---
cv2.imshow('YOLO Detection Output', img)

# Wait indefinitely for a key press (0) and then close all windows
cv2.waitKey(0)
cv2.destroyAllWindows()