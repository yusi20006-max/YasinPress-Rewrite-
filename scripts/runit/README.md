# YasinPress runit service

This directory contains the reproducible Termux `runit` service definition for YasinPress-Rewrite.

## Canonical service location

The installer deploys the service to:

```text
$PREFIX/var/service/yasinpress
```

This is the service directory monitored by the Termux `runsvdir` instance.

## Install / rebuild

From the repository root:

```sh
sh scripts/runit/install_yasinpress.sh
```

The installer:

1. Verifies `.venv/bin/yasinpress` exists.
2. Verifies Termux's `$PREFIX/var/service` exists.
3. Stops the current YasinPress service if present.
4. Installs the tracked `yasinpress/run` definition.
5. Makes the service executable.
6. Removes the previously attempted nested `log` service.
7. Starts YasinPress through `runit`.
8. Prints the final `sv status`.

## Service command

The tracked service definition is intentionally minimal:

```sh
#!/data/data/com.termux/files/usr/bin/sh

cd "$HOME/YasinPress-Rewrite-" || exit 1

exec "$HOME/YasinPress-Rewrite-/.venv/bin/yasinpress" run
```

`exec` ensures the supervised process is the YasinPress process itself.

## Operational commands

```sh
sv status "$PREFIX/var/service/yasinpress"
sv up "$PREFIX/var/service/yasinpress"
sv down "$PREFIX/var/service/yasinpress"
sv restart "$PREFIX/var/service/yasinpress"
sv kill "$PREFIX/var/service/yasinpress"
```

## Persistence behavior

`runsv` supervises `yasinpress run`. If the application process exits unexpectedly, `runit` starts it again. This behavior was validated on Termux by killing the active YasinPress process and observing a replacement process with a new PID.

## Logging

The current validated service does **not** include a nested `svlogd` logger. An earlier logger configuration repeatedly produced:

```text
unable to open supervise/ok: file does not exist
```

and did not create the expected `current` log file. The logger was therefore removed from the production service definition instead of keeping a known-broken configuration.

Persistent file logging can be implemented later as an independent operational task.

## Git policy

Commit these reproducible service definitions:

- `scripts/runit/yasinpress/run`
- `scripts/runit/install_yasinpress.sh`
- this README

Do **not** commit runtime-generated runit state such as:

- `supervise/`
- PID files
- control/status FIFOs
- `svlogd` runtime logs

The live Termux service remains outside the Git repository; Git stores only the instructions required to recreate it.
