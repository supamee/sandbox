import sqlite3
from abc import ABC

class Store(ABC):
    def __init__(self):
        self.connection = None
        self.check_same_thread = False

    def __enter__(self):
        pass

    def __exit__(self):
        pass

    def open(self, path=None):
        self.path = path
        if self.path is None:
            self.connection = sqlite3.connect(
                ":memory:", check_same_thread=self.check_same_thread
            )
        else:
            self.connection = sqlite3.connect(
                self.path, check_same_thread=self.check_same_thread
            )
        self.connection.execute("PRAGMA journal_mode = WAL")
        return self

    def close(self):
        self.connection.close()

    def begin(self):
        self.connection.execute("BEGIN TRANSACTION")

    def end(self):
        self.connection.execute("END TRANSACTION")

    def rollback(self):
        self.connection.execute("ROLLBACK")