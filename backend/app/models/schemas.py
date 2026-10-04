"""Pydantic request / response models. Response models allow extra fields so the full explainability
payload (method, inputs, output, limitations, calculation strings) is always returned."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TransitionRequest(BaseModel):
    current_occupation: str = Field(..., examples=["ICE Technician"])
    target_occupation: str = Field(..., examples=["EV Technician"])
    current_skills: Optional[List[str]] = Field(
        None, description="Optional custom list of the worker's canonical skills. Defaults to the current occupation's skills.")


class ExtractSkillsRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=5000, examples=[
        "Looking for an EV technician with experience in battery management systems, vehicle diagnostics, "
        "electrical systems and high-voltage safety."])


class WhatIfRequest(BaseModel):
    skill_id: str = Field(..., examples=["S01"])
    district_id: Optional[str] = Field(None, examples=["D04"], description="Omit for all demo districts")
    year: int = Field(2026, ge=2023, le=2028)
    demand_growth_pct: float = Field(0.0, ge=-90, le=300)
    capacity_change_pct: float = Field(0.0, ge=-90, le=300)


class Explainability(BaseModel):
    model_config = ConfigDict(extra="allow")
    method: str
    inputs: str
    output: str
    limitations: str


class TransitionResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    current_occupation: str
    target_occupation: str
    fit_score: float
    fit_band: str
    basic_overlap_pct: float
    skill_distance: float
    matched_skills: List[str]
    partial_skills: List[str]
    missing_skills: List[str]
    pathway: List[str]
    calculation: Dict[str, Any]
    explainability: Explainability


class ExtractSkillsResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    normalized_skills: List[str]
    best_occupation: Optional[str]
    stages: List[Dict[str, str]]
    explainability: Explainability


class ScenarioResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    demand: float
    capacity: float
    gap: float
    status: str
    calculation: str


class WhatIfResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    skill_name: str
    district_name: str
    year: int
    before: ScenarioResult
    after: ScenarioResult
    gap_change: float
    explainability: Explainability


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
