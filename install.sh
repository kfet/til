#!/bin/bash
# TIL Tool Installer Script
#
# Installs the `til` CLI via uv (preferred) or pipx, clones (or updates) the skills
# repository, optionally drops shell completion into the right place,
# and prints a clear post-install summary with PATH guidance.

set -euo pipefail

# ----------------------------- arguments -----------------------------------
INSTALL_COMPLETION="ask"   # ask | yes | no
INSTALL_AIRAN="ask"        # ask | yes | no
UNINSTALL=no
KEEP_REPO=no
ASSUME_YES=no
for arg in "$@"; do
    case "$arg" in
        --completion=yes|--completion) INSTALL_COMPLETION=yes ;;
        --completion=no|--no-completion) INSTALL_COMPLETION=no ;;
        --airan=yes|--airan) INSTALL_AIRAN=yes ;;
        --airan=no|--no-airan) INSTALL_AIRAN=no ;;
        --uninstall) UNINSTALL=yes ;;
        --keep-repo) KEEP_REPO=yes ;;
        --yes|-y) ASSUME_YES=yes ;;
        --help|-h)
            cat <<'USAGE'
Usage: install.sh [--completion=yes|no] [--airan=yes|no]
       install.sh --uninstall [--keep-repo] [--yes]

  --completion=yes     install shell completion non-interactively
  --completion=no      skip the completion prompt
  --airan=yes          also install airan (needed only by `til run`)
  --airan=no           skip the airan prompt
  (default: prompt when running interactively, skip otherwise)

  --uninstall          remove the CLI, completions, config and repo clone
  --keep-repo          with --uninstall: keep the cloned skills repo
  --yes, -y            do not prompt for confirmation

Environment:
  TIL_INSTALL_DIR      where to clone the TIL repo (default: ~/.til-repo)
USAGE
            exit 0
            ;;
    esac
done

# Default installation directory
REPO_DIR="${TIL_INSTALL_DIR:-$HOME/.til-repo}"

# ----------------------------- helpers -------------------------------------
note()  { printf '\033[1;34m▸\033[0m %s\n' "$*"; }
ok()    { printf '\033[1;32m✓\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m!\033[0m %s\n' "$*" >&2; }
err()   { printf '\033[1;31m✗\033[0m %s\n' "$*" >&2; }

has() { command -v "$1" >/dev/null 2>&1; }

# ----------------------------- uninstall -----------------------------------
if [ "$UNINSTALL" = yes ]; then
    printf '\n=============================================\n'
    printf '  Uninstalling TIL CLI Tool\n'
    printf '=============================================\n\n'

    # A Homebrew install must never be removed with uv/pipx: they are
    # different installations, and uv/pipx would silently report nothing to
    # do while leaving the brew copy on PATH.
    til_path="$(command -v til 2>/dev/null || true)"
    case "$til_path" in
        */Cellar/*|/opt/homebrew/*|/usr/local/Homebrew/*|/home/linuxbrew/*)
            err "This til was installed by Homebrew, not this script."
            warn "Remove it with:  brew uninstall til"
            exit 1
            ;;
    esac

    uv_has_til()   { has uv   && uv tool list --color never 2>/dev/null | grep -q '^til-cli '; }
    pipx_has_til() { has pipx && pipx list 2>/dev/null | grep -q 'package til-cli'; }

    targets=()
    uv_has_til   && targets+=("uv tool til-cli")
    pipx_has_til && targets+=("pipx package til-cli")
    for f in "$HOME/.local/share/bash-completion/completions/til" \
             "$HOME/.zsh/completions/_til" \
             "$HOME/.tilconfig" \
             "$HOME/.til_last_update"; do
        [ -e "$f" ] || [ -L "$f" ] && targets+=("$f")
    done
    if [ "$KEEP_REPO" = no ] && [ -d "$REPO_DIR" ]; then
        targets+=("$REPO_DIR  (skills repo clone)")
    fi

    if [ ${#targets[@]} -eq 0 ]; then
        ok "Nothing to remove — til does not appear to be installed."
        exit 0
    fi

    note "The following will be removed:"
    for t in "${targets[@]}"; do printf '    %s\n' "$t"; done
    printf '\n'

    if [ "$ASSUME_YES" != yes ] && [ -t 0 ]; then
        read -r -p "Proceed? [y/N] " reply
        case "$reply" in
            [yY]|[yY][eE][sS]) ;;
            *) note "Aborted."; exit 0 ;;
        esac
    fi

    if uv_has_til; then
        uv tool uninstall til-cli >/dev/null 2>&1 \
            && ok "removed uv tool til-cli" \
            || warn "uv tool uninstall til-cli failed — remove it manually"
    fi
    if pipx_has_til; then
        pipx uninstall til-cli >/dev/null 2>&1 \
            && ok "removed pipx package til-cli" \
            || warn "pipx uninstall til-cli failed — remove it manually"
    fi

    for f in "$HOME/.local/share/bash-completion/completions/til" \
             "$HOME/.zsh/completions/_til" \
             "$HOME/.tilconfig" \
             "$HOME/.til_last_update"; do
        if [ -e "$f" ] || [ -L "$f" ]; then
            rm -f "$f" && ok "removed $f"
        fi
    done

    if [ "$KEEP_REPO" = no ] && [ -d "$REPO_DIR" ]; then
        # This script may live inside REPO_DIR. Unlinking it is safe —
        # bash keeps reading through its open fd — but the working
        # directory must not be the tree being deleted.
        cd /
        rm -rf "$REPO_DIR" && ok "removed $REPO_DIR"
    elif [ "$KEEP_REPO" = yes ]; then
        note "kept skills repo at $REPO_DIR"
    fi

    printf '\n'
    ok "til uninstalled."
    note "If you added completions to your ~/.zshrc fpath by hand,"
    note "that line is still there — remove it if you want."
    exit 0
fi

# Banner
printf '\n=============================================\n'
printf '  Installing TIL CLI Tool\n'
printf '=============================================\n\n'

# ----------------------------- uv / pipx -----------------------------------
# Use whichever tool installer is already present — uv first, then pipx.
# If neither is available, install uv (standalone, no system Python
# packaging involved, so PEP 668 is a non-issue).
install_uv() {
    if has curl; then
        note "Installing uv via astral.sh installer..."
        curl -LsSf https://astral.sh/uv/install.sh | sh && return 0
    elif has wget; then
        note "Installing uv via astral.sh installer..."
        wget -qO- https://astral.sh/uv/install.sh | sh && return 0
    fi
    if has brew; then
        note "Installing uv via Homebrew..."
        brew install uv && return 0
    fi
    return 1
}

if has uv; then
    INSTALLER=uv
elif has pipx; then
    INSTALLER=pipx
else
    install_uv || {
        err "Could not install uv automatically."
        warn "Install uv (https://docs.astral.sh/uv/) or pipx, then re-run install.sh:"
        warn "  curl -LsSf https://astral.sh/uv/install.sh | sh   |   brew install uv"
        exit 1
    }
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
    if ! has uv; then
        err "uv installation succeeded but command not found on PATH."
        warn "Run:   export PATH=\"\$HOME/.local/bin:\$PATH\"   then re-run install.sh"
        exit 1
    fi
    INSTALLER=uv
fi
ok "Using $INSTALLER ($(command -v "$INSTALLER"))"

# ----------------------------- repo clone ----------------------------------
if [[ ! -d "$REPO_DIR" ]]; then
    note "Cloning TIL repository to $REPO_DIR..."
    git clone https://github.com/kfet/til.git "$REPO_DIR"
else
    note "TIL repository already exists at $REPO_DIR, updating..."
    (cd "$REPO_DIR" && git pull --ff-only --quiet) || \
        warn "git pull failed; continuing with existing checkout"
fi

# ----------------------------- tool install --------------------------------
note "Installing TIL CLI tool with $INSTALLER..."
if [ "$INSTALLER" = uv ]; then
    (cd "$REPO_DIR/til_cli" && uv tool install --quiet --force --reinstall . >/dev/null)
    TOOL_BIN="$(uv tool dir --bin --color never 2>/dev/null || echo "$HOME/.local/bin")"
else
    (cd "$REPO_DIR/til_cli" && pipx install --force . >/dev/null)
    TOOL_BIN="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo "$HOME/.local/bin")"
fi

# Make sure ``til`` is reachable for the configure step below.
export PATH="$PATH:$TOOL_BIN"

if ! has til; then
    err "'til' was installed by $INSTALLER but is not on PATH (looked under $TOOL_BIN)."
    warn "Add this to your shell rc and reopen the shell:"
    warn "  export PATH=\"\$PATH:$TOOL_BIN\""
    [ "$INSTALLER" = uv ] && warn "  (or run:  uv tool update-shell)"
    exit 1
fi

# ----------------------------- configure -----------------------------------
note "Configuring repository location..."
til config "$REPO_DIR" >/dev/null

# ----------------------------- shell completion ----------------------------
maybe_install_completion() {
    case "$INSTALL_COMPLETION" in
        no) return 0 ;;
        ask)
            # Prompt only when running interactively.
            if [[ ! -t 0 || ! -t 1 ]]; then
                note "Shell completion: skipped (non-interactive run)."
                note "Pass --completion=yes to install it, or see"
                note "  $REPO_DIR/completions/README.md"
                return 0
            fi
            read -r -p "Install shell completion (bash/zsh)? [y/N] " yn
            case "$yn" in
                y|Y|yes|YES|Yes) ;;
                *) note "Skipping completion install."; return 0 ;;
            esac
            ;;
    esac

    local shell_name installed=0
    shell_name="$(basename "${SHELL:-/bin/bash}")"

    if [[ "$shell_name" == "bash" ]] || [[ "$INSTALL_COMPLETION" == "yes" ]]; then
        local bash_dir="$HOME/.local/share/bash-completion/completions"
        mkdir -p "$bash_dir"
        ln -sf "$REPO_DIR/completions/til.bash" "$bash_dir/til"
        ok "Installed bash completion -> $bash_dir/til"
        installed=1
    fi

    if [[ "$shell_name" == "zsh" ]] || [[ "$INSTALL_COMPLETION" == "yes" ]]; then
        local zsh_dir="$HOME/.zsh/completions"
        mkdir -p "$zsh_dir"
        ln -sf "$REPO_DIR/completions/_til" "$zsh_dir/_til"
        ok "Installed zsh completion -> $zsh_dir/_til"
        cat <<EOF
   Make sure your ~/.zshrc contains, before \`compinit\`:
       fpath=($zsh_dir \$fpath)
       autoload -Uz compinit && compinit
EOF
        installed=1
    fi

    if [[ $installed -eq 0 ]]; then
        note "Unknown shell '$shell_name'; see $REPO_DIR/completions/README.md"
    fi
}

maybe_install_completion

# ----------------------------- airan (optional) ----------------------------
# `til run` dispatches a skill to an AI coding agent through airan
# (https://github.com/kfet/airan). Everything else — list/search/show/
# execute/validate — works without it, so airan is OFFERED, never
# imposed: nobody gets a Go binary pushed on them for `til show`.
AIRAN_STATUS="not installed"

maybe_install_airan() {
    if has airan; then
        AIRAN_STATUS="already installed ($(command -v airan))"
        return 0
    fi

    case "$INSTALL_AIRAN" in
        no) AIRAN_STATUS="skipped (--airan=no)"; return 0 ;;
        ask)
            if [[ ! -t 0 || ! -t 1 ]]; then
                AIRAN_STATUS="skipped (non-interactive run)"
                note "airan: skipped (non-interactive run). Only \`til run\` needs it;"
                note "  pass --airan=yes, or install later from"
                note "  https://github.com/kfet/airan"
                return 0
            fi
            echo
            note "airan dispatches a skill to an AI coding agent (\`til run\`)."
            note "Optional: every other til command works without it."
            read -r -p "Install airan? [y/N] " yn
            case "$yn" in
                y|Y|yes|YES|Yes) ;;
                *) AIRAN_STATUS="skipped"; note "Skipping airan install."; return 0 ;;
            esac
            ;;
    esac

    if ! has curl; then
        AIRAN_STATUS="failed (curl not found)"
        warn "Cannot install airan: curl not found."
        return 0
    fi

    note "Installing airan..."
    if curl -fsSL https://raw.githubusercontent.com/kfet/airan/main/install.sh | sh; then
        if has airan; then
            AIRAN_STATUS="installed ($(command -v airan))"
        else
            # The installer commonly drops the binary in ~/.local/bin,
            # which may not be on PATH in this shell.
            AIRAN_STATUS="installed (not on PATH in this shell)"
        fi
        ok "airan: $AIRAN_STATUS"
    else
        AIRAN_STATUS="failed"
        warn "airan install failed; \`til run\` will not work until it is on PATH."
    fi
}

maybe_install_airan

# ----------------------------- post-install summary ------------------------
printf '\n'
ok "Installation complete."
printf '\n'
echo "TIL repository: $REPO_DIR"
echo "til binary:     $(command -v til)"
echo "airan:          $AIRAN_STATUS"
echo
echo "Try:"
echo "  til list              # list every skill"
echo "  til search git        # search for git-related skills"
echo "  til show <slug>       # view a skill (uses bat/glow if installed)"
echo "  til validate          # check skill format"
echo "  til path <slug>       # print a skill's file path"
echo "  til run <slug>        # apply a skill to this host via an AI agent"
echo "  til update            # pull latest skills"
echo
if ! has airan; then
    note "\`til run\` needs airan. Install it any time with:"
    note "  curl -fsSL https://raw.githubusercontent.com/kfet/airan/main/install.sh | sh"
fi
if ! has glow && ! has bat; then
    warn "Neither 'glow' nor 'bat' is installed — \`til show\` will print"
    warn "plain text. Install one of them for syntax-highlighted output."
fi
