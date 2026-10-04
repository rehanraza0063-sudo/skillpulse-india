"""
SkillPulse engine: Demand + Supply -> Forecast -> Gap -> GIS matching.

All results are PROTOTYPE outputs computed from DEMO data. See app/ml/forecast.py for the forecasting method.
Gap definition (configurable thresholds in app/config.py):

    gap        = forecast demand - training capacity
    gap_ratio  = gap / forecast demand
    SHORTAGE if gap_ratio > shortage_threshold, SURPLUS if gap_ratio < surplus_threshold, else BALANCED
"""
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from ..config import DATA_DIR, DEMO_LABEL, settings
from ..db import Database
from ..ml.forecast import confidence_label, linear_forecast
from ..ml.nlp import KeywordSkillExtractor
from ..ml.taxonomy import Taxonomy
from ..utils.geo import haversine_km

ALL_YEARS = list(settings.history_years) + list(settings.forecast_years)


def parse_seats(s) -> Dict[str, int]:
    out = {}
    if isinstance(s, str) and s:
        for part in s.split(";"):
            k, _, v = part.partition("=")
            try:
                out[k] = int(v)
            except ValueError:
                pass
    return out


class Thresholds:
    def __init__(self, shortage: Optional[float] = None, surplus: Optional[float] = None):
        self.shortage = settings.shortage_threshold if shortage is None else shortage
        self.surplus = settings.surplus_threshold if surplus is None else surplus

    def classify(self, ratio: float) -> str:
        if ratio > self.shortage:
            return "SHORTAGE"
        if ratio < self.surplus:
            return "SURPLUS"
        return "BALANCED"

    def as_dict(self):
        return {"shortage_above": self.shortage, "surplus_below": self.surplus}


def ew_status(ratio: float) -> str:
    """Prototype early-warning class (not an official classification)."""
    if ratio <= settings.ew_low_max:
        return "LOW"
    if ratio <= settings.ew_growing_max:
        return "GROWING"
    return "CRITICAL"


class Engine:
    def __init__(self, db: Database, taxonomy: Taxonomy, ingestion_log: List[dict]):
        self.db = db
        self.tax = taxonomy
        self.ingestion_log = ingestion_log
        self.extractor = KeywordSkillExtractor(taxonomy)
        self.t = {n: db.read_table(n) for n in [
            "districts", "industries", "skills", "occupations", "jobs", "training_centres",
            "historical_demand", "training_capacity"]}
        self.dname = dict(zip(self.t["districts"].district_id, self.t["districts"].district_name))
        self.dcoord = {r.district_id: (r.latitude, r.longitude) for r in self.t["districts"].itertuples()}
        self.sname = dict(zip(self.t["skills"].skill_id, self.t["skills"].skill_name))
        self.sindustry = dict(zip(self.t["skills"].skill_id, self.t["skills"].industry_id))
        self.iname = dict(zip(self.t["industries"].industry_id, self.t["industries"].industry_name))
        self.oname = dict(zip(self.t["occupations"].occupation_id, self.t["occupations"].occupation_name))
        self.occ_skill = dict(zip(self.t["occupations"].occupation_name, self.t["occupations"].skill_id))
        self.occ_industry = dict(zip(self.t["occupations"].occupation_name, self.t["occupations"].industry_id))
        self._build_series()
        self.last_updated = self._last_updated()

    # ------------------------------------------------------------------ series
    def _last_updated(self) -> str:
        files = list(DATA_DIR.glob("*.csv"))
        ts = max((f.stat().st_mtime for f in files), default=datetime.now().timestamp())
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")

    def _build_series(self):
        dem, cap = self.t["historical_demand"], self.t["training_capacity"]
        cap_idx = {(r.district_id, r.skill_id, int(r.year)): float(r.capacity) for r in cap.itertuples()}
        growth = settings.capacity_growth_pct / 100.0
        rows, self.models = [], {}
        for (d, s), g in dem.groupby(["district_id", "skill_id"]):
            g = g.sort_values("year")
            pts, info = linear_forecast(g.year.tolist(), g.demand.tolist(), settings.forecast_years)
            self.models[(d, s)] = info
            for r in g.itertuples():
                y = int(r.year)
                rows.append((d, s, y, float(r.demand), float(r.demand), float(r.demand),
                             cap_idx.get((d, s, y), 0.0), False, 1.0))
            base_cap = cap_idx.get((d, s, settings.base_year), 0.0)
            for p in pts:
                rows.append((d, s, p.year, p.value, p.lower, p.upper,
                             base_cap * (1 + growth) ** (p.year - settings.base_year), True, p.confidence))
        self.series = pd.DataFrame(rows, columns=[
            "district_id", "skill_id", "year", "demand", "lo", "hi", "capacity", "is_forecast", "conf"])

    # ------------------------------------------------------------------ filters
    def resolve_skills(self, industry_id=None, occupation_id=None, skill_id=None) -> List[str]:
        ids = list(self.t["skills"].skill_id)
        if industry_id:
            ids = [s for s in ids if self.sindustry[s] == industry_id]
        if occupation_id:
            occ = self.t["occupations"]
            sk = occ.loc[occ.occupation_id == occupation_id, "skill_id"].tolist()
            ids = [s for s in ids if s in sk]
        if skill_id:
            ids = [s for s in ids if s == skill_id]
        return ids

    def aggregate(self, year: int, by: List[str], district_ids=None, skill_ids=None) -> pd.DataFrame:
        df = self.series[self.series.year == year]
        if district_ids is not None:
            df = df[df.district_id.isin(district_ids)]
        if skill_ids is not None:
            df = df[df.skill_id.isin(skill_ids)]
        df = df.assign(w=df.demand * df.conf)
        if by:
            g = df.groupby(by, as_index=False)[["demand", "lo", "hi", "capacity", "w"]].sum()
        else:
            g = df[["demand", "lo", "hi", "capacity", "w"]].sum().to_frame().T
        g["conf"] = (g.w / g.demand.where(g.demand > 0, 1)).clip(upper=0.95)
        g["is_forecast"] = year > settings.base_year
        return g.drop(columns="w")

    def with_gap(self, df: pd.DataFrame, th: Thresholds) -> pd.DataFrame:
        df = df.copy()
        df["gap"] = df.demand - df.capacity
        df["gap_ratio"] = df.gap / df.demand.where(df.demand > 0, 1)
        df["status"] = df.gap_ratio.apply(th.classify)
        df["ew_status"] = df.gap_ratio.apply(ew_status)
        return df

    @staticmethod
    def calc_text(demand: float, capacity: float, th: Thresholds) -> str:
        gap = demand - capacity
        ratio = gap / demand if demand else 0.0
        return (f"Gap = forecast demand - training capacity = {demand:,.0f} - {capacity:,.0f} = {gap:,.0f}; "
                f"gap ratio = {gap:,.0f} / {demand:,.0f} = {ratio * 100:.1f}% "
                f"(SHORTAGE if > {th.shortage * 100:.0f}%, SURPLUS if < {th.surplus * 100:.0f}%, else BALANCED)")

    # ------------------------------------------------------------------ simple lists
    def districts(self):
        return self.t["districts"].to_dict("records")

    def skills(self):
        th = Thresholds()
        agg = self.with_gap(self.aggregate(settings.base_year, ["skill_id"]), th).set_index("skill_id")
        out = []
        for r in self.t["skills"].itertuples():
            a = agg.loc[r.skill_id]
            out.append({**r._asdict(), "industry_name": self.iname[r.industry_id], "demand_2026": a.demand,
                        "capacity_2026": a.capacity, "status_2026": a.status})
        for o in out:
            o.pop("Index", None)
        return out

    def occupations(self):
        out = []
        for r in self.t["occupations"].itertuples():
            out.append({
                "occupation_id": r.occupation_id, "occupation_name": r.occupation_name, "skill_id": r.skill_id,
                "skill_name": self.sname[r.skill_id], "industry_id": r.industry_id,
                "industry_name": self.iname[r.industry_id], "nco_mapping": r.nco_mapping, "source_type": r.source_type,
                "competencies": [{"competency": c, "weight": w} for c, w in self.tax.requirements[r.occupation_name].items()],
            })
        return out

    def competencies(self):
        return [{"name": n, "category": c["category"]} for n, c in self.tax.competencies.items()]

    # ------------------------------------------------------------------ GIS
    def centres_for_skill(self, skill_id: str, district_id: Optional[str] = None) -> List[dict]:
        out = []
        for r in self.t["training_centres"].itertuples():
            if district_id and r.district_id != district_id:
                continue
            seats, avail = parse_seats(r.seats_by_skill), parse_seats(r.available_by_skill)
            if skill_id in seats:
                out.append({"centre_id": r.centre_id, "name": r.name, "district_id": r.district_id,
                            "district_name": r.district_name, "latitude": r.latitude, "longitude": r.longitude,
                            "seats_for_skill": seats[skill_id], "available_for_skill": avail.get(skill_id, 0),
                            "certification": r.certification, "source_type": r.source_type})
        return out

    def skill_gap_map(self, skill_id: str, year: int, forecast_year: int, th: Thresholds) -> dict:
        if skill_id not in self.sname:
            raise KeyError(f"Unknown skill_id: {skill_id}")
        cur = self.with_gap(self.aggregate(year, ["district_id"], skill_ids=[skill_id]), th).set_index("district_id")
        fc = self.with_gap(self.aggregate(forecast_year, ["district_id"], skill_ids=[skill_id]), th).set_index("district_id")
        rows = []
        for d in self.t["districts"].itertuples():
            c, f = cur.loc[d.district_id], fc.loc[d.district_id]
            rows.append({
                "district_id": d.district_id, "district_name": d.district_name,
                "latitude": d.latitude, "longitude": d.longitude, "region": d.region,
                "skill_id": skill_id, "skill_name": self.sname[skill_id], "year": year, "forecast_year": forecast_year,
                "demand": c.demand, "capacity": c.capacity, "gap": c.gap, "gap_ratio": c.gap_ratio, "status": c.status,
                "forecast_demand": f.demand, "forecast_lower": f.lo, "forecast_upper": f.hi,
                "forecast_capacity": f.capacity, "forecast_gap": f.gap, "forecast_gap_ratio": f.gap_ratio,
                "forecast_status": f.status, "confidence": f.conf, "confidence_label": confidence_label(f.conf),
                "calculation": self.calc_text(c.demand, c.capacity, th),
                "forecast_calculation": self.calc_text(f.demand, f.capacity, th),
            })
        tot_c = self.with_gap(self.aggregate(year, [], skill_ids=[skill_id]), th).iloc[0]
        tot_f = self.with_gap(self.aggregate(forecast_year, [], skill_ids=[skill_id]), th).iloc[0]
        return {
            "skill_id": skill_id, "skill_name": self.sname[skill_id], "year": year, "forecast_year": forecast_year,
            "thresholds": th.as_dict(), "districts": rows,
            "state_total": {"demand": tot_c.demand, "capacity": tot_c.capacity, "gap": tot_c.gap, "status": tot_c.status,
                            "forecast_demand": tot_f.demand, "forecast_capacity": tot_f.capacity,
                            "forecast_gap": tot_f.gap, "forecast_status": tot_f.status},
            "data_label": DEMO_LABEL, "forecast_label": "Prototype Forecast",
        }

    def nearby_surplus(self, skill_id: str, district_id: str, year: int, th: Thresholds,
                       radius_km: Optional[float] = None) -> dict:
        if district_id not in self.dname:
            raise KeyError(f"Unknown district_id: {district_id}")
        radius = radius_km or settings.nearby_radius_km
        gaps = self.with_gap(self.aggregate(year, ["district_id"], skill_ids=[skill_id]), th).set_index("district_id")
        me = gaps.loc[district_id]
        lat, lon = self.dcoord[district_id]
        cands = []
        for d, (la, lo) in self.dcoord.items():
            if d == district_id:
                continue
            row = gaps.loc[d]
            if row.status != "SURPLUS":
                continue
            dist = haversine_km(lat, lon, la, lo)
            if dist > radius:
                continue
            surplus = float(row.capacity - row.demand)
            transferable = min(max(float(me.gap), 0.0), surplus)
            cands.append({
                "district_id": d, "district_name": self.dname[d], "distance_km": round(dist, 1),
                "demand": row.demand, "capacity": row.capacity, "surplus_seats": surplus,
                "transferable_seats": transferable, "gap_ratio": row.gap_ratio,
                "centres": sorted(self.centres_for_skill(skill_id, d), key=lambda c: -c["available_for_skill"]),
            })
        cands.sort(key=lambda c: c["distance_km"])
        return {
            "skill_id": skill_id, "skill_name": self.sname[skill_id], "district_id": district_id,
            "district_name": self.dname[district_id], "year": year, "status": me.status,
            "shortage_seats": max(float(me.gap), 0.0), "radius_km": radius,
            "candidates": cands,
            "method": "Haversine straight-line distance between demo district coordinates (not road distance); "
                      "candidates are districts classified SURPLUS for this skill; transferable seats = min(shortage, surplus).",
            "message": (None if me.status == "SHORTAGE" else
                        f"{self.dname[district_id]} is {me.status} for {self.sname[skill_id]} in {year}; "
                        "nearby surplus matching is shown for reference."),
            "data_label": DEMO_LABEL,
        }

    def district_detail(self, skill_id: str, district_id: str, year: int, forecast_year: int, th: Thresholds,
                        radius_km: float = 120.0) -> dict:
        m = self.skill_gap_map(skill_id, year, forecast_year, th)
        row = next((r for r in m["districts"] if r["district_id"] == district_id), None)
        if row is None:
            raise KeyError(f"Unknown district_id: {district_id}")
        lat, lon = self.dcoord[district_id]
        near = []
        for c in self.centres_for_skill(skill_id):
            dist = haversine_km(lat, lon, c["latitude"], c["longitude"])
            if dist <= radius_km:
                near.append({**c, "distance_km": round(dist, 1)})
        near.sort(key=lambda c: c["distance_km"])
        return {**row, "nearby_centres": near, "centre_radius_km": radius_km,
                "forecast_model": self.models.get((district_id, skill_id)), "data_label": DEMO_LABEL}

    # ------------------------------------------------------------------ forecast
    def forecast_series(self, skill_id: str, district_id: Optional[str], th: Thresholds) -> dict:
        if skill_id not in self.sname:
            raise KeyError(f"Unknown skill_id: {skill_id}")
        d_ids = [district_id] if district_id else None
        if district_id and district_id not in self.dname:
            raise KeyError(f"Unknown district_id: {district_id}")
        rows = []
        for y in ALL_YEARS:
            a = self.with_gap(self.aggregate(y, [], d_ids, [skill_id]), th).iloc[0]
            rows.append({"year": y, "demand": a.demand, "lower": a.lo, "upper": a.hi, "capacity": a.capacity,
                         "gap": a.gap, "gap_ratio": a.gap_ratio, "status": a.status,
                         "is_forecast": y > settings.base_year,
                         "confidence": a.conf, "confidence_label": ("OBSERVED (demo)" if y <= settings.base_year else confidence_label(a.conf))})
        hist = [(r["year"], r["demand"]) for r in rows if not r["is_forecast"]]
        _, info = linear_forecast([h[0] for h in hist], [h[1] for h in hist], settings.forecast_years)
        return {"skill_id": skill_id, "skill_name": self.sname[skill_id],
                "district_id": district_id, "district_name": self.dname.get(district_id, "Maharashtra (all demo districts)"),
                "series": rows, "model": info, "capacity_assumption":
                    f"Training capacity held at the {settings.base_year} level"
                    + (f" plus {settings.capacity_growth_pct:.1f}%/yr" if settings.capacity_growth_pct else " (no new capacity assumed)"),
                "forecast_label": "Prototype Forecast", "data_label": DEMO_LABEL,
                "thresholds": th.as_dict()}
