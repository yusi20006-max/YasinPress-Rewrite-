# YasinPress Final Production Smoke Test

This checklist is the final operational certification gate after repository-side runtime certification, the Termux bootstrap, and Eitaa formatting fixes.

## Repository-side gate

Before using Termux, CI must certify:

- Runtime Worker and persistent publication queue remain separate.
- `RuntimeFactory.tick()` runs scheduler work, Worker execution, and persistent publication dispatch in the intended order.
- Persistent publication is idempotent and drains through the configured test publisher without external network I/O.
- The 12-hour freshness boundary is enforced before durable publication enqueue.
- Global and per-source publication limits remain covered by the existing queue regression suite.
- Repository-side tests pass without production credentials.

## Environment

- [ ] Run from a clean/current Termux environment using `scripts/install_termux.sh`.
- [ ] Confirm native `ruff --version` is available.
- [ ] Confirm `.env` contains no committed or logged credentials.
- [ ] Confirm configured Eitaa credentials are supplied only through the environment.

## Functional smoke cases

- [ ] Normal Persian title renders RTL correctly.
- [ ] Breaking Persian title renders the `خبر فوری` marker correctly.
- [ ] AI-modified article marker appears only when `ai_modified` is true.
- [ ] Title metadata suffixes are removed.
- [ ] HTML entities are escaped safely.
- [ ] Invisible bidi controls are absent from serialized message HTML.
- [ ] Source is rendered as a plain domain.
- [ ] Article URL is not emitted as a clickable/plain URL in the message body.
- [ ] Queue/retry/idempotency behavior remains unchanged.
- [ ] A real Eitaa publication succeeds with the configured production credentials.

## Automated repository gate

- [ ] `python -m compileall -q yasinpress tests`
- [ ] `python -m pytest -q`
- [ ] `ruff check .`
- [ ] `python -m yasinpress.cli.main --help`

Record the exact test count, commit SHA, Termux version, Python version, and any environment limitation before declaring `FINAL / GREEN`.
