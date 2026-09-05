# household-capability-audit

[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![pypi](https://img.shields.io/pypi/v/solystopia-household-capability-audit.svg)](https://pypi.org/project/solystopia-household-capability-audit/)

A structured questionnaire that maps where your household is exposed: where you have genuine capability, where you have access masquerading as capability, and where you are simply dependent.

Part of the [Solystopia](https://solystopia.tech) open-source toolkit.

---

## What it does

24 questions across 6 domains, scored against the four Solystopia capability questions:

| Question | What it tests |
|---|---|
| **Knowledge** | Do you understand how this works, or just how to use it? |
| **Competence** | Can you do it yourself, or only instruct a service? |
| **Substitutability** | Can you swap the supplier without losing the function? |
| **Recovery** | Can you get back to normal without the exact same infrastructure? |

**Six domains assessed:**
1. Compute & AI
2. Energy
3. Food & Water
4. Water
5. Connectivity
6. Fabrication & Repair

Output: a dependency profile with per-domain scores, a visual summary, and concrete next-action suggestions calibrated to where you are.

---

## Install

No dependencies beyond Python 3.9+. No repo to clone required — pick one:

```bash
# From PyPI
pip install solystopia-household-capability-audit
household-capability-audit

# As an agent skill (Claude Code, Cursor, Copilot, and others)
npx skills add arthursilas-ai/household-capability-audit

# Or standalone — one file, no install
curl -O https://raw.githubusercontent.com/arthursilas-ai/household-capability-audit/main/audit.py
python audit.py
```

---

## Usage

```bash
# Interactive questionnaire — all six domains
python audit.py

# Run with example answers to see what the output looks like
python audit.py --demo

# Assess specific domains only
python audit.py --domains compute energy

# Machine-readable output
python audit.py --json
python audit.py --demo --json
```

---

## Example output

```
  HOUSEHOLD CAPABILITY AUDIT — RESULTS

  Domain                  Score   Level
  ────────────────────────────────────────────────────────────
  Compute & AI            ██░░  2.00  partially dependent
  Energy                  █░░░  1.00  fully dependent
  Food & Water            ██░░  2.00  partially dependent
  Water                   █░░░  1.00  fully dependent
  Connectivity            ██░░  1.75  partially dependent
  Fabrication & Repair    ███░  2.50  partially capable

  Overall score: 1.71 / 4.00

  Most exposed: Energy (1.00)
  Most capable: Fabrication & Repair (2.50)

  NEXT ACTIONS

  Compute & AI (partially dependent)
    · Run a local model once — llama.cpp + a GGUF file is the minimum viable step
    · Document what cloud services you depend on and what would break without them
    · Read the Sovereign AI Harness: github.com/arthursilas-ai/sovereign-ai-harness
```

---

## The scoring scale

| Score | Level | Meaning |
|---|---|---|
| 4 | Fully capable | You understand it, can do it yourself, can swap suppliers, and can recover from failure |
| 3 | Partially capable | You can do it, but with constraints |
| 2 | Partially dependent | Some understanding or skill, but significant lock-in |
| 1 | Fully dependent | You rely entirely on a service you don't control or understand |

---

## Context

This audit is the entry point for the Solystopia approach to household resilience. The four capability questions — knowledge, competence, substitutability, recovery — apply consistently across every domain. Each step you take in any domain moves one of those dials.

The audit was designed as the starting point referenced in the `/tools` page of [solystopia.tech](https://solystopia.tech/tools) — the thing you do before you build.

Other tools in the Solystopia open-source ecosystem:
- [hearthmind-economics](https://github.com/arthursilas-ai/hearthmind-economics) — cost calculators for household compute
- [agent-preflight](https://github.com/arthursilas-ai/agent-preflight) — pre-deployment checks for AI agents
- [piper-local-tts-demo](https://github.com/arthursilas-ai/piper-local-tts-demo) — local text-to-speech
- [sovereign-ai-harness](https://github.com/arthursilas-ai/sovereign-ai-harness) — 10-stage local AI setup guide

---

## License

MIT.
