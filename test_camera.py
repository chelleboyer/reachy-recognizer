"""Quick camera test"""
import cv2

print("Testing cameras...")
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Camera {i} works! Resolution: {frame.shape[1]}x{frame.shape[0]}")
        else:
            print(f"✗ Camera {i} opened but can't read frames")
        cap.release()
    else:
        print(f"✗ Camera {i} not available")

print("\nTrying DirectShow backend on Windows...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap.isOpened():
    ret, frame = cap.read()
    if ret:
        print(f"✓ Camera 0 with DirectShow works! Resolution: {frame.shape[1]}x{frame.shape[0]}")
        print("\nTest successful! Use: python gesture_voice_demo.py --webcam")
    cap.release()
else:
    print("✗ DirectShow backend failed")
