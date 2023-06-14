from abc import ABC, abstractclassmethod, abstractmethod
from functools import total_ordering
from uuid import uuid4


@total_ordering
class Entity(ABC):
    """
    Abstract base class for objects used in
    farm analysis
   
    Parameters:
    -----------

    """

    def __init__(self, sentry: str):
        self.sentry = sentry

    @abstractclassmethod
    def build_from_record(cls):
        pass

    @abstractmethod
    def __lt__(self, other):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    def wrap_id(self, id: uuid4):
        """
        Helper method to wrap id with origin 
        sentry name.

        Parameters:
        -----------
        id: uuid

        Returns:
        -------
        str

        """
        return self.sentry + ":" + id

    def unwrap_id(self, id):
        """
        Helper method to unwrap id into
        tuple(sentry, object id)

        Parameters:
        -----------
        id: str

        Returns:
        -------
        Tuple[str, uuid4]

        """
        return id.split(":")

    def from_same_sentry(self, other) -> bool:
        """
        Helper method to compare track origin.

        Parameters:
        -----------
        other: SleepyTrack
            Another SleepyTrack to compare clouds against

        Returns:
        -------
        bool

        """
        return self.sentry == other.sentry
