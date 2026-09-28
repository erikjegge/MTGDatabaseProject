'''
    Ingests a TCGplayer pull sheet CSV and produces a pick list ordered to match the
    physical layout of box 10001: the main box is one alphabetical (by card name) run,
    plus zero or more subBoxCode containers that are each their own independent
    alphabetical run. Walking each container once, in the order printed, is the
    fastest way to collect everything on the sheet.

    The pull sheet's Condition column (e.g. "Lightly Played Foil") is parsed into a
    tbl_MTGCardLibrary.cardGrade code ("NM"/"LP"/"MP"/"HP"/"D") plus an isFoil flag,
    and cards are matched on name + set + grade + foil -- not just name + set -- so
    the pick list points at the exact physical copy that was ordered.

    Cards with no subBoxCode (the older, pre-grading inventory that's being phased
    out) were never tagged with a real cardGrade/isFoil, so a name+set match there is
    accepted regardless of what's actually stored on that row -- the pick list shows
    what was *ordered* (translated to a grade code) for those and marks them
    "Assumed (ungraded box)" in the Condition Source column, versus "Inventory" for
    a verified graded match.

    The pull sheet's Number column (collector number) is carried through to the pick
    list unmodified, purely for reference -- inventory doesn't track it, so it's not
    used for matching, but it's how you tell apart same-name/same-set cards that
    print more than once (e.g. basic lands) at a glance.

    This script is READ-ONLY against the database -- it never marks anything sold.

    Usage:
        python pullSheetPicker.py <path-to-pull-sheet.csv> [--box 10001]

    If no path is given, it picks the newest TCGplayer_PullSheet_*.csv found in the
    current directory or the project root.
'''
import csv
import difflib
import glob
import os
import re
import sys
from collections import defaultdict

import pyodbc
from decouple import config
from openpyxl import Workbook
from openpyxl.styles import Font

SERVER = config('SERVER')
DATABASE = config('DATABASE')
DB_USERNAME = config('DB_USERNAME')
DB_PASSWORD = config('DB_PASSWORD')
DRIVER = '{ODBC Driver 17 for SQL Server}'

DEFAULT_BOX_CODE = 10001
FUZZY_SET_MATCH_THRESHOLD = 0.55

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# TCGplayer's Condition column is a base condition, optionally suffixed with "Foil"
# (e.g. "Lightly Played Foil"). Maps the base condition to tbl_MTGCardLibrary.cardGrade.
CONDITION_TO_GRADE = {
    'near mint': 'NM',
    'lightly played': 'LP',
    'moderately played': 'MP',
    'heavily played': 'HP',
    'damaged': 'D',
}


def parse_condition(raw_condition):
    '''
    "Lightly Played Foil" -> ('LP', True). "Near Mint" -> ('NM', False).
    Returns (grade or None, is_foil). grade is None if the base condition text
    doesn't match anything in CONDITION_TO_GRADE (caller should treat as unresolved).
    '''
    text = (raw_condition or '').strip().lower()
    is_foil = False
    base = text
    if base.endswith(' foil'):
        is_foil = True
        base = base[:-len(' foil')].strip()
    return CONDITION_TO_GRADE.get(base), is_foil


def condition_label(grade, is_foil):
    return f"{grade} Foil" if is_foil else grade


def get_connection():
    return pyodbc.connect(
        f'DRIVER={DRIVER};PORT=1433;SERVER={SERVER};PORT=1443;DATABASE={DATABASE};'
        f'UID={DB_USERNAME};PWD={DB_PASSWORD}'
    )


def find_default_pull_sheet():
    candidates = []
    for folder in (os.getcwd(), PROJECT_ROOT):
        candidates.extend(glob.glob(os.path.join(folder, 'TCGplayer_PullSheet_*.csv')))
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


# ---------------------------------------------------------------------------
# Pull sheet parsing
# ---------------------------------------------------------------------------

def load_pull_sheet(path):
    '''
    Returns a list of dicts: {name, set, number, quantity, condition, grade, isFoil, conditionResolved}
    One entry per distinct (name, set, number, condition) on the sheet -- quantities are
    only summed across rows that repeat the exact same name/set/number/condition, since
    different conditions (or different printings sharing a name+set) need to be pulled
    as physically different cards. Number is carried through from the pull sheet as-is
    (not validated against inventory, which doesn't track it) purely so it's visible on
    the pick list -- some sets print the same card name multiple times with different
    collector numbers.
    '''
    rows_by_key = defaultdict(lambda: {
        'name': None, 'set': None, 'number': None, 'quantity': 0,
        'condition': None, 'grade': None, 'isFoil': False, 'conditionResolved': True,
    })

    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row.get('Product Line') or '').strip() != 'Magic':
                continue  # skips the trailing "Orders Contained in Pull Sheet:" line and non-Magic rows

            name = (row.get('Product Name') or '').strip()
            set_name = (row.get('Set') or '').strip()
            number = (row.get('Number') or '').strip()
            condition = (row.get('Condition') or '').strip()
            grade, is_foil = parse_condition(condition)
            try:
                qty = int(row.get('Quantity') or 0)
            except ValueError:
                qty = 0

            key = (name.lower(), set_name.lower(), number.lower(), condition.lower())
            entry = rows_by_key[key]
            entry['name'] = name
            entry['set'] = set_name
            entry['number'] = number
            entry['quantity'] += qty
            entry['condition'] = condition
            entry['grade'] = grade
            entry['isFoil'] = is_foil
            entry['conditionResolved'] = grade is not None

    return list(rows_by_key.values())


# ---------------------------------------------------------------------------
# Inventory loading
# ---------------------------------------------------------------------------

def load_box_inventory(conn, box_code):
    '''
    Returns:
      by_name: {lower(cardName): {setCode: [row, ...]}}  row = dict with pkCard, cardName,
               set, subBoxCode, isFoil, cardID, cardGrade
    '''
    cur = conn.cursor()
    cur.execute(
        "SELECT pkCard, cardName, [set], subBoxCode, isFoil, cardID, cardGrade "
        "FROM [dbo].[tbl_MTGCardLibrary] "
        "WHERE boxCode = ? AND isEnabled = 1 AND soldDate IS NULL",
        box_code
    )
    by_name = defaultdict(lambda: defaultdict(list))
    for pkCard, cardName, set_code, subBoxCode, isFoil, cardID, cardGrade in cur.fetchall():
        if not cardName:
            continue
        by_name[cardName.strip().lower()][set_code].append({
            'pkCard': pkCard,
            'cardName': cardName,
            'set': set_code,
            'subBoxCode': subBoxCode,
            'isFoil': bool(isFoil),
            'cardID': cardID,
            'cardGrade': (cardGrade or '').strip().upper(),
        })
    return by_name


def summarize_box_conditions(rows):
    '''Human-readable breakdown of what conditions/foilness the box actually has for a card+set.'''
    counts = defaultdict(int)
    for row in rows:
        if row['subBoxCode'] is None:
            label = 'Ungraded (main box)'
        else:
            label = condition_label(row['cardGrade'] or '?', row['isFoil'])
        counts[label] += 1
    parts = [f'{label}: {count}' for label, count in sorted(counts.items())]
    return ', '.join(parts) if parts else 'none'


def load_set_library(conn):
    '''Returns (setCode -> setName), (lower(setName) -> [setCode, ...]) for lookups/fuzzy matching.'''
    cur = conn.cursor()
    cur.execute("SELECT setName, setCode FROM [dbo].[tbl_MTGSetLibrary]")
    code_to_name = {}
    name_to_codes = defaultdict(list)
    for set_name, set_code in cur.fetchall():
        if not set_name or not set_code:
            continue
        code_to_name.setdefault(set_code, set_name)
        name_to_codes[set_name.strip().lower()].append(set_code)
    return code_to_name, name_to_codes


PAREN_SUFFIX_RE = re.compile(r'\s*\([^()]*\)\s*$')


def resolve_set_codes_from_name(pull_sheet_set_name, name_to_codes):
    '''Try exact match, then with a trailing "(...)" qualifier stripped (TCGplayer often appends the code).'''
    codes = set()
    raw = pull_sheet_set_name.strip().lower()
    if raw in name_to_codes:
        codes.update(name_to_codes[raw])

    stripped = PAREN_SUFFIX_RE.sub('', pull_sheet_set_name).strip().lower()
    if stripped and stripped != raw and stripped in name_to_codes:
        codes.update(name_to_codes[stripped])

    return codes


def disambiguate_set(pull_sheet_set_name, candidate_set_codes, code_to_name, name_to_codes):
    '''
    candidate_set_codes: the set codes actually present in the box for this card name.

    Resolves what set the pull sheet actually asked for FIRST (against the whole set
    library, not just what's in the box), then checks whether the box holds that
    printing. A card name having only one printing in the box is never, by itself,
    treated as proof that it's the right printing -- the box holding a *different*
    printing than what was ordered is exactly the case that must be caught.

    Returns (chosen_set_code or None, method_string).
    '''
    # 1. Exact (or "(CODE)" stripped) match against the full set library.
    resolved_codes = resolve_set_codes_from_name(pull_sheet_set_name, name_to_codes)
    resolution_method = 'matched set library name'

    if not resolved_codes:
        # 2. Fuzzy match against the full set library (not just box candidates) so we
        #    find what was actually ordered, not just whatever happens to be in the box.
        best_code, best_ratio = None, 0.0
        for code, lib_name in code_to_name.items():
            ratio = difflib.SequenceMatcher(None, pull_sheet_set_name.lower(), lib_name.lower()).ratio()
            if ratio > best_ratio:
                best_code, best_ratio = code, ratio
        if best_code and best_ratio >= FUZZY_SET_MATCH_THRESHOLD:
            resolved_codes = {best_code}
            resolution_method = f'fuzzy matched set library name ({best_ratio:.2f})'

    if resolved_codes:
        matched = resolved_codes & candidate_set_codes
        if len(matched) == 1:
            return next(iter(matched)), resolution_method
        if len(matched) > 1:
            return None, 'ambiguous (multiple matching printings present in box)'
        # We know what was ordered, and the box does not have it -- even if the box
        # has exactly one (different) printing of this card name, that is NOT a match.
        have = ', '.join(sorted(candidate_set_codes))
        return None, f'box has different printing(s) than ordered: {have}'

    # Could not resolve the pull sheet's set name to anything in the set library at all.
    if len(candidate_set_codes) == 1:
        only_code = next(iter(candidate_set_codes))
        return only_code, f'LOW CONFIDENCE: set name unresolved, assumed the box\'s only printing ({only_code}) -- verify by hand'

    return None, 'ambiguous (set name unresolved, multiple printings in box)'


def collect_set_name_mismatches(pull_sheet_rows, code_to_name, name_to_codes):
    '''
    For every unique set name TCGplayer used on the pull sheet that does NOT exactly
    (or "(CODE)"-stripped) match an entry in tbl_MTGSetLibrary, report the closest
    fuzzy guess so it's easy to check whether tbl_MTGSetLibrary is just missing an
    alias/entry for that set.
    '''
    seen_keys = set()
    mismatches = []

    for entry in pull_sheet_rows:
        set_name = entry['set']
        key = set_name.strip().lower()
        if not set_name or key in seen_keys:
            continue
        seen_keys.add(key)

        if resolve_set_codes_from_name(set_name, name_to_codes):
            continue  # exact match exists, nothing to report

        best_code, best_name, best_ratio = None, None, 0.0
        for code, lib_name in code_to_name.items():
            ratio = difflib.SequenceMatcher(None, set_name.lower(), lib_name.lower()).ratio()
            if ratio > best_ratio:
                best_code, best_name, best_ratio = code, lib_name, ratio

        mismatches.append({
            'pullSheetSetName': set_name,
            'bestGuessName': best_name,
            'bestGuessCode': best_code,
            'bestGuessScore': best_ratio,
        })

    return mismatches


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------

def match_pull_sheet(pull_sheet_rows, by_name, code_to_name, name_to_codes):
    picks = []       # list of dicts: container, cardName, set, qtyNeeded, qtyAvailable, isFoil, pkCards
    not_found = []    # cards with no matching name in the box at all
    needs_review = []  # ambiguous set match, or found but not enough copies

    for entry in pull_sheet_rows:
        name_key = entry['name'].strip().lower()
        candidates_by_set = by_name.get(name_key)

        if not candidates_by_set:
            not_found.append(entry)
            continue

        candidate_set_codes = set(candidates_by_set.keys())
        chosen_code, method = disambiguate_set(entry['set'], candidate_set_codes, code_to_name, name_to_codes)

        if chosen_code is None:
            needs_review.append({
                **entry,
                'reason': method,
                'candidates': {code: len(rows) for code, rows in candidates_by_set.items()},
            })
            continue

        set_rows = candidates_by_set[chosen_code]

        if entry['grade'] is None:
            needs_review.append({
                **entry,
                'reason': (
                    f"unrecognized condition on pull sheet: '{entry['condition']}' "
                    "(expected Near Mint/Lightly Played/Moderately Played/Heavily Played/Damaged, "
                    "optionally + Foil)"
                ),
                'candidates': {chosen_code: len(set_rows)},
            })
            continue

        box_summary_before = summarize_box_conditions(set_rows)
        qty_needed = entry['quantity']

        # Tier 1: real graded inventory (has a subBoxCode) matching the exact
        # condition + foil that was ordered.
        graded_matches = [
            row for row in set_rows
            if row['subBoxCode'] is not None
            and row['cardGrade'] == entry['grade']
            and row['isFoil'] == entry['isFoil']
        ]
        graded_take = graded_matches[:qty_needed]

        # Tier 2: legacy ungraded stock (subBoxCode IS NULL). This box is being
        # phased out and was never graded/foil-tagged card by card, so any card
        # found here by name+set is accepted as a match for whatever's still
        # needed -- the pick list shows what was ordered (translated to a grade
        # code), not the (absent) inventory value, since the latter can't be trusted.
        remaining_needed = qty_needed - len(graded_take)
        ungraded_take = []
        if remaining_needed > 0:
            ungraded_pool = [row for row in set_rows if row['subBoxCode'] is None]
            ungraded_take = ungraded_pool[:remaining_needed]

        # Remove whatever got allocated here from the shared pool so a later pull
        # sheet line for the same card+set (a different condition) can't also claim it.
        allocated_ids = {id(row) for row in graded_take + ungraded_take}
        set_rows[:] = [row for row in set_rows if id(row) not in allocated_ids]

        for row in graded_take:
            picks.append({
                'container': row['subBoxCode'],
                'cardName': row['cardName'],
                'set': row['set'],
                'number': entry['number'],
                'isFoil': row['isFoil'],
                'cardGrade': row['cardGrade'],
                'conditionSource': 'Inventory',
                'pkCard': row['pkCard'],
                'orderedName': entry['name'],
                'setMatchMethod': method,
            })
        for row in ungraded_take:
            picks.append({
                'container': row['subBoxCode'],
                'cardName': row['cardName'],
                'set': row['set'],
                'number': entry['number'],
                'isFoil': entry['isFoil'],
                'cardGrade': entry['grade'],
                'conditionSource': 'Assumed (ungraded box)',
                'pkCard': row['pkCard'],
                'orderedName': entry['name'],
                'setMatchMethod': method,
            })

        qty_taken = len(graded_take) + len(ungraded_take)
        if qty_taken < qty_needed:
            needs_review.append({
                **entry,
                'reason': (
                    f"short: need {qty_needed} {condition_label(entry['grade'], entry['isFoil'])}, "
                    f"only {qty_taken} in box (set {chosen_code}) "
                    f"-- box has: {box_summary_before}"
                ),
                'candidates': {chosen_code: qty_taken},
            })

    return picks, not_found, needs_review


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def container_sort_key(sub_box_code):
    return (0, 0) if sub_box_code is None else (1, sub_box_code)


def render_problem_section(title, entries, render_line):
    if not entries:
        return []
    lines = ['', f'=== {title} ({len(entries)}) ===']
    for entry in entries:
        lines.append(render_line(entry))
    return lines


def format_number(number):
    return f' #{number}' if number else ''


def render_not_found(entry):
    return (
        f"  {entry['name']} ({entry['set']}){format_number(entry['number'])} [{entry['condition']}] "
        f"x{entry['quantity']} -- no card with this name found in box"
    )


def render_needs_review(entry):
    candidates = ', '.join(f'{code}: {count} in box' for code, count in entry['candidates'].items())
    return (
        f"  {entry['name']} ({entry['set']}){format_number(entry['number'])} [{entry['condition']}] "
        f"x{entry['quantity']} -- {entry['reason']} [{candidates}]"
    )


def _autosize_columns(ws):
    for col_cells in ws.columns:
        length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(length + 2, 10), 60)
    ws.freeze_panes = 'A2'


def _header(ws, columns):
    ws.append(columns)
    for cell in ws[1]:
        cell.font = Font(bold=True)


def write_workbook(picks, not_found, needs_review, set_mismatches, box_code, out_path):
    wb = Workbook()

    ws_picks = wb.active
    ws_picks.title = 'Pick List'
    _header(ws_picks, ['Box', 'SubBox', 'Card Name', 'Set', 'Number', 'Condition', 'Condition Source', 'Foil', 'Ordered As', 'Match Method', 'Verify By Hand', 'pkCard'])
    grouped = defaultdict(list)
    for pick in picks:
        grouped[pick['container']].append(pick)
    for container in sorted(grouped.keys(), key=container_sort_key):
        rows = sorted(grouped[container], key=lambda r: r['cardName'].lower())
        for row in rows:
            ws_picks.append([
                box_code,
                container if container is not None else 'Main',
                row['cardName'],
                row['set'],
                row['number'],
                row['cardGrade'],
                row['conditionSource'],
                'Yes' if row['isFoil'] else '',
                '' if row['orderedName'].lower() == row['cardName'].lower() else row['orderedName'],
                row['setMatchMethod'],
                'YES' if row['setMatchMethod'].startswith('LOW CONFIDENCE') else '',
                row['pkCard'],
            ])

    ws_not_found = wb.create_sheet('Not Found In Box')
    _header(ws_not_found, ['Ordered Name', 'Ordered Set', 'Number', 'Condition', 'Quantity', 'Note'])
    for entry in not_found:
        ws_not_found.append([entry['name'], entry['set'], entry['number'], entry['condition'], entry['quantity'], 'No card with this name found in box'])

    ws_review = wb.create_sheet('Needs Review')
    _header(ws_review, ['Ordered Name', 'Ordered Set', 'Number', 'Condition', 'Quantity', 'Reason', 'What The Box Has'])
    for entry in needs_review:
        candidates = ', '.join(f'{code}: {count}' for code, count in entry['candidates'].items())
        ws_review.append([entry['name'], entry['set'], entry['number'], entry['condition'], entry['quantity'], entry['reason'], candidates])

    ws_sets = wb.create_sheet('Set Name Non-Matches')
    _header(ws_sets, ['Pull Sheet Set Name', 'Closest Set Library Match', 'Closest Match Set Code', 'Match Score', 'Add To tbl_MTGSetLibrary?'])
    for m in sorted(set_mismatches, key=lambda m: m['pullSheetSetName'].lower()):
        ws_sets.append([
            m['pullSheetSetName'],
            m['bestGuessName'] or '(no close match found)',
            m['bestGuessCode'] or '',
            round(m['bestGuessScore'], 2) if m['bestGuessName'] else '',
            '',
        ])

    for ws in (ws_picks, ws_not_found, ws_review, ws_sets):
        _autosize_columns(ws)

    wb.save(out_path)


# ---------------------------------------------------------------------------
# Orchestration (shared by the CLI and the GUI)
# ---------------------------------------------------------------------------

def process_pull_sheet(pull_sheet_path, box_code=DEFAULT_BOX_CODE, progress_cb=None):
    '''
    Runs the full pipeline for one pull sheet and writes "<name>_PickList.xlsx" next
    to it. Returns a summary dict. progress_cb, if given, is called with short status
    strings as the work proceeds (used by the GUI to show what's happening).
    '''
    def report(msg):
        if progress_cb:
            progress_cb(msg)

    report('Reading pull sheet...')
    pull_sheet_rows = load_pull_sheet(pull_sheet_path)
    if not pull_sheet_rows:
        raise ValueError('No Magic rows found in the pull sheet.')

    report('Connecting to database...')
    conn = get_connection()
    try:
        report(f'Loading box {box_code} inventory...')
        by_name = load_box_inventory(conn, box_code)
        report('Loading set library...')
        code_to_name, name_to_codes = load_set_library(conn)
    finally:
        conn.close()

    report('Matching cards...')
    picks, not_found, needs_review = match_pull_sheet(pull_sheet_rows, by_name, code_to_name, name_to_codes)
    set_mismatches = collect_set_name_mismatches(pull_sheet_rows, code_to_name, name_to_codes)

    out_path = os.path.splitext(pull_sheet_path)[0] + '_PickList.xlsx'
    report('Writing workbook...')
    write_workbook(picks, not_found, needs_review, set_mismatches, box_code, out_path)

    report('Done.')
    return {
        'pull_sheet_path': pull_sheet_path,
        'box_code': box_code,
        'total_ordered': sum(e['quantity'] for e in pull_sheet_rows),
        'matched_count': len(picks),
        'not_found_count': len(not_found),
        'needs_review_count': len(needs_review),
        'set_mismatch_count': len(set_mismatches),
        'output_path': out_path,
        'not_found': not_found,
        'needs_review': needs_review,
    }


# ---------------------------------------------------------------------------
# Main (CLI)
# ---------------------------------------------------------------------------

def main():
    args = sys.argv[1:]
    box_code = DEFAULT_BOX_CODE
    if '--box' in args:
        idx = args.index('--box')
        box_code = int(args[idx + 1])
        del args[idx:idx + 2]

    if args:
        pull_sheet_path = args[0]
    else:
        pull_sheet_path = find_default_pull_sheet()
        if not pull_sheet_path:
            print('No pull sheet CSV given and none found automatically. '
                  'Usage: python pullSheetPicker.py <path-to-pull-sheet.csv> [--box 10001]')
            sys.exit(1)
        print(f'No path given, using most recent pull sheet found: {pull_sheet_path}')

    summary = process_pull_sheet(pull_sheet_path, box_code, progress_cb=print)

    print()
    print(f"Cards ordered (all lines): {summary['total_ordered']}")
    print(f"Cards matched and ready to pull: {summary['matched_count']}")
    print(f"Order lines not found in box {box_code}: {summary['not_found_count']}")
    print(f"Order lines needing manual review: {summary['needs_review_count']}")
    print(f"TCGplayer set names with no exact match in your set library: {summary['set_mismatch_count']}")
    print('\n'.join(render_problem_section('NOT FOUND IN BOX', summary['not_found'], render_not_found)))
    print('\n'.join(render_problem_section('NEEDS MANUAL REVIEW', summary['needs_review'], render_needs_review)))
    print(f"\nFull pick list and details written to: {summary['output_path']}")


if __name__ == '__main__':
    main()
