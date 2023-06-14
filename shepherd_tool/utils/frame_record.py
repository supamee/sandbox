import json

from utils import count_row
from record import Record

class FrameRecord(Record):
    """
    Defines a video frame.
    """

    ID_TYPE = "frm"

    def __init__(self, frame_id=None):
        self.frame_id = frame_id or self.rec_id()
        self.image = None
        self.timestamp = None
        self.radio = dict()
        self.sentry = dict()


def create_table_frame(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS frame (
        id TEXT PRIMARY KEY,
        timestamp REAL NOT NULL,
        image BLOB NOT NULL,
        radio TEXT,
        sentry TEXT
        )"""
    )


def insert_frame(conn, frame):
    conn.execute(
        """
        INSERT INTO frame
        (id, timestamp, image, radio, sentry)
        VALUES (?, ?, ?, ?, ?)""",
        (
            frame.frame_id,
            frame.timestamp,
            frame.image,
            json.dumps(frame.radio),
            json.dumps(frame.sentry),
        ),
    )


def row_to_frame(row):
    if row is not None and len(row) == 5:
        frame = FrameRecord(row[0])
        frame.timestamp = row[1]
        frame.image = row[2]
        frame.radio = json.loads(row[3])
        frame.sentry = json.loads(row[4])
        return frame
    else:
        return None


def select_frame(conn, frame_id, *, include_image):
    cursor = conn.cursor()
    image_col = "image" if include_image else "NULL"
    cursor.execute(
        f"""
        SELECT id, timestamp, {image_col}, radio, sentry
        FROM frame WHERE id = ?""",
        (frame_id,),
    )
    return row_to_frame(cursor.fetchone())


def select_frame_latest(conn, *, include_image):
    cursor = conn.cursor()
    image_col = "image" if include_image else "NULL"
    cursor.execute(
        f"""
        SELECT id, timestamp, {image_col}, radio, sentry
        FROM frame ORDER BY timestamp DESC LIMIT 1"""
    )
    return row_to_frame(cursor.fetchone())


def select_all_frames(conn, *, include_image):
    cursor = conn.cursor()
    image_col = "image" if include_image else "NULL"
    cursor.execute(
        f"""
        SELECT id, timestamp, {image_col}, radio, sentry
        FROM frame ORDER BY timestamp ASC"""
    )
    frames = list()
    row = cursor.fetchone()
    while row:
        frame = row_to_frame(row)
        if frame is not None:
            frames.append(frame)
        row = cursor.fetchone()
    return frames


def delete_frame(conn, frame_id):
    conn.execute(
        """
        DELETE FROM frame WHERE id = ?""",
        (frame_id,),
    )


def count_frame(conn):
    return count_row(conn, "frame")
