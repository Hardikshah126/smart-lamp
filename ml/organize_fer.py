"""
organize_fer.py
Copies FER-2013 images into the structure train.py expects:
  ml/data/happy/
  ml/data/stressed/   (mapped from 'fear' + 'angry' + 'disgust')
  ml/data/sleepy/     (mapped from 'sad' + 'neutral')

Run from inside the ml/ folder:
  python organize_fer.py

When prompted, paste the full path to your unzipped FER folder.
Example: C:\\Users\\YourName\\Downloads\\archive
"""

import os
import shutil
from pathlib import Path

# ── Mapping FER-2013 classes → our 3 lamp classes ─────────────────────────────
# FER has: angry, disgust, fear, happy, sad, surprise, neutral
MAPPING = {
    "happy":    ["happy"],
    "stressed": ["angry", "fear", "disgust"],
    "sleepy":   ["sad", "neutral"],
}

def organize(fer_root: Path, output_dir: Path):
    total_copied = 0

    for our_label, fer_labels in MAPPING.items():
        out_folder = output_dir / our_label
        out_folder.mkdir(parents=True, exist_ok=True)
        count = 0

        for split in ["train", "test"]:
            for fer_label in fer_labels:
                src_folder = fer_root / split / fer_label
                if not src_folder.exists():
                    # try lowercase
                    src_folder = fer_root / split / fer_label.lower()
                if not src_folder.exists():
                    print(f"  [SKIP] Not found: {src_folder}")
                    continue

                images = list(src_folder.glob("*.jpg")) + list(src_folder.glob("*.png"))
                for img in images:
                    # Rename to avoid collisions: label_split_originalname
                    dest_name = f"{fer_label}_{split}_{img.name}"
                    shutil.copy2(img, out_folder / dest_name)
                    count += 1

        print(f"  ✅ {our_label:10s} → {count} images copied to ml/data/{our_label}/")
        total_copied += count

    print(f"\n🎉 Done! Total images: {total_copied}")
    print(f"📁 Dataset ready at: {output_dir.resolve()}")
    print("\nNext step → run:  python train.py --data ./data --epochs 30")


if __name__ == "__main__":
    print("=" * 55)
    print("  FER-2013 Dataset Organizer for Smart Lamp Project")
    print("=" * 55)
    print()
    print("Paste the full path to your unzipped FER folder.")
    print("It should contain 'train' and 'test' subfolders.")
    print("Example: C:\\Users\\YourName\\Downloads\\archive")
    print()

    raw = input("FER folder path: ").strip().strip('"').strip("'")
    fer_root = Path(raw)

    if not fer_root.exists():
        print(f"\n❌ Path not found: {fer_root}")
        print("Make sure you pasted the correct path and try again.")
        exit(1)

    if not (fer_root / "train").exists():
        print(f"\n❌ No 'train' folder found inside: {fer_root}")
        print("Expected structure:  your_folder/train/happy/  train/angry/ etc.")
        exit(1)

    # Output goes to ml/data/ (same folder as this script)
    script_dir = Path(__file__).parent
    output_dir = script_dir / "data"

    print(f"\n📂 Reading from : {fer_root}")
    print(f"📂 Writing to   : {output_dir}")
    print()

    organize(fer_root, output_dir)
