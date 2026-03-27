"""
collect_faces2.py
Better data collection — shows exactly what the model sees in real time.
Collect 500 images per emotion this time for better accuracy.
Run: python collect_faces2.py
"""

import cv2
import numpy as np
from pathlib import Path
import time

IMG_SIZE = (48, 48)
SAMPLES_PER_CLASS = 500

EMOTIONS = {
    "happy":    "😊 SMILE / LAUGH / SHOW TEETH",
    "stressed": "😰 FROWN / TENSE / FURROW BROWS / ANGRY",
    "sleepy":   "😴 HALF CLOSE EYES / NEUTRAL / TIRED LOOK",
}

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def collect(label, description, output_dir, target=SAMPLES_PER_CLASS):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear old data for this emotion
    for f in output_dir.glob("*.jpg"):
        f.unlink()
    print(f"[INFO] Cleared old {label} data. Collecting fresh {target} images.")

    cap = cv2.VideoCapture(0)
    count = 0
    last_capture = 0
    CAPTURE_INTERVAL = 0.05  # capture every 50ms = fast collection

    print(f"\n{'='*55}")
    print(f"  EMOTION: {label.upper()} — {description}")
    print(f"  Press SPACE to start | Q to finish early")
    print(f"{'='*55}\n")

    capturing = False

    while count < target:
        ret, frame = cap.read()
        if not ret:
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        face_detected = len(faces) > 0

        # Show what model sees (48x48 crop)
        preview = np.zeros((48, 48), dtype=np.uint8)
        if face_detected:
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            face_crop = gray[y:y+h, x:x+w]
            preview = cv2.resize(face_crop, IMG_SIZE)

        # Scale preview up for display
        preview_big = cv2.resize(preview, (144, 144), interpolation=cv2.INTER_NEAREST)
        preview_big = cv2.cvtColor(preview_big, cv2.COLOR_GRAY2BGR)
        cv2.putText(preview_big, "Model sees:", (5, 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0,255,255), 1)

        # Overlay on main frame
        frame[10:154, 10:154] = preview_big

        # Status bar
        color = (0,255,0) if capturing else (0,165,255)
        status = f"{'CAPTURING' if capturing else 'PAUSED'} | {count}/{target}"
        cv2.rectangle(frame, (0, frame.shape[0]-60), (frame.shape[1], frame.shape[0]), (0,0,0), -1)
        cv2.putText(frame, f"{label.upper()}: {description}", (10, frame.shape[0]-38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1)
        cv2.putText(frame, status, (10, frame.shape[0]-12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, "FACE OK" if face_detected else "NO FACE",
                    (frame.shape[1]-120, frame.shape[0]-12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                    (0,255,0) if face_detected else (0,0,255), 2)

        # Progress bar
        progress = int((count / target) * frame.shape[1])
        cv2.rectangle(frame, (0, frame.shape[0]-3), (progress, frame.shape[0]), (0,255,100), -1)

        cv2.imshow(f"Collecting: {label.upper()}", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord(" "):
            capturing = not capturing

        # Auto capture at interval
        now = time.time()
        if capturing and face_detected and (now - last_capture) >= CAPTURE_INTERVAL:
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            face_crop  = gray[y:y+h, x:x+w]
            face_small = cv2.resize(face_crop, IMG_SIZE)
            cv2.imwrite(str(output_dir / f"{label}_{count:05d}.jpg"), face_small)
            count += 1
            last_capture = now
            if count % 100 == 0:
                print(f"  {count}/{target} captured...")

    cap.release()
    cv2.destroyAllWindows()
    print(f"✅ {label}: {count} images saved.")
    return count


def main():
    base = Path("./my_face_data")
    print("\n🎥 Smart Lamp — Face Data Collector v2")
    print("Tips for best results:")
    print("  ✅ Good front lighting on your face")
    print("  ✅ Sit 40-60cm from camera")
    print("  ✅ Move head slightly while capturing (different angles)")
    print("  ✅ Vary your expression intensity\n")

    for label, desc in EMOTIONS.items():
        input(f"Ready for '{label.upper()}'? ({desc})\nPress ENTER when ready...")
        collect(label, desc, base / label)

    print("\n✅ Done! Now run:  python finetune.py")


if __name__ == "__main__":
    main()