# YasinPress Quality Gate

The release gate validates the package at three levels:

1. **Static contract** — package metadata, version, CLI entrypoint, package discovery, and required release documentation.
2. **Runtime smoke** — CLI version/status paths and database health wiring.
3. **CI execution** — Python 3.13 installation, compilation, full pytest suite, and Ruff.

The repository must not be marked READY solely from static checks. A successful current-main GitHub Actions run remains mandatory for the final release decision.
