---
name: linux-event-driven-rsync-backup
description: "Back up a data directory to a remote host automatically whenever it changes, using inotify + rsync as a systemd user service. TIL note about linux. Use when working with linux and the user mentions event-driven backup, inotify rsync, watch-and-sync, or scheduled/continuous backups."
---

# Event-driven rsync backup (inotify + systemd user service)

Continuously mirror a local data directory to a remote host **whenever it
changes** — no polling, no cron, no service downtime. An `inotifywait` watcher
debounces bursts (coalesces rapid writes into one sync after N seconds of
quiet), then runs an incremental `rsync`.

> **Default to a latest-only mirror.** Version *only* the handful of files that
> are irreplaceable and human-curated. Do **not** snapshot the whole tree on
> every sync — see the warning below.

## ⚠️ Do not snapshot every sync (the trap)

The obvious "safety" move is `rsync --backup --backup-dir=../APP-history/<ts>`
on every run, so deleted/overwritten files are stashed remotely. With an
*event-driven* watcher this is a disk-fill bomb: every sync that touches a
frequently-rewritten file (logs, append ndjson, etag state) copies the **whole
old file** into a **new dated dir**, and nothing prunes them. A real case: a
~80M data set produced 3815 history dirs and filled a 228G remote to 100%.

Instead:

- Keep **one latest mirror** (`--delete`, no `--backup-dir`).
- **Version only the irreplaceable curated files** (e.g. an OPML feed list, a
  config you hand-edit) as immutable timestamped copies — those are tiny and
  change rarely.
- Guard the mirror with **`--max-delete`** so a local corruption/wipe aborts
  the sync instead of propagating.
- Don't back up **derivable / telemetry** data at all (caches, poll logs,
  rebuildable indexes) — `--exclude` it.

## Prerequisites

```bash
sudo apt-get install -y inotify-tools   # provides inotifywait
which rsync                             # usually already present
ssh REMOTE 'echo ok'                    # passwordless SSH to the destination
ssh REMOTE 'mkdir -p ~/backups/APP ~/backups/APP-curated'
```

## Watcher script — `~/.local/bin/APP-backup-watch`

```bash
#!/usr/bin/env bash
# Watch a data dir; rsync to REMOTE after a quiet period (debounce).
# Latest-only mirror + version-history for curated files only.
set -uo pipefail

SRC="$HOME/.local/share/APP/"          # trailing slash matters for rsync
DEST="REMOTE:backups/APP/"
CURATED="$SRC/subscriptions.opml"      # the one irreplaceable, hand-edited file
CURATED_DEST_DIR="backups/APP-curated" # remote, relative to REMOTE:~
STATE_DIR="$HOME/.local/state/APP-backup"
QUIET="${BACKUP_QUIET:-30}"            # seconds of inactivity before syncing
MAX_DELETE="${BACKUP_MAX_DELETE:-500}" # abort if a sync would delete more
SSH_OPTS="ssh -o BatchMode=yes -o ConnectTimeout=15"
ts() { date -u +%FT%TZ; }

mirror() {
  rsync -az --delete --max-delete="$MAX_DELETE" \
    --exclude='observe/' --exclude='*.tmp' --exclude='.*.tmp' \
    -e "$SSH_OPTS" "$SRC" "$DEST"
  local rc=$?
  [ "$rc" -eq 0 ] && echo "[$(ts)] mirror ok" \
                  || echo "[$(ts)] mirror FAILED (rc=$rc)" >&2
}

# Immutable timestamped copy of a curated file, only when its content changes.
# Change detected via a locally-cached hash (no remote round-trip per sync).
archive_curated() {
  [ -f "$CURATED" ] || return 0
  mkdir -p "$STATE_DIR"
  local sum prev stamp
  sum="$(sha256sum "$CURATED" | awk '{print $1}')"
  prev="$(cat "$STATE_DIR/curated.sha" 2>/dev/null || true)"
  [ "$sum" = "$prev" ] && return 0
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  if rsync -az -e "$SSH_OPTS" \
       --rsync-path="mkdir -p $CURATED_DEST_DIR && rsync" \
       "$CURATED" "REMOTE:$CURATED_DEST_DIR/$(basename "$CURATED").$stamp"; then
    echo "$sum" > "$STATE_DIR/curated.sha"
    echo "[$(ts)] curated archived $stamp"
  else
    echo "[$(ts)] curated archive FAILED" >&2
  fi
}

do_sync() { mirror; archive_curated; }

echo "[$(ts)] initial sync"; do_sync

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
ssh REMOTE 'ls ~/backups/APP-curated/'    # versioned curated files
```

## Compression: don't gzip the mirror

A natural urge is to compress the remote copy. **Per-file gzip breaks rsync**:
a compressed file changes entirely when its source changes, so you lose both
delta transfer *and* the unchanged-file check, and every sync re-ships the
whole file.

- **Wire compression** is free and on: `rsync -z` (already in the script).
- **Storage compression** belongs at the **filesystem layer** on the
  destination (btrfs/zfs with `zstd`) — transparent to rsync, all checks stay
  effective, text data shrinks ~5-10x.
- A periodic `tar.zst` *cold archive* is a separate tool: great compression,
  but no incrementality and no mirror semantics. Only add it if you genuinely
  need whole-dataset point-in-time rollback; append-mostly / re-derivable data
  usually doesn't.

## Notes & gotchas

- **Debounce, not per-event.** Frequently-rewritten files would otherwise
  trigger constant syncs. `QUIET` (default 30s) is the quiet window after the
  last change before a sync fires. Tune via `BACKUP_QUIET`.
- **`--delete` makes it a true mirror.** Pair it with `--max-delete` so a
  local disaster aborts (rsync rc 25) and is logged, instead of silently
  wiping the backup.
- **Excluded files are protected from `--delete`** on the receiver. To purge
  something you newly excluded (e.g. an old `observe/`) from an existing
  mirror, run once with `--delete-excluded`, or `rm -rf` it on the remote.
- **No downtime.** It only reads the source; the watched app keeps running.
  Hot copies are fine for append-mostly data; for a strictly consistent
  snapshot, stop the app around `do_sync`.
- **`loginctl enable-linger`** is what lets the user service survive logout /
  start at boot without an active session.
- Add the **binary + unit file** to a second sync if you want a full restore,
  not just the data dir.

## Restore

```bash
systemctl --user stop APP
rsync -az REMOTE:backups/APP/ ~/.local/share/APP/
# curated point-in-time: pick a copy from REMOTE:backups/APP-curated/
systemctl --user start APP
```
