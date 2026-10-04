"""
Database layer (modular).

Default: SQLite via the standard library (no extra install, works on Windows).
PostgreSQL / PostGIS: set DATABASE_URL=postgresql+psycopg2://... and `pip install sqlalchemy psycopg2-binary`.
The latitude / longitude columns of `districts` and `training_centres` are where PostGIS geometry columns
(`ST_SetSRID(ST_MakePoint(lon, lat), 4326)`) and `ST_DWithin` distance queries would be added later;
the prototype computes haversine distances in Python instead (app/utils/geo.py).
"""
import sqlite3
from typing import List

import pandas as pd

from .config import DATABASE_URL


class Database:
    def __init__(self, url: str = DATABASE_URL):
        self.url = url
        self._engine = None
        if url.startswith("sqlite"):
            self.kind = "sqlite"
            self.path = url.split("///", 1)[1]
        else:
            self.kind = "sqlalchemy"
            try:
                from sqlalchemy import create_engine  # noqa: WPS433
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "DATABASE_URL points to a non-SQLite database; install sqlalchemy and the matching driver "
                    "(pip install sqlalchemy psycopg2-binary)."
                ) from exc
            self._engine = create_engine(url)

    def describe(self) -> str:
        if self.kind == "sqlite":
            return f"SQLite ({self.path}) - development fallback; PostgreSQL/PostGIS supported via DATABASE_URL"
        return "SQLAlchemy engine (" + self.url.split("@")[-1] + ")"

    def write_table(self, name: str, df: pd.DataFrame) -> None:
        if self.kind == "sqlite":
            con = sqlite3.connect(self.path)
            try:
                df.to_sql(name, con, if_exists="replace", index=False)
                con.commit()
            finally:
                con.close()
        else:  # pragma: no cover
            df.to_sql(name, self._engine, if_exists="replace", index=False)

    def read_table(self, name: str) -> pd.DataFrame:
        if self.kind == "sqlite":
            con = sqlite3.connect(self.path)
            try:
                return pd.read_sql_query(f'SELECT * FROM "{name}"', con)
            finally:
                con.close()
        return pd.read_sql_table(name, self._engine)  # pragma: no cover

    def list_tables(self) -> List[str]:
        if self.kind == "sqlite":
            con = sqlite3.connect(self.path)
            try:
                rows = con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            finally:
                con.close()
            return [r[0] for r in rows]
        from sqlalchemy import inspect  # pragma: no cover
        return inspect(self._engine).get_table_names()  # pragma: no cover
