import sqlite3, os
path = os.path.join('backend', 'fde_fallback.db')
print('exists', os.path.exists(path))
con = sqlite3.connect(path)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
print('tables', cur.fetchall())
for tbl in ['orders','deliveries','invoices','payments','order_items','products']:
    try:
        cur.execute(f'SELECT count(*) FROM {tbl}')
        print(tbl, cur.fetchone()[0])
    except Exception as e:
        print(tbl, 'ERROR', e)
con.close()
