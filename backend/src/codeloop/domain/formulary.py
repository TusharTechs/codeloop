"""Formulary: the bounded vocabulary of drugs, doses, energies and rhythms CodeLoop accepts."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import yaml

from .models import Rhythm

DEFAULT_PATH = Path(__file__).with_name("formulary.yaml")


@dataclass(frozen=True)
class Drug:
    key: str
    aliases: tuple[str, ...]
    unit: str
    usual: tuple[float, ...]
    bounds: tuple[float, float]
    interval_s: tuple[float, float] | None = None
    sequence: tuple[float, ...] = ()

    @property
    def display(self) -> str:
        return self.key.replace("_", " ")

    def in_bounds(self, dose: float) -> bool:
        return self.bounds[0] <= dose <= self.bounds[1]


@dataclass(frozen=True)
class Timers:
    cpr_cycle_s: float = 120
    cpr_cycle_warn_s: float = 105
    unacknowledged_s: float = 10
    unacknowledged_nudge_s: float = 15


@dataclass(frozen=True)
class Formulary:
    version: str
    drugs: dict[str, Drug]
    shock_bounds: tuple[float, float]
    shock_usual: tuple[float, ...]
    rhythm_aliases: dict[str, Rhythm]
    shockable: frozenset[Rhythm]
    timers: Timers
    _alias_index: dict[str, str] = field(default_factory=dict, repr=False)

    def drug_for(self, name: str | None) -> Drug | None:
        """Resolve a spoken or canonical drug name ("amio", "Epinephrine") to a Drug."""
        if not name:
            return None
        n = " ".join(name.lower().replace("_", " ").replace("-", " ").split())
        key = self._alias_index.get(n)
        return self.drugs.get(key) if key else None

    def rhythm_for(self, name: str | None) -> Rhythm | None:
        if not name:
            return None
        n = " ".join(name.lower().replace("-", " ").split())
        if n.upper() in Rhythm.__members__:
            return Rhythm(n.upper())
        return self.rhythm_aliases.get(n) or self.rhythm_aliases.get(n.replace(" ", ""))

    def shock_in_bounds(self, joules: float) -> bool:
        return self.shock_bounds[0] <= joules <= self.shock_bounds[1]

    def keyterms(self, limit: int = 100) -> list[str]:
        """Keyterms for AssemblyAI: canonical names first, then Latin-script aliases."""
        terms: list[str] = ["CodeLoop"]
        for d in self.drugs.values():
            terms.append(d.display)
        for d in self.drugs.values():
            terms.extend(a for a in d.aliases if a.isascii() and len(a) > 2)
        terms += [
            "V-fib",
            "V-tach",
            "pulseless VT",
            "PEA",
            "asystole",
            "ROSC",
            "joules",
            "milligrams",
            "compressions",
            "rhythm check",
            "pulse check",
            "code blue",
        ]
        seen: set[str] = set()
        out = []
        for t in terms:
            if t.lower() not in seen and len(t) <= 50:
                seen.add(t.lower())
                out.append(t)
        return out[:limit]


def _build(raw: dict) -> Formulary:
    drugs: dict[str, Drug] = {}
    alias_index: dict[str, str] = {}
    for key, d in raw["drugs"].items():
        drug = Drug(
            key=key,
            aliases=tuple(d.get("aliases", [])),
            unit=d["unit"],
            usual=tuple(float(x) for x in d.get("usual", [])),
            bounds=(float(d["bounds"][0]), float(d["bounds"][1])),
            interval_s=tuple(d["interval_s"]) if d.get("interval_s") else None,  # type: ignore[arg-type]
            sequence=tuple(float(x) for x in d.get("sequence", [])),
        )
        drugs[key] = drug
        for a in (key, key.replace("_", " "), *drug.aliases):
            alias_index[" ".join(a.lower().replace("-", " ").split())] = key
    rhythm_aliases: dict[str, Rhythm] = {}
    shockable: set[Rhythm] = set()
    for name, r in raw["rhythms"].items():
        rhythm = Rhythm(name)
        if r.get("shockable"):
            shockable.add(rhythm)
        for a in (name.lower(), *r.get("aliases", [])):
            norm = " ".join(a.lower().replace("-", " ").split())
            rhythm_aliases[norm] = rhythm
            rhythm_aliases[norm.replace(" ", "")] = rhythm
    t = raw.get("timers", {})
    return Formulary(
        version=raw.get("version", "custom"),
        drugs=drugs,
        shock_bounds=(float(raw["shock"]["bounds"][0]), float(raw["shock"]["bounds"][1])),
        shock_usual=tuple(float(x) for x in raw["shock"].get("usual", [])),
        rhythm_aliases=rhythm_aliases,
        shockable=frozenset(shockable),
        timers=Timers(**{k: float(v) for k, v in t.items()}),
        _alias_index=alias_index,
    )


def load_formulary(path: Path | None = None) -> Formulary:
    return _build(yaml.safe_load((path or DEFAULT_PATH).read_text()))


@cache
def default_formulary() -> Formulary:
    return load_formulary()
