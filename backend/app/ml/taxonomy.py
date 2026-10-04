"""
Competency / occupation taxonomy loader.

The prototype uses an illustrative taxonomy (data/taxonomy.json, data/transition_skills.json).
FUTURE: replace/extend with NCO-2015 occupation codes and NSQF qualification mappings. Only this
module needs to change; the rest of the engine works on canonical competency names.
"""
import json
from pathlib import Path


class Taxonomy:
    def __init__(self, data_dir: Path):
        tax = json.loads((data_dir / "taxonomy.json").read_text(encoding="utf-8"))
        trans = json.loads((data_dir / "transition_skills.json").read_text(encoding="utf-8"))
        self.competencies = {c["name"]: c for c in tax["competencies"]}
        self.requirements = {
            occ: {r["competency"]: r["weight"] for r in reqs} for occ, reqs in trans["occupation_requirements"].items()
        }
        self.similarity = {}
        for s in trans["similarity"]:
            self.similarity[(s["a"], s["b"])] = s["similarity"]
            self.similarity[(s["b"], s["a"])] = s["similarity"]
        self.bridge_programmes = trans["bridge_programmes"]

    def alias_map(self):
        """normalized alias -> canonical competency name (canonical name itself is also an alias)."""
        m = {}
        for name, c in self.competencies.items():
            for a in [name] + list(c["aliases"]):
                m[a] = name
        return m

    def bridge_hours(self, competency: str) -> int:
        return int(self.competencies.get(competency, {}).get("bridge_hours", 40))

    def sim(self, a: str, b: str) -> float:
        return self.similarity.get((a, b), 0.0)
