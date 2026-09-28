import asyncio
from datetime import date
import time
import scrython
import pyodbc
import aiohttp
from decouple import config

today = date.today()
d1 = today.strftime("%m/%d/%Y")

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'


def get_connection():
    return pyodbc.connect(
        f'DRIVER={driver};PORT=1433;SERVER={server};PORT=1443;DATABASE={database};UID={username};PWD={password}'
    )


def scryfall_call(fn, *args, **kwargs):
    while True:
        time.sleep(0.1)
        try:
            return fn(*args, **kwargs)
        except scrython.foundation.ScryfallError as e:
            if 'rate' in str(e).lower():
                print('Rate limited by Scryfall, waiting 65 seconds...')
                time.sleep(65)
            else:
                raise


def get_all_card_ids():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT cardID FROM [dbo].[tbl_MTGCardLibrary] WHERE cardID IS NOT NULL "
            "EXCEPT SELECT cardID FROM [dbo].[tbl_MTGPriceHistory] WHERE asOfDate = CAST(GETDATE() AS DATE) "
            "GROUP BY cardID")
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()

BATCH_SIZE = 100

def flush_batch(cursor, conn, sql, batch):
    try:
        cursor.executemany(sql, batch)
        conn.commit()
        batch.clear()
    except pyodbc.OperationalError as e:
        print("Commit failed:", e)


if __name__ == '__main__':
    sql = (
        "INSERT INTO [dbo].[tbl_MTGPriceHistory] VALUES(?, ?, ?, ?)"
    )
    tcg_sql = (
        "UPDATE [dbo].[tbl_MTGCardLibrary] SET tcgPlayerID = ? WHERE cardID = ?"
    )
    batch = []
    tcg_batch = []

    conn = get_connection()
    try:
        cursor = conn.cursor()
        for card_id in get_all_card_ids():
            try:
                print(card_id)
                card = scryfall_call(scrython.cards.Id, id=card_id)
                price = card.prices('usd') or 0.0
                foil_price = card.prices('usd_foil') or 0.0
                batch.append((card_id, price, d1, foil_price))

                # Not every printing has a TCGplayer product (some promos, digital-only cards)
                tcg_id = card.scryfallJson.get('tcgplayer_id')
                if tcg_id is not None:
                    tcg_batch.append((tcg_id, card_id))

                if len(batch) >= BATCH_SIZE:
                    flush_batch(cursor, conn, sql, batch)
                if len(tcg_batch) >= BATCH_SIZE:
                    flush_batch(cursor, conn, tcg_sql, tcg_batch)

            except (scrython.foundation.ScryfallError, asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ContentTypeError):
                print('card not found')

        if batch:
            flush_batch(cursor, conn, sql, batch)
        if tcg_batch:
            flush_batch(cursor, conn, tcg_sql, tcg_batch)
    finally:
        conn.close()
