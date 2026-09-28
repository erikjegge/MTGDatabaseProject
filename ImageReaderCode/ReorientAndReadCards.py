'''
    Re-reads cards whose name couldn't be determined (cardName = 'XXX') or whose set is
    unknown with a near-empty cardName. The orientation of these images isn't known ahead
    of time, so all four 90-degree rotations are OCR'd with EasyOCR and each candidate name
    is fuzzy-matched against the real card names already in tbl_MasterCardTable. Whichever
    rotation's OCR text most closely resembles an actual card name is treated as correct,
    and the matched (real) name is written back -- not the raw OCR text.

    Two earlier approaches were tried and rejected:
      - Scoring rotations by raw EasyOCR confidence: confidently misreads upside-down/
        sideways text as plausible-looking gibberish (e.g. "Professor of Zoomancy" read as
        "IOSSJJOId Jo KouBttooz"), so confidence doesn't indicate correct orientation.
      - Tesseract OSD (orientation/script detection): these images don't have enough text
        for OSD's algorithm (designed for dense scanned pages); forcing it past its
        "too few characters" safeguard produced low-confidence, wrong-script guesses.

    A candidate is only accepted if it clearly matches a real card name (ratio >=
    MATCH_THRESHOLD). Otherwise the row is left as 'XXX' for manual review rather than
    guessing wrong. Only cardName is updated on tbl_MTGCardLibrary -- no files are moved.
'''
import difflib
import os
import re
import threading
from threading import Thread
from time import perf_counter

import cv2
import easyocr
import pyodbc
from decouple import config

# globals
maxthreads = 2
sema = threading.Semaphore(value=maxthreads)
reader = easyocr.Reader(['en'], gpu=True)

IMAGE_ARCH = "Z:/MTGArchived"

# minimum similarity (0-1) between OCR text and a real card name to accept it
MATCH_THRESHOLD = 0.75

ROTATIONS = [
    None,
    cv2.ROTATE_90_CLOCKWISE,
    cv2.ROTATE_180,
    cv2.ROTATE_90_COUNTERCLOCKWISE,
]


def get_conn():
    server = config('SERVER')
    database = config('DATABASE')
    username = config('DB_USERNAME')
    password = config('DB_PASSWORD')
    driver = '{ODBC Driver 17 for SQL Server}'

    return pyodbc.connect(
        'DRIVER=' + driver + ';PORT=1433;SERVER=' + server + ';PORT=1443;DATABASE=' + database +
        ';UID=' + username + ';PWD=' + password
    )


def get_records():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT [pkCard], [cardName], [set], [filepath] "
        "FROM [dbo].[tbl_MTGCardLibrary] "
        "WHERE cardName = 'XXX' or ([set] = 'XXX' and len(cardName) <= 2)"
    )
    records = [list(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return records


def load_master_card_names():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT [CardName] FROM [dbo].[tbl_MasterCardTable]")
    names = [row[0] for row in cursor.fetchall() if row[0]]
    cursor.close()
    conn.close()

    return names


def merge_tokens(cleaned_tokens):
    merged = []
    i = 0

    while i < len(cleaned_tokens):
        if i + 1 < len(cleaned_tokens) and cleaned_tokens[i + 1].lower() == "s":
            merged.append(f"{cleaned_tokens[i]}'s")
            i += 2
        else:
            merged.append(cleaned_tokens[i])
            i += 1

    return " ".join(merged)


def find_card_top(gray):
    # scans down for the card's top black border: a row that's mostly dark and
    # stays that way for a while (unlike thin wires/clamp edges, which are dark
    # but only cover a sliver of the row's width)
    h, _ = gray.shape
    row_dark_frac = (gray < 70).mean(axis=1)

    for y in range(h):
        if row_dark_frac[y] > 0.6 and row_dark_frac[y:y + 30].mean() > 0.5:
            return y

    return None


def name_region_roi(gray, filepath):
    h, w = gray.shape

    if 'imageV3_' in filepath:
        y1 = 0
        y2 = int(h * 0.20)
        x1 = 0
        x2 = w
    else:
        # these camera-rig photos have clamp/rail hardware above the card, so the
        # name band isn't at a fixed fraction of the raw frame -- find the card's
        # actual top edge first, and fall back to the old fixed guess if not found
        top = find_card_top(gray)

        if top is None:
            y1 = int(h * 0.05)
            y2 = int(h * 0.35)
        else:
            y1 = top + int(h * 0.01)
            y2 = top + int(h * 0.12)

        x1 = int(w * 0.05)
        x2 = int(w * 0.95)

    return gray[y1:y2, x1:x2]


def extract_candidate_name(img, filepath):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=1.3, fy=1.3, interpolation=cv2.INTER_CUBIC)

    roi = name_region_roi(gray, filepath)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    roi = clahe.apply(roi)

    tokens = reader.readtext(roi, detail=0)
    cleaned_tokens = []

    for t in tokens:
        t = re.sub(r'\d+', '', t)
        t = t.strip()

        if t and t.replace(" ", "").isalpha():
            cleaned_tokens.append(t)

    return merge_tokens(cleaned_tokens)


def best_master_match(candidate_name, master_names_lower):
    if not candidate_name:
        return None, 0.0

    matches = difflib.get_close_matches(candidate_name.lower(), master_names_lower.keys(), n=1, cutoff=0.0)
    if not matches:
        return None, 0.0

    match_lower = matches[0]
    ratio = difflib.SequenceMatcher(None, candidate_name.lower(), match_lower).ratio()

    return master_names_lower[match_lower], ratio


def best_orientation_match(img, filepath, master_names_lower):
    best_name = None
    best_ratio = 0.0
    best_candidate = ""

    for rotate_code in ROTATIONS:
        rotated = cv2.rotate(img, rotate_code) if rotate_code is not None else img

        candidate = extract_candidate_name(rotated, filepath)
        matched_name, ratio = best_master_match(candidate, master_names_lower)

        if ratio > best_ratio:
            best_ratio = ratio
            best_name = matched_name
            best_candidate = candidate

    return best_name, best_ratio, best_candidate


def update_card_name(pkCard, cardName):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE [dbo].[tbl_MTGCardLibrary] SET cardName = ? WHERE pkCard = ?",
        cardName, pkCard
    )
    conn.commit()

    cursor.close()
    conn.close()


def process_record(record, master_names_lower):
    sema.acquire()

    pkCard, cardName, setCode, filepath = record

    try:
        image_path = os.path.join(IMAGE_ARCH, setCode, filepath)
        print(f'Processing pkCard={pkCard} ({image_path})')

        img = cv2.imread(image_path)
        if img is None:
            print(f"Failed to load image: {image_path}")
            return

        matched_name, ratio, candidate = best_orientation_match(img, filepath, master_names_lower)

        if not matched_name or ratio < MATCH_THRESHOLD:
            print(f'pkCard={pkCard}: no confident match (best "{candidate}" -> "{matched_name}" @ {ratio:.2f}), leaving as-is')
            return

        print(f'pkCard={pkCard}: matched "{matched_name}" (ratio={ratio:.2f}, raw="{candidate}")')
        update_card_name(pkCard, matched_name)

    except Exception as e:
        print(f"Error on pkCard={pkCard}: {e}")

    finally:
        sema.release()


def main():
    master_names = load_master_card_names()
    master_names_lower = {name.lower(): name for name in master_names}

    records = get_records()

    threads = [Thread(target=process_record, args=(record, master_names_lower)) for record in records]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    start_time = perf_counter()

    main()

    end_time = perf_counter()
    print(f'It took {end_time - start_time:0.2f} second(s) to complete.')
