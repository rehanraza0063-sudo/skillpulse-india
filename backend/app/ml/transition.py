"""
Workforce Transition Engine (prototype).

Transfer Fit Score (weighted, with partial credit):

    credit(skill) = 1.0                         if the worker already has the target skill
                  = max similarity(skill, held) if a related skill is held (partial credit, 0..1)
                  = 0                           otherwise
    fit = 100 * sum(weight * credit) / sum(weight)          (weight = importance 1..3 in the target occupation)

Also reported: the basic overlap  matched / target x 100  and skill distance = 100 - fit.

It is a prototype similarity measure based on skill overlap. It does NOT represent guaranteed employability.
"""
from typing import Dict, List, Optional

from .taxonomy import Taxonomy

HOURS_PER_WEEK = 20  # assumed part-time bridge-course intensity (illustrative)


def fit_band(score: float) -> str:
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MODERATE"
    return "LOW"


def analyze_transition(tax: Taxonomy, current_occupation: str, target_occupation: str,
                       current_skills: Optional[List[str]] = None) -> Dict:
    if target_occupation not in tax.requirements:
        raise KeyError(f"Unknown target occupation: {target_occupation}")
    if current_skills is None:
        if current_occupation not in tax.requirements:
            raise KeyError(f"Unknown current occupation: {current_occupation}")
        held = list(tax.requirements[current_occupation].keys())
    else:
        unknown = [s for s in current_skills if s not in tax.competencies]
        if unknown:
            raise KeyError(f"Unknown skills: {', '.join(unknown)}")
        held = list(current_skills)
    held_set = set(held)

    reqs = tax.requirements[target_occupation]
    total_w = sum(reqs.values())
    rows, matched, partial, missing = [], [], [], []
    earned = 0.0
    bridge_hours = 0.0
    for comp, w in reqs.items():
        if comp in held_set:
            credit, status, source = 1.0, "MATCHED", comp
            matched.append(comp)
        else:
            best, source = 0.0, None
            for h in held:
                s = tax.sim(comp, h)
                if s > best:
                    best, source = s, h
            credit = best
            if credit > 0:
                status = "PARTIAL"
                partial.append(comp)
            else:
                status = "MISSING"
            missing.append(comp)
            bridge_hours += tax.bridge_hours(comp) * (1 - credit)
        earned += w * credit
        rows.append({
            "competency": comp, "weight": w, "status": status, "credit": round(credit, 2),
            "weighted_credit": round(w * credit, 2), "related_skill_used": source if status == "PARTIAL" else None,
            "bridge_hours": 0 if status == "MATCHED" else round(tax.bridge_hours(comp) * (1 - credit)),
        })

    fit = 100.0 * earned / total_w if total_w else 0.0
    basic = 100.0 * len(matched) / len(reqs) if reqs else 0.0

    programme = next((p for p in tax.bridge_programmes
                      if p["from_occupation"] == current_occupation and p["to_occupation"] == target_occupation), None)
    if programme:
        bp = {**programme, "source": "Illustrative catalogue programme"}
    else:
        bp = {
            "programme_id": None,
            "name": f"Custom Bridge Training ({current_occupation} to {target_occupation})",
            "from_occupation": current_occupation, "to_occupation": target_occupation,
            "duration_weeks": max(1, round(bridge_hours / HOURS_PER_WEEK)) if missing else 0,
            "modules": list(missing),
            "note": "Auto-composed from the missing skills; not an approved curriculum",
            "source": "Auto-composed by the prototype",
        }
    bp["estimated_bridge_hours"] = round(bridge_hours)

    return {
        "current_occupation": current_occupation,
        "target_occupation": target_occupation,
        "current_skills": held,
        "target_skills": [{"competency": c, "weight": w} for c, w in reqs.items()],
        "fit_score": round(fit, 1),
        "fit_band": fit_band(fit),
        "basic_overlap_pct": round(basic, 1),
        "skill_distance": round(100.0 - fit, 1),
        "matched_skills": matched,
        "partial_skills": partial,
        "missing_skills": missing,
        "breakdown": rows,
        "bridge_training": bp,
        "pathway": [current_occupation, bp["name"], target_occupation] if missing else [current_occupation, target_occupation],
        "calculation": {
            "formula": "Fit = 100 x sum(weight x credit) / sum(weight)",
            "weighted_credit_sum": round(earned, 2),
            "total_weight": total_w,
            "result": f"100 x {earned:.2f} / {total_w} = {fit:.1f}",
            "basic_formula": "Basic overlap = matched / target skills x 100",
            "basic_result": f"{len(matched)} / {len(reqs)} x 100 = {basic:.1f}",
            "distance_formula": "Skill distance = 100 - Fit",
        },
        "explainability": {
            "method": "Weighted skill-overlap similarity with partial credit for related skills",
            "inputs": "Worker's current skills, target occupation's required skills with importance weights, skill similarity table",
            "output": "Transfer Fit Score (0-100), matched / partial / missing skills, bridge-training estimate",
            "limitations": (
                "Prototype similarity measure based on skill overlap. It does not represent guaranteed employability. "
                "Weights and similarities are illustrative placeholders that require validation with real data."
            ),
        },
    }
