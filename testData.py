import os
import pyodbc
from decouple import config
from PIL import Image, ImageEnhance
import cv2
import numpy as np

# CONFIG
IMAGE_DIR = "Z:/MTGCardImages"
OUTPUT_DIR = "Z:/MTGSymbolDataset"

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'


# --- IMAGE FUNCTIONS ---

def preprocess_image(path):
    img = Image.open(path).convert("RGB")
    img = img.resize((512, 512))
    return img


def crop_set_symbol(img: Image.Image):
    width, height = img.size

    return img.crop((
        int(width * 0.78),
        int(height * 0.48),
        int(width * 0.98),
        int(height * 0.72)
    ))

def preprocess_symbol_for_cnn(img: Image.Image):
    # Convert to grayscale (CNN-friendly for this task)
    img = img.convert("L")

    # Light contrast boost (helps learning, not destructive)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    return img


def process_and_save_image(scryid, set_code):
    input_path = os.path.join(IMAGE_DIR, f"{scryid}.png")

    if not os.path.exists(input_path):
        return False

    try:
        img = preprocess_image(input_path)
        symbol = crop_set_symbol(img)
        symbol = preprocess_symbol_for_cnn(symbol)

        # Resize for CNN (consistent input size)
        symbol = symbol.resize((64, 64))

        # Ensure output directory exists
        set_dir = os.path.join(OUTPUT_DIR, set_code)
        os.makedirs(set_dir, exist_ok=True)

        output_path = os.path.join(set_dir, f"{scryid}.png")
        symbol.save(output_path)

        return True

    except Exception as e:
        print(f"Error processing {scryid}: {e}")
        return False


# --- DATABASE ---

def get_master_cards():
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    cursor = conn.cursor()

    query = """
    SELECT [CardName], [ScryID], [SetCode], [pkid]
    FROM [dbo].[tbl_MasterCardTable]
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return rows


# --- MAIN ---

def main():
    rows = get_master_cards()

    success = 0
    skipped = 0

    for row in rows:
        card_name = row[0]
        scryid = row[1]
        set_code = row[2]

        if not set_code:
            skipped += 1
            continue

        ok = process_and_save_image(scryid, set_code)

        if ok:
            success += 1
        else:
            skipped += 1

        if success % 100 == 0:
            print(f"Processed: {success} images")

    print("Done.")
    print(f"Saved: {success}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()