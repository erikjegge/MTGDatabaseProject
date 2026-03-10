from array import array
import os
from PIL import Image
import sys
import time
import easyocr
import cv2
import re

# </snippet_imports>

# import into SQL server
import pyodbc

# copying files later to the archive
import shutil

# will try to time how long this takes
import time

#implementation of threading
import threading
from threading import Thread
from time import perf_counter

#credentials
from decouple import config

#globuels
maxthreads = 2
sema = threading.Semaphore(value=maxthreads)
reader = easyocr.Reader(['en'], gpu=True)

'''
    START
    send_and_archive takes the card object created by the rest of processing and imports it to the database
'''
# takes a list called card
def send_and_archive(card):
    #connection string
    server = config('SERVER')
    database = config('DATABASE')
    username = config('DB_USERNAME')
    password = config('DB_PASSWORD')
    driver= '{ODBC Driver 17 for SQL Server}'

    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()

    cardName = card[0].replace("'", "''")
    read_image_path = card[2]
    write_image_path = card[3]

    split_filepath = card[-1].split("_")
    pkCostBasisLot = split_filepath[2]
    boxCode = split_filepath[3]

    sqlString = (
            "INSERT INTO tbl_MTGCardLibrary ([cardName],[isEnabled],[color],[type],[set],[filepath],[isFoil],[pkCostBasisLot],[boxCode]) "
            "VALUES "
            "('"+cardName+"',1,NULL,NULL,'"+card[1]+"','"+card[-1]+"',0,"+pkCostBasisLot+","+boxCode+")"
    )

    if "_FOIL" in card[-1]:
        pkCostBasisLot = split_filepath[3]
        boxCode = split_filepath[4]
        sqlString = (
                "INSERT INTO tbl_MTGCardLibrary ([cardName],[isEnabled],[color],[type],[set],[filepath],[isFoil],[pkCostBasisLot],[boxCode]) "
                "VALUES "
                "('"+cardName+"',1,NULL,NULL,'"+card[1]+"','"+card[-1]+"',1,"+pkCostBasisLot+","+boxCode+")"
        )

    #print(sqlString)
    cursor.execute(sqlString)
    conn.commit()

    # move the file to the archive
    shutil.move(read_image_path, write_image_path)

    cursor.close()
    conn.close()

def ignore_files(dir, files):
    return [f for f in files if os.path.isfile(os.path.join(dir, f))]

def call_cv(read_image_path, write_image_path, setAbrev):
    sema.acquire()

    try:
        print(f'Processing the file {read_image_path}')

        img = cv2.imread(read_image_path)
        if img is None:
            print(f"Failed to load image: {read_image_path}")
            card_name = "XXX"
        else:
            # 1️⃣ Rotate counter-clockwise unless it's from the scanner then don't
            if 'Document_' not in read_image_path:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)

            # 2️⃣ Grayscale + slight upscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC)

            h, w = gray.shape

            # 3️⃣ Crop top-half name region
            y1 = int(h * 0.05)
            y2 = int(h * 0.35)
            x1 = int(w * 0.05)
            x2 = int(w * 0.95)

            roi = gray[y1:y2, x1:x2]

            # 4️⃣ Contrast normalization
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            roi = clahe.apply(roi)

            # 5️⃣ OCR
            tokens = reader.readtext(roi, detail=0)
            cleaned_tokens = []

            for t in tokens:
                # Remove digits
                t = re.sub(r'\d+', '', t)

                # Normalize
                t = t.strip()

                if t and t.replace(" ", "").isalpha():
                    cleaned_tokens.append(t)

            if not cleaned_tokens:
                card_name = "XXX"
            else:
                merged = []
                i = 0

                while i < len(cleaned_tokens):
                    if (
                        i + 1 < len(cleaned_tokens)
                        and cleaned_tokens[i + 1].lower() == "s"
                    ):
                        merged.append(f"{cleaned_tokens[i]}'s")
                        i += 2
                    else:
                        merged.append(cleaned_tokens[i])
                        i += 1

                card_name = " ".join(merged)

        print(card_name)
        # 7️⃣ Build card payload (always insert)
        card_results = [
            card_name,
            setAbrev,
            read_image_path,
            write_image_path,
            os.path.basename(read_image_path)
        ]

        send_and_archive(card_results)

    except Exception as e:
        print(f"OCR error on {read_image_path}: {e}")

        # Failsafe insert
        card_results = [
            "XXX",
            setAbrev,
            read_image_path,
            write_image_path,
            os.path.basename(read_image_path)
        ]
        send_and_archive(card_results)

    finally:
        sema.release()

def main():

    #start_time = time.time()

    source = 'Z:/MTGImages'
    destination = 'Z:/MTGArchived'

    # copying the directory structure from source into desitination
    shutil.copytree(source,destination,ignore=ignore_files, dirs_exist_ok=True)

    filesToAnalyze = []

    # this grabs the list of files we want to send through computer vision and appends them to our list
    for subdir, dirs, files in os.walk(source):
            if subdir != source:
                    head, tail = os.path.split(subdir)
                    if files:
                            for file in files:
                                    if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                                        sourceFile = os.path.join(subdir,file)
                                        sourceFile = sourceFile.replace('\\', '/')
                                        destFile = sourceFile.replace(source,destination)
                                        filesToAnalyze.append([sourceFile,destFile,tail])

    # threading implementation
    threads = [Thread(target=call_cv, args=(r[0], r[1], r[2]))
        for r in filesToAnalyze]

    # start the threads
    for thread in threads:
        thread.start()

    # wait for the threads to complete
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    start_time = perf_counter()

    main()

    end_time = perf_counter()
    print(f'It took {end_time- start_time :0.2f} second(s) to complete.')