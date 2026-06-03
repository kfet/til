---
name: linux-event-driven-rsync-backup
description: "Back up a data directory to a remote host automatically whenever it changes, using inotify + rsync as a systemd user service. TIL note about linux. Use when working with linux and the user mentions event-driven backup, inotify rsync, watch-and-sync, or scheduled/continuous backups."
---

# Event-driven rsync backup (inotify + systemd user service)

Continuously mirror a local data directory to a remote host **whenever it
changes** — no polling, no cron, no service downtime. An `inotifywait` watcher
debounces bursts (coalesces rapid writes into one sync after N seconds of
quiet), then runs an incremental `rsync`. Deleted/overwritten files are kept in
a dated history dir on the remote so an accidental local delete can't destroy
the backup.

## Prerequisites

```bash
sudo apt-get install -y inotify-tools   # provides inotifywait
which rsync                             # usually already present
ssh REMOTE 'echo ok'                    # passwordless SSH to the destination
ssh REMOTE 'mkdir -p ~/backups/APP'     # create the destination
```

## Watcher script — `~/.local/bin/APP-backup-watch`

```bash
#!/usr/bin/env bash
# Watch a data dir; rsync to REMOTE after a quiet period (debounce).
set -uo pipefail

SRC="$HOME/.local/share/APP/"          # trailing slash matters for rsync
DEST="REMOTE:backups/APP/"
QUIET="${BACKUP_QUIET:-30}"            # seconds of inactivity before syncing
SSH_OPTS="ssh -o BatchMode=yes -o ConnectTimeout=15"

do_sync() {
  local stamp; stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  rsync -az --delete \
    --backup --backup-dir="../APP-history/$stamp" \
    -e "$SSH_OPTS" "$SRC" "$DEST" \
    && echo "[$(date -u +%FT%TZ)] synced" \
    || echo "[$(date -u +%FT%TZ)] sync FAILED" >&2
}

echo "[$(date -u +%FT%TZ)] initial sync"; do_sync

inotifywait -m -r -q \
  -e modify,create,delete,move,close_write \
  --format '%e %w%f' "$SRC" | \
while true; do
  if read -r -t "$QUIET" _line; then
    dirty=1                            # event arrived; keep waiting for quiet
  else
    if [ "${dirty:-0}" = 1 ]; then do_sync; dirty=0; fi
  fi
done
```

```bash
chmod +x ~/.local/bin/APP-backup-watch
```

## Service — `~/.config/systemd/user/APP-backup.service`

```ini
[Unit]
Description=APP data backup (event-driven rsync to REMOTE)
After=network-online.target

[Service]
ExecStart=%h/.local/bin/APP-backup-watch
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now APP-backup.service
loginctl enable-linger "$USER"        # keep user services running after logout
```

## Operate

```bash
systemctl --user status APP-backup        # health
journalctl --user -u APP-backup -f        # watch syncs live
systemctl --user restart APP-backup       # apply script/QUIET changes
ssh REMOTE 'ls ~/backups/APP-history/'    # versioned deletes/overwrites
```

## Notes & gotchas

- **Debounce, not per-event.** Frequently-rewritten files (logs) would
  otherwise trigger constant syncs. `QUIET` (default 30s) is the quiet window
  after the last change before a sync fires. Tune via `BACKUP_QUIET` env.
- **`--delete` makes it a true mirror** — but `--backup --backup-dir=`
  rescues anything deleted/changed into `APP-history/<UTC-stamp>/` on the
  remote, so the mirror is safe against accidental local deletion.
- **No downtime.** It only reads the source; the watched app keeps running.
  Hot copies are fine for append-mostly data (feeds, logs); for a strictly
  consistent snapshot, stop the app around `do_sync`.
- **`loginctl enable-linger`** is what lets the user service survive logout /
  start at boot without an active session.
- **Prune history** with a separate timer if it grows unbounded, e.g.
  `find ~/backups/APP-history -maxdepth 1 -mtime +30 -exec rm -rf {} +`.
- Add the **binary + unit file** to `SRC` (or a second sync) if you want a
  full restore, not just the data dir.

## Restore

```bash
rsync -az REMOTE:backups/APP/ ~/.local/share/APP/
systemctl --user daemon-reload && systemctl --user enable --now APP-backup
```
