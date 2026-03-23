import os
import shutil

SOURCE_DIR = r"Z:\MTGTest\ModelImages"
DEST_ROOT = r"Z:\MTGSymbolDataset"

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
    move_images_to_set_folders()