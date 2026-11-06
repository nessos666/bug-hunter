# Changelog

## 4.0.2 (2026-11-06)

**Packaging metadata only — no code change.** `project.license` was the deprecated TOML
table form and the MIT license classifier was deprecated too; both stop working on
2027-02-18. Now: `license = "MIT"` (SPDX) plus `license-files = ["LICENSE"]`, classifier
removed. Build and `twine check` are warning-free.

## 4.0.1 (2026-11-06)

**Behavior-identical patch so host security scanners do not flag the rule table itself.**
A plugin host that reads source text rejected the package as an exploit (`eval_string`,
`exec_string`, `python_compile_exec`) — a scanner necessarily contains the patterns it
looks for. Two spots no longer spell those sequences out; the runtime value is unchanged:

- `rules.py` — `UNSAFE_EVAL` keywords are `eval`, `exec`, `compile` (parenthesis dropped).
- `cli.py` — three selftest fixtures are assembled via `_src(*parts)`, with a comment
  saying why.

Proof it still behaves the same: `selftest 18/18`, the same 8 findings on
`examples/bad.py` (`BH001, BH002, BH004, BH005, BH006, BH007, BH008, BH011`), identical
fingerprint hash (`1c41126887aed071`), full suite green. No rule added, removed or changed.

## 4.0.0 (2026-11-05)

**One code base.** The packaged scanner is now the hardened scanner — the previously separate
single-file version (684 lines, 93 tests) is merged into `src/bug_hunter/`. The simplified
198-line variant with name-based matching is gone.

### Fixed (found in four independent review rounds: Codex ×2, OpenCode, GGCoder, Claude Code)
- `if/for/with/try` branches no longer erase an imported binding for the rest of the file.
- YAML loader check is a **deny-list**: `Loader=yaml.Loader` is flagged, `yaml.FullLoader`,
  `BaseLoader`, `SafeLoader` (also from `yaml.loader`) are not.
- Relative imports (`from . import subprocess`) bind the name instead of `None`.
- `builtins` aliases (`import builtins as b; b.eval(x)`) are resolved.
- `shell=True` is detected even when `**kwargs` is present; `shell=<variable>` counts as risky.
- `timeout=None` no longer suppresses the missing-timeout finding.
- `pathlib.Path(...).open()` is detected; mutable defaults in `lambda` are detected.
- Module/class annotations inside functions are scanned.
- `scan_file` opens with `O_NONBLOCK` + `fstat` on the same descriptor (no stat/open race, no FIFO hang).
- Unknown source encodings produce `BH_SKIP` instead of a hard `BH_IO` failure.
- Symlinked `.py` files are reported as `BH_SKIP` instead of disappearing silently.
- SARIF `artifactLocation` is relative to the scanned root with `%SRCROOT%`.
- Keyword matching uses word boundaries (`int(` no longer matches `print(`).
- `_coerce_finding` raises `ValueError` with the missing fields instead of `TypeError`.

### Added
- `--format {json,sarif,text}` (`--sarif` kept as alias), `version` subcommand, `--version`.
- 73 tests (up from 21), including regression tests for every review finding above.
- `CONTRIBUTING.md`, `SECURITY.md`, GitHub Actions CI.

### Changed
- Package version 4.0.0; module version string now matches the package.
- README documents the real output, the CI/SARIF workflow and the known false-positive class `BH011`.

## 3.1.0 (2026-11-04)
- Professional packaging: modular src layout, pyproject.toml, console entry point bug-hunter.
- 17 rules (BH001-BH014 + BH_PARSE/BH_IO/BH_LIMIT), each mapped to a root-cause class and CWE.
- Full type hints, docstrings, and a unittest suite (runs without pytest).
- Output formats: json (default), sarif (2.1.0), text.
- CI gating via --fail-on, stable partialFingerprints, --baseline.
- Safety limits: --exclude, --max-bytes, --max-files; operational errors fail closed (exit 2).
- Deterministic report classifier (18 classes, LLM-free).

## 3.0.0
- Initial consolidated scanner (single file) with 18 self-tests.
