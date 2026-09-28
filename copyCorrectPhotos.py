import os
import shutil
import pyodbc
from decouple import config

SOURCE_DIR = r"Z:\MTGTest\ModelImages"
DEST_ROOT = r"Z:\MTGSymbolDataset"

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'


def get_connection():
    return pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )


def process_verify_table():
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all records from the verify table
    cursor.execute("SELECT pkCard, matchCardID, isMatch, [cardImage] FROM [dbo].[tbl_MTGCardLibraryVerify]")
    records = cursor.fetchall()

    deleted = 0
    updated = 0

    for row in records:
        pk_card, match_card_id, is_match, image_file_name = row

        if not is_match:
            # Delete the corresponding image from SOURCE_DIR
            if image_file_name:
                img_path = os.path.join(SOURCE_DIR, image_file_name)
                if os.path.exists(img_path):
                    os.remove(img_path)
                    print(f"Deleted image: {image_file_name}")
                else:
                    print(f"Image not found (skipping delete): {image_file_name}")
            deleted += 1
        else:
            # Update cardID in tbl_MTGCardLibrary where pkCard matches
            cursor.execute(
                "UPDATE [dbo].[tbl_MTGCardLibrary] SET cardID = ? WHERE pkCard = ?",
                match_card_id, pk_card
            )
            updated += 1

    conn.commit()
    print(f"\nProcessed verify table — Updated: {updated}, Deleted images: {deleted}")

    # Move matched images to set folders
    move_images_to_set_folders()

    # Clear the verify table
    cursor.execute("DELETE FROM [dbo].[tbl_MTGCardLibraryVerify]")
    conn.commit()
    print("Cleared tbl_MTGCardLibraryVerify.")

    cursor.close()
    conn.close()


def move_images_to_set_folders():
    moved = 0
    skipped = 0

    for filename in os.listdir(SOURCE_DIR):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        try:
            # Extract set code (before first underscore)
            set_code = filename.split("_")[0]

            if not set_code:
                print(f"Skipping (no set code): {filename}")
                skipped += 1
                continue

            dest_folder = os.path.join(DEST_ROOT, set_code)

            # Create folder if it doesn't exist
            os.makedirs(dest_folder, exist_ok=True)

            src_path = os.path.join(SOURCE_DIR, filename)
            dest_path = os.path.join(dest_folder, filename)

            # Move file
            shutil.move(src_path, dest_path)
            print(f"Moved: {filename} -> {dest_folder}")
            moved += 1

        except Exception as e:
            print(f"Error processing {filename}: {e}")
            skipped += 1

    print(f"\nDone. Moved: {moved}, Skipped: {skipped}")


if __name__ == "__main__":
    process_verify_table()
