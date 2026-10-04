"""
Planning layer built on the Engine: dashboard, industries / transition radar, early warning,
what-if scenarios, recommendations, data explorer. All outputs are PROTOTYPE decision support on DEMO data.
"""
from typing import Dict, List, Optional

import pandas as pd

from ..config import DEMO_LABEL, settings
from ..ml.forecast import confidence_label
from ..ml.transition import analyze_transition
from ..utils.geo import haversine_km
from .engine import Engine, Thresholds, ew_status

EW_YEARS = [2026, 2027, 2028]
LABEL_RECS = "Prototype Decision Support"
LABEL_EW = "Prototype Early Warning"


# ---------------------------------------------------------------------------- transitions
def transition_opportunities(e: Engine) -> List[dict]:
    """Declining-industry occupations -> occupations in growing industries, scored by Transfer Fit."""
    ind = e.t["industries"].set_index("industry_id")
    declining = [o for o, i in e.occ_industry.items() if ind.loc[i, "future_outlook"] == "DECLINING"]
    growing = [o for o, i in e.occ_industry.items() if ind.loc[i, "future_outlook"] == "GROWING"]
    th = Thresholds()
    out = []
    for src in declining:
        for dst in growing:
            r = analyze_transition(e.tax, src, dst)
            st = e.with_gap(e.aggregate(2027, [], None, [e.occ_skill[dst]]), th).iloc[0]
            out.append({
                "from_occupation": src, "from_industry": e.iname[e.occ_industry[src]],
                "to_occupation": dst, "to_industry": e.iname[e.occ_industry[dst]],
                "fit_score": r["fit_score"], "fit_band": r["fit_band"],
                "matched_skills": r["matched_skills"], "partial_skills": r["partial_skills"],
                "missing_skills": r["missing_skills"], "bridge_programme": r["bridge_training"]["name"],
                "bridge_weeks": r["bridge_training"]["duration_weeks"],
                "target_skill_id": e.occ_skill[dst], "target_status_2027": st.status,
                "is_opportunity": r["fit_score"] >= settings.transition_min_fit,
            })
    out.sort(key=lambda o: -o["fit_score"])
    return out


# ---------------------------------------------------------------------------- industries
def _cagr(a: float, b: float, years: int) -> float:
    if a <= 0 or years <= 0:
        return 0.0
    return (b / a) ** (1.0 / years) - 1.0


def industries(e: Engine) -> dict:
    th = Thresholds()
    opps = transition_opportunities(e)
    rows = []
    for r in e.t["industries"].itertuples():
        sids = [s for s, i in e.sindustry.items() if i == r.industry_id]
        d = {y: float(e.aggregate(y, [], None, sids).demand.iloc[0]) for y in [2023, 2026, 2028]}
        cap26 = float(e.aggregate(2026, [], None, sids).capacity.iloc[0])
        hist = _cagr(d[2023], d[2026], 3)
        fc = _cagr(d[2026], d[2028], 2)
        trend = "GROWING" if fc > settings.industry_growing_cagr else (
            "DECLINING" if fc < settings.industry_declining_cagr else "STABLE")
        occs = [o for o, i in e.occ_industry.items() if i == r.industry_id]
        skill_w: Dict[str, int] = {}
        for o in occs:
            for c, w in e.tax.requirements[o].items():
                skill_w[c] = max(skill_w.get(c, 0), w)
        req = sorted(skill_w.items(), key=lambda kv: (-kv[1], kv[0]))
        tracks = []
        for s in sids:
            g = e.with_gap(e.aggregate(2027, [], None, [s]), th).iloc[0]
            tracks.append({"skill_id": s, "skill_name": e.sname[s], "demand_2027": g.demand,
                           "capacity_2027": g.capacity, "status_2027": g.status})
        paths = []
        if r.future_outlook == "DECLINING":
            paths = [o for o in opps if o["from_industry"] == r.industry_name][:4]
        rows.append({
            "industry_id": r.industry_id, "industry_name": r.industry_name,
            "current_outlook": r.current_outlook, "future_outlook": r.future_outlook,
            "signal_score": r.signal_score, "signal_note": r.signal_note,
            "demand_2023": d[2023], "demand_2026": d[2026], "demand_2028_forecast": d[2028],
            "capacity_2026": cap26,
            "hist_cagr_pct": round(hist * 100, 1), "forecast_cagr_pct": round(fc * 100, 1),
            "computed_trend": trend,
            "required_skills": [{"competency": c, "weight": w} for c, w in req[:10]],
            "related_occupations": occs, "skill_tracks": tracks, "transition_pathways": paths,
            "source_type": r.source_type,
        })
    return {"industries": rows, "opportunities": opps,
            "trend_rule": (f"computed_trend = GROWING if forecast CAGR 2026-2028 > {settings.industry_growing_cagr * 100:.0f}%, "
                           f"DECLINING if < {settings.industry_declining_cagr * 100:.0f}%, else STABLE"),
            "data_label": DEMO_LABEL, "forecast_label": "Prototype Forecast"}


# ---------------------------------------------------------------------------- early warning
def early_warning(e: Engine, skill_id: Optional[str] = None, district_id: Optional[str] = None) -> dict:
    d_ids = [district_id] if district_id else None
    sids = [skill_id] if skill_id else list(e.t["skills"].skill_id)
    for s in sids:
        if s not in e.sname:
            raise KeyError(f"Unknown skill_id: {s}")
    if district_id and district_id not in e.dname:
        raise KeyError(f"Unknown district_id: {district_id}")
    th = Thresholds()
    skills, cards = [], []
    for s in sids:
        tl = []
        for y in EW_YEARS:
            a = e.with_gap(e.aggregate(y, [], d_ids, [s]), th).iloc[0]
            tl.append({"year": y, "demand": a.demand, "capacity": a.capacity, "gap": a.gap, "gap_ratio": a.gap_ratio,
                       "status": a.ew_status, "is_forecast": y > settings.base_year,
                       "confidence_label": "OBSERVED (demo)" if y <= settings.base_year else confidence_label(a.conf),
                       "calculation": e.calc_text(a.demand, a.capacity, th)})
        d26, d28 = tl[0]["demand"], tl[-1]["demand"]
        cagr = _cagr(d26, d28, 2)
        skills.append({"skill_id": s, "skill_name": e.sname[s], "industry_name": e.iname[e.sindustry[s]],
                       "timeline": tl, "demand_cagr_pct": round(cagr * 100, 1)})
        st = [t["status"] for t in tl]
        name = e.sname[s]
        if st[1] != "LOW" or st[2] != "LOW":
            cards.append({"skill_id": s, "skill_name": name, "type": "Potential future shortage",
                          "severity": "CRITICAL" if st[2] == "CRITICAL" else "GROWING",
                          "message": f"{name}: forecast demand is projected to exceed training capacity by {tl[-1]['gap']:,.0f} seats in 2028 (prototype classification: {st[2]}).",
                          "statuses": st})
        if st[2] == "CRITICAL":
            cards.append({"skill_id": s, "skill_name": name, "type": "Training capacity may need attention",
                          "severity": "CRITICAL",
                          "message": f"{name}: capacity covers only {100 * tl[-1]['capacity'] / max(tl[-1]['demand'], 1):.0f}% of 2028 forecast demand if no new seats are added.",
                          "statuses": st})
        if cagr >= 0.10:
            cards.append({"skill_id": s, "skill_name": name, "type": "Growing demand detected",
                          "severity": "GROWING",
                          "message": f"{name}: forecast demand grows about {cagr * 100:.0f}% per year between 2026 and 2028.",
                          "statuses": st})
    order = {"CRITICAL": 0, "GROWING": 1}
    cards.sort(key=lambda c: (order.get(c["severity"], 2), c["skill_name"]))
    skills.sort(key=lambda s: (-["LOW", "GROWING", "CRITICAL"].index(s["timeline"][-1]["status"]),
                               -s["timeline"][-1]["gap_ratio"]))
    return {
        "label": LABEL_EW, "skills": skills, "cards": cards,
        "district_name": e.dname.get(district_id, "Maharashtra (all demo districts)"),
        "rule": (f"Prototype classification on gap ratio = (forecast demand - capacity) / forecast demand: "
                 f"LOW <= {settings.ew_low_max * 100:.0f}%, GROWING <= {settings.ew_growing_max * 100:.0f}%, "
                 f"CRITICAL above. 'Critical' is a prototype label, not an official designation."),
        "explainability": {
            "method": "Linear-trend forecast of demand compared with training capacity held at the 2026 level",
            "inputs": "Historical demand 2023-2026 (demo), training capacity 2026 (demo), configurable thresholds",
            "output": "LOW / GROWING / CRITICAL status per year 2026-2028",
            "limitations": "Four demo data points; assumes no new capacity; requires validation with official datasets.",
        },
        "data_label": DEMO_LABEL, "forecast_label": "Prototype Forecast",
    }


# ---------------------------------------------------------------------------- what-if
PRESETS = [
    ("A", "Demand increases", 20.0, 0.0),
    ("B", "Training capacity increases", 0.0, 30.0),
    ("C", "Demand increases + training capacity increases", 20.0, 30.0),
    ("D", "Demand decreases", -15.0, 0.0),
]


def _scenario(demand: float, capacity: float, g: float, c: float, th: Thresholds) -> dict:
    d2, c2 = demand * (1 + g / 100.0), capacity * (1 + c / 100.0)
    gap = d2 - capacity * (1 + c / 100.0)
    ratio = gap / d2 if d2 else 0.0
    return {"demand": d2, "capacity": c2, "gap": gap, "gap_ratio": ratio, "status": th.classify(ratio),
            "calculation": (f"New demand = {demand:,.0f} x (1 + {g:g}%) = {d2:,.0f}; "
                            f"new capacity = {capacity:,.0f} x (1 + {c:g}%) = {c2:,.0f}; "
                            f"gap = {d2:,.0f} - {c2:,.0f} = {gap:,.0f}")}


def what_if(e: Engine, skill_id: str, district_id: Optional[str], year: int,
            demand_growth_pct: float, capacity_change_pct: float) -> dict:
    if skill_id not in e.sname:
        raise KeyError(f"Unknown skill_id: {skill_id}")
    if district_id and district_id not in e.dname:
        raise KeyError(f"Unknown district_id: {district_id}")
    th = Thresholds()
    d_ids = [district_id] if district_id else None
    base = e.aggregate(year, [], d_ids, [skill_id]).iloc[0]
    D, C = float(base.demand), float(base.capacity)
    before = _scenario(D, C, 0.0, 0.0, th)
    after = _scenario(D, C, demand_growth_pct, capacity_change_pct, th)
    years = []
    for y in [2026, 2027, 2028]:
        b = e.aggregate(y, [], d_ids, [skill_id]).iloc[0]
        bs = _scenario(float(b.demand), float(b.capacity), 0.0, 0.0, th)
        asx = _scenario(float(b.demand), float(b.capacity), demand_growth_pct, capacity_change_pct, th)
        years.append({"year": y, "before_demand": bs["demand"], "before_capacity": bs["capacity"], "before_gap": bs["gap"],
                      "after_demand": asx["demand"], "after_capacity": asx["capacity"], "after_gap": asx["gap"],
                      "after_status": asx["status"]})
    scenarios = []
    for sid, name, g, c in PRESETS:
        s = _scenario(D, C, g, c, th)
        scenarios.append({"id": sid, "name": name, "demand_growth_pct": g, "capacity_change_pct": c, **s,
                          "gap_change": s["gap"] - before["gap"]})
    return {
        "skill_id": skill_id, "skill_name": e.sname[skill_id], "district_id": district_id,
        "district_name": e.dname.get(district_id, "Maharashtra (all demo districts)"), "year": year,
        "is_forecast_year": year > settings.base_year,
        "inputs": {"demand_growth_pct": demand_growth_pct, "capacity_change_pct": capacity_change_pct},
        "before": before, "after": after, "gap_change": after["gap"] - before["gap"],
        "years": years, "scenarios": scenarios, "thresholds": th.as_dict(),
        "explainability": {
            "method": "Deterministic what-if arithmetic on the baseline (forecast) demand and training capacity",
            "inputs": "Baseline demand and capacity for the chosen skill / district / year plus % changes set by the planner",
            "output": "Scenario demand, capacity, gap and prototype status; preset scenarios A-D for comparison",
            "limitations": "Applies a flat % shift; ignores second-order effects (migration, enrolment lag, drop-outs). Illustrative only.",
        },
        "data_label": DEMO_LABEL,
    }


# ---------------------------------------------------------------------------- recommendations
def recommendations(e: Engine, year: int = 2027, district_id: Optional[str] = None) -> dict:
    th = Thresholds()
    recs: List[dict] = []
    skills = list(e.t["skills"].skill_id)
    state = e.with_gap(e.aggregate(year, ["skill_id"]), th).set_index("skill_id")
    prev = e.aggregate(settings.base_year, ["skill_id"]).set_index("skill_id")

    # 1. Geographic balancing
    geo = []
    for s in skills:
        dg = e.with_gap(e.aggregate(year, ["district_id"], None, [s]), th).set_index("district_id")
        for d, row in dg.iterrows():
            if row.status != "SHORTAGE" or row.gap < settings.min_balancing_seats:
                continue
            if district_id and d != district_id:
                continue
            lat, lon = e.dcoord[d]
            best = None
            for d2, r2 in dg.iterrows():
                if d2 == d or r2.status != "SURPLUS":
                    continue
                dist = haversine_km(lat, lon, *e.dcoord[d2])
                if dist <= settings.nearby_radius_km and (best is None or dist < best[1]):
                    best = (d2, dist, float(r2.capacity - r2.demand))
            if best:
                geo.append((float(row.gap), s, d, best))
    geo.sort(key=lambda g: -g[0])
    for gap, s, d, (d2, dist, surplus) in geo[:8]:
        recs.append({
            "type": "Geographic balancing", "priority": "HIGH" if gap >= 200 else "MEDIUM",
            "title": f"{e.sname[s]}: {e.dname[d]} <- {e.dname[d2]}",
            "text": (f"Potential geographic balancing opportunity: {e.dname[d]} has a prototype shortage while nearby "
                     f"{e.dname[d2]} has available training capacity."),
            "evidence": {"skill": e.sname[s], "shortage_district": e.dname[d], "shortage_seats": gap,
                         "surplus_district": e.dname[d2], "surplus_seats": surplus, "distance_km": round(dist, 1),
                         "year": year},
            "skill_id": s, "district_id": d})

    # 2. Increase training seats (statewide)
    for s in skills:
        r = state.loc[s]
        ews = ew_status(r.gap_ratio)
        if ews in ("GROWING", "CRITICAL") and not district_id:
            recs.append({
                "type": "Increase training seats", "priority": "HIGH" if ews == "CRITICAL" else "MEDIUM",
                "title": f"Consider adding seats for {e.sname[s]}",
                "text": (f"Consider increasing training seats for {e.sname[s]} by about {r.gap:,.0f} "
                         f"({r.gap_ratio * 100:.0f}% of {year} forecast demand) if no capacity is added elsewhere."),
                "evidence": {"skill": e.sname[s], "forecast_demand": r.demand, "capacity": r.capacity, "gap": r.gap,
                             "gap_ratio_pct": round(r.gap_ratio * 100, 1), "early_warning": ews, "year": year},
                "skill_id": s})

    # 3. Redirect capacity from falling-demand skills + 5. curriculum review
    for s in skills:
        r = state.loc[s]
        p = prev.loc[s]
        if r.status == "SURPLUS" and r.demand < p.demand:
            surplus = float(r.capacity - r.demand)
            recs.append({
                "type": "Redirect training capacity", "priority": "MEDIUM",
                "title": f"Redirect seats away from {e.sname[s]}",
                "text": (f"{e.sname[s]} shows about {surplus:,.0f} surplus seats and falling forecast demand; "
                         f"consider redirecting part of this capacity to skills with a prototype shortage."),
                "evidence": {"skill": e.sname[s], "forecast_demand": r.demand, "capacity": r.capacity,
                             "surplus_seats": surplus, "demand_change_vs_2026_pct": round((r.demand / p.demand - 1) * 100, 1)},
                "skill_id": s})
            recs.append({
                "type": "Review curriculum", "priority": "LOW",
                "title": f"Review curriculum: {e.sname[s]}",
                "text": f"Review the {e.sname[s]} curriculum for content that could be updated or bridged toward growing occupations.",
                "evidence": {"skill": e.sname[s], "status": r.status}, "skill_id": s})

    # 4. Bridge training
    opps = [o for o in transition_opportunities(e) if o["is_opportunity"] and o["target_status_2027"] != "SURPLUS"]
    for o in sorted(opps, key=lambda o: -o["fit_score"])[:5]:
        recs.append({
            "type": "Introduce bridge training", "priority": "HIGH" if o["target_status_2027"] == "SHORTAGE" else "MEDIUM",
            "title": f"Bridge: {o['from_occupation']} -> {o['to_occupation']}",
            "text": (f"Introduce bridge training for {o['from_occupation']} workers moving to {o['to_occupation']} "
                     f"(prototype fit {o['fit_score']:.0f}%, about {o['bridge_weeks']} weeks)."),
            "evidence": {"fit_score": o["fit_score"], "missing_skills": o["missing_skills"],
                         "target_status_2027": o["target_status_2027"], "programme": o["bridge_programme"]},
            "skill_id": o["target_skill_id"]})

    # 6. Monitor emerging skills
    for s in skills:
        hist = e.aggregate(2023, [], None, [s]).demand.iloc[0]
        now = e.aggregate(2026, [], None, [s]).demand.iloc[0]
        c = _cagr(float(hist), float(now), 3)
        if c >= 0.15 and now < 4000 and e.sindustry[s] not in ("I01",):
            recs.append({
                "type": "Monitor emerging skills", "priority": "LOW",
                "title": f"Monitor {e.sname[s]}",
                "text": f"{e.sname[s]} is a smaller but fast-growing skill (about {c * 100:.0f}% per year in the demo history); monitor it as new data arrives.",
                "evidence": {"skill": e.sname[s], "hist_cagr_pct": round(c * 100, 1), "demand_2026": float(now)},
                "skill_id": s})

    # 7. Investigate declining occupations
    for s in skills:
        r, p = state.loc[s], prev.loc[s]
        change = r.demand / p.demand - 1 if p.demand else 0
        if change <= -0.08:
            occs = [o for o, sk in e.occ_skill.items() if sk == s]
            recs.append({
                "type": "Investigate declining occupations", "priority": "MEDIUM",
                "title": f"Investigate: {', '.join(occs)}",
                "text": (f"Investigate declining occupations in {e.sname[s]}: forecast demand falls about "
                         f"{abs(change) * 100:.0f}% between 2026 and {year}."),
                "evidence": {"occupations": occs, "demand_2026": p.demand, "forecast_demand": r.demand},
                "skill_id": s})

    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recs.sort(key=lambda r: (order[r["priority"]], r["type"]))
    for i, r in enumerate(recs, 1):
        r["id"] = f"R{i:02d}"
        r["label"] = LABEL_RECS
    return {
        "label": LABEL_RECS, "year": year, "count": len(recs), "recommendations": recs,
        "disclaimer": ("Prototype Decision Support generated by rules over demo data. These are not automatic government "
                       "decisions or official recommendations and require validation with official datasets."),
        "explainability": {
            "method": "Rule-based engine over gap, forecast, nearby-surplus and transition-fit results",
            "inputs": "Skill-gap table for the chosen year, distances between demo districts, transition fit scores",
            "output": "Prioritised planning suggestions with supporting evidence",
            "limitations": "Rules and thresholds are illustrative; priorities are not validated.",
        },
        "data_label": DEMO_LABEL,
    }


# ---------------------------------------------------------------------------- dashboard
def dashboard(e: Engine, district_id=None, industry_id=None, occupation_id=None, skill_id=None, year: int = 2026) -> dict:
    th = Thresholds()
    sids = e.resolve_skills(industry_id, occupation_id, skill_id)
    d_ids = [district_id] if district_id else None
    if district_id and district_id not in e.dname:
        raise KeyError(f"Unknown district_id: {district_id}")
    empty = len(sids) == 0
    meta = {"pilot": "Maharashtra Pilot", "dataset": "Demo Dataset", "mode": "DEMO MODE",
            "mode_note": "Using prototype/demo data", "data_label": DEMO_LABEL,
            "last_updated": e.last_updated, "year": year, "is_forecast_year": year > settings.base_year}
    if empty:
        return {"meta": meta, "empty": True, "message": "No skills match the selected filters."}

    by_skill = e.with_gap(e.aggregate(year, ["skill_id"], d_ids, sids), th)
    by_skill["skill_name"] = by_skill.skill_id.map(e.sname)
    by_skill["industry_name"] = by_skill.skill_id.map(lambda s: e.iname[e.sindustry[s]])
    conf = float(e.aggregate(max(year, 2027), [], d_ids, sids).conf.iloc[0])
    meta["data_confidence"] = {"label": confidence_label(conf), "score": round(conf, 2),
                               "note": "Prototype model confidence on demo data; not a measure of real-world accuracy"}

    ind_all = industries(e)
    ind_rows = [i for i in ind_all["industries"] if any(e.sindustry[s] == i["industry_id"] for s in sids)]
    # filtered (district-aware) industry growth
    ind_chart = []
    for i in ind_rows:
        isids = [s for s in sids if e.sindustry[s] == i["industry_id"]]
        d23 = float(e.aggregate(2023, [], d_ids, isids).demand.iloc[0])
        d26 = float(e.aggregate(2026, [], d_ids, isids).demand.iloc[0])
        d28 = float(e.aggregate(2028, [], d_ids, isids).demand.iloc[0])
        fc = _cagr(d26, d28, 2)
        trend = "GROWING" if fc > settings.industry_growing_cagr else ("DECLINING" if fc < settings.industry_declining_cagr else "STABLE")
        ind_chart.append({"industry_id": i["industry_id"], "industry_name": i["industry_name"],
                          "hist_cagr_pct": round(_cagr(d23, d26, 3) * 100, 1), "forecast_cagr_pct": round(fc * 100, 1),
                          "trend": trend, "signal_outlook": i["future_outlook"]})

    opps = transition_opportunities(e)
    tgt = {e.occ_skill[o["to_occupation"]] for o in opps}
    n_opps = sum(1 for o in opps if o["is_opportunity"] and o["target_skill_id"] in sids)

    trend = []
    for y in range(2023, 2029):
        a = e.aggregate(y, [], d_ids, sids).iloc[0]
        trend.append({"year": y, "demand": a.demand, "lower": a.lo, "upper": a.hi, "capacity": a.capacity,
                      "is_forecast": y > settings.base_year})

    shortages = by_skill[by_skill.status == "SHORTAGE"].sort_values("gap", ascending=False).head(5)
    surplus = by_skill[by_skill.status == "SURPLUS"].assign(surplus=lambda d: -d.gap).sort_values("surplus", ascending=False).head(5)

    ew = early_warning(e, None, district_id)["skills"]
    ew = [s for s in ew if s["skill_id"] in sids][:6]

    cols = ["skill_id", "skill_name", "industry_name", "demand", "capacity", "gap", "gap_ratio", "status"]
    return {
        "meta": meta, "empty": False, "thresholds": th.as_dict(),
        "kpis": {
            "districts_covered": len(d_ids) if d_ids else len(e.dname),
            "skills_tracked": len(sids),
            "shortage_skills": int((by_skill.status == "SHORTAGE").sum()),
            "surplus_skills": int((by_skill.status == "SURPLUS").sum()),
            "growing_industries": sum(1 for i in ind_chart if i["trend"] == "GROWING"),
            "transition_opportunities": n_opps,
        },
        "demand_vs_capacity": by_skill[cols].to_dict("records"),
        "top_shortages": shortages[cols].to_dict("records"),
        "top_surplus": surplus[cols + ["surplus"]].to_dict("records"),
        "future_trend": trend,
        "industry_growth": ind_chart,
        "early_warning": [{"skill_id": s["skill_id"], "skill_name": s["skill_name"],
                           "statuses": {str(t["year"]): t["status"] for t in s["timeline"]},
                           "gap_ratio_2028": s["timeline"][-1]["gap_ratio"]} for s in ew],
        "forecast_label": "Prototype Forecast",
    }


# ---------------------------------------------------------------------------- data explorer
EXPLORE_TABLES = ["jobs", "training_centres", "skills", "occupations", "industries", "districts",
                  "historical_demand", "training_capacity"]


def explore(e: Engine, table: str, search: str = "", sort_by: Optional[str] = None, order: str = "asc",
            page: int = 1, page_size: int = 25, filters: Optional[Dict[str, str]] = None) -> dict:
    if table not in EXPLORE_TABLES:
        raise KeyError(f"Unknown table: {table}. Available: {', '.join(EXPLORE_TABLES)}")
    df = e.t[table].copy()
    if table in ("historical_demand", "training_capacity"):
        df.insert(1, "district_name", df.district_id.map(e.dname))
        df.insert(3, "skill_name", df.skill_id.map(e.sname))
    for col, val in (filters or {}).items():
        if col in df.columns and val not in (None, ""):
            df = df[df[col].astype(str) == str(val)]
    if search:
        s = search.lower()
        mask = pd.Series(False, index=df.index)
        for c in df.columns:
            mask |= df[c].astype(str).str.lower().str.contains(s, regex=False, na=False)
        df = df[mask]
    if sort_by:
        if sort_by not in df.columns:
            raise KeyError(f"Unknown column: {sort_by}")
        df = df.sort_values(sort_by, ascending=(order != "desc"), kind="stable")
    total = len(df)
    page_size = max(1, min(page_size, 200))
    page = max(1, page)
    chunk = df.iloc[(page - 1) * page_size: page * page_size]
    return {"table": table, "columns": list(df.columns), "total": total, "page": page, "page_size": page_size,
            "rows": chunk.to_dict("records"), "source_note": "Every row carries source_type; DEMO means fictional prototype data.",
            "data_label": DEMO_LABEL}
