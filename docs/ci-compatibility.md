# CI / Runtime Compatibility

YasinPress declares `requires-python >=3.13` in `pyproject.toml`.

The CI workflow currently exercises Python 3.11, 3.12, and 3.13. Until the package metadata is intentionally broadened, 3.13 is the authoritative supported runtime and 3.11/3.12 are compatibility probes rather than supported production runtimes.
