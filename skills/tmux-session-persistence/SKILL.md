#!/usr/bin/env airan
---
name: tmux-session-persistence
description: "Persist and restore tmux sessions and windows across a server restart. TIL note about tmux. Use when working with tmux and the user mentions session persistence, resurrect, continuum, restoring windows or cwd after reboot, or related topics."
---

# Persist and restore tmux sessions and windows across a server restart

## Summary

tmux sessions already survive SSH disconnects. You only need this to
survive a **server kill or reboot**.

| Option | State | Notes |
|---|---|---|
| tmux-resurrect + tmux-continuum | 13.0k / 4.0k stars, last push 2024-08 | De-facto standard. Restores panes, layouts, optionally running programs. Zero code with tpm. |
| script below | tested | ~35 lines, one TSV file, no deps. Use when other tooling must **read** the state. |
| tmuxp | actively maintained | `tmuxp freeze` → YAML. Good for versioned project layouts. |

Prefer resurrect + continuum unless the state file must be machine-readable.

## Details

With tpm installed, add above the `run '.../tpm'` line, then `prefix + I`:

```tmux
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-restore 'on'
```

## Script route

`~/.tmux/scripts/tmux-state.sh {save|restore|show}`. State defaults to
`~/.local/state/tmux/state.tsv` (`TMUX_STATE_FILE` overrides); `TMUX_BIN`
overrides the binary, which is how you test against a throwaway socket.
`restore` is idempotent — it only creates what is missing.

```bash
#!/usr/bin/env bash
# Minimal tmux session/window persistence.
set -uo pipefail

TMUX_BIN=${TMUX_BIN:-tmux}
STATE_FILE="${TMUX_STATE_FILE:-$HOME/.local/state/tmux/state.tsv}"
FMT='#{session_name}	#{window_index}	#{window_name}	#{pane_current_path}'

dump() { $TMUX_BIN list-windows -a -F "$FMT" 2>/dev/null; }

case "${1:-save}" in
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
  *) echo "usage: $0 {save|restore|show}" >&2; exit 2 ;;
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

Verified on tmux 3.4.

- **`after-kill-window` does not exist.** tmux 3.4 rejects it with
  `invalid option`, breaking config load. The kill-side hook is
  `window-unlinked`.
- **`after-new-window` does not fire for a new session.** A session's
  first window is created internally, not via the `new-window` command.
  `window-linked` covers both, plus `move-window` and `link-window`.
- **`session-created` is redundant** once `window-linked` is set.
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
  restores nothing.
- **cwd changes are not hookable.** Add a ~60s systemd user timer running
  `save` if live cwd tracking matters; otherwise cwd is captured at
  window and session boundaries.
