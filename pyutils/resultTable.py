import os.path
import sqlite3
from typing import *
from pathlib import PurePath
from datetime import datetime, date
import hashlib

def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

sqlite3.register_adapter(datetime.date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)

def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return date.fromisoformat(val.decode())

def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)

class Cursor:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def __enter__(self):
        self._conn = sqlite3.connect(self.db_path)
        self._cursor = self._conn.cursor()
        return self._cursor

    def __exit__(self, exc_type, exc_value, traceback):
        """Commits changes if no exception occurred, then closes the connection."""
        if self._conn:
            if exc_type is None:  # No exceptions, commit changes
                self._conn.commit()
            self._conn.close()

class LogWriter:
    def __init__(self, db_path, run_id: int):
        self.db_path = db_path
        self.run_id = run_id


class ResultTable:
    def __init__(self, db_path: str = "results/result_table.db"):
        if not os.path.exists(db_path):
            self.create_database(db_path)

        self.db_path = db_path

    def new_run(self, experiment_name: str,
                config_path: Union[str, PurePath],
                comment: Optional[str] = None):
        # TODO: Move config file to out dir and verify if modification to avoid duplicates
        start = datetime.now()
        config_str = str(config_path)
        config_hash = self.get_file_hash(config_path)
        comment = "" if comment is None else comment
        with self.cursor as cursor:
            # Insert the new row inside Experiments, then retrieve the runID
            cursor.execute("""
                            INSERT INTO Experiments (experiment, config, config_hash, comment, start) 
                            VALUES (?, ?, ?, ?, ?);
                        """, (experiment_name, config_str, config_hash, comment, start))

            # Retrieve the run_id assigned by SQLite
            run_id = cursor.lastrowid

        return LogWriter(self.db_path, run_id)

    def fetch_all_experiments(self):
        with self.cursor as cursor:
            cursor.execute("SELECT * FROM Experiments")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
    @property
    def cursor(self):
        return Cursor(self.db_path)

    @staticmethod
    def get_file_hash(file_path: str, hash_algo: str = 'sha256') -> str:
        """Returns the hash of the file at file_path using the specified hashing algorithm."""
        hash_func = hashlib.new(hash_algo)  # Create a new hash object for the specified algorithm

        with open(file_path, 'rb') as file:
            while chunk := file.read(8192):  # Read the file in chunks to avoid memory overflow
                hash_func.update(chunk)  # Update the hash with the current chunk

        return hash_func.hexdigest()

    @staticmethod
    def create_database(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create Experiments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Experiments (
            run_id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            experiment varchar(128) NOT NULL,
            config varchar(128) NOT NULL,
            config_hash varchar(64),
            comment TEXT,
            start DATETIME NOT NULL,
            UNIQUE(experiment, config, config_hash, comment)
        );
        """)

        # Create Results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            metric varchar(128) NOT NULL,
            value REAL NOT NULL,
            FOREIGN KEY (run_id) REFERENCES Experiments(run_id)
        );
        """)

        # Create Logs table
        # Wall time is in seconds
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Logs (
            run_id INTEGER NOT NULL,
            step INTEGER NOT NULL,
            split varchar(128) NOT NULL,
            label varchar(128) NOT NULL,
            value varchar(128) NOT NULL,
            wall_time REAL NOT NULL,
            PRIMARY KEY (run_id, step),
            FOREIGN KEY (run_id) REFERENCES Experiments(run_id)
        );
        """)

        conn.commit()
        conn.close()


if __name__ == "__main__":
    rtable = ResultTable()
    writer = rtable.new_run("Experiment1", "results/myconfig.yml")
    print(writer.run_id)
    rtable.fetch_all_experiments()