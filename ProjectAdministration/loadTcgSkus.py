'''
    Loads MTGJSON's TcgplayerSkus.json (or .json.gz) into [dbo].[tbl_TCGSkus],
    then pivots it into [dbo].[tbl_TCGSkus_Crosstab] (one row per tcgPlayerID,
    one SKU column per condition / foil combination).

    Each row is one TCGplayer SKU: a product (tcgPlayerID in tbl_MTGCardLibrary)
    in a specific condition / printing / language. The table is dropped and
    rebuilt on every run, so re-run it whenever you download a fresh file.

    Usage:
        python loadTcgSkus.py <path to TcgplayerSkus.json[.gz]> [--all-languages]

    By default only ENGLISH SKUs are loaded (~800k rows vs ~5.2M for all languages).
'''
import gzip
import json
import sys
import pyodbc
from decouple import config

server = config('SERVER')
database = config('DATABASE')
username = config('DB_USERNAME')
password = config('DB_PASSWORD')
driver = '{ODBC Driver 17 for SQL Server}'

BATCH_SIZE = 10000


def get_connection():
    return pyodbc.connect(
        f'DRIVER={driver};PORT=1433;SERVER={server};PORT=1443;DATABASE={database};UID={username};PWD={password}'
    )


def load_skus(path, english_only):
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as f:
        data = json.load(f)['data']

    # The same SKU is listed under every MTGJSON uuid that shares the product
    # (e.g. both faces of a card), so dedupe on skuId.
    skus = {}
    for sku_list in data.values():
        for s in sku_list:
            if english_only and s['language'] != 'ENGLISH':
                continue
            existing = skus.get(s['skuId'])
            if existing is None or (existing[5] is None and s.get('finish')):
                skus[s['skuId']] = (
                    s['skuId'], s['productId'], s['condition'],
                    s['printing'], s['language'], s.get('finish'),
                )
    return list(skus.values())


def rebuild_table(cursor):
    cursor.execute("DROP TABLE IF EXISTS [dbo].[tbl_TCGSkus]")
    cursor.execute(
        "CREATE TABLE [dbo].[tbl_TCGSkus] ("
        " skuID INT NOT NULL PRIMARY KEY,"
        " tcgPlayerID INT NOT NULL,"
        " condition NVARCHAR(20) NOT NULL,"
        " printing NVARCHAR(10) NOT NULL,"
        " language NVARCHAR(25) NOT NULL,"
        " finish NVARCHAR(10) NULL)"
    )


CONDITIONS = ['NEAR MINT', 'LIGHTLY PLAYED', 'MODERATELY PLAYED', 'HEAVILY PLAYED', 'DAMAGED']
PRINTINGS = ['NON FOIL', 'FOIL']


def rebuild_crosstab(cursor):
    '''One row per product with a column per condition/printing SKU (etched SKUs excluded).'''
    columns = ',\n'.join(
        f"    MAX(CASE WHEN condition = '{c}' AND printing = '{p}' THEN skuID END)"
        f" AS [{c.title()} {p.title()}]"
        for c in CONDITIONS for p in PRINTINGS
    )
    cursor.execute("DROP TABLE IF EXISTS [dbo].[tbl_TCGSkus_Crosstab]")
    cursor.execute(
        f"SELECT tcgPlayerID,\n{columns}\n"
        "INTO [dbo].[tbl_TCGSkus_Crosstab]\n"
        "FROM [dbo].[tbl_TCGSkus]\n"
        "WHERE language = 'ENGLISH' AND finish IS NULL\n"
        "GROUP BY tcgPlayerID"
    )
    cursor.execute(
        "ALTER TABLE [dbo].[tbl_TCGSkus_Crosstab]"
        " ADD CONSTRAINT PK_tbl_TCGSkus_Crosstab PRIMARY KEY (tcgPlayerID)"
    )


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(1)
    english_only = '--all-languages' not in sys.argv

    print('Reading', args[0])
    rows = load_skus(args[0], english_only)
    print(f'{len(rows)} unique SKUs to load')

    conn = get_connection()
    try:
        cursor = conn.cursor()
        rebuild_table(cursor)
        conn.commit()

        cursor.fast_executemany = True
        sql = "INSERT INTO [dbo].[tbl_TCGSkus] VALUES(?, ?, ?, ?, ?, ?)"
        for i in range(0, len(rows), BATCH_SIZE):
            cursor.executemany(sql, rows[i:i + BATCH_SIZE])
            conn.commit()
            print(f'{min(i + BATCH_SIZE, len(rows))} / {len(rows)}')

        # Lookups go product -> SKU, so index the product id
        cursor.execute(
            "CREATE INDEX IX_tbl_TCGSkus_tcgPlayerID ON [dbo].[tbl_TCGSkus]"
            " (tcgPlayerID, condition, printing)"
        )
        conn.commit()

        print('Building tbl_TCGSkus_Crosstab')
        rebuild_crosstab(cursor)
        conn.commit()
        print('Done')
    finally:
        conn.close()
