import os
import asyncio
import time
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
from rapidfuzz import process, fuzz
from PIL import Image, ImageEnhance
import imagehash
import torch
# Define model (same as training)
import torch.nn as nn

# -------------------
# LOAD CNN MODEL
# -------------------
MODEL_PATH = "mtg_symbol_model.pth"
CLASS_MAP_PATH = "mtg_symbol_classes.txt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load class list
with open(CLASS_MAP_PATH, "r") as f:
    classes = [line.strip() for line in f.readlines()]

class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(1, 16, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(32 * 16 * 16, 128),
            nn.ReLU(),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.conv(x)
        x = self.fc(x)
        return x

model = SimpleCNN(num_classes=len(classes)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

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
IMAGE_DIR = "Z:/MTGCardImages"
IMAGE_ARCH = "Z:/MTGArchived"
TEST_IMAGE_DIR = "Z:/MTGTest/SetMatchTest"
MODEL_IMAGE_DIR = "Z:/MTGTest/ModelImages"

def predict_set(image_path):
    # -------------------
    # preprocess image
    # -------------------
    img = preprocess_image(image_path)
    symbol = crop_set_symbol(img)

    symbol = symbol.convert("L")
    symbol = symbol.resize((64, 64))

    arr = np.array(symbol) / 255.0

    tensor = torch.tensor(arr).unsqueeze(0).unsqueeze(0).float().to(device)

    # -------------------
    # run model
    # -------------------
    with torch.no_grad():
        output = model(tensor)

        probs = torch.softmax(output, dim=1)

        pred_idx = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_idx].item()

    predicted_set = classes[pred_idx]

    return predicted_set, confidence

def save_debug_images(input_path, best_match_id, predicted_set=None, score=0.0):
    os.makedirs(TEST_IMAGE_DIR, exist_ok=True)

    inputfilename = os.path.basename(input_path) 

    # Input image
    input_img = preprocess_image(input_path)
    input_crop = crop_set_symbol(input_img)

    # Matched image
    match_path = os.path.join(IMAGE_DIR, f"{best_match_id}.png")

    if predicted_set:
        input_crop_str = f"{predicted_set}_{int(score * 1000)}_{inputfilename}"
        input_crop.save(os.path.join(MODEL_IMAGE_DIR, input_crop_str))

    if os.path.exists(match_path):
        match_img = preprocess_image(match_path)
        match_crop = crop_set_symbol(match_img)
        match_crop.save(os.path.join(TEST_IMAGE_DIR, f"{best_match_id}_matched_{inputfilename}"))
        input_crop.save(os.path.join(TEST_IMAGE_DIR, f"{best_match_id}_compare_{inputfilename}"))

    print(f"Saved debug images to {TEST_IMAGE_DIR}")
    return input_crop_str

def compare_symbols(path1, path2):
    img1 = preprocess_image(path1)
    img2 = preprocess_image(path2)

    sym1 = crop_set_symbol(img1)
    sym2 = crop_set_symbol(img2)

    sym1 = preprocess_symbol(sym1)
    sym2 = preprocess_symbol(sym2)

    sym1 = np.array(sym1)
    sym2 = np.array(sym2)

    sym1 = cv2.resize(sym1, (100, 100))
    sym2 = cv2.resize(sym2, (100, 100))

    _, sym1 = cv2.threshold(sym1, 160, 200, cv2.THRESH_BINARY_INV)
    _, sym2 = cv2.threshold(sym2, 160, 200, cv2.THRESH_BINARY_INV)

    kernel = np.ones((3,3), np.uint8)
    sym1 = cv2.morphologyEx(sym1, cv2.MORPH_OPEN, kernel)
    sym2 = cv2.morphologyEx(sym2, cv2.MORPH_OPEN, kernel)

    score, _ = ssim(sym1, sym2, full=True)

    return score  # higher = better (0 to 1)

def preprocess_symbol(img):
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(2.0)
    return img

def crop_set_symbol(img: Image.Image):
    width, height = img.size
    
    # Approx bottom-right quadrant
    return img.crop((
        int(width * 0.78),
        int(height * 0.48),
        int(width * 0.98),
        int(height * 0.72)
    ))

def get_symbol_hash(path):
    img = preprocess_image(path)
    symbol = crop_set_symbol(img)
    symbol = preprocess_symbol(symbol)
    return imagehash.phash(symbol)

def preprocess_image(path):
    img = Image.open(path).convert("L")  # grayscale

    img = img.resize((512, 512))

    return img

def get_hash(path):
    img = preprocess_image(path)
    return imagehash.phash(img)

def get_set_for_scryid(scryid):
    return scryid_to_set.get(scryid)

def find_best_match(input_image_path, candidate_scryids, setCompare=False):
    fadeSetList = ['PLST', 'ANB', 'CHR']
    # ---------------------------
    # SET COMPARE = CNN PIPELINE
    # ---------------------------
    if setCompare:
        print("Using CNN set classification...")

        try:
            predicted_set, confidence = predict_set(input_image_path)
            print(f"CNN predicted set: {predicted_set} (conf: {confidence:.2f})")

        except Exception as e:
            print(f"CNN failed: {e}")
            return None, None

        # Filter candidates
        filtered_candidates = [
            scryid for scryid in candidate_scryids
            if scryid_to_set.get(scryid) == predicted_set
        ]

        # if CNN is not confident or no matches in predicted set, compare against all candidates
        if not filtered_candidates:
            print("No candidates in predicted set, falling back to hash comparison against all candidates")
            filtered_candidates = candidate_scryids
        # if there is only one candidate in the predicted set, use that one
        elif len(filtered_candidates) == 1:
            print(f"Only one candidate in predicted set, using that match: {filtered_candidates[0]}")
            return filtered_candidates[0], confidence

        if confidence >= 0.75 and predicted_set not in fadeSetList:
            print("CNN confidence is high, skipping HASH comparison and returning best guess")
            return filtered_candidates[0], confidence

        # Hash within filtered set
        input_hash = get_hash(input_image_path)

        best_match = None
        best_score = float("inf")

        for scryid in filtered_candidates:
            compare_path = os.path.join(IMAGE_DIR, f"{scryid}.png")

            if not os.path.exists(compare_path):
                continue

            compare_hash = get_hash(compare_path)
            diff = input_hash - compare_hash

            if diff < best_score and get_set_for_scryid(scryid) not in fadeSetList:
                best_score = diff
                best_match = scryid

        print(f"Final match after HASH filter: {best_match} (confidence score: {confidence})")
        return best_match, confidence

def getKnownCards(set):
    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()

    query = ("SELECT cardName "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "WHERE [set] = '"+set+"' "
                "AND cardID IS NOT NULL "
                "AND cardName <> 'XXX' "
            "GROUP BY cardName ")

    cursor.execute(query)

    result = cursor.fetchall()

    conn.close
    cursor.close

    card_names = [row[0] for row in result]

    return card_names

conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

onlyNewCards = True

if onlyNewCards:
    query = ("SELECT cardName, [set], pkCard, filepath "
            "FROM [dbo].[tbl_MTGCardLibrary] "
            "WHERE [cardID] IS NULL AND filepath like 'imageV3_%' "
            "ORDER BY [set], cardName" )
else:
    # changed this to be, ALL but only if the card hasn't been added yet today
    query = ("SELECT cl.cardName, cl.[set], cl.cardID "
                "FROM [dbo].[tbl_MTGCardLibrary] cl "
                "WHERE cl.cardID NOT IN (SELECT cardID FROM (SELECT cardID, asOfDate "
                                        "FROM [dbo].[tbl_MTGPriceHistory] "
                                        "WHERE asOfDate = DATEADD(dd, 0, DATEDIFF(dd, 0, GETDATE())) "
                                        "GROUP BY cardID, asOfDate) a) "
                "AND [set] <> 'XXX' "
                "GROUP BY cl.cardName, cl.[set], cl.cardID " )

cursor.execute(query)

result = cursor.fetchall()

conn.close
cursor.close

listOfCards = [list(i) for i in result]

conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
cursor = conn.cursor()

query = ("SELECT [CardName],[ScryID],[SetCode],[pkid] "
            "FROM [dbo].[tbl_MasterCardTable]" )

cursor.execute(query)
result2 = cursor.fetchall()

conn.close
cursor.close

masterCardList = [list(i) for i in result2]
scryid_to_set = {row[1]: row[2] for row in masterCardList}

def scryfall_call(fn, *args, **kwargs):
    """Call a scrython constructor with retry on rate limit."""
    while True:
        time.sleep(0.5)
        try:
            return fn(*args, **kwargs)
        except scrython.foundation.ScryfallError as e:
            if 'rate' in str(e).lower():
                print('Rate limited by Scryfall, waiting 65 seconds...')
                time.sleep(65)
            else:
                raise

for r in listOfCards:
    try:
        conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
        cursor = conn.cursor()

        print('<><><><><><><><><><><><><><><><>')
        print(r[0])
        gName = r[0]
        setfinal = r[1]
        pkCard = r[2]
        filePath = r[3]
        matchedCardID = None
        fixedName = ''

        if setfinal == '_CON':
            setfinal = 'CON'

        if setfinal == 'XXX':
            # if there is only one match for the card name, use that set code
            data = scryfall_call(scrython.cards.Search, q="++{}".format(r[0]))
            if len(data.data()) == 1:
                for card in data.data():
                    matchedCardID = card["id"]
                    print('only print found from Scryfall with name: {}, using id code: {}'.format(r[0], matchedCardID))

            else:
                # if there are multiple matches, try to match against the master card list to find the correct card
                searchResult = [row for row in masterCardList if row[0] == r[0]]
                if searchResult: # we got something back from our table search
                    if len(searchResult) == 1:  # if there is only one, take that one's set code
                        #setfinal = searchResult[0][2].upper()
                        matchedCardID = searchResult[0][1]
                        print('-----------------------------')
                        print('Only one match found in master card list, using id code: {}'.format(matchedCardID))
                    else:
                        canditate_scryids = [row[1] for row in searchResult]
                        # always compare the set symbols
                        best_match, score = find_best_match(os.path.join(IMAGE_ARCH, setfinal, filePath), canditate_scryids, True)
                        print('-----------------------------')
                        predicted_set = get_set_for_scryid(best_match)
                        print(pkCard)
                        print(filePath)
                        print("Best match:", best_match)
                        print("Score:", score)
                        print("Predicted set:", predicted_set)
                        cardImage = save_debug_images(
                            os.path.join(IMAGE_ARCH, setfinal, filePath),
                            best_match, predicted_set, score
                        )
                        cursor.execute(
                            "INSERT INTO [dbo].[tbl_MTGCardLibraryVerify] (pkCard, matchCardID, cardImage) VALUES (?, ?, ?)",
                            pkCard, best_match, cardImage
                        )
                        conn.commit()
                        print('Inserted into verification table: pkCard={}, matchCardID={}'.format(pkCard, best_match))
                        # if score <= 0.85:
                        #     print('Match is still not good enough, skipping card for now and analyzing results')
                        #     predicted_set = get_set_for_scryid(best_match)
                        #     matchedCardID = None
                        # else:
                        #     print('Match is good enough based on set symbol, using id code: {}'.format(best_match))
                        #     matchedCardID = best_match
                else:
                    print('-----------------------------')
                    print('No matches found in master card list for card with name: {}'.format(r[0]))

                matchedCardID = None

        # in this for testing purposes, I want to skip all matches and analyze the results
        if matchedCardID is None:
            continue

        card = scryfall_call(scrython.cards.Id, id=matchedCardID)

        price = card.prices('usd')
        if not price:
            price = 0.0

        foilPrice = card.prices('usd_foil')
        if not foilPrice:
            foilPrice = 0.0

        try:
            card_type = card.type_line()
            card_type = card_type.replace("'", "''")
        except(KeyError):
            card_type = ''

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

        try:
            setFinal = card.scryfallJson["set"].upper()
        except(KeyError):
            setFinal = ''

        cardId = card.id()

        sqlString = (
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = '"+str(manaCost)+"', "
                            "color = '"+str(colors)+"', "
                            "[type] = '"+str(card_type)+"', "
                            "[cardID] = '"+str(cardId)+"', "
                            "cardName = '"+str(realName)+"', "
                            "[set] = '"+str(setfinal)+"' "
                    "WHERE pkCard = '"+str(pkCard)+"'"
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

    except (scrython.foundation.ScryfallError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ContentTypeError) as e:
        print('ERROR [{}]: {} | card={} set={} pkCard={}'.format(type(e).__name__, e, r[0], setfinal, pkCard))
        pass

conn.close
cursor.close