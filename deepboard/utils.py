from datetime import datetime, date
import sqlite3


def _adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def _adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

def _convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return date.fromisoformat(val.decode())


def _convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

def prepare_db():

    sqlite3.register_adapter(datetime.date, _adapt_date_iso)
    sqlite3.register_adapter(datetime, _adapt_datetime_iso)


    sqlite3.register_converter("date", _convert_date)
    sqlite3.register_converter("datetime", _convert_datetime)
