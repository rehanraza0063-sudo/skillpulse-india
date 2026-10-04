"""
Job Description Skill Extractor (prototype).

HONEST DESCRIPTION: this is a transparent, rule-based dictionary / phrase-matching extractor.
It is NOT a machine-learning or LLM model. The `SkillExtractor` interface exists so a real NLP model
(spaCy NER, a fine-tuned transformer, an LLM call...) can replace `KeywordSkillExtractor` without
touching the rest of the pipeline.

Pipeline: raw text -> normalisation -> longest-phrase alias matching -> canonical skills -> occupation mapping.
"""
import re
from abc import ABC, abstractmethod
from typing import Dict, List

from .taxonomy import Taxonomy

_ALLOWED = re.compile(r"[^a-z0-9&/+# ]")


def normalize_text(text: str) -> str:
    """Lower-case and replace punctuation by spaces 1:1 (character offsets stay aligned with the original)."""
    return _ALLOWED.sub(" ", text.lower())


class SkillExtractor(ABC):
    name = "abstract"

    @abstractmethod
    def extract(self, text: str) -> List[dict]:
        ...


class KeywordSkillExtractor(SkillExtractor):
    name = "Rule-based phrase matching (taxonomy aliases)"

    def __init__(self, taxonomy: Taxonomy):
        self.taxonomy = taxonomy
        amap = taxonomy.alias_map()
        entries = []
        for alias, canonical in amap.items():
            toks = normalize_text(alias).split()
            if not toks:
                continue
            pat = r"(?<![a-z0-9])" + r"\s+".join(re.escape(t) for t in toks) + r"s?(?![a-z0-9])"
            entries.append((len(" ".join(toks)), alias, canonical, re.compile(pat)))
        # longest phrase first so "high voltage safety" wins over "safety"
        entries.sort(key=lambda e: -e[0])
        self._entries = entries

    def extract(self, text: str) -> List[dict]:
        norm = normalize_text(text)
        taken = [False] * len(norm)
        found = []
        for _, alias, canonical, rx in self._entries:
            for m in rx.finditer(norm):
                s, e = m.span()
                if any(taken[s:e]):
                    continue
                for i in range(s, e):
                    taken[i] = True
                found.append({
                    "canonical": canonical,
                    "matched_text": text[s:e],
                    "alias": alias,
                    "start": s,
                    "end": e,
                    "category": self.taxonomy.competencies[canonical]["category"],
                })
        found.sort(key=lambda f: f["start"])
        return found


def map_to_occupations(taxonomy: Taxonomy, text: str, skills: List[str], top_n: int = 3) -> List[dict]:
    """Score occupations: weighted coverage of required competencies (+0.25 if the title appears in the text)."""
    norm = " " + " ".join(normalize_text(text).split()) + " "
    skill_set = set(skills)
    out = []
    for occ, reqs in taxonomy.requirements.items():
        total_w = sum(reqs.values())
        matched = [c for c in reqs if c in skill_set]
        matched_w = sum(reqs[c] for c in matched)
        coverage = matched_w / total_w if total_w else 0.0
        title_norm = " " + " ".join(normalize_text(occ).split()) + " "
        title_hit = title_norm in norm
        score = min(1.0, coverage + (0.25 if title_hit else 0.0))
        if matched or title_hit:
            out.append({
                "occupation": occ,
                "score": round(score * 100, 1),
                "coverage_pct": round(coverage * 100, 1),
                "title_mentioned": title_hit,
                "matched_competencies": matched,
                "missing_competencies": [c for c in reqs if c not in skill_set],
                "calculation": (
                    f"coverage = matched weight {matched_w} / total required weight {total_w} = {coverage:.2f}"
                    + (" ; +0.25 because the occupation title appears in the text" if title_hit else "")
                    + f" ; score = {score:.2f}"
                ),
            })
    out.sort(key=lambda o: (-o["score"], o["occupation"]))
    return out[:top_n]


def run_pipeline(extractor: SkillExtractor, taxonomy: Taxonomy, text: str) -> Dict:
    spans = extractor.extract(text)
    normalized = []
    for s in spans:
        if s["canonical"] not in normalized:
            normalized.append(s["canonical"])
    occs = map_to_occupations(taxonomy, text, normalized)
    return {
        "input_text": text,
        "stages": [
            {"stage": "Job Description", "detail": f"{len(text)} characters"},
            {"stage": "NLP Skill Extraction", "detail": f"{len(spans)} phrase match(es) found using {extractor.name}"},
            {"stage": "Normalized Skills", "detail": f"{len(normalized)} canonical skill(s) after alias normalisation"},
            {"stage": "Occupation Mapping", "detail": occs[0]["occupation"] if occs else "No occupation matched"},
        ],
        "extracted": spans,
        "normalized_skills": normalized,
        "occupations": occs,
        "best_occupation": occs[0]["occupation"] if occs else None,
        "explainability": {
            "method": extractor.name,
            "inputs": "Free-text job description; taxonomy of canonical competencies and aliases",
            "output": "Canonical skills with matched phrases and ranked occupation matches",
            "limitations": (
                "Dictionary matching only: it finds listed phrases and aliases, understands no context, "
                "and misses skills not in the taxonomy. It is not an ML/LLM model. "
                "Designed so a trained NLP model can replace it behind the SkillExtractor interface."
            ),
        },
    }
