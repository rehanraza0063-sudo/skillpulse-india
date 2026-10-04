"""REST API. Thin layer: validation + error mapping; all logic lives in app/services and app/ml."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from ..config import DEMO_LABEL, settings
from ..ml.nlp import run_pipeline
from ..ml.transition import analyze_transition
from ..models.schemas import (ExtractSkillsRequest, ExtractSkillsResponse, TransitionRequest, TransitionResponse,
                              WhatIfRequest, WhatIfResponse)
from ..services import planning
from ..services.engine import Engine, Thresholds
from ..services.ingestion import load_source_config
from ..utils.clean import clean

router = APIRouter(prefix="/api")

SAMPLE_JD = ("Looking for an EV technician with experience in battery management systems, vehicle diagnostics, "
             "electrical systems and high-voltage safety.")


def eng(request: Request) -> Engine:
    e = getattr(request.app.state, "engine", None)
    if e is None:
        raise HTTPException(status_code=503, detail="Engine is not initialised yet. Check the server log.")
    return e


def th_from(shortage: Optional[float], surplus: Optional[float]) -> Thresholds:
    t = Thresholds(shortage, surplus)
    if t.surplus >= t.shortage:
        raise HTTPException(status_code=400, detail="surplus_threshold must be lower than shortage_threshold")
    return t


YEAR = Query(2026, ge=2023, le=2028, description="2023-2026 demo history, 2027-2028 Prototype Forecast")


@router.get("/health")
def health(request: Request):
    return {"status": "ok", "mode": "DEMO MODE", "data_label": DEMO_LABEL,
            "engine_ready": getattr(request.app.state, "engine", None) is not None}


@router.get("/config")
def get_config():
    return {"thresholds": Thresholds().as_dict(),
            "early_warning": {"low_max": settings.ew_low_max, "growing_max": settings.ew_growing_max},
            "capacity_growth_pct": settings.capacity_growth_pct, "transition_min_fit": settings.transition_min_fit,
            "base_year": settings.base_year, "forecast_years": list(settings.forecast_years), "data_label": DEMO_LABEL}


@router.get("/dashboard")
def dashboard(request: Request, district_id: Optional[str] = None, industry_id: Optional[str] = None,
              occupation_id: Optional[str] = None, skill_id: Optional[str] = None, year: int = YEAR):
    return clean(planning.dashboard(eng(request), district_id, industry_id, occupation_id, skill_id, year))


@router.get("/districts")
def districts(request: Request):
    return clean({"districts": eng(request).districts(), "data_label": DEMO_LABEL})


@router.get("/skills")
def skills(request: Request):
    return clean({"skills": eng(request).skills(), "data_label": DEMO_LABEL})


@router.get("/occupations")
def occupations(request: Request):
    e = eng(request)
    return clean({"occupations": e.occupations(), "competencies": e.competencies(), "data_label": DEMO_LABEL})


@router.get("/industries")
def industries(request: Request):
    return clean(planning.industries(eng(request)))


@router.get("/training-centres")
def training_centres(request: Request, district_id: Optional[str] = None, skill_id: Optional[str] = None):
    e = eng(request)
    df = e.t["training_centres"]
    if district_id:
        df = df[df.district_id == district_id]
    if skill_id:
        df = df[df.skills_offered.str.contains(skill_id, regex=False)]
    return clean({"training_centres": df.to_dict("records"), "count": len(df), "data_label": DEMO_LABEL})


@router.get("/skill-gap")
def skill_gap(request: Request, skill_id: str, year: int = YEAR, forecast_year: int = Query(2028, ge=2026, le=2028),
              shortage_threshold: Optional[float] = None, surplus_threshold: Optional[float] = None):
    return clean(eng(request).skill_gap_map(skill_id, year, forecast_year, th_from(shortage_threshold, surplus_threshold)))


@router.get("/skill-gap/district")
def skill_gap_district(request: Request, skill_id: str, district_id: str, year: int = YEAR,
                       forecast_year: int = Query(2028, ge=2026, le=2028), radius_km: float = Query(120, gt=0, le=1000),
                       shortage_threshold: Optional[float] = None, surplus_threshold: Optional[float] = None):
    return clean(eng(request).district_detail(skill_id, district_id, year, forecast_year,
                                              th_from(shortage_threshold, surplus_threshold), radius_km))


@router.get("/skill-gap/nearby-surplus")
def nearby_surplus(request: Request, skill_id: str, district_id: str, year: int = YEAR,
                   radius_km: Optional[float] = Query(None, gt=0, le=1000),
                   shortage_threshold: Optional[float] = None, surplus_threshold: Optional[float] = None):
    return clean(eng(request).nearby_surplus(skill_id, district_id, year,
                                             th_from(shortage_threshold, surplus_threshold), radius_km))


@router.get("/forecast")
def forecast(request: Request, skill_id: str, district_id: Optional[str] = None,
             shortage_threshold: Optional[float] = None, surplus_threshold: Optional[float] = None):
    return clean(eng(request).forecast_series(skill_id, district_id, th_from(shortage_threshold, surplus_threshold)))


@router.post("/transition", response_model=TransitionResponse)
def transition(request: Request, body: TransitionRequest):
    e = eng(request)
    return clean(analyze_transition(e.tax, body.current_occupation, body.target_occupation, body.current_skills))


@router.get("/transition/opportunities")
def transition_opportunities(request: Request):
    return clean({"opportunities": planning.transition_opportunities(eng(request)), "data_label": DEMO_LABEL})


@router.post("/nlp/extract-skills", response_model=ExtractSkillsResponse)
def extract_skills(request: Request, body: ExtractSkillsRequest):
    e = eng(request)
    return clean(run_pipeline(e.extractor, e.tax, body.text))


@router.get("/nlp/sample")
def nlp_sample(request: Request):
    e = eng(request)
    jobs = e.t["jobs"].sample(5, random_state=7)
    return clean({"primary_example": SAMPLE_JD,
                  "demo_job_descriptions": jobs[["job_id", "title", "description"]].to_dict("records")})


@router.post("/what-if", response_model=WhatIfResponse)
def what_if(request: Request, body: WhatIfRequest):
    return clean(planning.what_if(eng(request), body.skill_id, body.district_id, body.year,
                                  body.demand_growth_pct, body.capacity_change_pct))


@router.get("/early-warning")
def early_warning(request: Request, skill_id: Optional[str] = None, district_id: Optional[str] = None):
    return clean(planning.early_warning(eng(request), skill_id, district_id))


@router.get("/recommendations")
def recommendations(request: Request, year: int = Query(2027, ge=2026, le=2028), district_id: Optional[str] = None):
    return clean(planning.recommendations(eng(request), year, district_id))


@router.get("/data-sources")
def data_sources(request: Request):
    e = eng(request)
    cfg = load_source_config()
    return clean({
        "mode": "DEMO MODE", "message": "Using prototype/demo data. No official dataset is connected.",
        "database": request.app.state.db.describe(), "sources": cfg["sources"],
        "ingestion_log": e.ingestion_log, "data_label": DEMO_LABEL,
        "note": "Entries marked PROPOSED_NOT_CONNECTED are proposed official sources only. The prototype uses controlled demo data.",
    })


@router.get("/data/{table}")
def data_explorer(request: Request, table: str, search: str = "", sort_by: Optional[str] = None,
                  order: str = Query("asc", pattern="^(asc|desc)$"), page: int = Query(1, ge=1),
                  page_size: int = Query(25, ge=1, le=200), district_id: Optional[str] = None,
                  skill_id: Optional[str] = None, industry_id: Optional[str] = None, year: Optional[int] = None):
    filters = {"district_id": district_id, "skill_id": skill_id, "industry_id": industry_id,
               "year": None if year is None else str(year)}
    return clean(planning.explore(eng(request), table, search, sort_by, order, page, page_size, filters))
