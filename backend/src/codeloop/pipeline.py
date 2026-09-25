"""Transcript → events → engine, with no I/O. Shared by the live orchestrator, replay and eval."""

from __future__ import annotations

from dataclasses import dataclass, field

from .domain.formulary import Formulary, default_formulary
from .domain.models import Event, EventSource, PromptPolicy, Utterance
from .engine.engine import CodeEngine, EngineOutput
from .extract.grammar import Candidate, Grammar
from .extract.resolve import Resolver


@dataclass
class TurnResult:
    utterance: Utterance
    candidates: list[Candidate] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    output: EngineOutput = field(default_factory=EngineOutput)


class TranscriptPipeline:
    def __init__(
        self,
        formulary: Formulary | None = None,
        policy: PromptPolicy = PromptPolicy.TIMERS_AND_LOOPS,
        low_confidence: float = 0.6,
    ) -> None:
        self.f = formulary or default_formulary()
        self.engine = CodeEngine(self.f, policy)
        self.grammar = Grammar(self.f)
        self.resolver = Resolver(self.f, low_confidence)

    def process(self, utt: Utterance, extra: list[tuple[Candidate, EventSource]] | None = None) -> TurnResult:
        """Extract, resolve and apply one final turn. `extra` carries LLM candidates."""
        res = TurnResult(utterance=utt)
        res.output.extend(self.engine.advance(utt.start_s))
        cands = [(c, EventSource.GRAMMAR) for c in self.grammar.extract(utt)]
        res.candidates = [c for c, _ in cands]
        if extra:
            cands = merge_candidates(cands, extra)
        # Everything said in one utterance is applied before timers run, so an order and its
        # read-back in the same breath never produce a transient "not acknowledged".
        for i, (c, source) in enumerate(sorted(cands, key=lambda x: x[0].char_span)):
            for ev in self.resolver.resolve(c, utt, self.engine, f"{utt.id}:{i}", source):
                res.events.append(ev)
                res.output.extend(self.engine.apply(ev, advance=False))
        res.output.extend(self.engine.advance(max(utt.end_s, self.engine.now_s)))
        return res

    def advance(self, now_s: float) -> EngineOutput:
        return self.engine.advance(now_s)


def _key(c: Candidate) -> tuple:
    return (str(c.kind), c.action, c.drug, c.dose, c.energy_j, c.rhythm, c.role)


def merge_candidates(
    grammar: list[tuple[Candidate, EventSource]], llm: list[tuple[Candidate, EventSource]]
) -> list[tuple[Candidate, EventSource]]:
    """Union of both extractors. Agreement marks the event BOTH; an LLM-only event whose
    value contradicts a grammar event for the same drug is kept but its confidence is zeroed
    so it is marked UNCONFIRMED."""
    out = list(grammar)
    gkeys = {_key(c): i for i, (c, _) in enumerate(grammar)}
    for c, src in llm:
        k = _key(c)
        if k in gkeys:
            gi = gkeys[k]
            out[gi] = (out[gi][0], EventSource.BOTH)
            continue
        clash = any(
            g.drug == c.drug
            and g.action == c.action
            and c.action is not None
            and (g.dose, g.energy_j) != (c.dose, c.energy_j)
            for g, _ in grammar
        )
        if clash:
            c.value_confidence = 0.0
        out.append((c, src))
    return out
