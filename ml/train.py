"""
train.py - Retrain with balanced classes (cap all to same count)
Run: python train.py --data ./data --epochs 30
"""

import argparse
import os
import random
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import cv2
from pathlib import Path

LABELS     = {"happy": 0, "stressed": 1, "sleepy": 2}
LABEL_NAMES = ["happy", "stressed", "sleepy"]
IMG_SIZE   = (48, 48)
NUM_CLASSES = 3
MODEL_SAVE_PATH = "model.h5"

# ── Cap all classes to this number so dataset is perfectly balanced ───────────
MAX_PER_CLASS = 8000   # just below the smallest class (happy=8989)


# ── Load dataset with hard balance cap ────────────────────────────────────────
def load_dataset(data_dir: str):
    X, y = [], []
    skipped = 0

    for label_name, label_idx in LABELS.items():
        folder = Path(data_dir) / label_name
        images = list(folder.glob("*.jpg")) + list(folder.glob("*.png"))

        # Shuffle and cap to MAX_PER_CLASS
        random.shuffle(images)
        images = images[:MAX_PER_CLASS]

        print(f"[INFO] {label_name}: using {len(images)} images (capped from {len(list(folder.glob('*.*')))})")

        for img_path in images:
            img = cv2.imread(str(img_path))
            if img is None:
                skipped += 1
                continue
            try:
                gray    = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, IMG_SIZE)
                normed  = resized.astype("float32") / 255.0
                X.append(np.expand_dims(normed, axis=-1))
                y.append(label_idx)
            except Exception:
                skipped += 1

    print(f"[INFO] Total: {len(X)} images loaded, {skipped} skipped.")
    return np.array(X), np.array(y)


# ── Model ─────────────────────────────────────────────────────────────────────
def build_model():
    model = models.Sequential([
        # Block 1
        layers.Conv2D(32, (3,3), activation="relu", padding="same", input_shape=(48,48,1)),
        layers.BatchNormalization(),
        layers.Conv2D(32, (3,3), activation="relu", padding="same"),
        layers.MaxPooling2D(2,2),
        layers.Dropout(0.25),

        # Block 2
        layers.Conv2D(64, (3,3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.Conv2D(64, (3,3), activation="relu", padding="same"),
        layers.MaxPooling2D(2,2),
        layers.Dropout(0.25),

        # Block 3
        layers.Conv2D(128, (3,3), activation="relu", padding="same"),
        layers.BatchNormalization(),
        layers.MaxPooling2D(2,2),
        layers.Dropout(0.25),

        # Head
        layers.Flatten(),
        layers.Dense(256, activation="relu"),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(NUM_CLASSES, activation="softmax"),
    ])
    return model


# ── Train ─────────────────────────────────────────────────────────────────────
def train(data_dir: str, epochs: int = 30, batch_size: int = 32):
    print(f"\n[INFO] Loading balanced dataset from: {data_dir}")
    X, y = load_dataset(data_dir)

    # Verify balance
    for i, name in enumerate(LABEL_NAMES):
        print(f"  {name}: {np.sum(y == i)} samples")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.18, random_state=42, stratify=y_train)

    print(f"\n[INFO] Train:{len(X_train)}  Val:{len(X_val)}  Test:{len(X_test)}")

    # Simple numpy augmentation (no Keras augmentation layers = no TFLite issues)
    def augment(images):
        aug = []
        for img in images:
            # Random horizontal flip
            if random.random() > 0.5:
                img = np.fliplr(img)
            # Random brightness shift
            delta = random.uniform(-0.1, 0.1)
            img = np.clip(img + delta, 0, 1)
            aug.append(img)
        return np.array(aug)

    X_train = augment(X_train)

    # Build and compile
    model = build_model()
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.summary()

    cb = [
        callbacks.ModelCheckpoint(MODEL_SAVE_PATH, save_best_only=True,
                                   monitor="val_accuracy", verbose=1),
        callbacks.EarlyStopping(patience=8, restore_best_weights=True,
                                monitor="val_accuracy"),
        callbacks.ReduceLROnPlateau(factor=0.5, patience=4,
                                    monitor="val_loss", verbose=1),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        callbacks=cb,
    )

    # Evaluate
    loss, acc = model.evaluate(X_test, y_test)
    print(f"\n✅ Test Accuracy: {acc * 100:.2f}%")

    # Per-class accuracy
    preds = np.argmax(model.predict(X_test, verbose=0), axis=1)
    for i, name in enumerate(LABEL_NAMES):
        mask     = y_test == i
        cls_acc  = np.mean(preds[mask] == y_test[mask]) * 100
        print(f"   {name}: {cls_acc:.1f}% accuracy ({np.sum(mask)} test samples)")

    # Save TFLite (clean, no augmentation layers this time)
    try:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        with open("model.tflite", "wb") as f:
            f.write(tflite_model)
        print("[INFO] TFLite model saved to model.tflite ✅")
    except Exception as e:
        print(f"[WARNING] TFLite export skipped: {e}")

    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"],     label="Train")
    axes[0].plot(history.history["val_accuracy"], label="Val")
    axes[0].set_title("Accuracy"); axes[0].legend()
    axes[1].plot(history.history["loss"],     label="Train")
    axes[1].plot(history.history["val_loss"], label="Val")
    axes[1].set_title("Loss"); axes[1].legend()
    plt.tight_layout()
    plt.savefig("training_curves.png")
    print("[INFO] Training curves saved.")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   type=str, default="./data")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch",  type=int, default=32)
    args = parser.parse_args()
    train(data_dir=args.data, epochs=args.epochs, batch_size=args.batch)