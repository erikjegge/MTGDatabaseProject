'''
    Finds the 5 storage boxes with the most recent pricing "hits" and writes an Excel
    workbook with one tab per boxCode listing the cards worth pulling from that box.

    A "hit" is one of the top 500 cards in vw_getCardPrices by FivePPD (priced at
    $0.50+, not damaged, and not in one of the excluded working/holding boxes). Boxes
    are ranked by how many of those 500 hits they hold.

    Each box tab lists every card in that box that's $0.50+, not damaged, and has a
    positive FivePPD, ordered by FivePVD descending. A Summary tab up front shows each
    box's hit count and total estimated price of its hits.

    Each box tab starts with five working columns -- Picked, Grade, Subbox (left blank
    to fill in while pulling), SQL, a formula that builds a
    "(pkCard, Subbox, 'Grade')," values row from what's typed in, and TCGSku, a
    formula that picks the TCGplayer SKU matching the Grade (NM/LP/MP/HP/DMG) and
    isFoil, left blank until a Grade is entered or when no valid SKU is found.

    After the query columns come TCGplayer inventory-import columns (TCGplayer Id,
    Product Line, Set Name, Product Name, Condition, Add to Quantity, TCG Marketplace
    Price), filled in once per SKU so the block can be pasted into an import file.

    This script is READ-ONLY against the database.

    Usage:
        python topBoxPullList.py                 # top 5 boxes -> TopBoxes_YYYY-MM-DD.xlsx
        python topBoxPullList.py --boxCode 99    # one box     -> BoxCode_99_YYYY-MM-DD.xlsx

    Single-box mode skips the top-box ranking (so it works for the excluded
    working/holding boxes too) and writes just that box's tab, no Summary.
    Output is written to OUTPUT_DIR.
'''
import argparse
import os
from datetime import date

import pyodbc
from decouple import config
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

SERVER = config('SERVER')
DATABASE = config('DATABASE')
DB_USERNAME = config('DB_USERNAME')
DB_PASSWORD = config('DB_PASSWORD')
DRIVER = '{ODBC Driver 17 for SQL Server}'

OUTPUT_DIR = r'C:\Users\erikj\OneDrive\Desktop\TCG'

# Blank working columns prepended to each box tab, followed by the SQL and TCGSku
# formula columns. With these five in front, the view's pkCard lands in column F.
WORKING_COLUMNS = ['Picked', 'Grade', 'Subbox', 'SQL', 'TCGSku']
SQL_FORMULA = '''=CONCATENATE("(",{pk}{r},", ",C{r},", '",B{r},"'),")'''

# tbl_TCGSkus_Crosstab's SKU columns come in this order, a Non Foil / Foil pair per
# grade. TCGSku picks the pair for the Grade typed in, then the half matching
# isFoil. It stays blank until a Grade is entered, and also when the grade isn't
# recognised or TCGplayer has no SKU for that combination (e.g. foil of a
# non-foil-only card).
SKU_GRADES = ['NM', 'LP', 'MP', 'HP', 'DMG']
SKU_FIRST_COLUMN = 'Near Mint Non Foil'
SKU_LAST_COLUMN = 'Damaged Foil'
_SKU_LOOKUP = (
    'INDEX({first}{r}:{last}{r}, '
    '(MATCH(B{r},{{' + ','.join(f'"{g}"' for g in SKU_GRADES) + '}},0)-1)*2'
    '+IF({foil}{r},2,1))'
)
TCGSKU_FORMULA = f'=IF(B{{r}}="","",IFERROR(IF({_SKU_LOOKUP}="","",{_SKU_LOOKUP}),""))'

# TCGplayer inventory-import columns appended after the query columns, so the block
# can be copied straight into an import file. Each SKU fills in on its first row
# only, with Add to Quantity counting every row in the sheet with that SKU; rows
# with no SKU or a repeat SKU stay blank so nothing is imported twice. Rows whose
# set isn't in tbl_MTGSetLibrary (no setName) also stay blank and are left out.
SKU_CONDITIONS = ['Near Mint', 'Lightly Played', 'Moderately Played', 'Heavily Played', 'Damaged']
IMPORT_COLUMNS = [
    ('TCGplayer Id', '{sku}{r}'),
    ('Product Line', '"Magic"'),
    ('Set Name', '{setName}{r}'),
    ('Product Name', '{cardName}{r}'),
    ('Condition', 'INDEX({{' + ','.join(f'"{c}"' for c in SKU_CONDITIONS) + '}},'
                  'MATCH(B{r},{{' + ','.join(f'"{g}"' for g in SKU_GRADES) + '}},0))'
                  '&IF({isFoil}{r}," Foil","")'),
    ('Add to Quantity', 'COUNTIF({sku}$2:{sku}${last},{sku}{r})'),
    ('TCG Marketplace Price', '{EstPrice}{r}'),
]
IMPORT_FORMULA = (
    '=IF(OR({sku}{r}="",{setName}{r}="",COUNTIF({sku}$2:{sku}{r},{sku}{r})>1),"",{value})'
)

TOP_BOXES_SQL = '''
SELECT TOP 5 a.boxCode, SUM(a.EstPrice) AS totalEstPrice, COUNT(1) AS hitCount
FROM (SELECT TOP 500 *
      FROM dbo.vw_getCardPrices
      WHERE boxCode NOT IN (0,3,99,1000,1002,1001,9999,10000,3000,10001)
        AND EstPrice >= .25
        AND Damaged <> 1
      ORDER BY FivePVD DESC) AS a
GROUP BY a.boxCode
ORDER BY COUNT(1) DESC
'''

BOX_CARDS_SQL = '''
SELECT *
FROM dbo.vw_getCardPrices vgcp
	INNER JOIN [dbo].[tbl_TCGSkus_Crosstab] ttc ON vgcp.[tcgPlayerID] = ttc.[tcgPlayerID]
    LEFT JOIN dbo.tbl_MTGSetLibrary csl ON vgcp.[set] = csl.[setCode]
WHERE vgcp.EstPrice >= .25
  AND vgcp.FivePVD > 0
  AND vgcp.Damaged <> 1
  AND vgcp.boxCode = ?
ORDER BY FivePVD DESC
'''


def get_connection():
    return pyodbc.connect(
        f'DRIVER={DRIVER};PORT=1433;SERVER={SERVER};PORT=1443;DATABASE={DATABASE};'
        f'UID={DB_USERNAME};PWD={DB_PASSWORD}'
    )


def get_top_boxes(conn):
    cursor = conn.cursor()
    cursor.execute(TOP_BOXES_SQL)
    return [
        {'boxCode': row.boxCode, 'totalEstPrice': row.totalEstPrice, 'hitCount': row.hitCount}
        for row in cursor.fetchall()
    ]


def get_box_cards(conn, box_code):
    '''Returns (column names, rows) for one box.'''
    cursor = conn.cursor()
    cursor.execute(BOX_CARDS_SQL, box_code)
    columns = [col[0] for col in cursor.description]
    return columns, [list(row) for row in cursor.fetchall()]


def _autosize_columns(ws):
    for col_cells in ws.columns:
        length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(length + 2, 10), 60)
    ws.freeze_panes = 'A2'


def _header(ws, columns):
    ws.append(columns)
    for cell in ws[1]:
        cell.font = Font(bold=True)


def write_workbook(top_boxes, cards_by_box, out_path, include_summary=True):
    wb = Workbook()
    # Drop the default sheet; tabs are created explicitly below
    wb.remove(wb.active)

    if include_summary:
        ws_summary = wb.create_sheet('Summary')
        _header(ws_summary, ['Rank', 'boxCode', 'Hits (of top 500)', 'Hit Total EstPrice', 'Cards To Pull'])
        for rank, box in enumerate(top_boxes, start=1):
            _, rows = cards_by_box[box['boxCode']]
            ws_summary.append([rank, box['boxCode'], box['hitCount'], box['totalEstPrice'], len(rows)])
        _autosize_columns(ws_summary)

    for box in top_boxes:
        columns, rows = cards_by_box[box['boxCode']]
        ws = wb.create_sheet(str(box['boxCode']))
        headers = WORKING_COLUMNS + columns
        letter = {name: get_column_letter(i) for i, name in reversed(list(enumerate(headers, start=1)))}
        _header(ws, headers + [name for name, _ in IMPORT_COLUMNS])
        last_row = len(rows) + 1
        for excel_row, row in enumerate(rows, start=2):
            sql = SQL_FORMULA.format(pk=letter['pkCard'], r=excel_row)
            sku = TCGSKU_FORMULA.format(
                first=letter[SKU_FIRST_COLUMN], last=letter[SKU_LAST_COLUMN],
                foil=letter['isFoil'], r=excel_row,
            )
            refs = dict(
                sku=letter['TCGSku'], setName=letter['setName'], cardName=letter['cardName'],
                isFoil=letter['isFoil'], EstPrice=letter['EstPrice'], r=excel_row, last=last_row,
            )
            import_cells = [
                IMPORT_FORMULA.format(value=value.format(**refs), **refs)
                for _, value in IMPORT_COLUMNS
            ]
            ws.append([None, None, None, sql, sku] + row + import_cells)
        _autosize_columns(ws)

    wb.save(out_path)


def main():
    parser = argparse.ArgumentParser(description='Build a box pull list workbook.')
    parser.add_argument('--boxCode', type=int,
                        help='Only build the pull list for this box instead of the top 5')
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if args.boxCode is not None:
        out_path = os.path.join(OUTPUT_DIR, f'BoxCode_{args.boxCode}_{date.today():%Y-%m-%d}.xlsx')
    else:
        out_path = os.path.join(OUTPUT_DIR, f'TopBoxes_{date.today():%Y-%m-%d}.xlsx')

    conn = get_connection()
    try:
        if args.boxCode is not None:
            columns, rows = get_box_cards(conn, args.boxCode)
            print(f'Box {args.boxCode}: {len(rows)} cards to pull')
            box = {'boxCode': args.boxCode, 'hitCount': None, 'totalEstPrice': None}
            write_workbook([box], {args.boxCode: (columns, rows)}, out_path, include_summary=False)
            print(f'Wrote {out_path}')
            return

        top_boxes = get_top_boxes(conn)
        if not top_boxes:
            print('No boxes returned by the top-box query.')
            return
        cards_by_box = {}
        for box in top_boxes:
            cards_by_box[box['boxCode']] = get_box_cards(conn, box['boxCode'])
            print(f"Box {box['boxCode']}: {box['hitCount']} hits, "
                  f"{len(cards_by_box[box['boxCode']][1])} cards to pull")
    finally:
        conn.close()

    write_workbook(top_boxes, cards_by_box, out_path)
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    main()
