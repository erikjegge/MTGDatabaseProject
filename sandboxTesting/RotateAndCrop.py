import pytesseract
from PIL import Image
import cv2
import numpy as np

# Specify path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Optional: explicitly set path to tesseract if not in PATH
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Linux
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows

def correct_image_orientation(image_path):
    img = Image.open(image_path)

    # Get orientation data
    osd = pytesseract.image_to_osd(img)
    rotation_angle = int([line for line in osd.split('\n') if "Rotate" in line][0].split(':')[-1])
    print(f"Detected rotation: {rotation_angle} degrees")

    # Rotate the image to correct orientation
    corrected = img.rotate(-rotation_angle, expand=True)
    return corrected


def crop_card(input_path, output_path, min_width=800, min_height=1000):
    image = cv2.imread(input_path)
    orig = image.copy()

    # Convert to grayscale and threshold to get the card
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    if not contours:
        cv2.imwrite(output_path, orig)
        return output_path

    # Get the bounding rect of the largest contour
    x, y, w, h = cv2.boundingRect(contours[0])

    # Check size
    if w < min_width or h < min_height:
        cv2.imwrite(output_path, orig)
        return output_path

    cropped = orig[y:y+h, x:x+w]
    cv2.imwrite(output_path, cropped)
    return output_path

# Usage example
rotated_image = correct_image_orientation('input.jpg')
rotated_image.save('corrected_image.jpg')
cropped = crop_card("corrected_image.jpg", "cropped_card_output.jpg")