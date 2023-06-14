import numpy as np
import logging
from collections import Counter
from uuid import uuid4
from typing import Type, List

from embedding import SparseEmbeddingCloud


def timelines_overlap(a_s: int, a_e: int, b_s: int, b_e: int) -> bool:
    """
    First overlapping condition:
        D1, {T1, M1}:
            4______________11
        D2, {T1, M1}:
                5______________12
    Second overlapping condition:
        D1, {T1, M1}:
            3________________12
        D2, {T1, M1}
            4______________11

    To simplify the overlapping conditions,
    if the second timeline starts before
    the first timelines start flip the assignment
    of timelines.

    Parameters:
    -----------
    a_s: int
    a_e: int
    b_s: int
    b_e: int

    Returns:
    -------
    bool:
        Whether A's timeline overlaps with B's

    """
    if b_s < a_s:
        a_s, a_e, b_s, b_e = b_s, b_e, a_s, a_e
    if (a_e > b_s and b_e >= a_e) or (b_e >= a_s and b_e <= a_e):
        return True
    return False

def create_cloud(
    embeddings: np.ndarray,
    dim: int = 512,
    entity_type: str = "face",
    representative_method: str = "volume",
    pca_dim: int = 15,
    **kwargs,
) -> Type[SparseEmbeddingCloud]:
    """
    Rebuild the cloud representation of faces within
    the track context. Only embeddings that comprise the
    cloud in the device context are sent over the network
    so the cloud in the shepherd context should match 1-1.

    Parameters:
    -----------
    embeddings: np.ndarray
        Set of embeddings to create the
        SparseEmbeddingCloud from.
    dim: int
        Dimension of an individual embedding
        i.e. (1, dim).

    Returns:
    -------
    cloud: SparseEmbeddingCloud

    """
    cloud = SparseEmbeddingCloud(
        ambient_dim=dim,
        entity_type="face",
        representative_method="volume",
        pca_dim=15,
        **kwargs,
    )
    for emb in embeddings:
        cloud.add_vector(emb)
    return cloud
