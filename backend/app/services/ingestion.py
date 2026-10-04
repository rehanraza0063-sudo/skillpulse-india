"""
Data ingestion: Data sources -> cleaning -> normalisation -> database tables.

Only LocalDemoCSVAdapter is functional. The other adapters are documented stubs showing WHERE official
file / API ingestion would be connected later. They deliberately raise NotImplementedError so nothing can
silently pretend to be official data. Do not scrape websites aggressively; use agreed files or APIs.
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

import pandas as pd

from ..config import DATA_DIR
from ..db import Database
from ..ml.nlp import KeywordSkillExtractor
from ..ml.taxonomy import Taxonomy

TABLES = ["districts", "industries", "skills", "occupations", "jobs", "training_centres",
          "historical_demand", "training_capacity"]
KEYS = {
    "districts": ["district_id"], "industries": ["industry_id"], "skills": ["skill_id"],
    "occupations": ["occupation_id"], "jobs": ["job_id"], "training_centres": ["centre_id"],
    "historical_demand": ["district_id", "skill_id", "year"],
    "training_capacity": ["district_id", "skill_id", "year"],
}
NUMERIC = {
    "historical_demand": ["year", "demand"], "training_capacity": ["year", "capacity"],
    "training_centres": ["latitude", "longitude", "total_capacity", "available_seats", "utilization"],
    "districts": ["latitude", "longitude", "base_weight"], "jobs": ["openings", "posted_year"],
    "industries": ["signal_score"],
}


class DataSourceAdapter(ABC):
    """Interface every data source implements: return a dict of table name -> DataFrame."""
    source_id = "abstract"

    @abstractmethod
    def load(self) -> Dict[str, pd.DataFrame]:
        ...


class LocalDemoCSVAdapter(DataSourceAdapter):
    source_id = "demo_csv"

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir

    def load(self) -> Dict[str, pd.DataFrame]:
        out = {}
        for t in TABLES:
            p = self.data_dir / f"{t}.csv"
            if not p.exists():
                raise FileNotFoundError(f"Missing data file: {p}. Run: python scripts/generate_demo_data.py")
            out[t] = pd.read_csv(p)
        return out


class _NotConnected(DataSourceAdapter):
    hint = ""

    def load(self):
        raise NotImplementedError(f"{self.source_id}: not connected in the prototype. {self.hint}")


class PLFSAdapter(_NotConnected):
    source_id = "plfs"
    hint = "FUTURE: ingest published PLFS releases (file ingestion) -> aggregate to district/sector -> supply-side indicators."


class NCSAdapter(_NotConnected):
    source_id = "ncs"
    hint = "FUTURE: vacancy / job-posting signals via an agreed data-sharing arrangement or API -> jobs table."


class EShramAdapter(_NotConnected):
    source_id = "eshram"
    hint = "FUTURE: anonymised aggregate worker-registry extracts -> supply estimation."


class NCOTaxonomyAdapter(_NotConnected):
    source_id = "nco"
    hint = "FUTURE: NCO-2015 code table -> occupations.nco_mapping and app/ml/taxonomy.py."


class HiringSignalsAdapter(_NotConnected):
    source_id = "hiring_signals"
    hint = "FUTURE: industry hiring outlook feeds -> industries.signal_score."


class TrainingNSQFAdapter(_NotConnected):
    source_id = "nsqf_training"
    hint = "FUTURE: training-provider capacity / enrolment files -> training_centres and training_capacity."


ADAPTERS = {a.source_id: a for a in [LocalDemoCSVAdapter, PLFSAdapter, NCSAdapter, EShramAdapter,
                                      NCOTaxonomyAdapter, HiringSignalsAdapter, TrainingNSQFAdapter]}


def load_source_config() -> dict:
    return json.loads((Path(__file__).resolve().parents[1] / "data" / "data_sources.json").read_text(encoding="utf-8"))


def clean_table(name: str, df: pd.DataFrame, log: dict) -> pd.DataFrame:
    """Cleaning + normalisation: trim strings, coerce numerics, drop duplicates / invalid keys, tag source_type."""
    log["rows_read"] = len(df)
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": None})
    for c in NUMERIC.get(name, []):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    before = len(df)
    df = df.drop_duplicates()
    log["dropped_duplicates"] = before - len(df)
    before = len(df)
    df = df.dropna(subset=[k for k in KEYS[name] if k in df.columns])
    num_required = [c for c in ("demand", "capacity") if c in df.columns]
    if num_required:
        df = df.dropna(subset=num_required)
        df = df[(df[num_required] >= 0).all(axis=1)]
    log["dropped_invalid"] = before - len(df)
    if "source_type" not in df.columns:
        df["source_type"] = "UNKNOWN"
    log["rows_loaded"] = len(df)
    return df.reset_index(drop=True)


def ingest_all(db: Database, taxonomy: Taxonomy, adapter: DataSourceAdapter = None) -> List[dict]:
    adapter = adapter or LocalDemoCSVAdapter()
    raw = adapter.load()
    extractor = KeywordSkillExtractor(taxonomy)
    log = []
    for name in TABLES:
        entry = {"table": name, "source": adapter.source_id, "steps": ["ingest", "clean", "normalise"]}
        df = clean_table(name, raw[name].copy(), entry)
        if name == "jobs":
            # normalisation step: run the NLP extractor over every job description (alias -> canonical skills)
            df["extracted_skills"] = df["description"].apply(
                lambda t: "|".join(dict.fromkeys(s["canonical"] for s in extractor.extract(t))))
            entry["steps"].append("NLP skill extraction + alias normalisation")
        db.write_table(name, df)
        log.append(entry)
    return log
