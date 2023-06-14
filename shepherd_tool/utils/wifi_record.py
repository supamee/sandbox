import json
import time

from utils import (
    count_row,
    RECORD_NOT_SENT,
    RECORD_SENT,
    RECORD_SENT_NOT_FINISHED,
)
from record import Record


class WifiRecord(Record):
    """
    Defines a wifi capture
    """

    ID_TYPE = "rad"

    def __init__(
        self,
        wifi_id: str,
        address: str = None,
        sentry: str = None,
        start_timestamp: float = None,
        end_timestamp: float = None,
        antenna: list = list(),
        attr: dict = dict(),
        **kwargs,
    ):
        self.wifi_id = wifi_id
        self.address = address
        self.sentry = sentry
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.antenna = antenna
        self.attr = attr

    def __lt__(self, other):
        return self.start_timestamp < other.start_timestamp

    def to_json(self):
        return {
            "wifi_id": self.wifi_id,
            "address": self.address,
            "sentry": self.sentry,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "antenna": self.antenna,
            "attr": self.attr,
        }

    def from_json(self):
        return {
            "wifi_id": self.wifi_id,
            "address": self.address,
            "sentry": self.sentry,
            "start_timestamp": self.start_timestamp,
            "end_timestamp": self.end_timestamp,
            "antenna": self.antenna,
            "attr": self.attr,
        }


def create_table_wifi(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS wifis (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        wifi_id TEXT NOT NULL,
        address TEXT,
        sentry TEXT, 
        start_timestamp REAL, 
        end_timestamp REAL, 
        RF1 REAL, 
        RF2 REAL,
        INFO TEXT,
        sent INTEGER NOT NULL)"""
    )


def insert_wifi(conn, collect):
    conn.execute(
        """
        INSERT INTO wifis
        (wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, INFO, sent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            collect.wifi_id,
            collect.address,
            collect.sentry,
            collect.start_timestamp,
            collect.end_timestamp,
            collect.antenna[0],
            collect.antenna[1],
            json.dumps(collect.attr),
            RECORD_NOT_SENT,
        ),
    )


def insert_wifis(conn, collects):
    for collect in collects:
        insert_wifi(conn, collect)


def row_to_wifi(rows):
    wifis = []
    if not isinstance(rows, list):
        rows = [rows]
    for row in rows:
        if row is not None and len(row) == 9:
            wifi = WifiRecord(wifi_id=row[0])
            wifi.address = row[1]
            wifi.sentry = row[2]
            wifi.start_timestamp = row[3]
            wifi.end_timestamp = row[4]
            wifi.antenna = [row[5], row[6]]
            wifi.attr = json.loads(row[7])
            wifis.append(wifi)
    return wifis


def select_wifi_by_wifi_id(conn, wifi_id):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        WHERE wifi_id = ?""",
        (wifi_id,),
    )
    return row_to_wifi(cursor.fetchone())


def select_wifi_by_sentry(conn, sentry):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        WHERE sentry = ?""",
        (sentry,),
    )
    return row_to_wifi(cursor.fetchall())


def select_wifi_by_address(conn, address):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        WHERE address = ?""",
        (address,),
    )
    return row_to_wifi(cursor.fetchall())


def select_all_wifis(conn):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        """
    )
    wifis = list()
    row = cursor.fetchone()
    while row:
        wifi = row_to_wifi(row)
        if wifi is not None:
            wifis.append(wifi)
        row = cursor.fetchone()
    return wifis


def select_wifi_in_time_window(conn, mac, start, end):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis
        WHERE address = ? AND start_timestamp >= ? AND end_timestamp <= ?""",
        (mac, start, end),
    )
    return row_to_wifi(cursor.fetchall())


def select_next_wifi(conn):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
        FROM wifis 
        WHERE sent = ?
        ORDER BY start_timestamp ASC
        LIMIT 1""",
        (RECORD_NOT_SENT,),
    )
    wifi_record_not_sent = row_to_wifi(cursor.fetchone())
    if len(wifi_record_not_sent) == 0:
        cursor.execute(
            f"""
            SELECT wifi_id, address, sentry, start_timestamp, end_timestamp, RF1, RF2, info, sent
            FROM wifis 
            WHERE sent = ?
            ORDER BY start_timestamp ASC
            LIMIT 1""",
            (RECORD_SENT_NOT_FINISHED,),
        )
        wifi_record_sent_not_finished = row_to_wifi(cursor.fetchone())
        if len(wifi_record_sent_not_finished) == 0:
            return []
        else:
            return wifi_record_sent_not_finished
    else:
        return wifi_record_not_sent


def update_wifi_end_time(conn, mac, front_strength, back_strength):
    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE wifis 
        SET end_timestamp = ?,
            RF1 = ?,
            RF2 = ?
        WHERE id = (
            SELECT id 
            FROM wifis 
            WHERE address = ? 
            ORDER BY start_timestamp DESC 
            LIMIT 1)
        """,
        (time.time(), front_strength, back_strength, mac),
    )


def update_wifi_sent_status(conn, id):
    cursor = conn.cursor()
    wr = select_wifi_by_wifi_id(conn, id)[0]
    status = RECORD_SENT if wr.end_timestamp != None else RECORD_SENT_NOT_FINISHED
    cursor.execute(
        f"""
        UPDATE wifis
        SET sent = ?
        WHERE wifi_id = ?""",
        (status, id),
    )


def delete_wifi(conn, wifi):
    conn.execute(
        """
        DELETE FROM wifis WHERE id = ?""",
        (wifi,),
    )


def count_wifi(conn):
    return count_row(conn, "wifis")
