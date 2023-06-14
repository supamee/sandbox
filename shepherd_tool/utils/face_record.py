import json
import numpy as np

from utils import StorageError, row_to_array, count_row
from utils import array_to_dict, dict_to_array
from utils import base64_encode, base64_decode
from record import Record


__all__ = ["FaceRecord"]


class FaceRecord(Record):
    """
    Defines a face embedding.
    """

    ID_TYPE = "fac"

    def __init__(self, face_id=None):
        self.face_id = face_id or self.rec_id()
        self.embedding = None
        self.image = None
        self.attr = dict()

    def __lt__(self, other):
        return self.face_id < other.face_id

    def to_json(self):
        return {
            "face_id": self.face_id,
            "embedding": array_to_dict(self.embedding) if self.embedding is not None else None,
            "image": base64_encode(self.image) if self.image is not None else None,
            "attr": self.attr,
        }


class MessageFaceRecord:
    def __init__(self, face_record: FaceRecord, **kwargs):
        self.face_record = face_record
        self.kwargs = kwargs

    def __lt__(self, other):
        return self.face_record.face_id < other.face_record.face_id

    def to_json(self):
        msg = self.face_record.to_json()
        msg.update(self.kwargs)
        return msg


def build_face_record(obj):
    face = FaceRecord(face_id=obj.get("face_id"))
    face.embedding = dict_to_array(obj.get("embedding"))
    face.image = base64_decode(obj.get("image"))
    face.attr = obj.get("attr")
    return face


def create_table_face(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS face (
        id TEXT PRIMARY KEY,
        embedding_data BLOB NOT NULL,
        embedding_shape TEXT NOT NULL,
        embedding_dtype TEXT NOT NULL,
        image BLOB NOT NULL,
        attr TEXT NOT NULL
        )"""
    )


def insert_face(conn, face):
    if face.embedding is None:
        raise StorageError("face embedding must be defined")
    if not isinstance(face.embedding, np.ndarray):
        raise StorageError("face embedding must be an ndarray")
    conn.execute(
        """
        INSERT OR REPLACE INTO face
        (id,
        embedding_data, embedding_shape, embedding_dtype,
        image, attr)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            face.face_id,
            face.embedding,
            str(face.embedding.shape),
            str(face.embedding.dtype),
            face.image,
            json.dumps(face.attr),
        ),
    )


def select_face(conn, face_id, *, include_image):
    cursor = conn.cursor()
    image_col = "image" if include_image else "NULL"
    cursor.execute(
        f"""
        SELECT embedding_data, embedding_shape, embedding_dtype,
        {image_col}, attr
        FROM face WHERE id = ?""",
        (face_id,),
    )
    row = cursor.fetchone()
    if row is not None:
        face = FaceRecord(face_id)
        face.embedding = row_to_array(*row[0:3])
        face.image = row[3]
        face.attr = json.loads(row[4])
        return face
    else:
        return None


def select_all_faces(conn, *, include_image):
    cursor = conn.cursor()
    image_col = "image" if include_image else "NULL"
    cursor.execute(
        f"""
        SELECT embedding_data, embedding_shape, embedding_dtype,
        {image_col}, attr, id
        FROM face"""
    )
    faces = list()
    row = cursor.fetchone()
    while row:
        face = FaceRecord(row[5])
        face.embedding = row_to_array(*row[0:3])
        face.image = row[3]
        face.attr = json.loads(row[4])
        faces.append(face)
        row = cursor.fetchone()
    return faces


def delete_face(conn, face_id):
    conn.execute(
        """
        DELETE FROM face WHERE id = ?""",
        (face_id,),
    )


def count_face(conn):
    return count_row(conn, "face")
