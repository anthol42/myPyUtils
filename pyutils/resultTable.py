import os.path
import sqlite3
import time
from typing import *
from pathlib import PurePath
from datetime import datetime, date
import hashlib
import shutil


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

class Scalar:
    def __init__(self, run_id, epoch, step, split, label, value, wall_time):
        self.run_id = run_id
        self.epoch = epoch
        self.step = step
        self.split = split
        self.label = label
        self.value = value
        self.wall_time = wall_time

class LogWriter:
    def __init__(self, db_path, run_id: int, start: datetime, flush_each: int = 10, keep_each: int = 1):
        if keep_each <= 0:
            raise ValueError("Parameter keep_each must be grater than 0: {1, 2, 3, ...}")
        if flush_each <= 0:
            raise ValueError("Parameter keep_each must be grater than 0: {1, 2, 3, ...}")
        self.db_path = db_path
        self.run_id = run_id
        self.start = start
        self.flush_each = flush_each
        self.keep_each = keep_each
        self.global_step = {}
        self.buffer = {}
        self.log_count = {}
        self.enabled = True
    def add_scalar(self, tag: str, scalar_value: Union[float, int],
                   step: Optional[int] = None, epoch: Optional[int] = None, walltime: Optional[float] = None):
        """
        Add a scalar to the resultTable
        :param tag: The tag, formatted as: Split/name
        :param scalar_value: The value
        :param step: The global step. If none, the one calculated is used
        :param epoch: The epoch. If None, none is saved
        :param walltime: Override the wall time with this
        :return: None
        """
        if not self.enabled:
            raise RuntimeError("The LogWriter is read only! This might be due to the fact that you loaded an already"
                               "existing one or you reported final metrics.")
        # Early return if we are not supposed to keep this run.
        if not self._keep(tag):
            return

        # We split the tag as a split and a name for readability
        splitted_tag = tag.split("/")
        if len(splitted_tag) == 2:
            split, name = splitted_tag[0], splitted_tag[1]
        else:
            split, name = "", splitted_tag[0]

        scalar_value = float(scalar_value)  # Cast it as float

        step = self._get_global_step(tag) if step is None else step

        walltime = (datetime.now() - self.start).total_seconds() if walltime is None else walltime

        epoch = 0 if epoch is None else epoch

        # Added a row to table logs
        self._log(tag, epoch, step, split, name, scalar_value, walltime)

    def read_scalar(self, tag):
        splitted_tag = tag.split("/")
        if len(splitted_tag) == 2:
            split, name = splitted_tag[0], splitted_tag[1]
        else:
            split, name = "", splitted_tag[0]

        with self._cursor as cursor:
            cursor.execute("SELECT * FROM Logs WHERE run_id=? AND split=? AND label=?", (self.run_id, split, name))
            # cursor.execute("SELECT * FROM Logs", (self.run_id, split, name))
            rows = cursor.fetchall()
            return [Scalar(*row[1:]) for row in rows]

    def _get_global_step(self, tag):
        """
        Keep track of the global step for each tag.
        :param tag: The tag to get the step
        :return: The current global step
        """
        if tag not in self.global_step:
            self.global_step[tag] = 0

        out = self.global_step[tag]
        self.global_step[tag] += 1
        return out

    def _log(self, tag: str, epoch: int, step: int, split: str, name: str, scalar_value: float, walltime: float):
        """
        Store the scalar log into the buffer, and flush the buffer if it is full.
        :param tag: The tag
        :param epoch: The epoch
        :param step: The step
        :param split: The split
        :param name: The name
        :param scalar_value: The value
        :param walltime: The wall time
        :return: None
        """
        if tag not in self.buffer:
            self.buffer[tag] = []
        self.buffer[tag].append((self.run_id, epoch, step, split, name, scalar_value, walltime))

        if len(self.buffer[tag]) >= self.flush_each:
            self._flush(tag)

    def _flush(self, tag: str):
        """
        Flush the scalar values into the db and reset the buffer.
        :param tag: The tag to flush
        :return: None
        """
        query = """
                INSERT INTO Logs (run_id, epoch, step, split, label, value, wall_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
        with self._cursor as cursor:
            cursor.executemany(query, self.buffer[tag])

        # Reset the buffer
        self.buffer[tag] = []

    def _keep(self, tag: str) -> bool:
        """
        Assert if we need to record this log or drop it. Depends on the kep_each attribute
        :param tag: The tag
        :return: True if we need to keep it and False if we drop it
        """
        if tag not in self.log_count:
            self.log_count[tag] = 0
        self.log_count[tag] += 1
        if self.log_count[tag] >= self.keep_each:
            self.log_count[tag] = 0
            return True
        else:
            return False

    @property
    def _cursor(self):
        return Cursor(self.db_path)

class ResultTable:
    def __init__(self, db_path: str = "results/result_table.db"):
        if not os.path.exists(db_path):
            self.create_database(db_path)
        db_path = PurePath(db_path) if not isinstance(db_path, PurePath) else db_path

        # The configuration files will be back up there
        self.configs_path = db_path.parent / "configs"
        if not os.path.exists(self.configs_path):
            os.mkdir(self.configs_path)

        self.db_path = db_path

    def load_run(self, run_id):
        logwriter = LogWriter(self.db_path, run_id, datetime.now())
        logwriter.readonly = False  # We cannot log with a used writer
        return logwriter
    def new_run(self, experiment_name: str,
                config_path: Union[str, PurePath],
                cli: dict,
                comment: Optional[str] = None,
                flush_each: int = 10,
                keep_each: int = 1
                ) -> LogWriter:
        """
        Create a new socket to log the results.
        :param experiment_name: The name of the current experiment
        :param config_path: The path to the configuration path
        :param cli: The cli arguments
        :param comment: The comment, if any
        :param flush_each: Every how many logs does the logger save them to the database?
        :param keep_each: If the training has a lot of steps, it might be preferable to not
        log every step to save space and speed up the process. This parameter controls every how many step we store the
        log. 1 means we save at every steps. 10 would mean that we drop 9 steps to save 1.
        :return: The log writer
        """
        start = datetime.now()
        config_str = str(config_path)
        config_hash = self.get_file_hash(config_path)
        comment = "" if comment is None else comment
        cli = " ".join([f'{key}={value}' for key, value in cli.values()])
        with self.cursor as cursor:
            # Step 1: Check if the configuration already exists
            cursor.execute("""
                    SELECT * FROM Experiments
                    WHERE experiment = ?
                      AND config = ?
                      AND config_hash = ?
                      AND cli = ?
                      AND comment = ?
            """, (experiment_name, config_str, config_hash, cli, comment))
            res = cursor.fetchone()
            if res is not None:
                run_id = res[0]
                raise RuntimeError(f"Configuration has already been run with runID {run_id}. Consider changing "
                                   f"parameter to avoid duplicate runs or add a comment.")
            # Insert the new row inside Experiments, then retrieve the runID
            cursor.execute("""
                            INSERT INTO Experiments (experiment, config, config_hash, cli, comment, start) 
                            VALUES (?, ?, ?, ?, ?, ?);
                        """, (experiment_name, config_str, config_hash, cli, comment, start))

            # Retrieve the run_id assigned by SQLite
            run_id = cursor.lastrowid

        if not isinstance(config_path, PurePath):
            config_path = PurePath(config_path)
        config_name = config_path.name

        extension = config_name.split(".")[-1]
        shutil.copy(config_path, self.configs_path / f'{run_id}.{extension}')

        return LogWriter(self.db_path, run_id, datetime.now(), flush_each=flush_each, keep_each=keep_each)

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
            cli varchar(256),
            comment TEXT,
            start DATETIME NOT NULL,
            UNIQUE(experiment, config, config_hash, cli, comment)
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
            id_ INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            epoch INTEGER,
            step INTEGER NOT NULL,
            split varchar(128) NOT NULL,
            label varchar(128) NOT NULL,
            value REAL NOT NULL,
            wall_time REAL NOT NULL,
            FOREIGN KEY (run_id) REFERENCES Experiments(run_id)
        );
        """)

        # Create index for speed
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_hash ON Experiments(experiment, config, config_hash, cli, comment);")
        conn.commit()
        conn.close()


if __name__ == "__main__":
    rtable = ResultTable()
    cli = {}
    start = datetime.now()
    # writer = rtable.new_run("Experiment1", "results/myconfig.yml", cli=cli)
    writer = rtable.load_run(2)
    print(writer.run_id)
    val_step = [s.value for s in writer.read_scalar("Valid/acc")]
    train_step = [s.value for s in writer.read_scalar("Train/acc")]
    print(train_step)
    print(val_step)
    # for i in range(100):
    #     writer.add_scalar("Train/acc", 2 * i / 100, i)
    #     writer.add_scalar("Valid/acc", 2 * i / 100, walltime=(datetime.now() - start).total_seconds())
    #     writer.add_scalar("Test/acc", 2 * i / 100, epoch=1)
    #     time.sleep(1)
    #     print(i)