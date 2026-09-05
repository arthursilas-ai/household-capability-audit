---
name: household-capability-audit
description: A 24-question audit across 6 domains (compute, energy, food, water, connectivity, fabrication) that scores knowledge, competence, substitutability, and recovery for each. Use when someone wants to know where a household, small team, or organization is dependent on providers it can't easily replace, or wants a starting point before investing in local/offline capability.
---

# Household Capability Audit

Maps where you're exposed before you decide what to build. Six domains,
four questions each, scored 1 (fully dependent) to 4 (fully capable).

## Run it

```bash
python3 audit.py                    # interactive, all 6 domains
python3 audit.py --domains compute energy   # just the domains you care about
python3 audit.py --demo             # see sample output without answering
python3 audit.py --demo --json      # machine-readable output, for scripting
```

The four questions per domain:

1. **Knowledge** — do you understand the system well enough to reason about it?
2. **Competence** — could you operate or rebuild it yourself?
3. **Substitutability** — could you swap the provider without losing function?
4. **Recovery** — could you restore it after total failure?

## When to use it

- Someone is planning a move toward local/offline capability (compute,
  energy, food, etc.) and doesn't know where to start.
- Assessing single points of failure in a household's or small team's
  reliance on outside providers.
- As the entry point before `hearthmind-economics` or
  `sovereign-ai-harness` — this tells you *where* you're exposed; the
  others tell you what it costs to fix and how.

## Install

```bash
pip install git+https://github.com/arthursilas-ai/household-capability-audit.git
household-capability-audit --demo
```

Or as an agent skill: `npx skills add arthursilas-ai/household-capability-audit`
