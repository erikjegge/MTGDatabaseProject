from distro import name
import scrython
import requests
import pytds
import certifi
import time
from decouple import config
import os

DB_SERVER = config('SERVER')
DB_NAME = config('DATABASE')
DB_USER = config('DB_USERNAME')
DB_PASSWORD = config('DB_PASSWORD')

def get_current_master_sets():
    with pytds.connect(
        server=DB_SERVER,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=1433,
        cafile=certifi.where(),   # enables TLS
        validate_host=True        # validates certificate
    ) as conn:
        
        with conn.cursor() as cursor:

            sql = "SELECT [CardName],[ScryID],[SetCode],[pkid] FROM [dbo].[tbl_MasterCardTable]"
            cursor.execute(sql)
            sets = cursor.fetchall()

    return [s[0] for s in sets]

def insert_master_cards(card_list):
    with pytds.connect(
        server=DB_SERVER,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=1433,
        cafile=certifi.where(),   # enables TLS
        validate_host=True        # validates certificate
    ) as conn:
        
        with conn.cursor() as cursor:

            sql = """
            INSERT INTO dbo.tbl_MasterCardTable (CardName, ScryID, SetCode)
            SELECT %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM dbo.tbl_MasterCardTable WHERE ScryID = %s
            )
            """

            cursor.executemany(sql, card_list)

        conn.commit()

    print(f"{len(card_list)} cards inserted successfully.")

def save_image(path, url, name):
    file_path = f"{path}{name}.png"

    # 🔥 Skip if already exists
    if os.path.exists(file_path):
        return

    response = requests.get(url, stream=True)

    if response.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

def get_all_cards_in_set(code):
    url = f"https://api.scryfall.com/cards/search?q=set:{code}"
    all_cards = []

    while url:
        response = requests.get(url)

        # 🔥 Catch HTTP errors
        if response.status_code != 200:
            print(f"HTTP error {response.status_code} for set {code}")
            break

        data = response.json()

        # 🔥 Catch Scryfall errors
        if "data" not in data:
            print(f"Scryfall error for set {code}: {data}")
            break

        all_cards.extend(data["data"])

        if data.get("has_more"):
            url = data.get("next_page")
        else:
            url = None

    return all_cards

IMAGE_PATH = "Z:/MTGCardImages/"
url = "https://api.scryfall.com/sets"
data = requests.get(url).json()

sets = []
card_list = []

for s in data["data"]:
    sets.append((s["name"], s["code"].upper()))

# 🔥 NEW: trim sets to start FROM...   TSR
start_code = "TSR"

start_index = next(
    (i for i, (_, code) in enumerate(sets) if code == start_code),
    None
)

if start_index is None:
    raise ValueError(f"Start set {start_code} not found in Scryfall data")

sets = sets[start_index:]

for name, code in sets:
    card_list = []
    print(f"{name} = {code}")
    try:
        time.sleep(1)
        cards = get_all_cards_in_set(code)
        time.sleep(1)
    except scrython.foundation.ScryfallError:
        print(f"Error occurred while fetching cards for set: {name}")
        continue

    for card in cards:
        card_list.append([card['name'], card['id'], card['set'].upper()])
        try:
            image_url = card.get("image_uris", {}).get("normal")

            if image_url:
                save_image(IMAGE_PATH, image_url, card["id"])
            else:
                print(f"No image for {card['name']}")

        except Exception as e:
            print(f"Error saving image for {card['name']}: {e}")

    card_list_fixed = [(c[0], c[1], c[2], c[1]) for c in card_list]
    insert_master_cards(card_list_fixed)

print(f"Total sets: {len(sets)}"
      f"\nTotal cards: {len(card_list)}")

