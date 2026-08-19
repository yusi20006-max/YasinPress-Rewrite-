# CI Command Parity

The repository certification contract is intentionally duplicated in CI and release documentation so drift is testable.

Canonical commands:

```text
python -m compileall -q yasinpress tests
python -m pytest -q
ruff check .
python -m yasinpress.cli.main --help
```

The contract test `tests/test_ci_release_command_contract.py` verifies that every canonical command appears in both the CI workflow and the release gate. CI contains no production credentials and does not invoke external publishing.
