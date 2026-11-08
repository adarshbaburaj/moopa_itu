"""Common agent machinery for CareGuard.

An agent has a mandate and a list of rules. When the coordinator releases an
event to it, the agent:
  1. matches the event's facts against its rules (only facts it was shown),
  2. for each matching rule, queries the knowledge base twice: restricted to the
     rule's authority documents, and unrestricted (to show what else the KB holds),
  3. decides. Backend "rules" (default fallback) takes the rule's decision and
     cites the best retrieved authority chunk, or reports that no supporting
     authority was retrieved. Backend "ollama" asks a local LLM to write the
     decision and reasoning from the retrieved chunks only, and validates that
     every chunk it cites was actually retrieved; if not, it falls back to rules.
Every turn returns a structured record that the coordinator writes to the JSONL
audit trace.
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass, field
from typing import Any

MIN_SUPPORT_SCORE = float(os.environ.get("CAREGUARD_MIN_SUPPORT", "6.0"))  # BM25 scale


@dataclass
class Rule:
    id: str
    when_all: list[str]                     # facts that must all be visible to the agent
    question: str                           # the issue this rule takes a stance on
    stance: str                             # short machine-readable stance
    decision: str                           # what the agent decides / recommends
    query: str                              # KB query used to find the authority
    authority_docs: list[str]               # doc_ids that can ground this decision
    when_any: list[str] = field(default_factory=list)
    global_docs: list[str] = field(default_factory=list)   # global examples to retrieve
    global_query: str = ""
    gap: str | None = None                  # gap id this rule surfaces, if any
    escalation: str | None = None           # none | family | clinic | emergency | regulator | human_review
    min_score: float | None = None          # override MIN_SUPPORT_SCORE for this rule

    def matches(self, facts: set[str]) -> bool:
        if not all(f in facts for f in self.when_all):
            return False
        return not self.when_any or any(f in facts for f in self.when_any)


def _hit_view(h: dict) -> dict:
    return {"chunk_id": h["chunk_id"], "doc_id": h["doc_id"], "page": h["page"], "score": h["score"],
            "excerpt": h["text"][:280]}


class OllamaLLM:
    """Minimal Ollama /api/chat client (no extra dependency)."""

    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.environ.get("CAREGUARD_LLM", "qwen2.5:14b")
        self.host = host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    def available(self) -> bool:
        try:
            with urllib.request.urlopen(f"{self.host}/api/tags", timeout=3) as r:
                tags = json.loads(r.read())
            return any(m.get("name", "").startswith(self.model.split(":")[0]) for m in tags.get("models", []))
        except Exception:  # noqa: BLE001
            return False

    def chat_json(self, system: str, user: str) -> dict:
        body = json.dumps({"model": self.model, "stream": False, "format": "json",
                           "options": {"temperature": 0},
                           "messages": [{"role": "system", "content": system},
                                        {"role": "user", "content": user}]}).encode()
        req = urllib.request.Request(f"{self.host}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(json.loads(r.read())["message"]["content"])


class Agent:
    name = "agent"
    role = "generic"                 # ITU sandbox role: innovative_solution | policy_adviser | institutional
    mandate = ""
    rules: list[Rule] = []

    def __init__(self, retriever, backend: str = "rules", llm: OllamaLLM | None = None, k: int = 3):
        self.retriever, self.backend, self.llm, self.k = retriever, backend, llm, k
        self.seen_facts: set[str] = set()
        self.fired: set[str] = set()

    # ------------------------------------------------------------------
    def handle(self, event: dict, peer_messages: list[dict] | None = None) -> list[dict]:
        """Process one released event. Returns one record per rule that fires (or one 'noted' record)."""
        self.seen_facts |= set(event.get("facts", []))
        for m in peer_messages or []:          # facts other agents surfaced to this one
            self.seen_facts |= set(m.get("shared_facts", []))
        out = []
        for rule in self.rules:
            if rule.id in self.fired or not rule.matches(self.seen_facts):
                continue
            self.fired.add(rule.id)
            out.append(self._decide(rule, event, peer_messages or []))
        if not out:
            out.append({"rule_id": None, "question": None, "stance": "noted", "decision": "No rule in this agent's mandate is triggered by the information it has seen so far; event noted.",
                        "reasoning_summary": f"Visible facts {sorted(self.seen_facts)} do not satisfy any rule of {self.name}.",
                        "retrieved": [], "retrieved_open": [], "cited_authority": None, "supported": None,
                        "gap": None, "escalation": None, "backend": self.backend})
        return out

    # ------------------------------------------------------------------
    def _decide(self, rule: Rule, event: dict, peers: list[dict]) -> dict:
        auth_hits = self.retriever.search(rule.query, k=self.k, doc_ids=rule.authority_docs) if rule.authority_docs else []
        open_hits = self.retriever.search(rule.query, k=self.k)
        glob_hits = self.retriever.search(rule.global_query or rule.query, k=2, doc_ids=rule.global_docs) if rule.global_docs else []
        threshold = rule.min_score if rule.min_score is not None else MIN_SUPPORT_SCORE
        best = auth_hits[0] if auth_hits else None
        supported = bool(best and best["score"] >= threshold)
        rec: dict[str, Any] = {
            "rule_id": rule.id, "question": rule.question, "stance": rule.stance,
            "retrieved": [_hit_view(h) for h in auth_hits],
            "retrieved_open": [_hit_view(h) for h in open_hits],
            "retrieved_global": [_hit_view(h) for h in glob_hits],
            "support_threshold": threshold, "supported": supported,
            "cited_authority": ({"doc_id": best["doc_id"], "title": best["title"], "page": best["page"],
                                 "chunk_id": best["chunk_id"], "score": best["score"]} if supported else None),
            "gap": rule.gap, "escalation": rule.escalation,
        }
        if self.backend == "ollama" and self.llm is not None:
            llm_rec = self._llm_decide(rule, event, peers, auth_hits + open_hits + glob_hits)
            if llm_rec:
                rec.update(llm_rec, backend=f"ollama:{self.llm.model}")
                return rec
        rec["decision"] = rule.decision if supported else (
            f"{rule.decision} [NOT GROUNDED: no chunk from {', '.join(rule.authority_docs)} scored >= {threshold}; "
            f"flagged for human review]")
        cite = (f"strongest authority {best['doc_id']} p.{best['page']} (score {best['score']})" if supported
                else "no authority chunk above threshold")
        rec["reasoning_summary"] = (
            f"Facts visible to {self.name}: {sorted(self.seen_facts)}. Rule {rule.id} requires {rule.when_all}"
            f"{' + any of ' + str(rule.when_any) if rule.when_any else ''}. KB query '{rule.query}' -> {cite}. "
            f"Decision taken from the rule base (deterministic fallback backend).")
        rec["backend"] = "rules"
        return rec

    def _llm_decide(self, rule: Rule, event: dict, peers: list[dict], hits: list[dict]) -> dict | None:
        ctx = "\n\n".join(f"[{h['chunk_id']}] ({h['doc_id']} p.{h['page']})\n{h['text'][:1200]}" for h in hits)
        peer_txt = "\n".join(f"- {p['agent']}: {p['decision']}" for p in peers[-6:])
        system = (f"You are the {self.name} in a policy-grounded elderly home-care system. Mandate: {self.mandate}. "
                  "Answer ONLY from the provided sources. Reply as JSON with keys: decision (string), "
                  "reasoning_summary (<=80 words), cited_chunk_ids (list of ids from the sources), stance (short string).")
        user = (f"Event ({event.get('t')}): {event['text']}\nIssue to decide: {rule.question}\n"
                f"Baseline recommendation from the rule base: {rule.decision}\nOther agents so far:\n{peer_txt or '-'}\n\nSources:\n{ctx}")
        try:
            out = self.llm.chat_json(system, user)
        except Exception:  # noqa: BLE001
            return None
        valid = {h["chunk_id"]: h for h in hits}
        cited = [c for c in out.get("cited_chunk_ids", []) if c in valid]
        if not cited or not out.get("decision"):
            return None          # ungrounded LLM answer -> caller falls back to rules
        h = valid[cited[0]]
        return {"decision": out["decision"], "reasoning_summary": out.get("reasoning_summary", ""),
                "stance": out.get("stance", rule.stance), "supported": True,
                "cited_authority": {"doc_id": h["doc_id"], "title": h["title"], "page": h["page"],
                                    "chunk_id": h["chunk_id"], "score": h["score"]},
                "llm_cited_chunk_ids": cited}
