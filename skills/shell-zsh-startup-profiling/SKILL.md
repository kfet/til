---
name: shell-zsh-startup-profiling
description: "Diagnose and fix slow zsh startup, and decide whether oh-my-zsh is worth keeping. TIL note about shell. Use when a shell feels slow to open, when profiling zsh with zprof, when considering oh-my-zsh or a zsh framework/plugin manager, or when writing a .zshrc to share across several machines."
---

# Diagnosing slow zsh startup (and whether to keep oh-my-zsh)

Numbers below come from measuring a mix of machines: x86_64 Ubuntu servers,
aarch64 and armv6l Raspberry Pis, and an arm64 Mac. Worst case went from
**~2.5s to well under 250ms**.

The headline lesson: **"oh-my-zsh is heavy" is usually wrong as a diagnosis.**
Profile first. The top three costs were, in order, a duplicated `compinit`,
`nvm`, and `eval "$(tool completion)"` subprocesses — none of which are
oh-my-zsh, and all of which survive a framework swap untouched.

Timings are illustrative of the *shape* of the problem, not targets. Slow
storage (SD card) and slow single-core CPUs magnify everything; on an SSD
x86 box the same mistakes cost tens of milliseconds instead of seconds.

## Measure before theorising

```bash
# median of 5, portable (works on macOS too — no /usr/bin/time -f)
zsh -c 'zmodload zsh/datetime
for i in {1..5}; do s=$EPOCHREALTIME; zsh -i -c exit >/dev/null 2>&1; e=$EPOCHREALTIME
  t+=( $(( (e-s)*1000 )) ); done
t=( ${(on)t} ); printf "%.0fms median\n" $t[3]'
```

Then profile — put `zmodload zsh/zprof` as the FIRST line of `.zshrc` and
`zprof` as the last.

### Three profiling traps that produce fake numbers

1. **Profiling in a sandbox `ZDOTDIR` with no zcompdump.** That forces a full
   completion rebuild, so `compinit`/`compdump` dominate and you "discover" a
   bottleneck that never happens in real use. Copy the real dump in, or profile
   the real config. A cold-dump profile showed 831 `compdef` calls; the warm
   number was 12.
2. **A leaked `ZDOTDIR` export**, making your "before" and "after" measure the
   same config. Wrap comparisons in `env -u ZDOTDIR`.
3. **Machine load.** A single-core ARMv6 box shortly after boot read 1942ms;
   idle, the same config read 915ms — a 2x error from background work alone.
   Check `/proc/loadavg` and wait for it to settle before trusting a number.

`zprof` only counts *functions*. If the total is much larger than the profile,
the rest is fork/exec and file parsing — real, but invisible there.

## The wins, in payoff order

### 1. Duplicated compinit — the big one on Debian/Ubuntu/Raspbian

`/etc/zsh/zshrc` runs an unconditional, uncached `compinit` **before** your
`.zshrc` gets control. Then oh-my-zsh (or your own rc) runs it again. The
escape hatch is documented in that file:

```bash
echo 'skip_global_compinit=1' >> ~/.zshenv
```

Empty-rc floor on a Pi: **390ms -> 40ms**. One line.

Then check for a *third* `compinit` in your own rc. A stray
`autoload -Uz compinit && compinit` below the framework block is common
copy-paste, and it re-dumps everything; hosts carrying one barely improved
until it was removed:

```bash
grep -n compinit ~/.zshrc      # should find none if a framework runs it
```

### 2. Cache compinit yourself

Full `compinit` scans and audits every `fpath` dir. Run it at most daily,
otherwise trust the dump, and compile it:

```zsh
autoload -Uz compinit
() {
  local dump=${ZDOTDIR:-$HOME}/.zcompdump
  zmodload -F zsh/stat b:zstat 2>/dev/null
  local -a st
  if zstat -A st +mtime "$dump" 2>/dev/null && (( EPOCHSECONDS - st[1] < 86400 )); then
    compinit -C -d "$dump"          # trust it
  else
    compinit -i -d "$dump"
    { rm -f "$dump.zwc"; zcompile -R -- "$dump" } &!
  fi
}
```

Pi: 1030ms -> 210ms. Verify the dump is actually reused — `stat` its mtime
across two shell starts. If it changes every time, it is being regenerated
and you are getting none of the benefit.

### 3. Never `eval "$(tool completion zsh)"` at startup

Each one is a process spawn on every shell. Measured on a Pi: `uv` 300ms warm
(4200ms cold), `bun` 600ms, `uvx` 155ms. Generate them to files once, at
install time, and put the dir on `fpath` before `compinit`:

```bash
mkdir -p ~/.zsh/completions
uv generate-shell-completion zsh > ~/.zsh/completions/_uv
gh completion -s zsh              > ~/.zsh/completions/_gh
rustup completions zsh            > ~/.zsh/completions/_rustup
rm -f ~/.zcompdump*   # force one rebuild so the new files register
```

`direnv hook zsh` is the exception — it must run, and it is only ~55ms.

### 4. Lazy-load nvm

`nvm.sh` cost **~2s** on one machine and ~515ms on another (via the `zsh-nvm`
plugin) — bigger than everything else combined. Put the default node on `PATH`
directly and defer the rest until first use:

```zsh
export NVM_DIR="$HOME/.nvm"
if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  if [[ -s "$NVM_DIR/alias/default" ]]; then
    _nvm_def=$(<"$NVM_DIR/alias/default")
    for _d in "$NVM_DIR/versions/node/v${_nvm_def#v}"*/bin(N); do path=($_d $path); break; done
    unset _nvm_def _d
  fi
  _nvm_load(){ unfunction nvm node npm npx 2>/dev/null; source "$NVM_DIR/nvm.sh" }
  nvm(){ _nvm_load; nvm "$@" }
  node(){ _nvm_load; command node "$@" }
  npm(){ _nvm_load; command npm "$@" }
  npx(){ _nvm_load; command npx "$@" }
fi
```

### 5. `tmux a` belongs in `.zprofile`, not `.zshrc`

In `.zshrc` it means: ssh -> zsh full init -> tmux -> *inner* zsh -> full init
again. You pay startup twice per login. Use `.zprofile` (login shells only),
and write `tmux attach || exec tmux new` so it does not error after a reboot.

## vcs_info is a per-prompt tax, not a startup cost

This is the trap that survives every startup optimisation, because it is paid
on **every Enter**, not once. On an ARMv6 Pi:

| approach | per prompt |
| --- | --- |
| `vcs_info`, branch only | 146ms |
| `vcs_info` + `check-for-changes` | 350ms |
| `vcs_info` when NOT in a repo | 34ms |
| raw `git rev-parse` subprocess | 38ms |
| **read `.git/HEAD` in pure zsh** | **1.4ms** |

`vcs_info` supports Mercurial, SVN, Bazaar and more; it is slower than just
shelling out to git, and it charges you even outside a repo. A branch name is
a string in a file:

```zsh
_git_branch() {
  REPLY=""
  local d=$PWD g
  while [[ $d != / ]]; do
    [[ -e $d/.git ]] && { g=$d/.git; break }
    d=${d:h}
  done
  [[ -n $g ]] || return
  [[ -f $g ]] && g=${$(<$g)#gitdir: }          # worktrees / submodules
  local head
  head=$(<$g/HEAD) 2>/dev/null || return
  if [[ $head == ref:* ]]; then REPLY=${head##*/}   # branch
  else REPLY=${head[1,7]}                            # detached: short sha
  fi
}
```

Validated against `git rev-parse` across many repos, plus detached HEAD,
subdirectory walk-up, and `.git`-as-a-file (worktrees, submodules).

### Prompt gotcha: colours inside `${...:+...}` break

```zsh
PROMPT+='${_pgit:+ %F{blue}git:(%F{red}${_pgit}%F{blue})%f}'   # WRONG
```

The `{` in `%F{blue}` closes the `:+` expansion early and you get literal
`master)}` junk in your prompt. Build the coloured segment in `precmd` and
reference a plain variable:

```zsh
precmd() {
  _git_branch
  if [[ -n $REPLY ]]; then _pgit=" %F{blue}git:(%F{red}${REPLY}%F{blue})%f"
  else _pgit=''; fi
}
PROMPT='%(?:%F{green}➜:%F{red}➜)%f %F{cyan}%c%f${_pgit} '
```

Needs `setopt prompt_subst`.

## Then decide about oh-my-zsh

Do the above first, *then* re-measure. What is left of oh-my-zsh is
`_omz_source` — reading ~23 lib and plugin files. That is a file-I/O cost, so
it scales with how slow the disk is:

- SSD/x86: ~100ms. Noise. Keeping omz is defensible.
- SD card / ARMv6: ~490ms of a 930ms startup. Worth removing.

**oh-my-zsh cannot be made to use a cached `compinit`.** It calls
`compinit -i -d` unconditionally and re-autoloads the function near the top of
`oh-my-zsh.sh`, so a shim defined earlier is clobbered. An `fpath`
override to shadow `compinit` *looks* like it works — it measured 0.61s vs
0.69s — but it recursed 498 times and silently disabled all completions and
aliases. **Any fix that makes things faster by breaking them will look like a
win in a benchmark.** Always assert correctness alongside timing:

```bash
zsh -i -c 'echo "aliases=$(alias|wc -l) git=${_comps[git]:-MISSING}"'
zsh -i -c exit 2>&1 | head   # must be empty
```

### Audit what you actually use before replacing anything

```bash
sed 's/^: [0-9]*:[0-9]*;//' ~/.zsh_history | awk '{print $1}' \
  | sort | uniq -c | sort -rn | head -40
```

In one such audit spanning ~9000 recorded commands, oh-my-zsh supplied 229
aliases and **4 were ever used**: `l`, `ll`, `ls`, `grep`. Zero git aliases —
`git` was typed bare ~1000 times. The only omz *function* ever called was
`omz` itself, to update it. Your own numbers will differ; run the audit rather
than assuming this result.

Two things people assume omz provides and it does not:

- **git completion.** `_git` ships with zsh at
  `/usr/share/zsh/functions/Completion/Unix/_git`. omz's git plugin contains
  no completion at all — just 197 aliases and 17 functions.
- **autosuggestions / syntax highlighting.** Not in omz core.

What you *do* lose and will miss silently is `lib/key-bindings.zsh` —
Home/End/Delete/Ctrl-arrow. Copy those bindings across.

## Plugins without a framework

A plugin is a file you `source`. No manager needed:

```bash
git clone --depth=1 https://github.com/zsh-users/zsh-autosuggestions \
  ~/.zsh/plugins/zsh-autosuggestions
```

```zsh
ZSH_AUTOSUGGEST_MANUAL_REBIND=1     # skips a widget rebind every prompt
source ~/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
# syntax-highlighting MUST be sourced last
source ~/.zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
```

ARMv6 cost: autosuggestions +36ms, syntax-highlighting +178ms (and the latter
adds per-keystroke lag on slow hardware — enable it on x86, not on Pis).

Not worth it: **zinit/znap/sheldon** (new dependency, per-arch binaries, and
they *defer* the completion cost rather than remove it); **starship** (another
binary per arch, plus a subprocess on every prompt draw — and note armv6l
boxes cannot run most prebuilt Rust binaries at all).

## Deploying across a fleet

Do not reach for a config manager. One `.zshrc` in a git repo, per-host bits
in `~/.zshrc.local`, and `scp`. When migrating, always:

- `zsh -n newrc` **before** installing it — it is a login shell on a remote box
- back up to a timestamped file, and leave `~/.oh-my-zsh` on disk
- carry the host-specific lines below the omz block into `~/.zshrc.local`
  rather than dropping them (pyenv/deno/govm/nvm shims live there)
- drive it over `ssh host 'bash -l -s' <<'EOF'`, so a broken zsh cannot lock
  you out

Migration also surfaces latent bugs the framework was masking. One host had
`eval "$(pyenv init - bash)"` — bash init in a zsh shell — which only stopped
being silent once omz's `bashcompinit` was gone. The fix was `- zsh`.

## Results

Grouped by hardware class, since that — not the config — determines the scale:

| class | before | after |
| --- | --- | --- |
| x86_64 server, SSD | 190-2560ms | 30-115ms |
| arm64 laptop, SSD | 646ms | 51ms |
| aarch64 SBC, SD card | 1340-1810ms | 198-234ms |
| armv6l SBC, SD card | 980-1220ms | 153-203ms |

The 2560ms outlier was eager `nvm` plus a duplicated `compinit`, not the
framework. Per-prompt cost went from ~146ms to ~1.9ms on the SD-card machines.

Two general shapes worth internalising:

- **Startup cost scales with storage speed**, because most of it is reading
  and parsing many small files. The same `.zshrc` is nearly free on an SSD.
- **Per-prompt cost scales with everything**, and is the one users actually
  feel. Optimise it first even though it does not show up in startup numbers.
