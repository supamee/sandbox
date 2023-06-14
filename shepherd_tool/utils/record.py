from abc import ABC

from utils import new_id

class Record(ABC):
    """
    Base class for record.
    """

    def rec_id(self):
        """
        Creates a new record ID.
        """
        return new_id(self.ID_TYPE)

    ID_TYPE = "rec"

    @classmethod
    def is_id(cls, id: str):
        """
        Determines if an ID string represents an ID of the record type.
        """
        return id.startswith(cls.ID_TYPE)