# cropping and orenting pictures

import cv2
import os

INPUT_DIR = "Z:/MTGImages/XXX"
#OUTPUT_DIR = "Z:/MTGTest"

#os.makedirs(OUTPUT_DIR, exist_ok=True)

# 🔧 Tune these once
ROTATE = True

# Current config crop values!
CROP = {
    "y1": 510, 
    "y2": 3200,
    "x1": 440, 
    "x2": 2350 
}

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h))

    return rotated

def process_image(path, output_path):
    img = cv2.imread(path)

    if img is None:
        print(f"Failed to load {path}")
        return

    # 1. Rotate (fix orientation)
    if ROTATE:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

        img = rotate_image(img, -0.5)  # tweak this value

    # 2. Crop
    cropped = img[CROP["y1"]:CROP["y2"], CROP["x1"]:CROP["x2"]]

    # 3. Optional resize (standardize size for matching)
    cropped = cv2.resize(cropped, (488, 680))  # MTG card ratio

    # Save
    cv2.imwrite(output_path, cropped)


for filename in os.listdir(INPUT_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        input_path = os.path.join(INPUT_DIR, filename)
        #output_path = os.path.join(OUTPUT_DIR, filename)

        process_image(input_path, input_path)

print("Done!")