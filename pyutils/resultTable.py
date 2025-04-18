import os.path
import sqlite3
import time
from typing import *
from pathlib import PurePath
from datetime import datetime, date
import hashlib
import shutil
from glob import glob
import sys

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
    def __init__(self, run_id, epoch, step, split, label, value, wall_time, run_rep):
        self.run_id = run_id
        self.epoch = epoch
        self.step = step
        self.split = split
        self.label = label
        self.value = value
        self.wall_time = wall_time
        self.run_rep = run_rep

    def __str__(self):
        return (f"Scalar(run_id={self.run_id}, epoch={self.epoch}, step={self.step}, split={self.split}, "
                f"label={self.label}, value={self.value}, wall_time={self.wall_time}, run_rep={self.run_rep})")

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
        self.run_rep = 0

        # Set the exception handler to set the status to failed and disable the logger if the program crashes
        self._exception_handler()

    def new_repetition(self):
        """
        Create a new repetition of the current run. This is useful if you want to log multiple repetitions of the same run.
        :return: None
        """
        # Start by flushing the buffer
        for tag in self.buffer.keys():
            self._flush(tag)

        self.run_rep += 1

        # Reset the writer
        self.log_count = {}
        self.global_step = {}
        self.start = datetime.now()

    def add_scalar(self, tag: str, scalar_value: Union[float, int],
                   step: Optional[int] = None, epoch: Optional[int] = None,
                   walltime: Optional[float] = None):
        """
        Add a scalar to the resultTable
        :param tag: The tag, formatted as: Split/name
        :param scalar_value: The value
        :param step: The global step. If none, the one calculated is used
        :param epoch: The epoch. If None, none is saved
        :param walltime: Override the wall time with this
        :param run_rep: When the code is run multiple time, the run_rep can be used to log multiple repetitions of the same run_id
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
        self._log(tag, epoch, step, split, name, scalar_value, walltime, self.run_rep)

    def __getitem__(self, tag):
        """
        Get the scalar values for a given tag.
        """
        return self.read_scalar(tag)

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

    def get_hparams(self) -> Dict[str, Any]:
        """
        Get the hyperparameters of the current run
        :return: A dict of hyperparameters
        """
        with self._cursor as cursor:
            cursor.execute("SELECT metric, value FROM Results WHERE run_id=? AND is_hparam=1", (self.run_id,))
            rows = cursor.fetchall()
            return {row[0]: row[1] for row in rows}

    def get_repetitions(self) -> List[int]:
        """
        Get the repetitions of the current run
        :return: A list of repetitions
        """
        with self._cursor as cursor:
            cursor.execute("SELECT DISTINCT run_rep FROM Logs WHERE run_id=?", (self.run_id,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]

    def write_result(self, **kwargs):
        """
        Log the results of the run to the table, then disable the logger.
        :param kwargs: The metrics to save
        :return: None
        """
        # Start by flushing the buffer
        for tag in self.buffer.keys():
            self._flush(tag)

        # Then, prepare the data to save
        query = "INSERT INTO Results (run_id, metric, value, is_hparam) VALUES (?, ?, ?, ?)"
        data = [(self.run_id, key, value, False) for key, value in kwargs.items()]
        with self._cursor as cursor:
            cursor.executemany(query, data)

        # Set the status to finished
        self.set_status("finished")

        # Disable the logger
        self.enabled = False

    def add_hparams(self, **kwargs):
        """
        Add hyperparameters to the result table
        :param kwargs: The hyperparameters to save
        :return: None
        """

        # Prepare the data to save
        query = "INSERT INTO Results (run_id, metric, value, is_hparam) VALUES (?, ?, ?, ?)"
        data = [(self.run_id, key, value, True) for key, value in kwargs.items()]
        with self._cursor as cursor:
            cursor.executemany(query, data)

    @property
    def status(self) -> str:
        """
        Get the status of the run
        :return: The status of the run
        """
        with self._cursor as cursor:
            cursor.execute("SELECT status FROM Experiments WHERE run_id=?", (self.run_id,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(f"Run {self.run_id} does not exist.")
            return row[0]

    @property
    def scalars(self) -> List[str]:
        """
        Return the tags of all scalars logged in the run
        """
        # We need to format the tags as Split/Label
        # If split is empty, we just return the label
        rows = [(row[0] + "/" + row[1]) if row[0] != "" else row[1] for row in self.formatted_scalars]
        return rows

    @property
    def formatted_scalars(self) -> List[Tuple[str, str]]:
        """
        Return the scalars values as split and label
        """
        with self._cursor as cursor:
            cursor.execute("SELECT DISTINCT split, label FROM Logs WHERE run_id=?", (self.run_id,))
            rows = cursor.fetchall()
            # We need to format the tags as Split/Label
            # If split is empty, we just return the label
            return [(row[0], row[1]) for row in rows]

    def set_status(self, status: Literal["running", "finished", "failed"]):
        """
        Set the status of the run
        :param status: The status to set
        :return: None
        """
        if status not in ["running", "finished", "failed"]:
            raise ValueError("Status must be one of: running, finished, failed")
        with self._cursor as cursor:
            cursor.execute("UPDATE Experiments SET status=? WHERE run_id=?", (status, self.run_id))

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

    def _log(self, tag: str, epoch: int, step: int, split: str, name: str, scalar_value: float, walltime: float,
             run_rep: int):
        """
        Store the scalar log into the buffer, and flush the buffer if it is full.
        :param tag: The tag
        :param epoch: The epoch
        :param step: The step
        :param split: The split
        :param name: The name
        :param scalar_value: The value
        :param walltime: The wall time
        :param run_rep: The run repetition
        :return: None
        """
        if tag not in self.buffer:
            self.buffer[tag] = []
        self.buffer[tag].append((self.run_id, epoch, step, split, name, scalar_value, walltime, run_rep))

        if len(self.buffer[tag]) >= self.flush_each:
            self._flush(tag)

    def _flush(self, tag: str):
        """
        Flush the scalar values into the db and reset the buffer.
        :param tag: The tag to flush
        :return: None
        """
        query = """
                INSERT INTO Logs (run_id, epoch, step, split, label, value, wall_time, run_rep)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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

    def _exception_handler(self):
        """
        Set the exception handler to set the status to failed and disable the logger if the program crashes
        """
        previous_hooks = sys.excepthook
        def handler(exc_type, exc_value, traceback):
            # Set the status to failed
            self.set_status("failed")
            # Disable the logger
            self.enabled = False

            # Call the previous exception handler
            previous_hooks(exc_type, exc_value, traceback)

        # Set the new exception handler
        sys.excepthook = handler

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

    def load_config(self, run_id: int) -> str:
        """
        Load the configuration file of a given run id
        :param run_id: The run id
        :return: The path to the configuration file
        """
        valid_files = glob(str(self.configs_path / f"{run_id}.*"))
        if len(valid_files) > 1:
            print(f"Warning: More than one configuration file found for run {run_id}. ")
        with open(valid_files[0], 'r') as f:
            content = f.read()
        return content

    def load_run(self, run_id):
        logwriter = LogWriter(self.db_path, run_id, datetime.now())
        logwriter.enabled = False  # We cannot log with a used writer
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
        cli = " ".join([f'{key}={value}' for key, value in cli.items()])
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
                status = res[7]
                run_id = res[0]
                if status != "failed":
                    raise RuntimeError(f"Configuration has already been run with runID {run_id}. Consider changing "
                                       f"parameter to avoid duplicate runs or add a comment.")

                # If here, the run does exist, but failed. So we will retry it
                self.delete_run(run_id)

                # Create a new one with the same run_id
                cursor.execute("""
                                            INSERT INTO Experiments (run_id, experiment, config, config_hash, cli, comment, start) 
                                            VALUES (?, ?, ?, ?, ?, ?, ?);
                                        """, (run_id, experiment_name, config_str, config_hash, cli, comment, start))
            else:
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

    def delete_run(self, run_id: int):
        """
        Delete the run with the given run_id from the database.
        """
        with self.cursor as cursor:
            # Delete the failed run and replace it with the new one
            cursor.execute("DELETE FROM Experiments WHERE run_id=?", (run_id,))
            # Delete logs
            cursor.execute("DELETE FROM Logs WHERE run_id=?", (run_id,))
            # Delete results
            cursor.execute("DELETE FROM Results WHERE run_id=?", (run_id,))

    def fetch_all_experiments(self):
        with self.cursor as cursor:
            cursor.execute("SELECT * FROM Experiments")
            rows = cursor.fetchall()
            for row in rows:
                print(row)

    def fetch_experiment(self, run_id: int):
        with self.cursor as cursor:
            cursor.execute("SELECT * FROM Experiments WHERE run_id=?", (run_id,))
            row = cursor.fetchone()
            return row

    def set_column_order(self, columns: Dict[str, Optional[int]]):
        """
        Set the order of the column in the result table. If order is None, it will be set to NULL
        :param columns: A dict of column name and their order. The order is the index of the column in the table.
        If the order is None, it will be set to NULL and be hidden
        :return: None
        """
        with self.cursor as cursor:
            # Batch update
            for column, order in columns.items():
                cursor.execute("UPDATE ResultDisplay SET display_order=? WHERE Name=?", (order, column))

    def set_column_alias(self, columns: Dict[str, str]):
        """
        Set the alias of the column in the result table.
        :param columns: A dict of column name and their alias. The alias is the name displayed in the table.
        :return: None
        """
        with self.cursor as cursor:
            # Batch update
            for column, alias in columns.items():
                cursor.execute("UPDATE ResultDisplay SET alias=? WHERE Name=?", (alias, column))

    def hide_column(self, column: str):
        """
        Hide a column in the result table.
        :param column: The column name to hide.
        :return: None
        """
        with self.cursor as cursor:
            cursor.execute("UPDATE ResultDisplay SET display_order=NULL WHERE Name=?", (column,))
            # Change the order of every other columns such that they are continuous
            cursor.execute("""
            UPDATE ResultDisplay 
                SET display_order=(
                    SELECT COUNT(*) FROM ResultDisplay AS R2
                    WHERE R2.display_order < ResultDisplay.display_order
                    ) + 1
                WHERE display_order IS NOT NULL;""", )

    def show_column(self, column: str, order: int = -1):
        """
        Show a column in the result table.
        If order is -1, it will be set to the last column.
        """
        # If the column is already at this order, do nothing
        current = {col_id: order for col_id, (order, alias) in self.result_columns.items()}[column]
        if current == order:
            return
        with self.cursor as cursor:
            # Get the max order
            cursor.execute("SELECT MAX(display_order) FROM ResultDisplay")
            max_order = cursor.fetchone()[0]
            if max_order is None:
                max_order = 0
            else:
                max_order += 1

            if order == -1:
                order = max_order

            # Update all display orders
            cursor.execute("""
                UPDATE ResultDisplay
                SET display_order = display_order + 1
                WHERE display_order >= ?
            """, (order,))
            # print(self.result_columns)
            # Insert the column
            cursor.execute("UPDATE ResultDisplay SET display_order=? WHERE Name=?", (order, column))

    def get_results(self, run_id: Optional[int] = None) -> Tuple[List[str], List[str], List[List[Any]]]:
        """
        Get the result table as a dict
        :param run_id: the run id. If none is specified, it fetches all results
        :return: A list of columns names, a list of column ids and a list of rows
        """
        out = {}
        exp_info = {}
        with self.cursor as cursor:
            if run_id is None:
                cursor.execute("SELECT E.run_id, E.experiment, E.config, E.config_hash, E.cli, E.comment, E.start, R.metric, R.value "
                               "FROM Experiments E LEFT JOIN Results R ON E.run_id = R.run_id")
            else:
                cursor.execute("SELECT E.run_id, E.experiment, E.config, E.config_hash, E.cli, E.comment, E.start, R.metric, R.value "
                               "FROM Experiments E LEFT JOIN Results R ON E.run_id = R.run_id WHERE E.run_id=?", (run_id, ))
            rows = cursor.fetchall()

        for row in rows:
            run_id, metric, value = row[0], row[7], row[8]
            if run_id not in out:  # Run id already stored
                out[run_id] = {}
                exp_info[run_id] = dict(
                    run_id=run_id,
                    experiment=row[1],
                    config=row[2],
                    config_hash=row[3],
                    cli=row[4],
                    comment=row[5],
                    start=datetime.fromisoformat(row[6])
                )
            out[run_id][metric] = value

        # Merge them together:
        for run_id, metrics in out.items():
            exp_info[run_id].update(metrics)

        # Sort the columns of the result table
        columns = [(col_id, col_order, col_alias) for col_id, (col_order, col_alias) in self.result_columns.items() if
                   col_order is not None]
        columns.sort(key=lambda x: x[1])

        table = [[row.get(col[0]) for col in columns] for key, row in exp_info.items()]
        return [col[2] for col in columns], [col[0] for col in columns], table

    @property
    def result_columns(self) -> Dict[str, Tuple[Optional[int], str]]:
        with self.cursor as cursor:
            cursor.execute("SELECT Name, display_order, alias FROM ResultDisplay")
            rows = cursor.fetchall()
            return {row[0]: (row[1], row[2]) for row in rows}

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
            status TEXT CHECK(status IN ('running', 'finished', 'failed')) DEFAULT 'running',
            UNIQUE(experiment, config, config_hash, cli, comment)
        );
        """)

        # Create Results table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Results (
            id_ INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            metric varchar(128) NOT NULL,
            value NOT NULL,
            is_hparam INTEGER DEFAULT 0,
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
            run_rep INTEGER NOT NULL,
            FOREIGN KEY (run_id) REFERENCES Experiments(run_id)
        );
        """)

        # Display Table
        # This table stores every column of Results, their order and whether they displayed or not
        # If order is Null, it means that the column is not displayed
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ResultDisplay (
            Name varchar(128) NOT NULL, display_order INTEGER, alias varchar(128) NOT NULL,
            PRIMARY KEY (Name)
        );
        """)  # We can put order to unique, because each NULL value will be unique

        # Add default columns
        cursor.execute("""
        INSERT OR IGNORE INTO ResultDisplay (Name, display_order, alias) VALUES
        ('run_id', 0, 'Run ID'),
        ('experiment', 1, 'Experiment'),
        ('config', 2, 'Config'),
        ('config_hash', NULL, 'Config Hash'),
        ('cli', 3, 'Cli'),
        ('comment', 4, 'Comment'),
        ('start', 5, 'Start');
        """)

        # Create a trigger to add a new metric to the display table
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS after_result_insert
        AFTER INSERT ON Results
        BEGIN
            -- Insert a row into ResultDisplay if the Name does not exist
            INSERT OR IGNORE INTO ResultDisplay (Name, display_order, alias)
            SELECT NEW.metric, 
                   COALESCE(MAX(display_order), 0) + 1, 
                   NEW.metric
            FROM ResultDisplay;
        END;
        """)
        # Create index for speed
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_config_hash ON Experiments(experiment, config, config_hash, cli, comment);")
        conn.commit()
        conn.close()


if __name__ == "__main__":
    import numpy as np
    rtable = ResultTable()
    cli = {
        "fract": 0.25,
        "sample_inputs": False,
        "dataset": "Pâques",
    }
    start = datetime.now()
    writer = rtable.new_run("Experiment1", "results/myconfig.yml", cli=cli)
    writer.add_hparams(**cli)
    # writer = rtable.load_run(2)
    # print(writer.run_id)
    # val_step = [s.value for s in writer.read_scalar("Valid/acc")]
    # train_step = [s.value for s in writer.read_scalar("Train/acc")]
    # print(train_step)
    # print(val_step)
    for rep in range(3):
        if rep > 0:
            writer.new_repetition()
        for e in range(10):
            for i in range(100):
                writer.add_scalar("Train/acc", np.sqrt(i / 10) / 3.5, epoch=e)
                writer.add_scalar("Valid/acc", np.sqrt(i / 10) / 3.7, epoch=e)
                writer.add_scalar("Train/f1", np.sqrt(i / 10) / 3.4, epoch=e)
                writer.add_scalar("Valid/f1", np.sqrt(i / 10) / 3.8, epoch=e)
                time.sleep(0.05)
                print(rep, e, i)

    writer.write_result(loss=0.37, accuracy=0.92, f1=0.90)
    columns, col_ids, data = rtable.get_results()
    print(columns)
    for row in data:
        print(row)