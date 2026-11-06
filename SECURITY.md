# Security Policy

## Scope

`bug_hunter` is a **static analyzer**: it reads Python source and prints findings. It never imports,
executes, evaluates or sends scanned code anywhere. There is no network code, no telemetry and no
runtime dependency beyond the Python standard library.

## Reporting a vulnerability

Please report privately — do **not** open a public issue for a security problem.

Include:
- affected version (`bug-hunter version`),
- a minimal reproduction (source file plus the command you ran),
- what you expected versus what happened.

Especially interesting classes:
- a crafted input that makes the scanner hang or exhaust memory,
- a path traversal or symlink that makes it read outside the given root,
- a crash (`Traceback`) instead of a clean exit code `2`,
- a rule that can be bypassed trivially, so a real defect goes unreported.

## Guarantees this project intends to keep

| Guarantee | Meaning |
|---|---|
| Read-only | scanned files are opened `O_RDONLY`, never imported |
| Bounded | `--max-bytes`, `--max-files`, regular-file check, symlink policy |
| Fail closed | incomplete scan → exit code `2` |
| Deterministic | same input produces byte-identical output |
| Offline | no sockets opened by library code |

## Non-goals

- Proving exploitability.
- Full dataflow or taint analysis.
- Replacing a human security review.

Findings are review candidates. A clean scan is **not** a security guarantee, and this project does
not claim otherwise.
