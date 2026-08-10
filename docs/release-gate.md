# YasinPress Release Gate

## Automated

- [ ] Python 3.11 CI passes
- [ ] Python 3.12 CI passes
- [ ] Python 3.13 CI passes
- [ ] `compileall` passes
- [ ] Full pytest suite passes

## Integration

- [ ] Feed ingestion reaches processing pipeline
- [ ] Duplicate feed items are rejected deterministically
- [ ] Article persistence survives restart
- [ ] Publisher retry records attempts and final outcome
- [ ] Successful delivery creates an idempotency key
- [ ] Repeated delivery does not publish twice
- [ ] Interrupted jobs recover on startup
- [ ] CLI health/config/runtime paths remain functional

## Release

- [ ] No unresolved production TODO/FIXME/NotImplemented markers
- [ ] README and operations documentation match the current runtime
- [ ] Version and changelog are synchronized
- [ ] CI is green on the release commit
