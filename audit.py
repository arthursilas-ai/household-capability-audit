#!/usr/bin/env python3
"""
audit.py — Household Capability Audit

Maps where your household is exposed: where you have genuine capability,
where you have access masquerading as capability, and where you are
simply dependent.

Based on the four capability questions from the Solystopia framework:
  1. Knowledge   — do you understand how this works, or just how to use it?
  2. Competence  — can you do it yourself, or only instruct a service?
  3. Substitutability — can you swap the supplier without losing the function?
  4. Recovery    — can you get back to normal without the exact same infrastructure?

Each question is scored 1–4:
  1 = fully dependent
  2 = partially dependent (some knowledge/skill, high lock-in)
  3 = partially capable (can do it, but constrained)
  4 = fully capable / substitutable / recoverable

Six domains are assessed:
  compute, energy, food, water, connectivity, fabrication

Usage:
    python audit.py              # interactive questionnaire
    python audit.py --json       # output results as JSON
    python audit.py --demo       # run with example answers (no prompts)

Output: a dependency profile with per-domain scores and next-action suggestions.

Part of the Solystopia open-source toolkit: solystopia.tech
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── scoring ──────────────────────────────────────────────────────────────────

SCORE_LABELS = {
    1: "fully dependent",
    2: "partially dependent",
    3: "partially capable",
    4: "fully capable",
}

SCORE_DESCRIPTIONS = {
    1: "You rely entirely on a service you don't control or understand.",
    2: "Some understanding or skill, but significant lock-in or single points of failure.",
    3: "You can do this yourself, but with constraints (supply chain, tooling, knowledge gaps).",
    4: "You understand it, can do it yourself, could swap suppliers, and could recover from failure.",
}


def _prompt_score(question: str, hint: str = "") -> int:
    """Ask a 1–4 question and return the integer score."""
    if hint:
        print(f"    ({hint})")
    while True:
        val = input(f"    {question} [1–4]: ").strip()
        if val in ("1", "2", "3", "4"):
            return int(val)
        print("    Please enter 1, 2, 3, or 4.")


# ── domains ──────────────────────────────────────────────────────────────────

@dataclass
class DomainResult:
    name: str
    display_name: str
    knowledge: int
    competence: int
    substitutability: int
    recovery: int
    score: float = field(init=False)
    level: str = field(init=False)

    def __post_init__(self):
        self.score = round(
            (self.knowledge + self.competence + self.substitutability + self.recovery) / 4, 2
        )
        if self.score >= 3.5:
            self.level = "capable"
        elif self.score >= 2.5:
            self.level = "partially capable"
        elif self.score >= 1.5:
            self.level = "partially dependent"
        else:
            self.level = "fully dependent"


DOMAINS = {
    "compute": {
        "display_name": "Compute & AI",
        "description": "Your ability to run software, AI models, and data systems.",
        "questions": {
            "knowledge": (
                "How well do you understand the compute stack you use daily?",
                "1=black box  2=user-level  3=can configure/debug  4=can build/maintain",
            ),
            "competence": (
                "Could you set up your own compute environment from scratch if needed?",
                "1=no  2=with significant help  3=yes, with documentation  4=yes, from memory",
            ),
            "substitutability": (
                "Could you swap your primary compute provider without losing function?",
                "1=locked in  2=very hard  3=possible but costly  4=easy, open standards",
            ),
            "recovery": (
                "Could you restore your compute setup after a total failure?",
                "1=no path  2=months + external help  3=weeks + documentation  4=days, self-sufficient",
            ),
        },
        "actions": {
            "low": [
                "Run a local model once — llama.cpp + a GGUF file is the minimum viable step",
                "Document what cloud services you depend on and what would break without them",
                "Read the Sovereign AI Harness: github.com/arthursilas-ai/sovereign-ai-harness",
            ],
            "mid": [
                "Move at least one recurring AI task to a local model",
                "Run agent-preflight on any AI systems you operate: github.com/arthursilas-ai/agent-preflight",
                "Back up your model weights, configs, and fine-tunes to local storage",
            ],
            "high": [
                "Document your setup so someone else could reproduce it",
                "Consider local TTS/STT to reduce voice interface dependency: github.com/arthursilas-ai/piper-local-tts-demo",
                "Run hearthmind-economics to plan your next hardware step",
            ],
        },
    },
    "energy": {
        "display_name": "Energy",
        "description": "Your ability to produce, store, and manage electricity and heat.",
        "questions": {
            "knowledge": (
                "Do you understand your household's energy profile — sources, draws, peaks?",
                "1=no idea  2=rough idea  3=have measured it  4=full picture, documented",
            ),
            "competence": (
                "Could you manage your energy use during a grid outage?",
                "1=completely dependent  2=a few hours  3=days with rationing  4=weeks, self-sufficient",
            ),
            "substitutability": (
                "How substitutable is your energy supplier?",
                "1=one provider, no alternative  2=could switch slowly  3=partial renewables on-site  4=significant on-site generation",
            ),
            "recovery": (
                "Could you recover normal household function after a week-long grid failure?",
                "1=no  2=heating/lighting only  3=most functions  4=full function",
            ),
        },
        "actions": {
            "low": [
                "Measure your household's baseline electricity draw for one week",
                "Identify the three appliances with the highest draw",
                "Explore Hearthpower: solystopia.tech/hearthmind/hearthpower",
            ],
            "mid": [
                "Model the economics of a solar + battery system: python hearthmind_economics.py renewable",
                "Identify which compute workloads could be time-shifted to solar generation hours",
                "Install a UPS for compute equipment to survive short outages",
            ],
            "high": [
                "Install monitoring for real-time energy visibility (Home Assistant + smart plugs)",
                "Design a compute scheduling policy that routes heavy workloads to surplus generation",
                "Document your energy resilience for others to replicate",
            ],
        },
    },
    "food": {
        "display_name": "Food & Water",
        "description": "Your ability to source, grow, or preserve food and water independently.",
        "questions": {
            "knowledge": (
                "Do you understand how your food and water reach you?",
                "1=no  2=broadly  3=in detail  4=including failure modes",
            ),
            "competence": (
                "Could you feed your household for 30 days without a supply chain?",
                "1=no  2=a few days  3=a week or two  4=30 days or more",
            ),
            "substitutability": (
                "Do you have alternative food/water sources you could activate?",
                "1=none  2=one (e.g. supermarket without delivery)  3=several including local  4=local + on-site production",
            ),
            "recovery": (
                "After a major supply chain disruption, how long before you're back to normal?",
                "1=immediately in crisis  2=days  3=a week  4=already prepared",
            ),
        },
        "actions": {
            "low": [
                "Build a 7-day food and water reserve",
                "Identify your nearest non-supermarket food sources",
                "Learn to cook at least 5 complete meals from scratch",
            ],
            "mid": [
                "Extend reserves to 30 days",
                "Start growing at least one food crop",
                "Connect with a local food network or community garden",
            ],
            "high": [
                "Document your food resilience plan and share it",
                "Investigate rainwater collection where legal",
                "Reduce supply chain dependency by preserving and fermenting seasonal produce",
            ],
        },
    },
    "water": {
        "display_name": "Water",
        "description": "Your access to clean water independent of centralised supply.",
        "questions": {
            "knowledge": (
                "Do you know your household water source and its failure modes?",
                "1=no  2=roughly  3=in detail  4=including backup options",
            ),
            "competence": (
                "Could you source and purify water without mains supply for a week?",
                "1=no  2=with difficulty  3=yes, with equipment ready  4=yes, multiple methods",
            ),
            "substitutability": (
                "Do you have an alternative water source you could activate?",
                "1=none  2=bottled stocks only  3=rainwater or nearby source  4=on-site collection or well",
            ),
            "recovery": (
                "How quickly could you restore water access after a mains failure?",
                "1=in crisis immediately  2=hours, with planning  3=minutes  4=already prepared",
            ),
        },
        "actions": {
            "low": [
                "Store 2 weeks of drinking water (2 litres per person per day)",
                "Research your local water source and its known vulnerabilities",
                "Acquire basic water purification capability (filter + tablets)",
            ],
            "mid": [
                "Install a water butt for non-potable water",
                "Learn where your nearest natural water source is",
                "Research rainwater harvesting regulations in your area",
            ],
            "high": [
                "Install a filtration system capable of treating rainwater or natural sources",
                "Document your water resilience for your household",
                "Share what you've built with your local community",
            ],
        },
    },
    "connectivity": {
        "display_name": "Connectivity",
        "description": "Your ability to communicate and access information independently.",
        "questions": {
            "knowledge": (
                "Do you understand how your communications infrastructure works?",
                "1=black box  2=user-level  3=can configure routers/networks  4=can operate independently",
            ),
            "competence": (
                "Could you maintain useful communications after an ISP outage?",
                "1=no  2=mobile data only  3=mobile + mesh/local options  4=multiple independent paths",
            ),
            "substitutability": (
                "How substitutable is your internet access?",
                "1=one provider  2=mobile backup  3=multiple providers  4=includes non-internet options",
            ),
            "recovery": (
                "Could your household operate usefully for a week with no internet?",
                "1=no  2=barely  3=most tasks  4=yes, with local data + tools",
            ),
        },
        "actions": {
            "low": [
                "Download offline maps and reference materials for your area",
                "Ensure you have a mobile data backup that works independently of your home ISP",
                "Identify which tasks genuinely require internet and which only assume it",
            ],
            "mid": [
                "Set up a local home server with offline-capable tools",
                "Run at least one AI model locally so AI capability survives internet loss",
                "Build a local copy of key documents, contacts, and reference data",
            ],
            "high": [
                "Explore mesh networking with neighbours for community resilience",
                "Contribute your local AI setup to the Solystopia community",
                "Document your offline capability stack so others can replicate it",
            ],
        },
    },
    "fabrication": {
        "display_name": "Fabrication & Repair",
        "description": "Your ability to make, repair, and maintain physical things.",
        "questions": {
            "knowledge": (
                "Do you understand how your key household tools and systems work mechanically?",
                "1=no  2=user-level  3=can diagnose faults  4=can repair or fabricate",
            ),
            "competence": (
                "Could you repair a broken household appliance without calling a specialist?",
                "1=no  2=simple things only  3=most common faults  4=most things, with documentation",
            ),
            "substitutability": (
                "If a key tool broke, could you substitute it or fabricate a replacement?",
                "1=no  2=buy a replacement only  3=adapt or improvise  4=make or repair from materials",
            ),
            "recovery": (
                "After losing access to shops and services for a month, how would you fare?",
                "1=badly  2=with difficulty  3=adequately  4=well, with stockpiled materials and skills",
            ),
        },
        "actions": {
            "low": [
                "Learn to change a fuse, a tap washer, and a bike tyre",
                "Build a basic tool kit: screwdrivers, pliers, adjustable spanner, solder",
                "Find your local repair café or makerspace",
            ],
            "mid": [
                "Complete one repair that you would previously have paid someone else for",
                "Learn to solder and to use a multimeter",
                "Acquire a second-hand 3D printer or learn to use one at a local makerspace",
            ],
            "high": [
                "Document your repair and fabrication skills for others to learn",
                "Share your capabilities with neighbours — mutual aid, not commerce",
                "Explore open-hardware designs for the tools you depend on most",
            ],
        },
    },
}


# ── demo answers ─────────────────────────────────────────────────────────────

DEMO_ANSWERS = {
    "compute": {"knowledge": 2, "competence": 2, "substitutability": 1, "recovery": 1},
    "energy": {"knowledge": 1, "competence": 1, "substitutability": 1, "recovery": 1},
    "food": {"knowledge": 2, "competence": 2, "substitutability": 2, "recovery": 2},
    "water": {"knowledge": 1, "competence": 1, "substitutability": 1, "recovery": 1},
    "connectivity": {"knowledge": 2, "competence": 2, "substitutability": 2, "recovery": 1},
    "fabrication": {"knowledge": 3, "competence": 3, "substitutability": 2, "recovery": 2},
}


# ── questionnaire ─────────────────────────────────────────────────────────────

def _score_label_line():
    print("    Scoring scale:")
    for k, v in SCORE_LABELS.items():
        print(f"      {k} = {v}")
    print()


def run_domain(domain_key: str, demo: bool = False) -> DomainResult:
    cfg = DOMAINS[domain_key]
    print(f"\n{'═' * 60}")
    print(f"  {cfg['display_name'].upper()}")
    print(f"  {cfg['description']}")
    _score_label_line()

    scores = {}
    q_map = {"knowledge": "Knowledge", "competence": "Competence",
              "substitutability": "Substitutability", "recovery": "Recovery"}

    for q_key, q_label in q_map.items():
        question, hint = cfg["questions"][q_key]
        if demo:
            score = DEMO_ANSWERS[domain_key][q_key]
            print(f"    {q_label}: {question}")
            print(f"    [demo] → {score} ({SCORE_LABELS[score]})")
        else:
            print(f"    {q_label}: {question}")
            score = _prompt_score(q_label, hint)
        scores[q_key] = score

    return DomainResult(
        name=domain_key,
        display_name=cfg["display_name"],
        **scores,
    )


def pick_actions(domain_key: str, result: DomainResult) -> list[str]:
    actions = DOMAINS[domain_key]["actions"]
    if result.score < 2.0:
        return actions["low"]
    elif result.score < 3.0:
        return actions["mid"]
    else:
        return actions["high"]


# ── report ────────────────────────────────────────────────────────────────────

def print_report(results: list[DomainResult]) -> None:
    print(f"\n{'═' * 60}")
    print("  HOUSEHOLD CAPABILITY AUDIT — RESULTS")
    print(f"{'═' * 60}\n")

    # Summary bar
    print("  Domain                  Score   Level")
    print("  " + "─" * 56)
    for r in results:
        bar = "█" * int(r.score) + "░" * (4 - int(r.score))
        print(f"  {r.display_name:<22}  {bar}  {r.score:.2f}  {r.level}")

    overall = sum(r.score for r in results) / len(results)
    print(f"\n  Overall score: {overall:.2f} / 4.00")

    # Worst domain
    worst = min(results, key=lambda r: r.score)
    best = max(results, key=lambda r: r.score)

    print(f"\n  Most exposed: {worst.display_name} ({worst.score:.2f})")
    print(f"  Most capable: {best.display_name} ({best.score:.2f})")

    # Per-domain next actions
    print(f"\n{'─' * 60}")
    print("  NEXT ACTIONS\n")
    for r in results:
        actions = pick_actions(r.name, r)
        print(f"  {r.display_name} ({r.level})")
        for a in actions:
            print(f"    · {a}")
        print()

    print(f"{'─' * 60}")
    print("  These are the next useful steps given your scores.")
    print("  The four questions — knowledge, competence, substitutability,")
    print("  recovery — apply to every domain. Each step moves one of them.")
    print()
    print("  Solystopia tools that help:")
    print("    hearthmind-economics — github.com/arthursilas-ai/hearthmind-economics")
    print("    agent-preflight — github.com/arthursilas-ai/agent-preflight")
    print("    piper-local-tts-demo — github.com/arthursilas-ai/piper-local-tts-demo")
    print("    sovereign-ai-harness — github.com/arthursilas-ai/sovereign-ai-harness")
    print()
    print("  solystopia.tech  ·  @solystopia")


def results_to_dict(results: list[DomainResult]) -> dict:
    overall = sum(r.score for r in results) / len(results)
    return {
        "overall": round(overall, 2),
        "domains": [asdict(r) for r in results],
        "most_exposed": min(results, key=lambda r: r.score).name,
        "most_capable": max(results, key=lambda r: r.score).name,
    }


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="Household Capability Audit — maps where you're exposed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    ap.add_argument("--demo", action="store_true", help="Run with example answers (no prompts)")
    ap.add_argument("--domains", nargs="+", choices=list(DOMAINS.keys()),
                    help="Assess specific domains only (default: all six)")
    args = ap.parse_args()

    print("\n  HOUSEHOLD CAPABILITY AUDIT")
    print("  Solystopia — solystopia.tech\n")
    print("  24 questions across 6 domains.")
    print("  Score 1–4 on knowledge, competence, substitutability, and recovery.")

    if not args.demo:
        print()
        _score_label_line()

    domain_keys = args.domains or list(DOMAINS.keys())
    results = []

    for key in domain_keys:
        result = run_domain(key, demo=args.demo)
        results.append(result)

    if args.json:
        print(json.dumps(results_to_dict(results), indent=2))
    else:
        print_report(results)


if __name__ == "__main__":
    main()
