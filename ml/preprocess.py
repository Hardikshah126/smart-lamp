"""
preprocess.py
Face detection using OpenCV's built-in Haar Cascade — works on all platforms
without mediapipe version issues.
"""

import cv2
import numpy as np
from pathlib import Path

# Target image size for the CNN
IMG_SIZE = (48, 48)

# OpenCV built-in face detector — no extra install needed
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def detect_and_crop_face(frame: np.ndarray, padding: float = 0.2):
    """
    Detect the largest face in a frame and return a cropped image.
    Returns None if no face is found.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )

    if len(faces) == 0:
        return None

    # Pick the largest face
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])

    # Add padding
    pad_w = int(w * padding)
    pad_h = int(h * padding)
    x1 = max(0, x - pad_w)
    y1 = max(0, y - pad_h)
    x2 = min(frame.shape[1], x + w + pad_w)
    y2 = min(frame.shape[0], y + h + pad_h)

    return frame[y1:y2, x1:x2]


def normalize_face(face: np.ndarray) -> np.ndarray:
    """
    Convert to grayscale, resize to 48x48, normalize to [0,1].
    Returns shape (48, 48, 1).
    """
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, IMG_SIZE)
    normalized = resized.astype("float32") / 255.0
    return np.expand_dims(normalized, axis=-1)  # (48, 48, 1)


def preprocess_frame(frame: np.ndarray):
    """
    Full pipeline: detect face → normalize.
    Returns (processed_array, face_crop) or (None, None).
    """
    face = detect_and_crop_face(frame)
    if face is None:
        return None, None
    processed = normalize_face(face)
    return processed, face


def load_dataset(data_dir: str):
    """
    Load images from:
        data_dir/happy/
        data_dir/stressed/
        data_dir/sleepy/

    Returns (X, y) as numpy arrays.
    """
    LABELS = {"happy": 0, "stressed": 1, "sleepy": 2}
    X, y = [], []
    skipped = 0

    for label_name, label_idx in LABELS.items():
        folder = Path(data_dir) / label_name
        if not folder.exists():
            print(f"[WARNING] Missing folder: {folder}")
            continue

        images = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))
        print(f"[INFO] {label_name}: found {len(images)} images, processing...")

        for img_path in images:
            img = cv2.imread(str(img_path))
            if img is None:
                skipped += 1
                continue

            # FER images are already cropped faces — skip detection, just normalize
            try:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, IMG_SIZE)
                normalized = resized.astype("float32") / 255.0
                processed = np.expand_dims(normalized, axis=-1)
                X.append(processed)
                y.append(label_idx)
            except Exception:
                skipped += 1
                continue

    if not X:
        raise ValueError("No valid images found. Check your data directory structure.")

    print(f"[INFO] Loaded {len(X)} images. Skipped {skipped} bad files.")
    return np.array(X), np.array(y)


if __name__ == "__main__":
    # Quick webcam test
    cap = cv2.VideoCapture(0)
    print("Webcam test — press Q to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        processed, face_crop = preprocess_frame(frame)
        if face_crop is not None:
            cv2.imshow("Face", face_crop)
        cv2.imshow("Webcam", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()