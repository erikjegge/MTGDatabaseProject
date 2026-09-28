'''
    This program is designed to read only new cards into the db and populate meta data in the MTG library table only
'''
import os
import time
import itertools
import scrython
import pyodbc
from decouple import config
import numpy as np
from PIL import Image, ImageEnhance
import imagehash
import torch
import torch.nn as nn

# -------------------
# LOAD CNN MODEL
# -------------------
MODEL_PATH = "mtg_symbol_model.pth"
CLASS_MAP_PATH = "mtg_symbol_classes.txt"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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
        return self.fc(x)


model = SimpleCNN(num_classes=len(classes)).to(device)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

IMAGE_DIR = "Z:/MTGCardImages"
IMAGE_ARCH = "Z:/MTGArchived"
TEST_IMAGE_DIR = "Z:/MTGTest/SetMatchTest"
MODEL_IMAGE_DIR = "Z:/MTGTest/ModelImages"

DB_CONN_STR = f'DRIVER={driver};PORT=1433;SERVER={server};PORT=1443;DATABASE={database};UID={username};PWD={password}'

scryid_to_set = {}


def predict_set(image_path):
    img = preprocess_image(image_path)
    symbol = crop_set_symbol(img).convert("L").resize((64, 64))
    arr = np.array(symbol) / 255.0
    tensor = torch.tensor(arr).unsqueeze(0).unsqueeze(0).float().to(device)

    with torch.no_grad():
        output = model(tensor)
        probs = torch.softmax(output, dim=1)
        pred_idx = torch.argmax(probs, dim=1).item()
        confidence = probs[0][pred_idx].item()

    return classes[pred_idx], confidence


def save_debug_images(input_path, best_match_id, predicted_set=None, score=0.0):
    os.makedirs(TEST_IMAGE_DIR, exist_ok=True)

    inputfilename = os.path.basename(input_path)
    input_crop = crop_set_symbol(preprocess_image(input_path))
    match_path = os.path.join(IMAGE_DIR, f"{best_match_id}.png")

    input_crop_str = ''
    if predicted_set:
        input_crop_str = f"{predicted_set}_{int(score * 1000)}_{inputfilename}"
        input_crop.save(os.path.join(MODEL_IMAGE_DIR, input_crop_str))

    if os.path.exists(match_path):
        match_crop = crop_set_symbol(preprocess_image(match_path))
        match_crop.save(os.path.join(TEST_IMAGE_DIR, f"{best_match_id}_matched_{inputfilename}"))
        input_crop.save(os.path.join(TEST_IMAGE_DIR, f"{best_match_id}_compare_{inputfilename}"))

    print(f"Saved debug images to {TEST_IMAGE_DIR}")
    return input_crop_str


def preprocess_symbol(img):
    return ImageEnhance.Contrast(img).enhance(2.0)


def crop_set_symbol(img: Image.Image):
    width, height = img.size
    return img.crop((
        int(width * 0.78),
        int(height * 0.48),
        int(width * 0.98),
        int(height * 0.72)
    ))


def get_symbol_hash(path):
    return imagehash.phash(preprocess_symbol(crop_set_symbol(preprocess_image(path))))


def preprocess_image(path):
    return Image.open(path).convert("L").resize((512, 512))


def get_hash(path):
    return imagehash.phash(preprocess_image(path))


def get_set_for_scryid(scryid):
    return scryid_to_set.get(scryid)


def find_best_match(input_image_path, candidate_scryids, setCompare=False):
    fadeSetList = ['PLST', 'ANB', 'CHR', 'SLC']

    if setCompare:
        print("Using CNN set classification...")

        try:
            predicted_set, confidence = predict_set(input_image_path)
            print(f"CNN predicted set: {predicted_set} (conf: {confidence:.2f})")
        except Exception as e:
            print(f"CNN failed: {e}")
            return None, None

        filtered_candidates = [
            scryid for scryid in candidate_scryids
            if scryid_to_set.get(scryid) == predicted_set
        ]

        if not filtered_candidates:
            print("No candidates in predicted set, falling back to hash comparison against all candidates")
            filtered_candidates = candidate_scryids
        elif len(filtered_candidates) == 1:
            if get_set_for_scryid(filtered_candidates[0]) not in fadeSetList:
                print(f"Only one candidate in predicted set, using that match: {filtered_candidates[0]}")
                return filtered_candidates[0], confidence

        if confidence >= 0.75 and predicted_set not in fadeSetList:
            print("CNN confidence is high, skipping HASH comparison and returning best guess")
            return filtered_candidates[0], confidence

        input_hash = get_hash(input_image_path)
        best_match = None
        best_score = float("inf")

        for scryid in filtered_candidates:
            compare_path = os.path.join(IMAGE_DIR, f"{scryid}.png")
            if not os.path.exists(compare_path):
                continue
            diff = input_hash - get_hash(compare_path)
            if diff < best_score and get_set_for_scryid(scryid) not in fadeSetList:
                best_score = diff
                best_match = scryid

        print(f"Final match after HASH filter: {best_match} (confidence score: {confidence})")
        return best_match, confidence


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


def scryfall_call_with_name_scramble(name, set_code):
    """Try cleaned and word-order permutations of `name` when the exact lookup fails.

    Filters out garbage tokens (1-2 chars, e.g. 't', 'Lo') before permuting.
    Only generates permutations for names with 4 or fewer words to avoid
    combinatorial explosion.
    """
    try:
        return scryfall_call(scrython.cards.Named, exact=name, set=set_code)
    except scrython.foundation.ScryfallError as e:
        if 'No cards found' not in str(e):
            raise

    words = [w for w in name.split() if len(w) > 2]

    if not words:
        msg = f'No valid words remaining after filtering "{name}"'
        raise scrython.foundation.ScryfallError({'details': msg}, msg)

    if len(words) <= 4:
        candidates = list(dict.fromkeys(' '.join(p) for p in itertools.permutations(words)))
    else:
        candidates = [' '.join(words)]

    for candidate in candidates:
        if candidate == name:
            continue
        try:
            result = scryfall_call(scrython.cards.Named, exact=candidate, set=set_code)
            print(f'  Name scramble succeeded: "{name}" -> "{candidate}"')
            return result
        except scrython.foundation.ScryfallError as e:
            if 'No cards found' in str(e):
                continue
            raise

    msg = f'No cards found matching "{name}" (tried {len(candidates)} permutations after filtering)'
    raise scrython.foundation.ScryfallError({'details': msg}, msg)


def main():
    # conn = pyodbc.connect(DB_CONN_STR)
    # cursor = conn.cursor()
    # cursor.execute(
    #     "SELECT cardName, [set], pkCard, filepath "
    #     "FROM [dbo].[tbl_MTGCardLibrary] "
    #     "WHERE [cardID] IS NULL AND [set] = 'XXX' AND cardName <> 'XXX' AND filepath like 'imageV3_%' "
    #     "ORDER BY [set], cardName"
    # )
    # listOfCards = [list(row) for row in cursor.fetchall()]
    # cursor.close()
    # conn.close()

    # for r in listOfCards:
    #     setfinal = r[1]
    #     pkCard = r[2]
    #     filePath = r[3]
    #     matchedCardID = None

    #     try:
    #         conn = pyodbc.connect(DB_CONN_STR)
    #         cursor = conn.cursor()

    #         print('<><><><><><><><><><><><><><><><>')
    #         print(r[0])

    #         data = scryfall_call(scrython.cards.Search, q="++{}".format(r[0]))
    #         results = data.data()
    #         if len(results) == 1:
    #             matchedCardID = results[0]["id"]
    #             print(f'Only one result found from Scryfall with name: {r[0]}, using id: {matchedCardID}')
    #         else:
    #             for card in results:
    #                 scryid_to_set[card["id"]] = card["set"].upper()
    #             candidate_scryids = [card["id"] for card in results]
    #             best_match, score = find_best_match(
    #                 os.path.join(IMAGE_ARCH, setfinal, filePath),
    #                 candidate_scryids,
    #                 True
    #             )
    #             print('-----------------------------')
    #             predicted_set = get_set_for_scryid(best_match)
    #             print(pkCard)
    #             print(filePath)
    #             print(f"Best match: {best_match}")
    #             print(f"Score: {score}")
    #             print(f"Predicted set: {predicted_set}")
    #             cardImage = save_debug_images(
    #                 os.path.join(IMAGE_ARCH, setfinal, filePath),
    #                 best_match, predicted_set, score
    #             )
    #             cursor.execute(
    #                 "INSERT INTO [dbo].[tbl_MTGCardLibraryVerify] (pkCard, matchCardID, cardImage) VALUES (?, ?, ?)",
    #                 pkCard, best_match, cardImage
    #             )
    #             conn.commit()
    #             print(f'Inserted into verification table: pkCard={pkCard}, matchCardID={best_match}')
    #             matchedCardID = None

    #         if matchedCardID is None:
    #             cursor.close()
    #             conn.close()
    #             continue

    #         card = scryfall_call(scrython.cards.Id, id=matchedCardID)

    #         try:
    #             card_type = card.type_line()
    #         except KeyError:
    #             card_type = ''

    #         try:
    #             manaCost = card.mana_cost()
    #         except KeyError:
    #             manaCost = ''

    #         try:
    #             colors = ''.join(card.colors())
    #         except KeyError:
    #             colors = ''

    #         try:
    #             realName = ''.join(card.name())
    #         except KeyError:
    #             realName = ''

    #         try:
    #             set = card.set_code().upper()
    #         except KeyError:
    #             set = ''

    #         cardId = card.id()

    #         try:
    #             cursor.execute(
    #                 "UPDATE [dbo].[tbl_MTGCardLibrary] "
    #                 "SET manaCost = ?, color = ?, [type] = ?, [cardID] = ?, cardName = ?, [set] = ? "
    #                 "WHERE pkCard = ?",
    #                 str(manaCost), str(colors), str(card_type), str(cardId), str(realName), str(set), str(pkCard)
    #             )
    #             conn.commit()
    #         except pyodbc.OperationalError as e:
    #             print("Commit failed:", e)

    #         cursor.close()
    #         conn.close()

    #     except Exception as e:
    #         print(f'ERROR [{type(e).__name__}]: {e} | card={r[0]} set={setfinal} pkCard={pkCard}')
    
    # # Need to add second and third data set process here.
    # # 2. Have ID but set = XXX
    # print('trying 2nd scenario')
    # conn = pyodbc.connect(DB_CONN_STR)
    # cursor = conn.cursor()
    # cursor.execute(
    #     "SELECT [cardID], pkCard "
    #     "FROM [dbo].[tbl_MTGCardLibrary] "
    #     "WHERE [cardID] IS NOT NULL AND [set] = 'XXX' "
    #     "ORDER BY [set], cardName"
    # )
    # listOfCards = [list(row) for row in cursor.fetchall()]
    # cursor.close()
    # conn.close()

    # for x in listOfCards:
    #     cardID = x[0]
    #     pkCard = x[1]
    #     try:
    #         conn = pyodbc.connect(DB_CONN_STR)
    #         cursor = conn.cursor()

    #         card = scryfall_call(scrython.cards.Id, id=cardID)

    #         try:
    #             card_type = card.type_line()
    #         except KeyError:
    #             card_type = ''

    #         try:
    #             manaCost = card.mana_cost()
    #         except KeyError:
    #             manaCost = ''

    #         try:
    #             colors = ''.join(card.colors())
    #         except KeyError:
    #             colors = ''

    #         try:
    #             realName = ''.join(card.name())
    #         except KeyError:
    #             realName = ''

    #         try:
    #             set = card.set_code().upper()
    #         except KeyError:
    #             set = ''

    #         try:
    #             cursor.execute(
    #                 "UPDATE [dbo].[tbl_MTGCardLibrary] "
    #                 "SET manaCost = ?, color = ?, [type] = ?, cardName = ?, [set] = ? "
    #                 "WHERE pkCard = ?",
    #                 str(manaCost), str(colors), str(card_type), str(realName), str(set), str(pkCard)
    #             )
    #             conn.commit()
    #         except pyodbc.OperationalError as e:
    #             print("Commit failed:", e)

    #         cursor.close()
    #         conn.close()

    #     except Exception as e:
    #         print(f'ERROR [{type(e).__name__}]: {e} | card={r[0]} set={setfinal} pkCard={pkCard}')


    # 3. CardID NULL, Card name <> XXX, Set <> XXX
    print('trying 3rd scenario')
    conn = pyodbc.connect(DB_CONN_STR)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT [cardID], pkCard, [set], cardName "
        "FROM [dbo].[tbl_MTGCardLibrary] "
        "WHERE [cardID] IS NULL AND [set] <> 'XXX' AND cardName <> 'XXX' "
        "ORDER BY [set], cardName"
    )
    listOfCards = [list(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    for x in listOfCards:
        #cardID = x[0]
        pkCard = x[1]
        dbset = x[2]
        dbcardName = x[3]

        try:
            conn = pyodbc.connect(DB_CONN_STR)
            cursor = conn.cursor()

            card = scryfall_call_with_name_scramble(dbcardName, dbset)

            try:
                card_type = card.type_line()
            except KeyError:
                card_type = ''

            try:
                manaCost = card.mana_cost()
            except KeyError:
                manaCost = ''

            try:
                colors = ''.join(card.colors())
            except KeyError:
                colors = ''

            try:
                realName = ''.join(card.name())
            except KeyError:
                realName = ''

            cardId = card.id()

            try:
                cursor.execute(
                    "UPDATE [dbo].[tbl_MTGCardLibrary] "
                    "SET manaCost = ?, color = ?, [type] = ?, cardName = ?, cardID = ? "
                    "WHERE pkCard = ?",
                    str(manaCost), str(colors), str(card_type), str(realName), str(cardId), str(pkCard)
                )
                conn.commit()
            except pyodbc.OperationalError as e:
                print("Commit failed:", e)

            cursor.close()
            conn.close()

        except Exception as e:
            print(f'ERROR [{type(e).__name__}]: {e} | card={dbcardName} set={dbset} pkCard={pkCard}')

if __name__ == '__main__':
    main()