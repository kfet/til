---
name: tmux-session-persistence
description: "Persist and restore tmux sessions and windows across a server restart. TIL note about tmux. Use when working with tmux and the user mentions session persistence, resurrect, continuum, restoring windows or cwd after reboot, manually saving or restoring a snapshot, or a session that failed to restore / was not restored after a crash."
---

# Persist and restore tmux sessions and windows across a server restart

## Summary

tmux sessions already survive SSH disconnects. You only need this to
survive a **server kill or reboot**.

| Option | State | Notes |
|---|---|---|
| tmux-resurrect + tmux-continuum | 13.0k / 4.0k stars, last push 2024-08 | De-facto standard. Restores panes, layouts, optionally running programs. Little config with tpm — but read the resurrect + continuum gotchas first; it fails silently. |
| script below | tested | ~68 lines, one TSV file, no deps. Use when other tooling must **read** the state. |
| tmuxp | actively maintained | `tmuxp freeze` → YAML. Good for versioned project layouts. |

Prefer resurrect + continuum unless the state file must be machine-readable.

## Details

With tpm installed, add above the `run '.../tpm'` line, then `prefix + I`:

```tmux
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-restore 'on'
```

## Manual save and restore (resurrect)

Continuum is only automation around resurrect's two scripts. Both are
callable directly, which is what you want when auto-restore silently
does nothing (see *Gotchas → resurrect + continuum* below).

| Action | Key | Script |
|---|---|---|
| save | `prefix + C-s` | `~/.tmux/plugins/tmux-resurrect/scripts/save.sh` |
| restore | `prefix + C-r` | `~/.tmux/plugins/tmux-resurrect/scripts/restore.sh` |

```bash
~/.tmux/plugins/tmux-resurrect/scripts/restore.sh
```

Restore is safe to run against a live server: `restore.sh` guards with
`session_exists` / `window_exists` and skips anything already present,
so it only fills in what is missing. The corollary is that a window
index already in use is **not** restored — if the crashed server came
back with a placeholder window at index 0, the saved window 0 is lost.

Snapshots are per-run files plus a `last` symlink:

```bash
ls -lt ~/.local/share/tmux/resurrect/ | head
cat  ~/.local/share/tmux/resurrect/last     # TSV: pane/window/state lines
```

The save directory is **not** `~/.tmux/resurrect` unless that directory
already exists — `scripts/helpers.sh:1` prefers it only if present,
otherwise falls back to `${XDG_DATA_HOME:-$HOME/.local/share}/tmux/resurrect`.
Looking in the documented default and finding nothing proves nothing.
`@resurrect-dir` overrides both.

A snapshot is readable, so you can confirm what you are about to get
back before running restore — and recover a cwd list by hand if not.

## Script route

`~/.tmux/scripts/tmux-state.sh {save|restore|show|help}`. State defaults
to `~/.local/state/tmux/state.tsv` (`TMUX_STATE_FILE` overrides);
`TMUX_BIN` overrides the binary, which is how you test against a
throwaway socket. `restore` is idempotent — it only creates what is
missing, so it is safe to re-run.

Put it on `$PATH` so it is usable as a normal command. The usage text
derives its own name from `$0`, so the symlink reports `tmux-state`:

```bash
mkdir -p ~/.local/bin
ln -sfn ~/.tmux/scripts/tmux-state.sh ~/.local/bin/tmux-state
tmux-state --help
```

Restoring after a reboot is two commands, run from **outside** tmux:

```bash
tmux-state restore
tmux attach
```

That rebuilds the session/window skeleton with each window's saved cwd.
It does **not** restore running programs — that is what resurrect buys
you and this does not.

```bash
#!/usr/bin/env bash
# Minimal tmux session/window persistence.
set -uo pipefail

TMUX_BIN=${TMUX_BIN:-tmux}
STATE_FILE="${TMUX_STATE_FILE:-$HOME/.local/state/tmux/state.tsv}"
FMT='#{session_name}	#{window_index}	#{window_name}	#{pane_current_path}'

dump() { $TMUX_BIN list-windows -a -F "$FMT" 2>/dev/null; }

usage() {
  cat <<EOF
usage: ${0##*/} {save|restore|show|help}

Persist tmux sessions and windows across a server restart.

commands:
  save      snapshot live sessions/windows to the state file (default)
  restore   recreate any saved session/window that is missing; idempotent
  show      print live state to stdout without writing the state file
  help      this message

state file:
  $STATE_FILE
  TSV: session <TAB> window_index <TAB> window_name <TAB> cwd

environment:
  TMUX_STATE_FILE   state file path (default ~/.local/state/tmux/state.tsv)
  TMUX_BIN          tmux binary/socket (default: tmux); set to
                    "tmux -L test" to work against a throwaway server

notes:
  restore only creates what is missing, so it is safe to re-run. It
  restores the session/window skeleton with cwds, not running programs.
  save never overwrites the state file with an empty dump.
EOF
}

case "${1:-save}" in
  -h|--help|help) usage ;;
  show) dump ;;
  save)
    mkdir -p "$(dirname "$STATE_FILE")"
    out=$(dump) || exit 0
    [ -n "$out" ] || exit 0            # never clobber state with an empty dump
    printf '%s\n' "$out" > "$STATE_FILE.$$" && mv "$STATE_FILE.$$" "$STATE_FILE"
    ;;
  restore)
    [ -s "$STATE_FILE" ] || { echo "no state at $STATE_FILE" >&2; exit 1; }
    while IFS=$'\t' read -r sess idx name path; do
      [ -n "${sess:-}" ] || continue
      [ -d "${path:-}" ] || path="$HOME"
      : "${name:=$sess}"
      if ! $TMUX_BIN has-session -t "=$sess" 2>/dev/null; then
        $TMUX_BIN new-session -d -s "$sess" -n "$name" -c "$path" 2>/dev/null
        cur=$($TMUX_BIN list-windows -t "=$sess" -F '#{window_index}' 2>/dev/null | head -1)
        [ "${cur:-$idx}" = "$idx" ] || \
          $TMUX_BIN move-window -s "=$sess:$cur" -t "=$sess:$idx" 2>/dev/null
        continue
      fi
      if ! $TMUX_BIN list-windows -t "=$sess" -F '#{window_index}' 2>/dev/null \
           | grep -qx "$idx"; then
        $TMUX_BIN new-window -d -t "=$sess:$idx" -n "$name" -c "$path" 2>/dev/null
      fi
    done < "$STATE_FILE"
    ;;
  *) usage >&2; exit 2 ;;
esac
```

Every captured field comes from one format string, so extending it is a
one-line change:

```tmux
#{session_name}	#{window_index}	#{window_name}	#{pane_current_path}
```

## Auto-save hooks

```tmux
set-hook -g window-linked   'run-shell -b "~/.tmux/scripts/tmux-state.sh save"'
set-hook -g window-unlinked 'run-shell -b "~/.tmux/scripts/tmux-state.sh save"'
set-hook -g window-renamed  'run-shell -b "~/.tmux/scripts/tmux-state.sh save"'
set-hook -g session-closed  'run-shell -b "~/.tmux/scripts/tmux-state.sh save"'
set-hook -g client-detached 'run-shell -b "~/.tmux/scripts/tmux-state.sh save"'
```

## Periodic cwd capture

cwd changes are not hookable, so the hooks above only capture cwd at
window and session boundaries. If live cwd tracking matters, add a ~60s
timer running `save`.

Linux, `~/.config/systemd/user/tmux-state.timer` plus a matching
`tmux-state.service` running the script:

```ini
[Unit]
Description=Snapshot tmux session state

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min

[Install]
WantedBy=timers.target
```

macOS has no systemd — use a launchd agent at
`~/Library/LaunchAgents/tmux-state.plist`, then
`launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/tmux-state.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>tmux-state</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/YOU/.tmux/scripts/tmux-state.sh</string>
    <string>save</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>HOME</key><string>/Users/YOU</string>
    <key>TMUX_BIN</key><string>/opt/homebrew/bin/tmux</string>
  </dict>
  <key>StartInterval</key><integer>60</integer>
  <key>RunAtLoad</key><true/>
  <key>ProcessType</key><string>Background</string>
  <key>StandardErrorPath</key><string>/Users/YOU/Library/Logs/tmux-state.err.log</string>
</dict>
</plist>
```

launchd gives the job a bare `PATH` with no Homebrew, so pin `TMUX_BIN`
to an absolute path. Force a run with
`launchctl kickstart -p gui/$(id -u)/tmux-state`; disable with
`launchctl bootout gui/$(id -u)/tmux-state`.

To prove the timer really reaches the live server — rather than
silently saving nothing — delete the state file, kick the job, and
confirm it comes back populated.

## Verify (executable)

Never test against the live server — use a separate socket:

```bash
export TMUX_BIN="tmux -L statetest" TMUX_STATE_FILE=/tmp/statetest.tsv
tmux -L statetest new-session -d -s alpha -n edit -c /tmp
tmux -L statetest new-window -d -t alpha -n logs -c /var/log
~/.tmux/scripts/tmux-state.sh save
tmux -L statetest kill-server; sleep 0.3
~/.tmux/scripts/tmux-state.sh restore
~/.tmux/scripts/tmux-state.sh show   # expect alpha:0 edit /tmp, alpha:1 logs /var/log
tmux -L statetest kill-server
```

## Gotchas

Verified on tmux 3.4 and 3.7b.

- **`after-kill-window` does not exist.** tmux 3.4 rejects it with
  `invalid option`, breaking config load. The kill-side hook is
  `window-unlinked`.
- **`after-new-window` does not fire for a new session.** A session's
  first window is created internally, not via the `new-window` command.
  `window-linked` covers both, plus `move-window` and `link-window`.
- **`session-created` is redundant** once `window-linked` is set.
- **`window-renamed` is a window-scoped hook.** `set-hook -g` sets it
  correctly, but it lands in the global *window* option table, so
  `show-hooks -g` does not list it — only `show-hooks -gw` does. The
  other four hooks show under `-g`. Checking only `-g` makes a working
  hook look like it failed to register.
- **Hooks fire after the change lands** — a save triggered by
  `window-unlinked` does not see the killed window. No sleep needed.
- **Hooks can fire twice concurrently.** Writing `$STATE_FILE.$$` then
  `mv` means a race only loses the newer snapshot, never tears the file.
- **Never let an empty dump overwrite the state file.** Killing the last
  session dumps nothing; without the guard one clean shutdown erases
  everything.
- **A top-level `new-session` in `~/.tmux.conf`** creates a phantom
  session on a fresh server that collides with restore
  (`duplicate session: 0`). A naive `set -e` loop aborts on it and
  restores nothing. The `has-session` guard here tolerates it, but the
  phantom session gets saved and re-created forever.
- **tmux puts its socket in `/tmp/tmux-$UID`, not `$TMPDIR`** — unless
  `TMUX_TMPDIR` is set. This is what lets a launchd agent find the live
  server at all, since agents get a different `$TMPDIR` than your shell.
  Set `TMUX_TMPDIR` in a shell rc and the timer silently dumps nothing;
  the empty-dump guard then keeps the stale file, so state just freezes
  with no error. Export it to the timer too, or don't set it.
- **cwd changes are not hookable.** See *Periodic cwd capture* above;
  otherwise cwd is captured at window and session boundaries.

### resurrect + continuum

Verified on tmux 3.7c, resurrect `cff343c`, continuum `0698e8f`.

- **Continuum's multi-server guard silently disables everything.** Both
  auto-restore and auto-save are gated on
  `another_tmux_server_running_on_startup` (`continuum/scripts/helpers.sh:46`),
  which counts every `^tmux` process except your own server and trips at
  **more than one**:

  ```bash
  another_tmux_server_running_on_startup() {
      # there are 2 tmux processes (current tmux server + 1) on tmux startup
      [ "$(number_tmux_processes_except_current_server)" -gt 1 ]
  }
  ```

  The budget of one is your own client. *Any* second server — a
  `tmux -S .../claude.sock` from an agent tool, a stale `tmux -L test`
  from testing this very note — makes the count 2 and continuum refuses
  to act. Nothing is logged. `@continuum-restore` still reads `on`,
  which is why the config looks correct while doing nothing.

  Reproduce the decision without guessing:

  ```bash
  cd ~/.tmux/plugins/tmux-continuum/scripts && source ./helpers.sh
  all_tmux_processes
  number_tmux_processes_except_current_server
  another_tmux_server_running_on_startup && echo "restore+save SKIPPED"
  ```

- **The save half fails the same way, and that is the worse half.** A
  missed restore is visible; a missed save is not. Check whether
  auto-save is actually armed for this server:

  ```bash
  tmux show-option -gv status-right | grep -c continuum_save.sh   # 0 = disabled
  tmux show-option -gqv @continuum-save-last-timestamp            # empty = never saved
  ```

  Continuum has no timer — it *prepends* a `#(...continuum_save.sh)`
  interpolation to `status-right` and lets the status bar redraw drive
  it. If the guard tripped, the interpolation was never added and
  snapshots simply stop. Re-arm it by hand, below the tpm line (append
  is fine; the interpolation prints nothing):

  ```tmux
  set -ag status-right "#(~/.tmux/plugins/tmux-continuum/scripts/continuum_save.sh)"
  ```

- **Auto-restore only fires within 10s of server start.**
  `just_started_tmux_server` compares `#{start_time}` against
  `@continuum-restore-max-delay` (default 10). A slow plugin load, or
  sourcing the config by hand later, misses the window — so a manual
  `restore.sh` is the only route after that point.

- **Restoring processes is opt-in.** Without `@resurrect-processes`,
  only `@resurrect-default-processes` come back —
  `vi vim view nvim emacs man less more tail top htop irssi weechat mutt`.
  Everything else restores as a bare shell in the right cwd. A pane
  running a long-lived agent, dev server or watcher is *not* relaunched,
  even on a fully successful restore.
