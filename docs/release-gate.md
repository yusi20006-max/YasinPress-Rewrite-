# YasinPress Release Gate

## Canonical repository certification commands

The repository gate and CI must execute this exact command set:

```text
python -m compileall -q yasinpress tests
python -m pytest -q
ruff check .
python -m yasinpress.cli.main --help
```

## Automated repository gate

- [ ] Python 3.11 CI passes where compatibility workflow applies
- [ ] Python 3.12 CI passes where compatibility workflow applies
- [ ] Python 3.13 CI passes
- [ ] `python -m compileall -q yasinpress tests` passes
- [ ] `python -m pytest -q` passes
- [ ] `ruff check .` passes
- [ ] `python -m yasinpress.cli.main --help` passes
- [ ] Runtime Worker and persistent publication queue remain distinct
- [ ] No repository test requires production credentials or live external publishing

## CI automation boundary

All workflows under `.github/workflows/` are repository verification only:

- Workflows declare explicit read-only `contents` permissions.
- Workflows must not reference repository secrets or production tokens.
- Workflows must not invoke live Eitaa, Telegram, or other external publisher calls.
- The Ruff workflow may calculate safe fixes in its ephemeral runner workspace, but it must not commit or push changes.
- Live production publication remains an operational Termux gate and is never part of GitHub Actions.

The regression suite enforces this boundary for every workflow file so a future workflow cannot silently reintroduce credentials or live publishing.

## Integration

- [ ] Feed ingestion reaches processing pipeline
- [ ] Duplicate feed items are rejected deterministically
- [ ] Article persistence survives restart
- [ ] Publisher retry records attempts and final outcome
- [ ] Successful delivery creates an idempotency key
- [ ] Repeated delivery does not publish twice
- [ ] Interrupted jobs recover on startup
- [ ] Freshness and publication rate limits remain enforced
- [ ] CLI health/config/runtime paths remain functional

## Operational production gate

These checks cannot be represented as repository-only completion:

- [ ] Final clean/current Termux smoke test
- [ ] Live Eitaa publication with production credentials
- [ ] Production AI provider verification
- [ ] PWA/RSS public hosting verification, if release scope requires it

## Release decision

A repository merge may certify the **repository code gate** only. The release must not be called fully production-certified until the operational production gate is explicitly recorded in `docs/RELEASE_STATUS.md`.
