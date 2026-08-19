# YasinPress Release Gate

## Automated repository gate

- [ ] Python 3.11 CI passes where compatibility workflow applies
- [ ] Python 3.12 CI passes where compatibility workflow applies
- [ ] Python 3.13 CI passes
- [ ] `compileall` passes
- [ ] Full pytest suite passes
- [ ] Ruff passes
- [ ] CLI help/startup contract passes
- [ ] Runtime Worker and persistent publication queue remain distinct
- [ ] No repository test requires production credentials or live external publishing

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
