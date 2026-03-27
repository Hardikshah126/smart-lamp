"""
finetune.py
Fine-tunes the existing model.h5 on your own face data.
Takes ~5 minutes. Run AFTER collect_faces.py.
Run: python finetune.py
"""

import cv2
import numpy as np
import tensorflow as tf
from pathlib import Path
from sklearn.model_selection import train_test_split
import random

IMG_SIZE    = (48, 48)
LABELS      = {"happy": 0, "stressed": 1, "sleepy": 2}
LABEL_NAMES = ["happy", "stressed", "sleepy"]
MODEL_PATH  = "model.h5"
DATA_DIR    = Path("./my_face_data")


def load_my_data():
    X, y = [], []
    for label, idx in LABELS.items():
        folder = DATA_DIR / label
        if not folder.exists():
            print(f"[WARNING] Missing: {folder}")
            continue
        images = list(folder.glob("*.jpg"))
        print(f"[INFO] {label}: {len(images)} personal images")
        for img_path in images:
            img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            resized = cv2.resize(img, IMG_SIZE).astype("float32") / 255.0
            X.append(np.expand_dims(resized, -1))
            y.append(idx)
    return np.array(X), np.array(y)


def augment(X):
    out = []
    for img in X:
        if random.random() > 0.5:
            img = np.fliplr(img)
        img = np.clip(img + random.uniform(-0.15, 0.15), 0, 1)
        out.append(img)
    return np.array(out)


def finetune():
    print("[INFO] Loading base model...")
    model = tf.keras.models.load_model(MODEL_PATH)

    print("[INFO] Loading your personal face data...")
    X, y = load_my_data()

    if len(X) == 0:
        print("[ERROR] No data found! Run collect_faces.py first.")
        return

    # Augment to get more samples
    X_aug = augment(X)
    X_all = np.concatenate([X, X_aug, X_aug])  # triple the data
    y_all = np.concatenate([y, y, y])

    X_train, X_val, y_train, y_val = train_test_split(
        X_all, y_all, test_size=0.2, random_state=42, stratify=y_all)

    print(f"[INFO] Fine-tuning on {len(X_train)} samples...")

    # Use a very low learning rate so we don't overwrite FER knowledge
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    cb = [
        tf.keras.callbacks.ModelCheckpoint(
            MODEL_PATH, save_best_only=True, monitor="val_accuracy", verbose=1),
        tf.keras.callbacks.EarlyStopping(
            patience=5, restore_best_weights=True, monitor="val_accuracy"),
    ]

    model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=20,
        batch_size=16,
        callbacks=cb,
    )

    # Test per-class accuracy
    preds = np.argmax(model.predict(X_val, verbose=0), axis=1)
    print("\n📊 Per-class accuracy on your face:")
    for i, name in enumerate(LABEL_NAMES):
        mask = y_val == i
        if np.sum(mask) == 0:
            continue
        acc = np.mean(preds[mask] == y_val[mask]) * 100
        print(f"   {name}: {acc:.1f}%")

    print(f"\n✅ Fine-tuned model saved to {MODEL_PATH}")
    print("Run python infer.py to test it live!")


if __name__ == "__main__":
    finetune()