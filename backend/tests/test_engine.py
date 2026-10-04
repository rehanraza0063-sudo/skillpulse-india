"""Engine tests. They encode the demo storyline so that regenerating the data cannot silently break the demo.
Run:  cd backend && python -m pytest -q      (or: python tests/run_all.py)"""
from app.ml.forecast import linear_forecast
from app.ml.nlp import run_pipeline
from app.ml.transition import analyze_transition
from app.services import planning as P
from app.services.engine import Thresholds

from helpers import get_engine

TH = Thresholds()
EV, PUNE, NASHIK = "S01", "D04", "D05"


def test_data_is_tagged_demo():
    e = get_engine()
    for name, df in e.t.items():
        assert (df["source_type"] == "DEMO").all(), name


def test_forecast_linear_and_interval():
    pts, info = linear_forecast([2023, 2024, 2025, 2026], [100, 200, 300, 400], [2027, 2028])
    assert round(pts[0].value) == 500 and round(pts[1].value) == 600
    assert pts[0].lower <= pts[0].value <= pts[0].upper
    assert info["label"] == "Prototype Forecast" and info["n_observations"] == 4
    assert pts[0].confidence <= 0.95


def test_pune_ev_shortage_and_nashik_surplus():
    e = get_engine()
    m = {d["district_id"]: d for d in e.skill_gap_map(EV, 2026, 2028, TH)["districts"]}
    assert m[PUNE]["demand"] == 1000 and m[PUNE]["capacity"] == 700
    assert m[PUNE]["status"] == "SHORTAGE" and m[PUNE]["gap"] == 300
    assert m[NASHIK]["status"] == "SURPLUS"


def test_nearest_surplus_for_pune_is_nashik():
    e = get_engine()
    r = e.nearby_surplus(EV, PUNE, 2026, TH)
    assert r["candidates"][0]["district_name"] == "Nashik"
    assert r["candidates"][0]["surplus_seats"] == 240
    assert r["candidates"] == sorted(r["candidates"], key=lambda c: c["distance_km"])


def test_thresholds_are_configurable():
    e = get_engine()
    loose = e.skill_gap_map(EV, 2026, 2028, Thresholds(shortage=0.5, surplus=-0.9))
    pune = next(d for d in loose["districts"] if d["district_id"] == PUNE)
    assert pune["status"] == "BALANCED"


def test_early_warning_ev_low_growing_critical():
    e = get_engine()
    ew = P.early_warning(e, EV)
    assert [t["status"] for t in ew["skills"][0]["timeline"]] == ["LOW", "GROWING", "CRITICAL"]
    assert ew["label"] == "Prototype Early Warning"


def test_what_if_matches_spec_example():
    e = get_engine()
    r = P.what_if(e, EV, PUNE, 2026, 20, 0)
    assert r["before"]["demand"] == 1000 and r["before"]["capacity"] == 700
    assert round(r["after"]["demand"]) == 1200 and round(r["after"]["gap"]) == 500
    r2 = P.what_if(e, EV, PUNE, 2026, 20, 30)
    assert r2["after"]["gap"] < r["after"]["gap"]
    assert r2["after"]["capacity"] == 910
    assert [s["id"] for s in r["scenarios"]] == ["A", "B", "C", "D"]
    assert P.what_if(e, EV, PUNE, 2026, -15, 0)["after"]["gap"] < r["before"]["gap"]


def test_transition_ice_to_ev():
    e = get_engine()
    r = analyze_transition(e.tax, "ICE Technician", "EV Technician")
    assert set(r["matched_skills"]) == {"Electrical Systems", "Vehicle Diagnostics", "Workplace Safety"}
    assert {"High Voltage Safety", "Battery Systems", "Battery Management System", "High Voltage Diagnostics"} == set(r["missing_skills"])
    assert r["basic_overlap_pct"] == round(100 * 3 / 7, 1)
    assert 0 < r["fit_score"] < 100 and r["skill_distance"] == round(100 - r["fit_score"], 1)
    assert r["pathway"] == ["ICE Technician", "EV Bridge Training (ICE to EV)", "EV Technician"]
    # fit with itself is perfect
    assert analyze_transition(e.tax, "EV Technician", "EV Technician")["fit_score"] == 100.0


def test_transition_custom_skills_change_score():
    e = get_engine()
    base = analyze_transition(e.tax, "ICE Technician", "EV Technician")["fit_score"]
    more = analyze_transition(e.tax, "ICE Technician", "EV Technician",
                              ["Electrical Systems", "Vehicle Diagnostics", "Workplace Safety", "Battery Systems"])["fit_score"]
    assert more > base


def test_nlp_extraction_and_mapping():
    e = get_engine()
    text = ("Looking for an EV technician with experience in battery management systems, vehicle diagnostics, "
            "electrical systems and high-voltage safety.")
    r = run_pipeline(e.extractor, e.tax, text)
    assert set(r["normalized_skills"]) == {"Battery Management System", "Vehicle Diagnostics", "Electrical Systems", "High Voltage Safety"}
    assert r["best_occupation"] == "EV Technician"
    # alias normalisation
    r2 = run_pipeline(e.extractor, e.tax, "Needs BMS and electric vehicle diagnostics")
    assert "Battery Management System" in r2["normalized_skills"] and "Vehicle Diagnostics" in r2["normalized_skills"]
    # honesty: the method is described as rule-based
    assert "not an ML/LLM" in r["explainability"]["limitations"]


def test_industries_radar_labels():
    e = get_engine()
    inds = {i["industry_name"]: i for i in P.industries(e)["industries"]}
    assert inds["Traditional ICE Automotive"]["computed_trend"] == "DECLINING"
    assert inds["EV / Battery"]["computed_trend"] == "GROWING"
    assert inds["Traditional ICE Automotive"]["transition_pathways"]


def test_dashboard_filters_change_values():
    e = get_engine()
    all_ = P.dashboard(e)
    pune = P.dashboard(e, district_id=PUNE)
    assert all_["kpis"]["districts_covered"] == 10 and pune["kpis"]["districts_covered"] == 1
    assert sum(r["demand"] for r in pune["demand_vs_capacity"]) < sum(r["demand"] for r in all_["demand_vs_capacity"])
    assert P.dashboard(e, skill_id=EV)["kpis"]["skills_tracked"] == 1
    assert P.dashboard(e, industry_id="I01", skill_id="S03")["empty"] is True


def test_recommendations_contain_balancing_text():
    e = get_engine()
    r = P.recommendations(e, 2027)
    texts = [x["text"] for x in r["recommendations"]]
    assert ("Potential geographic balancing opportunity: Pune has a prototype shortage while nearby Nashik "
            "has available training capacity.") in texts
    assert all(x["label"] == "Prototype Decision Support" for x in r["recommendations"])
    types = {x["type"] for x in r["recommendations"]}
    assert {"Increase training seats", "Introduce bridge training", "Investigate declining occupations"} <= types


def test_data_explorer_search_sort_filter():
    e = get_engine()
    r = P.explore(e, "jobs", search="battery", sort_by="openings", order="desc", page_size=5)
    assert r["total"] > 0 and len(r["rows"]) <= 5
    opens = [x["openings"] for x in r["rows"]]
    assert opens == sorted(opens, reverse=True)
    r = P.explore(e, "historical_demand", filters={"skill_id": EV, "year": "2026", "district_id": PUNE})
    assert r["total"] == 1 and r["rows"][0]["demand"] == 1000
    try:
        P.explore(e, "nope")
        assert False
    except KeyError:
        pass
