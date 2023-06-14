import numpy as np
from typing import Type

# from foundation.pasture.common.face_record import FaceRecord
# from foundation.utils.dists import cosine_distance
from entity import Entity

__all__ = ["SleepyFace"]

class SleepyFace(Entity):
    """

    Parameters:
    -----------

    """

    def __init__(
        self,
        face_id: str,
        sentry: str,
        timestamp: float,
        embedding: np.ndarray,
        known_identity: str,
        **kwargs,
    ):
        super().__init__(sentry)
        self.face_id = self.wrap_id(face_id)
        self.timestamp = timestamp
        self.embedding = embedding
        self.known_identity = known_identity

    def __repr__(self):
        return f"{'(id: ' + self.face_id + ' -> '  + 'sentry: ' + self.sentry + ' -> ' + 'time: ' + str(int(self.timestamp)) + ')'}"

    def __lt__(self, other: Type["SleepyFace"]):
        return self.timestamp < other.timestamp

    def __eq__(self, other: Type["SleepyFace"]):
        return self.face_id == self.face_id

    @classmethod
    def build_from_record(cls, record):
        return cls(**record.from_json())

    # def get_embedding_similarity(self, other: Type["SleepyFace"]) -> float:
    #     """
    #     Compute the similarity in face embeddings.

    #     Parameters:
    #     -----------
    #     other: SleepyFace
    #         Another SleepyFace to compare clouds against

    #     Returns:
    #     -------
    #     sim: float
    #         Similiarity between embedding clouds

    #     """
    #     return cosine_distance(self.embedding, other.embedding)
