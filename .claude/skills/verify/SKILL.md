---
name: verify
description: How to run and verify the daglint CLI end-to-end in this repo.
---

# Verifying daglint

The surface is the `daglint` CLI, installed editable in the project venv:

```bash
.venv/bin/daglint check examples/invalid_dag.py    # errors + warnings, exit 1
.venv/bin/daglint check examples/valid_dag.py      # clean, exit 0
```

- `examples/` has ready-made valid/invalid fixtures (classic and TaskFlow).
- For a warnings-only fixture, copy `examples/valid_dag.py` and delete the
  `doc_md=` line — only the warning-severity `doc_md_validation` rule fires.
- Always check `echo "EXIT=$?"` — exit-code semantics are part of the contract:
  0 = clean or warnings-only, 1 = errors (or any issue with `--strict`), 2 = usage error.
- `--format json` output must stay parseable when piped (`| python -m json.tool`),
  including with `--verbose`.
- `make check` runs format-check + lint + tests; run it before committing.
