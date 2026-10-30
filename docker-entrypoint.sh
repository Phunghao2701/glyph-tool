#!/bin/sh
set -eu

: "${VFK_KEYRING_PASSWORD:?Set VFK_KEYRING_PASSWORD in .env}"

exec dbus-run-session -- /bin/sh -eu -c '
  printf "%s" "$VFK_KEYRING_PASSWORD" | gnome-keyring-daemon --unlock --components=secrets >/dev/null
  eval "$(gnome-keyring-daemon --start --components=secrets)"
  exec "$@"
' docker-entrypoint "$@"
