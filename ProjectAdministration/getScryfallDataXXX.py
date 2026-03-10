import os
import shutil
import asyncio
from datetime import date
from pickle import FALSE, TRUE
import scrython
import pyodbc
import aiohttp
from decouple import config
import requests
import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np
import pytesseract
from PIL import Image

# Specify path to tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

today = date.today()
d1 = today.strftime("%m/%d/%Y")

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver= '{ODBC Driver 17 for SQL Server}'
gSet = ''
gName = ''
gNamePrev = ''
IMAGE_PATH = "./candidates/"

conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

query = ("SELECT pkCard, cardName, [set], [set]+'/'+filepath as fileLink "
        "FROM [dbo].[tbl_MTGCardLibrary] "
        "WHERE [Type] IS NULL "
        #"WHERE [Type] IS NULL AND boxCode = 22 AND pkCostBasisLot = 65 AND filepath like '%Document%' "
        "ORDER BY cardName" )

cursor.execute(query)

result = cursor.fetchall()

conn.close
cursor.close

listOfCards = [list(i) for i in result]

# ---------------------- HELPER FUNCTIONS ----------------------
def correct_image_orientation(image_path):
    img = Image.open(image_path)

    # Get orientation data
    osd = pytesseract.image_to_osd(img, config='--psm 0 -c min_characters_to_try=5')
    rotation_angle = int([line for line in osd.split('\n') if "Rotate" in line][0].split(':')[-1])
    print(f"Detected rotation: {rotation_angle} degrees")

    # Rotate the image to correct orientation
    corrected = img.rotate(-rotation_angle, expand=True)
    return corrected

def save_image(path, url, name):
    response = requests.get(url)

    with open('{}{}.png'.format(path, name), 'wb') as f:
        f.write(response.content)

def delete_images(folder_path):
    image_extensions = ('.jpg', '.jpeg', '.png')
    deleted_files = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            file_path = os.path.join(folder_path, filename)
            try:
                os.remove(file_path)
                deleted_files.append(filename)
            except Exception as e:
                print(f"Failed to delete {filename}: {e}")

    print(f"Deleted {len(deleted_files)} images:")
    for f in deleted_files:
        print(f" - {f}")

def load_image(path):
    image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)  # use grayscale for comparison
    return cv2.resize(image, (300, 300))  # resize for consistent comparison

def compare_images(imageA, imageB):
    score, _ = ssim(imageA, imageB, full=True)
    return score  # higher = more similar

def find_best_match(query_path, candidates_folder):
    query_image = load_image(query_path)
    best_score = -1
    best_match = None

    for filename in os.listdir(candidates_folder):
        candidate_path = os.path.join(candidates_folder, filename)
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        candidate_image = load_image(candidate_path)
        score = compare_images(query_image, candidate_image)
        print(f"Comparing with {filename}: SSIM = {score:.4f}")
        if score > best_score:
            best_score = score
            best_match = filename

    return best_match, best_score

def copy_image_if_exists(source_path, destination_path):
    if os.path.exists(source_path):
        shutil.copy2(source_path, destination_path)
        print(f"Copied '{source_path}' to '{destination_path}'")
        return True
    else:
        print(f"Image not found at '{source_path}'")
        return False

import cv2
import numpy as np

def crop_card(
    input_path: str,
    output_path: str,
    width: int = 1080,
    min_width: int = 800,
    min_height: int = 800,
) -> str:
    """
    Detect the largest rectangular card in the image, crop and warp it.
    If detected card's width or height is smaller than min_width or min_height,
    it will save the original image as output.
    """
    image = cv2.imread(input_path)
    orig = image.copy()

    # Preprocess
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 0)
    edges = cv2.Canny(gray, 50, 200)

    # Find contours
    contours, _ = cv2.findContours(
        edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    card_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            card_contour = approx
            break

    if card_contour is None:
        cv2.imwrite(output_path, orig)
        return output_path

    # Order points
    pts = card_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    (tl, tr, br, bl) = rect

    # Get target width/height
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxWidth = int(max(widthA, widthB))
    maxHeight = int(max(heightA, heightB))

    # Check min size before cropping
    if maxWidth < min_width or maxHeight < min_height:
        cv2.imwrite(output_path, orig)
        return output_path

    # Warp and resize
    dst = np.array(
        [[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))

    scale = width / maxWidth
    warped = cv2.resize(warped, (width, int(maxHeight * scale)))
    cv2.imwrite(output_path, warped)
    return output_path

def resize_image(input_path: str, output_path: str, width: int = 488, height: int = 680) -> None:
    """
    Resize an image to a specific width and height.

    Parameters:
        input_path (str): Path to the source image.
        output_path (str): Path to save the resized image.
        width (int): Target width (default: 488).
        height (int): Target height (default: 680).
    """
    img = Image.open(input_path)
    img_resized = img.resize((width, height), Image.LANCZOS)  # high-quality downsampling
    img_resized.save(output_path)
    print(f"✅ Saved resized image to {output_path}")

# ---------------------- HELPER FUNCTIONS ----------------------

# clear directory before start
delete_images(IMAGE_PATH)

for r in listOfCards:
    try:
        skip_flag = False
        conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = conn.cursor()

        print('<><><><><><><><><><><><><><><><>')
        print(r[1])
        gName = r[1].replace("'", "''")
        fileLink = r[3]
        pkCard = r[0]

        # if the name isn't the same as the last card, clear dir and then regrab new images
        if gName != gNamePrev:
            # clear the dir
            delete_images(IMAGE_PATH)
            # find all prints of that card and place them in the directory for analysis
            data = scrython.cards.Search(q="++{}".format(gName))
            for r in data.data():
                card = scrython.cards.Id(id=r['id'])
                try:
                    save_image(IMAGE_PATH, card.image_uris(0, 'normal'), card.id())
                except(TypeError):
                    pass

        if not copy_image_if_exists('Z:/MTGArchived/'+ fileLink, "query.jpg"):
            skip_flag = True
        else:
            skip_Flag = False

        if skip_flag:
            continue
        
        try:
            rotated_image = correct_image_orientation('query.jpg')
            rotated_image.save('query.jpg')
        except(pytesseract.pytesseract.TesseractError):
            print("rotating error thingy")
            pass

        cropped = crop_card("query.jpg", "cropped_card_output.jpg")

        resize_image("cropped_card_output.jpg","resized.jpg")
 
        query = "resized.jpg"

        candidates_folder = "./candidates"
        match, score = find_best_match(query, candidates_folder)
        print(f"\nBest match: {match} with SSIM score {score:.4f}")

        try:
            matchingCard = match.replace(".png", "")
        except(AttributeError):
            print("no match")
            continue

        card = scrython.cards.Id(id=matchingCard)

        setfinal = card.set_code().upper()
        gSet = setfinal
        #card names can have single quotes
        cardName = gName
        gNamePrev = gName

        price = card.prices('usd')
        if not price:
            price = 0.0

        foilPrice = card.prices('usd_foil')
        if not foilPrice:
            foilPrice = 0.0

        try:
            type = card.type_line()
            type = type.replace("'", "''")
        except(KeyError):
            type = ''

        try:
            manaCost = card.mana_cost()
        except(KeyError):
            manaCost = ''

        try:
            colors = ''.join(card.colors())
        except(KeyError):
            colors = ''

        # change name for double cards
        try:
            realName = ''.join(card.name())
            realName = realName.replace("'", "''")
        except(KeyError):
            realName = ''

        cardId = card.id()

        print(pkCard)
        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET [set] = '"+setfinal+"' "
                    "WHERE pkCard = " + str(pkCard)
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = '"+str(manaCost)+"', color = '"+str(colors)+"', [type] = '"+str(type)+"', [cardID] = '"+str(cardId)+"', cardName = '"+str(realName)+"' "
                    "WHERE pkCard = " + str(pkCard)
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass

        sqlString = (
                    "IF NOT EXISTS(SELECT 1 FROM [dbo].[tbl_MTGPriceHistory] WHERE [cardID] = '"+str(cardId)+"' AND [asOfDate] = '"+d1+"') "
                    "INSERT INTO [dbo].[tbl_MTGPriceHistory]  "
                    "VALUES('"+str(cardId)+"', "+str(price)+", '"+d1+"',"+str(foilPrice)+") "
        )

        try:
            cursor.execute(sqlString)
            conn.commit()
        except pyodbc.OperationalError as e:
            print("Commit failed:", e)
            # Optionally reconnect or log the failure
            pass

        conn.close
        cursor.close

    except (scrython.foundation.ScryfallError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ContentTypeError):
        print('card not found')
        pass

conn.close
cursor.close