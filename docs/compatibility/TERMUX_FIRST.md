# Termux-First Compatibility

YasinPress is intended to run as a first-class service on Termux/Android ARM64.

## Reference environment

- Termux on Android
- ARM64
- Python 3.14.x
- Android API 30 reference device
- No mandatory systemd dependency

## Runtime requirements

The runtime installation must succeed without requiring desktop-Linux-only packages. Native/build dependencies, when introduced, must be validated at runtime rather than only at build time.

The service entrypoint must support non-interactive operation and clean shutdown/restart on Termux.

## Validation

A Termux validation should cover:

1. Python version and ARM64/Android detection.
2. Clean virtual-environment installation of runtime dependencies.
3. `yasinpress version`, `status`, `health`, and `config`.
4. A real `yasinpress run` startup and clean shutdown.
5. SQLite/database initialization and runtime writes.
6. RSS/PWA output generation without requiring Eitaa credentials.
7. Scheduler/worker operation without systemd assumptions.
8. Python 3.14 compatibility.

Development-only tools that require native compilation must not block a valid runtime installation; their Android compatibility should be documented separately.
