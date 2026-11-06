# bug_hunter

[![Tests](https://github.com/nessos666/bug-hunter/actions/workflows/ci.yml/badge.svg)](https://github.com/nessos666/bug-hunter/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Tests](https://img.shields.io/badge/tests-73%20passing-brightgreen)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

**Offline, deterministic, LLM-free Python bug scanner.**
Every finding carries a **CWE id**, a **root-cause class** and a stable **fingerprint**; output speaks
**SARIF 2.1.0** for GitHub code scanning.

No network. No API key. No model. Your code never leaves the machine — which is the point in
banking, health and government environments where cloud scanners are not allowed.

## Why

AI coding agents ship code faster than reviewers can read it. This tool is the first pass:
deterministic, reproducible, and boring on purpose. Same input → same output, always.

- **Deterministic** — no randomness, no clock, no model temperature. Findings are sorted and fingerprinted.
- **Read-only** — source is parsed with `ast`, never imported, never executed.
- **LLM-free** — no token cost, no hallucinated line numbers, no data leaving the host.
- **Honest** — heuristic AST checks. It does not prove exploits, and it says so.

## Install

From a checkout (no PyPI release yet):

```bash
git clone https://github.com/nessos666/bug-hunter.git && cd bug-hunter
pipx install .          # or: python3 -m pip install .
```

Requirements: Python >= 3.10, no runtime dependencies.

## Quickstart

```bash
bug-hunter selftest                 # 18/18 built-in cases
bug-hunter scan path/to/code        # JSON
bug-hunter scan path/to/code --format text
bug-hunter scan path/to/code --format sarif > results.sarif
```

Real output on the bundled example:

```
$ bug-hunter scan examples --format text
examples/bad.py:3:22 WARNING BH007 Mutable default argument
examples/bad.py:4:9 WARNING BH001 Dynamic eval/exec call: eval
examples/bad.py:5:5 WARNING BH004 Shell command execution; review input trust: os.system
examples/bad.py:6:5 ERROR   BH002 Unsafe deserialization via pickle/marshal: pickle.loads
examples/bad.py:7:9 NOTE    BH008 open() outside a context manager
examples/bad.py:10:5 WARNING BH005 Bare except catches BaseException
examples/bad.py:10:5 WARNING BH011 Exception handler silently discards exception
examples/bad.py:12:8 NOTE    BH006 Comparison to None using == or !=

8 finding(s)
```

## Commands

| Command | Purpose |
|---|---|
| `scan PATH` | scan a file or directory (`--format json\|sarif\|text`, `--fail-on`, `--baseline`, `--exclude`, `--max-bytes`, `--max-files`) |
| `report TEXT` | classify a traceback/report text into one of 18 root-cause classes |
| `rules` | print the rule table as JSON |
| `selftest` | run the 18 built-in cases |
| `version` | print version |

## Use in CI (GitHub code scanning)

```yaml
name: bug-hunter
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install .
      - run: bug-hunter scan . --format sarif --fail-on error > bug-hunter.sarif || true
      - uses: github/codeql-action/upload-sarif@v3
        with: { sarif_file: bug-hunter.sarif }
```

Findings then appear in the repository's **Security → Code scanning** tab.
`--fail-on error` additionally breaks the build on ERROR findings.

### Baselines (adopting on an existing codebase)

```bash
bug-hunter scan . > baseline.json
# later, only new findings are reported:
bug-hunter scan . --baseline baseline.json --fail-on warning
```

Fingerprints are content-based, so they survive code moving up or down the file.

## Rules

| ID | Root cause | CWE | Severity |
|---|---|---|---|
| BH001 | UNSAFE_EVAL — `eval`/`exec` | CWE-95 | WARNING |
| BH002 | UNSAFE_EVAL — `pickle`/`marshal`/`dill` | CWE-502 | ERROR |
| BH003 | UNSAFE_EVAL — unsafe YAML loader | CWE-502 | ERROR |
| BH004 | UNSAFE_SHELL — `os.system`/`os.popen` | CWE-78 | WARNING |
| BH005 | BAD_ERROR_HANDLING — bare `except` | CWE-703 | WARNING |
| BH006 | MISSING_GUARD — `== None` | — | NOTE |
| BH007 | DATA_SHAPE_MISMATCH — mutable default | — | WARNING |
| BH008 | RESOURCE_LEAK — `open()` without `with` | — | NOTE |
| BH009 | TIMEOUT — `subprocess` without timeout | CWE-400 | NOTE |
| BH010 | UNSAFE_EVAL — `yaml.unsafe_load` | CWE-502 | ERROR |
| BH011 | BAD_ERROR_HANDLING — silently swallowed exception | — | WARNING |
| BH012 | UNSAFE_SHELL — `shell=True` | CWE-78 | WARNING |
| BH013 | UNSAFE_EVAL — `compile()` | CWE-95 | WARNING |
| BH014 | UNSAFE_EVAL — `yaml.load` without a safe Loader | CWE-502 | ERROR |
| BH_SKIP | file not scanned (symlink / unknown encoding) | — | NOTE |

Operational diagnostics — `BH_IO` (unreadable), `BH_PARSE` (unparseable), `BH_LIMIT` (size/count limit) —
are always **ERROR** and always exit `2`, even with `--baseline`. A scan that could not finish must never look clean.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | clean, or only findings below `--fail-on` |
| 1 | findings at or above `--fail-on` |
| 2 | operational error (partial scan, unreadable/unparseable input, limit) |

## How it works

`ast` parse → single pass with **scope and binding tracking** (imports, aliases, relative imports,
`builtins`, function/class/lambda scopes, branch and loop merges) → rule match → finding with
CWE, root cause, remediation and a content fingerprint.

Binding tracking is what separates it from grep-style linters: `sp.run(..., shell=True)` is caught
after `import subprocess as sp`, while a local function named `run` is **not** reported.

## Limitations

Read this before trusting a number:

- **Heuristic, not sound.** No dataflow, no taint tracking, no interprocedural analysis, no proof of exploitability.
- **Precision is not calibrated yet.** There is no published precision/recall measurement against a
  labelled bug corpus. Expect false positives on dynamic code; use `--baseline`.
- **Some rules are noisy by design.** `BH011` fires on any `except …: pass`, including legitimate
  best-effort cleanup — a known false-positive class, not a defect in your code.
- **Python only.** No C, JS, Go, or cross-file call graphs.
- **Input to a review, not a verdict.**

## Development

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest                 # 73 tests
python3 -m bug_hunter selftest    # 18/18
```

No secrets, no network calls, no telemetry in the codebase — by design, not by promise.

## License

MIT — see [LICENSE](LICENSE).
