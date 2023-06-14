from store import Store
from frame_record import (
    create_table_frame,
    insert_frame,
    select_frame,
    select_all_frames,
    select_frame_latest,
    delete_frame,
    count_frame,
)
from face_record import (
    create_table_face,
    insert_face,
    select_all_faces,
    select_face,
    delete_face,
    count_face,
)


class DetectionStore(Store):
    def __init__(self):
        super().__init__()

    def open(self, path=None):
        super().open(path)
        with self.connection:
            # create_table_detection(self.connection)
            create_table_frame(self.connection)
            create_table_face(self.connection)
            # create_table_face_frame(self.connection)
            # create_table_device(self.connection)
            # create_table_match(self.connection)
        return self

    def write_detection(self, detection):
        with self.connection:
            insert_detection(self.connection, detection)

    def write_frame(self, frame):
        with self.connection:
            insert_frame(self.connection, frame)

    def write_face(self, face):
        with self.connection:
            insert_face(self.connection, face)

    def write_face_frame(self, face_frame):
        with self.connection:
            insert_face_frame(self.connection, face_frame)

    def write_device(self, device):
        with self.connection:
            insert_device(self.connection, device)

    def write_match(self, match):
        with self.connection:
            insert_match(self.connection, match)

    def read_detection(self, detection_id=None):
        with self.connection:
            if detection_id is not None:
                return select_detection(self.connection, detection_id)
            # No id specified so attempt to return first record
            for d in select_all_detections(self.connection):
                return d
            return None

    def read_all_detections(self):
        with self.connection:
            return select_all_detections(self.connection)

    def read_frame(self, frame_id, include_image=False):
        with self.connection:
            return select_frame(self.connection, frame_id, include_image=include_image)

    def read_frame_latest(self, include_image=False):
        with self.connection:
            return select_frame_latest(self.connection, include_image=include_image)

    def read_all_frames(self, include_image=False):
        with self.connection:
            return select_all_frames(self.connection, include_image=include_image)

    def read_face(self, face_id, include_image=False):
        with self.connection:
            return select_face(self.connection, face_id, include_image=include_image)

    def read_all_faces(self, include_image=False):
        with self.connection:
            return select_all_faces(self.connection, include_image=include_image)

    def read_face_frames(self, face_id):
        with self.connection:
            return select_face_frames_for_face(self.connection, face_id)

    def read_device(self, device_id):
        with self.connection:
            return select_device(self.connection, device_id)

    def read_all_devices(self):
        with self.connection:
            return select_all_devices(self.connection)

    def read_match(self, match_id):
        with self.connection:
            return select_match(self.connection, match_id)

    def read_all_matches(self):
        with self.connection:
            return select_all_matches(self.connection)

    def drop_detection(self, detection_id):
        with self.connection:
            delete_detection(self.connection, detection_id)

    def drop_frame(self, frame_id):
        with self.connection:
            delete_frame(self.connection, frame_id)

    def drop_face(self, face_id):
        with self.connection:
            delete_face(self.connection, face_id)

    def drop_face_frame(self, face_id, frame_id):
        with self.connection:
            delete_face_frame(self.connection, face_id, frame_id)

    def drop_device(self, device_id):
        with self.connection:
            delete_device(self.connection, device_id)

    def drop_match(self, match_id):
        with self.connection:
            delete_match(self.connection, match_id)

    def count_detection(self):
        with self.connection:
            return count_detection(self.connection)

    def count_frame(self):
        with self.connection:
            return count_frame(self.connection)

    def count_face(self):
        with self.connection:
            return count_face(self.connection)

    def count_face_frame(self):
        with self.connection:
            return count_face_frame(self.connection)

    def count_match(self):
        with self.connection:
            return count_match(self.connection)

    def count_device(self):
        with self.connection:
            return count_device(self.connection)
