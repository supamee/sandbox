import json
import sqlite3
import base58
import base64
import os
import io
import ast
import numpy as np
import PIL.Image

RECORD_NOT_SENT = 0
RECORD_SENT = 1
RECORD_SENT_NOT_FINISHED = 2


def adapt_list_to_JSON(lst):
    if isinstance(lst, np.ndarray):
        lst = lst.tolist()
    return json.dumps(lst).encode("utf8")


def convert_JSON_to_list(data):
    return json.loads(data.decode("utf8"))


sqlite3.register_adapter(list, adapt_list_to_JSON)
sqlite3.register_converter("json", convert_JSON_to_list)


def array_to_dict(x: np.ndarray) -> dict:
    return dict(data=base64_encode(x), dtype=str(x.dtype), shape=list(x.shape))


def dict_to_array(x: dict) -> np.ndarray:
    a = np.frombuffer(base64_decode(x["data"]), dtype=x["dtype"])
    a = a.reshape(x["shape"])
    return a


class StorageError(Exception):
    """
    Raised for storage errors.
    """

    pass


def new_id(name=None):
    """
    Generate a DB suitable object id to be used as a key.
    This is similar to what Stripe uses.
    """
    a = base58.b58encode(os.urandom(18)).decode("utf-8")
    return a if name is None else name + "_" + a


def row_to_array(data, shape, dtype):
    """
    Converts row fields to an array.
    """
    s = ast.literal_eval(shape)
    d = np.dtype(dtype)
    return np.frombuffer(data, d).reshape(s)


def count_row(conn, table):
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(rowid) FROM {table}")
    row = cursor.fetchone()
    return row[0]


def base64_encode(data):
    """
    Return a base64 encoded string.
    """
    return base64.b64encode(data).decode("ascii")


def base64_decode(data):
    """
    Returns base64 decoded bytes.
    """
    return base64.b64decode(data)


def image_encode(image):
    """
    Converts a PIL or numpy image to JPEG.
    """
    if isinstance(image, np.ndarray):
        image = PIL.Image.fromarray(image)
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return buf.getvalue()


def image_decode(image):
    """
    Converts a JPEG image to a PIL image.
    """
    return PIL.Image.open(io.BytesIO(image))

