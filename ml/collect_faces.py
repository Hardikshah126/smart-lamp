"""
collect_faces.py
Collects your own face images for each emotion class.
Run: python collect_faces.py
Press SPACE to capture, Q to quit each session.
"""

import cv2
import numpy as np
from pathlib import Path

IMG_SIZE = (48, 48)
SAMPLES_PER_CLASS = 300  # collect 300 images per emotion

EMOTIONS = {
    "happy":    "😊 SMILE WIDE / LAUGH",
    "stressed": "😰 FROWN / LOOK TENSE / FURROW BROWS",
    "sleepy":   "😴 HALF CLOSE EYES / LOOK TIRED / NEUTRAL",
}

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

def collect_for_emotion(label: str, description: str, output_dir: Path, target: int = SAMPLES_PER_CLASS):
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = len(list(output_dir.glob("*.jpg")))
    
    cap = cv2.VideoCapture(0)
    count = 0
    auto_capture = False

    print(f"\n{'='*50}")
    print(f"COLLECTING: {label.upper()} — {description}")
    print(f"Already have: {existing} images. Collecting {target} more.")
    print(f"Press SPACE to start auto-capture, Q to finish early.")
    print(f"{'='*50}\n")

    while count < target:
        ret, frame = cap.read()
        if not ret:
            break

        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60,60))

        face_detected = len(faces) > 0

        # Draw face box
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)

        # Overlay
        cv2.rectangle(frame, (0,0), (640, 90), (0,0,0), -1)
        cv2.putText(frame, f"Emotion: {label.upper()} — {description}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,100), 2)
        cv2.putText(frame, f"Captured: {count}/{target} | SPACE=auto Q=done",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 1)
        cv2.putText(frame, "FACE DETECTED ✓" if face_detected else "NO FACE DETECTED",
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0,255,0) if face_detected else (0,0,255), 1)

        cv2.imshow("Face Collector — Smart Lamp", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord(" "):
            auto_capture = not auto_capture
            print(f"Auto-capture: {'ON' if auto_capture else 'OFF'}")

        # Save face crop
        if (auto_capture or key == ord("s")) and face_detected and count < target:
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])
            face_crop = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_crop, IMG_SIZE)
            
            filename = output_dir / f"{label}_{existing + count:05d}.jpg"
            cv2.imwrite(str(filename), face_resized)
            count += 1

            if count % 50 == 0:
                print(f"  Captured {count}/{target}...")

    cap.release()
    cv2.destroyAllWindows()
    print(f"✅ Done! Collected {count} images for '{label}'")
    return count


def main():
    base_dir = Path("./my_face_data")
    print("\n🎥 Smart Lamp — Personal Face Data Collector")
    print("This collects YOUR face to fine-tune the emotion model.")
    print("Make sure you're in good lighting, face the camera directly.\n")

    for label, description in EMOTIONS.items():
        out = base_dir / label
        input(f"\nReady to collect '{label.upper()}'? ({description})\nPress ENTER to start...")
        collect_for_emotion(label, description, out)

    print("\n" + "="*50)
    print("✅ All done! Your face data is in: ./my_face_data/")
    print("\nNow run fine-tuning:")
    print("  python finetune.py")
    print("="*50)


if __name__ == "__main__":
    main()