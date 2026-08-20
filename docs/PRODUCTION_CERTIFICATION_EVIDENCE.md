# Production Certification Evidence

This document defines the evidence required to move YasinPress from repository-code GREEN to operational `FINAL / GREEN`.

## Boundary

GitHub Actions certifies repository code only. Production certification is performed manually on the target Termux host. Production credentials stay in the local environment and are never printed, committed, or used by automated CI.

## Preflight

Run from the deployed YasinPress checkout:

```sh
python scripts/production_certification_preflight.py --json
```

The preflight is read-only. It never calls an external publisher and reports only whether protected environment variables are configured, never their values.

## Required evidence

Record these fields in `docs/RELEASE_STATUS.md` before declaring `FINAL / GREEN`:

- repository commit SHA
- YasinPress package version
- Python version
- Termux/platform information
- Ruff version
- Hermes service state
- Yasin-AI service state
- YasinPress service state
- YasinRelay service state
- protected credential configuration status (configured/not configured only)
- manual Eitaa smoke-test result
- manual production AI-provider result
- final operator timestamp

## Manual production gate

After preflight passes, the operator may perform the live Eitaa publication using credentials already configured in the local environment. The token and any provider credentials must never be copied into logs, issue comments, PRs, screenshots, or repository files.

The final evidence should state success/failure and relevant non-secret identifiers only.
