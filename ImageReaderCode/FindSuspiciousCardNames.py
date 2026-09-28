'''
    Read-only audit: flags tbl_MTGCardLibrary rows whose cardName doesn't exactly match
    a real card name in tbl_MasterCardTable. Most of these are legitimate (foreign-language
    cards, OCR token-order quirks, double-faced/adventure card names) but some may be
    leftover garbage from an earlier OCR run that overwrote 'XXX' placeholders with
    unreadable text before a match-confidence check existed.

    Prints candidates sorted worst-match-first so the most likely garbage rows are easy to
    spot for manual review. Makes no database changes.
'''
import difflib

import pyodbc
from decouple import config

# below this, a cardName is unlikely to be a lightly-mangled version of the matched
# real name -- probably actual garbage rather than a formatting quirk
SUSPICIOUS_BELOW = 0.85


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


def load_master_card_names():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT [CardName] FROM [dbo].[tbl_MasterCardTable]")
    names = [row[0] for row in cursor.fetchall() if row[0]]
    cursor.close()
    conn.close()

    return names


def get_non_xxx_records():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT [pkCard], [cardName], [set], [filepath] "
        "FROM [dbo].[tbl_MTGCardLibrary] "
        "WHERE cardName <> 'XXX' AND cardName IS NOT NULL"
    )
    records = [list(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    return records


def main():
    master_names = load_master_card_names()
    master_names_lower = {name.lower(): name for name in master_names}

    records = get_non_xxx_records()
    print(f'Checking {len(records)} rows against {len(master_names)} known card names...')

    flagged = []
    for pkCard, cardName, setCode, filepath in records:
        if cardName.lower() in master_names_lower:
            continue

        matches = difflib.get_close_matches(cardName.lower(), master_names_lower.keys(), n=1, cutoff=0.0)
        closest, ratio = None, 0.0
        if matches:
            closest = master_names_lower[matches[0]]
            ratio = difflib.SequenceMatcher(None, cardName.lower(), matches[0]).ratio()

        flagged.append((ratio, pkCard, cardName, closest, setCode, filepath))

    flagged.sort(key=lambda r: r[0])

    print(f'{len(flagged)} rows do not exactly match a known card name:\n')
    for ratio, pkCard, cardName, closest, setCode, filepath in flagged:
        marker = '  <-- likely garbage' if ratio < SUSPICIOUS_BELOW else ''
        print(f'pkCard={pkCard} set={setCode} ratio={ratio:.2f} cardName="{cardName}" closest="{closest}" filepath={filepath}{marker}')


if __name__ == '__main__':
    main()
