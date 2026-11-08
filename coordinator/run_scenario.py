"""CareGuard coordinator: the ML Function Orchestrator (Y.3172 MLFO role) for scenario runs.

Releases a scenario's events in chunks to *different* agents (no agent sees
everything), forwards agent messages to the Policy & Legal Adviser, records
disagreements, checks the run against the scenario's expected behaviour and
writes a JSONL audit trace plus a human-readable timeline.

Usage
  python coordinator/run_scenario.py scenarios/A_dropped_meds.yaml
  python coordinator/run_scenario.py scenarios/*.yaml --backend auto --retriever auto
  python coordinator/run_scenario.py scenarios/C_consent.yaml \
      --inject "Vendor starts using in-home video to train its next model" \
      --inject-to care_agent,data_protection,policy_adviser --inject-facts secondary_use_training

Backends
  --backend rules   deterministic rule-and-retrieval fallback (default, no GPU)
  --backend ollama  local LLM via Ollama (CAREGUARD_LLM, default qwen2.5:14b); falls back to rules per turn
  --backend auto    ollama if reachable with the model pulled, else rules
  --retriever bm25|chroma|auto
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "kb"))

from agents import REGISTRY  # noqa: E402
from agents.base import OllamaLLM  # noqa: E402
from retriever import get_retriever  # noqa: E402

Y3172_NODE = {  # which Y.3172 pipeline node an event channel / agent output maps to
    "wearable": "SRC", "family_app": "SRC", "device_management": "C", "audit_log": "C", "clinic_portal": "SINK",
    "incident_report": "SRC", "case_file": "SRC", "coordinator": "MLFO", "judges": "SRC",
}
AGENT_NODE = {"care_agent": "M", "policy_adviser": "P", "health_regulator": "P", "data_protection": "P",
              "telecom_regulator": "P", "medical_products": "P", "social_care": "P"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def run(scenario_path: Path, backend: str, retriever_name: str, out_dir: Path, inject: dict | None = None) -> dict:
    sc = yaml.safe_load(scenario_path.read_text())
    events = list(sc["events"])
    if inject:
        events.insert(len(events) - 1 if events and "audit_requested" in events[-1].get("facts", []) else len(events),
                      {"t": inject.get("t", "T+inject"), "release_to": inject["to"], "channel": "judges",
                       "text": inject["text"], "facts": inject["facts"], "injected": True})
    retriever = get_retriever(retriever_name)
    llm = OllamaLLM()
    eff_backend = backend
    if backend == "auto":
        eff_backend = "ollama" if llm.available() else "rules"
    elif backend == "ollama" and not llm.available():
        print(f"[coordinator] Ollama model {llm.model} not reachable; using rules backend")
        eff_backend = "rules"

    names = []
    for e in events:
        for a in e["release_to"]:
            if a not in names:
                names.append(a)
    agents = {n: REGISTRY[n](retriever, backend=eff_backend, llm=llm if eff_backend == "ollama" else None) for n in names}

    run_id = f"{sc['id']}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:6]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_path = out_dir / f"{sc['id']}.jsonl"
    records, messages = [], []          # messages: everything agents have said (forwarded to the adviser)
    knows = defaultdict(list)            # agent -> events it was shown (who knew what, when)

    with open(trace_path, "w", encoding="utf-8") as f:
        def write(rec: dict) -> None:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            records.append(rec)

        write({"type": "run_start", "run_id": run_id, "timestamp": now(), "scenario": sc["id"], "title": sc["title"],
               "backend": eff_backend, "retriever": retriever.name, "agents": names,
               "python": platform.python_version(), "context": sc.get("context", "").strip()})

        for step, ev in enumerate(events, start=1):
            write({"type": "event_release", "run_id": run_id, "timestamp": now(), "step": step, "sim_time": ev["t"],
                   "channel": ev.get("channel"), "y3172_node": Y3172_NODE.get(ev.get("channel"), "SRC"),
                   "released_to": ev["release_to"], "withheld_from": [n for n in names if n not in ev["release_to"]],
                   "text": ev["text"], "facts": ev.get("facts", []), "injected": bool(ev.get("injected"))})
            order = [a for a in ev["release_to"] if a != "policy_adviser"] + (["policy_adviser"] if "policy_adviser" in ev["release_to"] else [])
            for name in order:
                agent = agents[name]
                knows[name].append(f"{ev['t']}: {ev['text']}")
                peers = list(messages) if name == "policy_adviser" else []
                for out in agent.handle(ev, peers):
                    rec = {
                        "type": "agent_turn", "run_id": run_id, "timestamp": now(), "step": step, "sim_time": ev["t"],
                        "agent": name, "role": agent.role, "y3172_node": AGENT_NODE.get(name, "P"),
                        "inputs_seen": {"event_text": ev["text"], "channel": ev.get("channel"), "facts": ev.get("facts", []),
                                        "cumulative_facts": sorted(agent.seen_facts),
                                        "peer_messages": [{"agent": p["agent"], "decision": p["decision"][:200]} for p in peers]},
                        **out,
                    }
                    write(rec)
                    if out.get("rule_id"):
                        messages.append({"agent": name, "decision": out["decision"], "shared_facts": ev.get("facts", [])})

        turns = [r for r in records if r["type"] == "agent_turn" and r.get("rule_id")]
        # ---- disagreements: same question, different stances from different agents
        by_q = defaultdict(list)
        for r in turns:
            by_q[r["question"]].append((r["agent"], r["stance"]))
        disagreements = [{"question": q, "stances": [{"agent": a, "stance": s} for a, s in v]}
                         for q, v in by_q.items() if len({s for _, s in v}) > 1]
        for d in disagreements:
            write({"type": "disagreement", "run_id": run_id, "timestamp": now(), **d,
                   "resolution": "recorded for human review; coordinator does not override institutional mandates"})

        # ---- evaluation against the scenario's expected behaviour
        exp = sc.get("expected", {})
        fired = {r["rule_id"]: r for r in turns}
        exp_rules = exp.get("rules", [])
        rules_hit = [r for r in exp_rules if r in fired]
        cites = exp.get("citations", {})
        cite_ok = {rid: bool(fired.get(rid) and fired[rid].get("cited_authority") and fired[rid]["cited_authority"]["doc_id"] == doc)
                   for rid, doc in cites.items()}
        gaps_found = sorted({r["gap"] for r in turns if r.get("gap")})
        exp_gaps = exp.get("gaps", [])
        escalations = sorted({r["escalation"] for r in turns if r.get("escalation")})
        grounded = sum(1 for r in turns if r.get("supported"))
        summary = {
            "type": "run_summary", "run_id": run_id, "timestamp": now(), "scenario": sc["id"], "backend": eff_backend,
            "retriever": retriever.name, "agent_turns": len(turns),
            "expected_rules_fired": f"{len(rules_hit)}/{len(exp_rules)}",
            "missing_rules": [r for r in exp_rules if r not in fired],
            "unexpected_rules": [r for r in fired if r not in exp_rules],
            "citation_accuracy": f"{sum(cite_ok.values())}/{len(cite_ok)}", "citation_checks": cite_ok,
            "grounded_turns": f"{grounded}/{len(turns)}",
            "ungrounded_rules": [r["rule_id"] for r in turns if not r.get("supported")],
            "gaps_found": gaps_found, "expected_gaps_found": f"{len(set(gaps_found) & set(exp_gaps))}/{len(exp_gaps)}",
            "escalations": escalations, "disagreements": len(disagreements),
            "who_knew_what": dict(knows),
        }
        write(summary)

    write_timeline(sc, records, out_dir / f"{sc['id']}_timeline.md")
    return summary


def write_timeline(sc: dict, records: list[dict], path: Path) -> None:
    start = records[0]
    lines = [f"# {sc['title']}", "", f"Run `{start['run_id']}` · backend `{start['backend']}` · retriever `{start['retriever']}` · "
             f"started {start['timestamp']}", "", f"Context: {start['context']}", ""]
    for r in records[1:]:
        if r["type"] == "event_release":
            tag = " (injected)" if r["injected"] else ""
            lines += [f"## Step {r['step']} · {r['sim_time']} · {r['channel']} [{r['y3172_node']}]{tag}", "",
                      f"> {r['text']}", "", f"Released to: {', '.join(r['released_to'])}. Withheld from: {', '.join(r['withheld_from']) or 'none'}.", ""]
        elif r["type"] == "agent_turn":
            if not r.get("rule_id"):
                lines.append(f"- **{r['agent']}**: noted (no rule triggered)")
                continue
            c = r.get("cited_authority")
            cite = f"{c['doc_id']} p.{c['page']} (score {c['score']})" if c else "none above threshold"
            gap = f" · gap {r['gap']}" if r.get("gap") else ""
            lines.append(f"- **{r['agent']}** `{r['rule_id']}` → {r['decision']}  \n  cites: {cite}{gap} · escalation: {r.get('escalation') or '-'}")
        elif r["type"] == "disagreement":
            lines += ["", f"**Disagreement on `{r['question']}`:** " + "; ".join(f"{s['agent']} = {s['stance']}" for s in r["stances"])]
        elif r["type"] == "run_summary":
            lines += ["", "## Summary", "", "```json", json.dumps({k: v for k, v in r.items() if k not in ('type', 'who_knew_what')}, indent=2), "```"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenarios", nargs="+", type=Path)
    ap.add_argument("--backend", default="rules", choices=["rules", "ollama", "auto"])
    ap.add_argument("--retriever", default="bm25", choices=["bm25", "chroma", "auto"])
    ap.add_argument("--out", type=Path, default=ROOT / "logs")
    ap.add_argument("--inject", help="text of a live event to add before the audit step")
    ap.add_argument("--inject-to", default="care_agent,policy_adviser")
    ap.add_argument("--inject-facts", default="")
    args = ap.parse_args()
    inject = None
    if args.inject:
        inject = {"text": args.inject, "to": args.inject_to.split(","), "facts": [x for x in args.inject_facts.split(",") if x]}
    for p in args.scenarios:
        s = run(p, args.backend, args.retriever, args.out, inject)
        print(f"{s['scenario']}: rules {s['expected_rules_fired']}, citations {s['citation_accuracy']}, "
              f"grounded {s['grounded_turns']}, gaps {s['gaps_found']} ({s['expected_gaps_found']} expected), "
              f"escalations {s['escalations']}, disagreements {s['disagreements']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
