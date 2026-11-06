# Contributing

Thanks for taking a look. This is a small, deliberately boring tool — the bar for changing it is
that behaviour must stay **deterministic** and **explainable**.

## Ground rules

1. **No network, no LLM, no telemetry** in library code. Ever. A finding must be reproducible offline.
2. **Read-only.** Scanned source is parsed, never imported or executed.
3. **Every rule needs a test and a false-positive case.** A rule that only has a positive test will
   regress into noise.
4. **Fail closed.** If a scan could not be completed, the exit code is `2` — a partial scan must never
   look clean.
5. **No new runtime dependencies.** Standard library only.

## Setup

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m bug_hunter selftest
```

## Adding a rule

1. Add the entry to `RULES` in `src/bug_hunter/rules.py` (root cause, CWE if applicable, severity,
   description, remediation). Use the next free `BH0xx` id.
2. Emit it from `Scanner` in `src/bug_hunter/scanner.py`.
3. Add **two** tests in `tests/`: one that triggers it, one that must *not* trigger it
   (the false-positive case is the important one).
4. Note it in `CHANGELOG.md` and in the rule table in `README.md`.

## Reporting a false positive

Open an issue with the smallest snippet that reproduces it, the rule id, and what you expected.
False positives are the main quality metric here — they matter more than new rules.

## Style

- Type hints on public functions.
- `python3 -m pytest` must stay green; `python3 -m bug_hunter selftest` must stay at 18/18.
- Keep the scanner free of global state — one `Scanner` instance per file.

## Commits

Small, focused commits. Explain *why* in the message, not just *what*.
