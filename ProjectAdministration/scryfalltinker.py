from distro import name
import scrython
import requests
import pytds
import certifi
import time
from decouple import config

DB_SERVER = config('SERVER')
DB_NAME = config('DATABASE')
DB_USER = config('DB_USERNAME')
DB_PASSWORD = config('DB_PASSWORD')

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
            VALUES (%s, %s, %s)
            """

            cursor.executemany(sql, card_list)

        conn.commit()

    print(f"{len(card_list)} cards inserted successfully.")

def save_image(path, url, name):
    response = requests.get(url)

    with open('{}{}.png'.format(path, name), 'wb') as f:
        f.write(response.content)

IMAGE_PATH = "D:/MTGCardImages/"
url = "https://api.scryfall.com/sets"
data = requests.get(url).json()

sets = []
card_list = []

for s in data["data"]:
    sets.append((s["name"], s["code"].upper()))

for name, code in sets:
    print(f"{name} = {code}")
    try:
        time.sleep(1)
        cards = scrython.cards.Search(q=f"set:{code}")
        time.sleep(1)
    except scrython.foundation.ScryfallError:
        print(f"Error occurred while fetching cards for set: {name}")
        continue

    for card in cards.data():
        #append to card list if not already in list
        #print(f"Processing card: {card['name']} from set: {code}")
        card_list.append([card['name'], card['id'], card['set'].upper()])
        #card = scrython.cards.Id(id=card['id'])
        #try:
        #    save_image(IMAGE_PATH, card.image_uris(0, 'normal'), card.id())
        #except(TypeError):
        #    print(f"Error occurred while saving image for card: {card.name()}")
        #   pass

#print(card_list)
print(f"Total sets: {len(sets)}"
      f"\nTotal cards: {len(card_list)}")

insert_master_cards(card_list)