# YasinPress Release Candidate

## Release baseline

- Package: `yasinpress-rewrite`
- Current version: `1.0.0`
- Authoritative runtime: Python `>=3.13`
- Default branch: `main`

## Verified repository configuration

- Canonical publishing contract is exposed from `yasinpress.publishing`.
- Legacy publishing imports are compatibility-shimmed through the canonical contract.
- SQLite persistence covers application state and publishing state.
- GitHub Actions runs compilation and pytest across the configured Python matrix.

## Release gate

The repository should only be marked **READY** after the current `main` commit has a successful GitHub Actions run and the full test suite passes in CI.

No production support claim is made for Python 3.11/3.12 merely because they are present in the CI matrix; `pyproject.toml` declares Python `>=3.13` as the supported runtime.
