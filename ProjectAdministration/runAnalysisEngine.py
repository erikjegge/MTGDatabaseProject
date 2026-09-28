'''
    Runs the box lot code update followed by the analysis engine, one after the other:

        exec sp_updateBoxLotCodes
        exec [dbo].[sp_AnalysisEngine]

    sp_AnalysisEngine is long-running, so the query timeout is disabled (0 = wait
    forever). Each proc's result sets / row-count messages are drained with nextset()
    so Python waits for the proc to actually finish before moving on -- otherwise
    pyodbc can return early after the first statement inside the proc.

    Usage:
        python runAnalysisEngine.py
'''
import time

import pyodbc
from decouple import config

SERVER = config('SERVER')
DATABASE = config('DATABASE')
DB_USERNAME = config('DB_USERNAME')
DB_PASSWORD = config('DB_PASSWORD')
DRIVER = '{ODBC Driver 17 for SQL Server}'

PROCS = [
    'exec sp_updateBoxLotCodes',
    'exec [dbo].[sp_AnalysisEngine]',
]


def run_proc(conn, sql):
    print(f'Running: {sql}', flush=True)
    start = time.time()
    cursor = conn.cursor()
    cursor.execute(sql)
    # Drain every result set so we block until the proc is fully done.
    while cursor.nextset():
        pass
    cursor.close()
    print(f'  Finished in {time.time() - start:,.1f}s', flush=True)


def main():
    conn = pyodbc.connect(
        'DRIVER=' + DRIVER + ';SERVER=' + SERVER + ';PORT=1433;DATABASE=' + DATABASE
        + ';UID=' + DB_USERNAME + ';PWD=' + DB_PASSWORD,
        autocommit=True,
        timeout=30,  # login timeout only
    )
    conn.timeout = 0  # query timeout: 0 = no limit
    try:
        for sql in PROCS:
            run_proc(conn, sql)
    finally:
        conn.close()
    print('All done.')


if __name__ == '__main__':
    main()
