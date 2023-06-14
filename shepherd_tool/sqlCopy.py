# from Ayman
import sqlite3
import sys

def open_db(nam):
    conn = sqlite3.connect(nam)
    # Let rows returned be of dict/tuple type
    conn.row_factory = sqlite3.Row
    print ("Openned database %s as %r" % (nam, conn))
    return conn

def copy_table(table, src, dest):
    print("Copying %s %s => %s" % (table, src, dest))
    sc = src.execute('SELECT * FROM %s' % table)
    ins = None
    dc = dest.cursor()
    for row in sc.fetchall():
        if not ins:
            cols = tuple([k for k in row.keys() if k != 'id'])
            ins = 'INSERT OR REPLACE INTO %s %s VALUES (%s)' % (table, cols,
                                                     ','.join(['?'] * len(cols)))
            print('INSERT stmt = ' + ins)
        c = [row[c] for c in cols]
        print("C",c)
        dc.execute(ins, c)

    dest.commit()
src_conn  = open_db('collect.db')
dest_conn = open_db('wifi.db')
# src_conn  = 'folder/20201113-1041/20201113-104130-415760'
# dest_conn = 'temp.db'

# dest_conn.execute(
#     """
#     CREATE TABLE IF NOT EXISTS detection (
#     id TEXT PRIMARY KEY,
#     frame_id TEXT NOT NULL,
#     frame_timestamp REAL NOT NULL,
#     attr TEXT
#     )"""
# )
dest_conn.execute(
    """
    CREATE TABLE IF NOT EXISTS wifis (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    wid TEXT NOT NULL,
    address TEXT,
    sentry TEXT, 
    start_timestamp REAL, 
    end_timestamp REAL, 
    RF1 REAL, 
    RF2 REAL,
    INFO TEXT,
    sent INTEGER NOT NULL)"""
)



# cursor = dest_conn.cursor() 
# cursor.execute(
#         f"""
#         pragma table_info(wifis)
#         """
#     )

# test=cursor.fetchall()
# table_format=[i[1] for i in test]
# import pdb
# pdb.set_trace()
copy_table('wifis', src_conn, dest_conn)
