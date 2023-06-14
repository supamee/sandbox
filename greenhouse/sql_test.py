import sqlite3
import time

conn = sqlite3.connect("file::memory:?cache=shared")


conn.execute(
        """
        CREATE TABLE IF NOT EXISTS temp (
        timestamp REAL, 
        temp REAL
        )"""
    )
conn.execute(
    """
    INSERT INTO temp
    (timestamp, temp)
    VALUES (?, ?)""",
    (
        time.time(),
        6.8,
    ),
)
cursor = conn.cursor()
cursor.execute(
        """
        SELECT MAX(timestamp), temp
        FROM temp 
        """,
    )
print(cursor.fetchall())
