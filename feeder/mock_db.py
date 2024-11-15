import sqlite3
conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL
    )
''')
sample_data = [(100.0,), (200.5,), (300.75,)]
cursor.executemany('INSERT INTO transactions (amount) VALUES (?)', sample_data)

conn.commit()
conn.close()