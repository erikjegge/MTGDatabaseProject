'''
    GUI tool for cleaning up a TCGplayer "MyPricing" export CSV:

    1. Drops every row where Total Quantity = 0 (nothing to price -- TCGplayer
       won't list it anyway).
    2. Recalculates TCG Marketplace Price from TCG Low Price With Shipping (K),
       using the same rule as the spreadsheet formula:
           =IF(K2-1.99<1, ROUND(MAX(F, F+((K2-1.99)*0.23)), 2), K2-1.49)
       where F (the price floor) depends on how long the card has sat in
       inventory box 10001 (matched by product name + set name):
           under a month, or no inventory match  -> 0.23
           older than a month                    -> 0.17
           older than two months, or no date     -> 0.13
    3. Keeps only rows whose TCG Marketplace Price actually changed (rows
       already at the correct price, or with no TCG Low Price With Shipping
       to recalculate from, are dropped).

    Writes a new CSV (original file is left untouched) named
    "<original>_corrected.csv" next to the source file, in the same quoting
    style TCGplayer exports use (bare header row, every data field quoted).

    Launch by double-clicking RunTcgPricingCorrector.bat, or:
        pythonw tcgPricingCorrector.py
'''
import csv
import calendar
import os
import queue
import threading
from datetime import date, datetime
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

QTY_FIELD = 'Total Quantity'
SHIPPED_LOW_FIELD = 'TCG Low Price With Shipping'
MARKETPLACE_PRICE_FIELD = 'TCG Marketplace Price'
NAME_FIELD = 'Product Name'
SET_FIELD = 'Set Name'
REQUIRED_FIELDS = (QTY_FIELD, SHIPPED_LOW_FIELD, MARKETPLACE_PRICE_FIELD, NAME_FIELD, SET_FIELD)

INVENTORY_BOX_CODE = 10001
DEFAULT_FLOOR = 0.23
OLD_FLOOR = 0.17        # older than one month
VERY_OLD_FLOOR = 0.13   # older than two months, or no date


# ---------------------------------------------------------------------------
# Parsing / math helpers
# ---------------------------------------------------------------------------

def parse_float(value):
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_qty(value):
    value = (value or '').strip()
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        try:
            return int(float(value))
        except ValueError:
            return 0


def months_ago(today, months):
    month_index = today.year * 12 + (today.month - 1) - months
    year, month = divmod(month_index, 12)
    month += 1
    day = min(today.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def floor_for_date(box_date, today=None):
    '''Price floor for a card last modified in the box on box_date (None = no date).'''
    today = today or date.today()
    if box_date is None:
        return VERY_OLD_FLOOR
    if isinstance(box_date, datetime):
        box_date = box_date.date()
    if box_date < months_ago(today, 2):
        return VERY_OLD_FLOOR
    if box_date < months_ago(today, 1):
        return OLD_FLOOR
    return DEFAULT_FLOOR


def calculate_marketplace_price(shipped_low, floor=DEFAULT_FLOOR):
    '''
    Port of: =IF(K2-1.99<1, ROUND(MAX(floor, floor+((K2-1.99)*0.23)), 2), K2-1.49)
    '''
    adjusted = shipped_low - 1.99
    if adjusted < 1:
        value = max(floor, floor + (adjusted * 0.23))
        return round(value, 2)
    return round(shipped_low - 1.49, 2)


def inventory_key(name, set_name):
    return ((name or '').strip().lower(), (set_name or '').strip().lower())


def load_inventory_floors():
    '''
    Returns {(lower(cardName), lower(setName)): floor} for everything in box
    INVENTORY_BOX_CODE. When several copies share a name+set, the newest one
    decides (a fresh copy means the listing is fresh); a null boxModifiedDate
    only counts if every copy is null.
    '''
    import pyodbc
    from decouple import config

    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};PORT=1433;SERVER={config('SERVER')};"
        f"PORT=1443;DATABASE={config('DATABASE')};UID={config('DB_USERNAME')};"
        f"PWD={config('DB_PASSWORD')}"
    )
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT cl.cardName, sl.setName, MAX(cl.boxModifiedDate) "
            "FROM [dbo].[tbl_MTGCardLibrary] cl "
            "INNER JOIN [dbo].[tbl_MTGSetLibrary] sl ON cl.[set] = sl.setCode "
            "WHERE cl.boxCode = ? "
            "GROUP BY cl.cardName, sl.setName",
            INVENTORY_BOX_CODE
        )
        return {inventory_key(name, set_name): floor_for_date(box_date)
                for name, set_name, box_date in cur.fetchall()}
    finally:
        conn.close()


def format_price(value):
    return f'{value:.4f}'


# ---------------------------------------------------------------------------
# Core processing
# ---------------------------------------------------------------------------

def build_output_path(input_path):
    root, ext = os.path.splitext(input_path)
    return f'{root}_corrected{ext or ".csv"}'


def process_pricing_file(input_path, output_path=None, progress_cb=None, inventory_floors=None):
    '''
    Reads the TCGplayer pricing CSV at input_path, drops zero-quantity rows,
    recalculates TCG Marketplace Price, and writes the result to output_path
    (defaults to "<input>_corrected.csv"). Returns a summary dict.

    inventory_floors is {(name, set): floor} from load_inventory_floors(); it is
    loaded from the database when not supplied. Rows with no match use DEFAULT_FLOOR.
    '''
    def log(msg):
        if progress_cb:
            progress_cb(msg)

    output_path = output_path or build_output_path(input_path)

    with open(input_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [field for field in REQUIRED_FIELDS if field not in fieldnames]
        if missing:
            raise ValueError(
                f'This file is missing expected column(s): {", ".join(missing)}. '
                'Is this a TCGplayer pricing export?'
            )
        rows = list(reader)

    log(f'Read {len(rows)} row(s) from {os.path.basename(input_path)}')

    if inventory_floors is None:
        log(f'Loading box {INVENTORY_BOX_CODE} inventory dates...')
        inventory_floors = load_inventory_floors()
    floor_counts = {DEFAULT_FLOOR: 0, OLD_FLOOR: 0, VERY_OLD_FLOOR: 0}
    unmatched = 0

    total_rows = len(rows)
    kept_rows = []
    dropped_zero_qty = 0
    updated_prices = 0
    unchanged_prices = 0
    skipped_no_price = 0

    for row in rows:
        if parse_qty(row.get(QTY_FIELD)) == 0:
            dropped_zero_qty += 1
            continue

        shipped_low = parse_float(row.get(SHIPPED_LOW_FIELD))
        if shipped_low is None:
            skipped_no_price += 1
            continue

        floor = inventory_floors.get(inventory_key(row.get(NAME_FIELD), row.get(SET_FIELD)))
        if floor is None:
            unmatched += 1
            floor = DEFAULT_FLOOR
        floor_counts[floor] += 1

        new_price = calculate_marketplace_price(shipped_low, floor)
        old_price = parse_float(row.get(MARKETPLACE_PRICE_FIELD))
        if old_price is not None and round(old_price, 2) == new_price:
            unchanged_prices += 1
            continue

        row[MARKETPLACE_PRICE_FIELD] = format_price(new_price)
        updated_prices += 1
        kept_rows.append(row)

    log(f'Dropping {dropped_zero_qty} row(s) with {QTY_FIELD} = 0')
    log(f'Changed {MARKETPLACE_PRICE_FIELD} for {updated_prices} row(s)')
    log(f'Dropping {unchanged_prices} row(s) whose {MARKETPLACE_PRICE_FIELD} is already correct')
    log(f'Floors used: ${DEFAULT_FLOOR:.2f} x {floor_counts[DEFAULT_FLOOR]} '
        f'({unmatched} not found in box {INVENTORY_BOX_CODE}), '
        f'${OLD_FLOOR:.2f} x {floor_counts[OLD_FLOOR]}, '
        f'${VERY_OLD_FLOOR:.2f} x {floor_counts[VERY_OLD_FLOOR]}')
    if skipped_no_price:
        log(f'Dropping {skipped_no_price} row(s) missing {SHIPPED_LOW_FIELD}')

    # utf-8 (no BOM) on write -- 'utf-8-sig' here would *inject* a BOM into
    # every output file, and TCGplayer's importer chokes on that (misreads
    # it as literal characters glued onto the first header name, which
    # breaks its column matching and it stops after "seeing" one record).
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        # Match csv.writer's default CRLF line terminator so the header line
        # doesn't end in a bare LF while every data row ends in CRLF -- a
        # mixed-line-ending file trips up strict CSV parsers (including
        # TCGplayer's importer), which can lose track of record boundaries
        # after the first row.
        f.write(','.join(fieldnames) + '\r\n')
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        for row in kept_rows:
            writer.writerow([row.get(field, '') for field in fieldnames])

    log(f'Wrote {len(kept_rows)} row(s) to {os.path.basename(output_path)}')

    return {
        'input_path': input_path,
        'output_path': output_path,
        'total_rows': total_rows,
        'dropped_zero_qty': dropped_zero_qty,
        'updated_prices': updated_prices,
        'unchanged_prices': unchanged_prices,
        'skipped_no_price': skipped_no_price,
        'remaining_rows': len(kept_rows),
    }


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class TcgPricingCorrectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('TCG Pricing Corrector')
        self.root.geometry('640x460')
        self.root.minsize(560, 380)

        self.selected_path = tk.StringVar()
        self.status_queue = queue.Queue()
        self.last_output_path = None

        self._build_widgets()
        self._poll_status_queue()

    def _build_widgets(self):
        pad = {'padx': 10, 'pady': 6}

        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill='x', **pad)
        ttk.Label(file_frame, text='TCGplayer pricing CSV:').pack(side='left')
        ttk.Entry(file_frame, textvariable=self.selected_path, state='readonly').pack(
            side='left', fill='x', expand=True, padx=(8, 8))
        ttk.Button(file_frame, text='Browse...', command=self._browse).pack(side='left')

        self.run_button = ttk.Button(self.root, text='Run', command=self._run_clicked, state='disabled')
        self.run_button.pack(**pad)

        self.log_box = scrolledtext.ScrolledText(self.root, height=16, state='disabled', wrap='word')
        self.log_box.pack(fill='both', expand=True, padx=10, pady=(0, 6))

        result_frame = ttk.Frame(self.root)
        result_frame.pack(fill='x', padx=10, pady=(0, 10))
        self.open_file_button = ttk.Button(
            result_frame, text='Open Corrected CSV', command=self._open_output, state='disabled')
        self.open_file_button.pack(side='left')
        self.open_folder_button = ttk.Button(
            result_frame, text='Open Folder', command=self._open_folder, state='disabled')
        self.open_folder_button.pack(side='left', padx=(8, 0))

    def _browse(self):
        path = filedialog.askopenfilename(
            title='Select TCGplayer pricing export',
            filetypes=[('CSV files', '*.csv'), ('All files', '*.*')],
        )
        if path:
            self.selected_path.set(path)
            self.run_button['state'] = 'normal'

    def _log(self, message):
        self.log_box['state'] = 'normal'
        self.log_box.insert('end', message + '\n')
        self.log_box.see('end')
        self.log_box['state'] = 'disabled'

    def _run_clicked(self):
        path = self.selected_path.get()
        if not path:
            return

        self.log_box['state'] = 'normal'
        self.log_box.delete('1.0', 'end')
        self.log_box['state'] = 'disabled'
        self.run_button['state'] = 'disabled'
        self.open_file_button['state'] = 'disabled'
        self.open_folder_button['state'] = 'disabled'
        self.last_output_path = None

        thread = threading.Thread(target=self._run_worker, args=(path,), daemon=True)
        thread.start()

    def _run_worker(self, path):
        try:
            summary = process_pricing_file(path, progress_cb=lambda msg: self.status_queue.put(('log', msg)))
            self.status_queue.put(('summary', summary))
        except Exception as e:
            self.status_queue.put(('error', str(e)))

    def _poll_status_queue(self):
        try:
            while True:
                kind, payload = self.status_queue.get_nowait()
                if kind == 'log':
                    self._log(payload)
                elif kind == 'error':
                    self._log(f'ERROR: {payload}')
                    self.run_button['state'] = 'normal'
                    messagebox.showerror('Failed', payload)
                elif kind == 'summary':
                    self._show_summary(payload)
        except queue.Empty:
            pass
        self.root.after(150, self._poll_status_queue)

    def _show_summary(self, summary):
        self._log('')
        self._log(f"Rows read: {summary['total_rows']}")
        self._log(f"Rows dropped (Total Quantity = 0): {summary['dropped_zero_qty']}")
        self._log(f"Rows with changed Marketplace Price: {summary['updated_prices']}")
        self._log(f"Rows dropped (price already correct): {summary['unchanged_prices']}")
        if summary['skipped_no_price']:
            self._log(f"Rows dropped (missing {SHIPPED_LOW_FIELD}): {summary['skipped_no_price']}")
        self._log(f"Rows remaining: {summary['remaining_rows']}")
        self._log('')
        self._log(f"Corrected CSV written to: {summary['output_path']}")

        self.last_output_path = summary['output_path']
        self.run_button['state'] = 'normal'
        self.open_file_button['state'] = 'normal'
        self.open_folder_button['state'] = 'normal'

    def _open_output(self):
        if self.last_output_path and os.path.exists(self.last_output_path):
            os.startfile(self.last_output_path)

    def _open_folder(self):
        if self.last_output_path:
            os.startfile(os.path.dirname(os.path.abspath(self.last_output_path)))


def main():
    root = tk.Tk()
    TcgPricingCorrectorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
