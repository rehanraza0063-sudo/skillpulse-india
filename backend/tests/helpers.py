import os
import tempfile
from functools import lru_cache

from app.config import DATA_DIR
from app.db import Database
from app.ml.taxonomy import Taxonomy
from app.services.engine import Engine
from app.services.ingestion import ingest_all


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Builds an engine on a throw-away SQLite file so tests never touch the dev database."""
    db = Database("sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db").replace("\\", "/"))
    tax = Taxonomy(DATA_DIR)
    return Engine(db, tax, ingest_all(db, tax))
