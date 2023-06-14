import numpy as np
import logging
from typing import Type, Union, List
from operator import itemgetter
from uuid import uuid4
from collections import Counter

# from foundation.pasture.common.track_record import TrackRecord

from cluster import ChineseWhispers
from entity import Entity
from face import SleepyFace
# from shepherd.farm.utils import timelines_overlap
from farm_utils import create_cloud

__all__ = ["SleepyTrack"]


class SleepyTrack(Entity):
    """
    Represents a track created in the
    device context on the Shepherd side.
   
    Parameters:
    -----------
    track_id: str
        uuid of track object
    sentry: str
        The sentry device the track
        derives from.
    start_timestamp: float
    end_timestamp: float
    embeddings: np.ndarray
        Collection of face embeddings
        that represented the track in
        the device context.
    known_identities: list
        Set of iids that were matched
        against in the device context
        if any.
    r_wifis: list
        A sorted list of most probable
        wifi assignment to least probable
        wifi assignment. This list will be
        empty until the association step
        occurs.
    """

    def __init__(
        self,
        track_id: str,
        sentry: str,
        start_timestamp: float,
        end_timestamp: float,
        embeddings: np.ndarray,
        known_identities: list,
        derived_from_faces: bool = False,
        faces: list = [],
        **kwargs,
    ):
        super().__init__(sentry)
        self.track_id = self.wrap_id(track_id)
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.embeddings = embeddings
        self.known_identities = known_identities
        self.cloud = create_cloud(embeddings)
        self.r_wifis = []

    def __repr__(self):
        return f"{'(id: ' + self.track_id + ' -> '  + 'sentry: ' + self.sentry + ' -> ' + 'time: ' + str(self.rounded_start_timestamp) + '|' + str(self.rounded_end_timestamp) + ')'}"

    def __lt__(self, other: Type["SleepyTrack"]):
        return self.start_timestamp < other.start_timestamp

    def __eq__(self, other: Type["SleepyTrack"]):
        return self.track_id == other.track_id

    @property
    def rounded_start_timestamp(self):
        return int(self.start_timestamp)

    @property
    def rounded_end_timestamp(self):
        return int(self.end_timestamp)

    # @property
    # def cloud(self):
    #     return self._cloud

    # @cloud.setter
    # def cloud(self):
    #     n = len(self.embeddings)
    #     if n == 0:
    #         self._cloud = None
    #     if isinstance(self.embeddings, list):
    #         self.embeddings = np.ndarray(self.embeddings)
    #     self.embeddings = self.embeddings.reshape(n, -1)
    #     cloud = create_cloud(self.embeddings)
    #     self._cloud = cloud

    @classmethod
    def build_from_record(cls, record):
        return cls(**record.from_json())

    def do_timelines_overlap(self, other: Type["SleepyTrack"]) -> bool:
        """
        Compute whether the track timelines overlap

        Parameters:
        -----------
        other: SleepyTrack
            Another SleepyTrack to compare clouds against

        Returns:
        -------
        bool

        """
        return timelines_overlap(
            self.start_timestamp,
            self.end_timestamp,
            other.start_timestamp,
            other.end_timestamp,
        )

    def get_cloud_similarity(self, other: Type["SleepyTrack"]) -> float:
        """
        Compute the similarity in cloud embedding structures. 
        Similarity values closer to 1 represent highly
        similiar objects.

        Parameters:
        -----------
        other: SleepyTrack
            Another SleepyTrack to compare clouds against

        Returns:
        -------
        sim: float
            Similiarity between embedding clouds

        """
        if self.cloud is None or other.cloud is None:
            return 0.0
        if len(self.embeddings) < len(other.embeddings):
            sim = other.cloud.multi_query(self.cloud.reductor.embeddings)
        else:
            sim = self.cloud.multi_query(other.cloud.reductor.embeddings)
        return sim

    def which_identities_overlap(
        self, other: Type["SleepyTrack"]
    ) -> Union[bool, List[str]]:
        """
        Compute the intersection of known identities.

        Parameters:
        -----------
        other: SleepyTrack
            Another SleepyTrack to compare known
            identities against

        Returns:
        -------
        [bool, set]

        """
        common_iids = set(self.known_identities) & set(other.known_identities)
        return (True, common_iids) if len(common_iids) > 0 else (False, common_iids)


def build_tracks_from_faces(
    faces: List[Type[SleepyFace]],
    cw_iterations: int = 5,
    cw_threshold: float = 0.79,
    minimum_cluster_size: int = 2,
    minimum_track_time: float = 3.0,
    append_face_object: bool = False,
    return_intermediate: bool = False,
) -> List[Type[SleepyTrack]]:
    """
    Build SleepyTracks from SleepyFaces. When devices are run
    in passive mode only Faces are collected. Using the time
    and embedding attributes of each SleepyFace create psuedo
    tracks using the ChineseWhispers algorithm. Clusters
    that are formed with size greater than minimum_cluster_size
    become track candidates.

    Parameters:
    -----------


    Returns:
    -------

    """
    if len(faces) == 0:
        return {} if return_intermediate else []
    else:
        sentry = faces[0].sentry
        logging.info(f"building tracks from faces for sentry: {sentry}")
    cw = ChineseWhispers(iterations=cw_iterations, threshold=cw_threshold)
    sentry_device_embeddings = []
    for f in faces:
        sentry_device_embeddings.append(f.embedding)
    batch_face_embeddings = np.stack(sentry_device_embeddings, axis=1).squeeze(0)
    cluster_ids = cw.fit_predict(batch_face_embeddings)
    cluster_id_counts = Counter(cluster_ids)
    t = {}
    for i, ci in enumerate(cluster_ids):
        if cluster_id_counts[ci] >= minimum_cluster_size:
            if ci not in t:
                t[ci] = []
            if append_face_object:
                t[ci].append(faces[i])
            else:
                t[ci].append(
                    [
                        faces[i].face_id,
                        faces[i].timestamp,
                        faces[i].embedding,
                        faces[i].known_identity,
                    ]
                )
    if return_intermediate:
        return t
    for v in t.values():
        sv = sorted(v, key=itemgetter(1), reverse=False)
        start, end = int(sv[0][1]), int(sv[-1][1])
        if end - start > minimum_track_time:
            embeddings = np.stack([i[2] for i in v], axis=1).squeeze(0)
            st = SleepyTrack(
                track_id=str(uuid4()),
                sentry=sentry,
                start_timestamp=start,
                end_timestamp=end,
                embeddings=embeddings,
                known_identities=[i[3] for i in v],
                derived_from_faces=True,
                faces=[i[0] for i in v],
            )
            tracks.append(st)
    return tracks
