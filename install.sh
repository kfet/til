#!/bin/bash
# TIL Tool Installer Script
#
# Installs the `til` CLI via pipx, clones (or updates) the skills
# repository, optionally drops shell completion into the right place,
# and prints a clear post-install summary with PATH guidance.

set -euo pipefail

# ----------------------------- arguments -----------------------------------
INSTALL_COMPLETION="ask"   # ask | yes | no
UNINSTALL=no
KEEP_REPO=no
ASSUME_YES=no
for arg in "$@"; do
    case "$arg" in
        --completion=yes|--completion) INSTALL_COMPLETION=yes ;;
        --completion=no|--no-completion) INSTALL_COMPLETION=no ;;
        --uninstall) UNINSTALL=yes ;;
        --keep-repo) KEEP_REPO=yes ;;
        --yes|-y) ASSUME_YES=yes ;;
        --help|-h)
            cat <<'USAGE'
Usage: install.sh [--completion=yes|no]
       install.sh --uninstall [--keep-repo] [--yes]

  --completion=yes     install shell completion non-interactively
  --completion=no      skip the completion prompt
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

    # A Homebrew install must never be removed with pipx: they are
    # different installations, and pipx would silently report nothing to
    # do while leaving the brew copy on PATH.
    til_path="$(command -v til 2>/dev/null || true)"
    case "$til_path" in
        */Cellar/*|/opt/homebrew/*|/usr/local/Homebrew/*|/home/linuxbrew/*)
            err "This til was installed by Homebrew, not this script."
            warn "Remove it with:  brew uninstall til"
            exit 1
            ;;
    esac

    targets=()
    has pipx && pipx list 2>/dev/null | grep -q 'package til-cli' \
        && targets+=("pipx package til-cli")
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

    if has pipx && pipx list 2>/dev/null | grep -q 'package til-cli'; then
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

# ----------------------------- pipx ----------------------------------------
install_pipx() {
    # Ubuntu 24.04 / Debian 12+ ship PEP 668 "externally managed"
    # interpreters where `pip install --user` hard-fails, and a fresh
    # Ubuntu Server has no `pip` at all. Prefer the OS package manager,
    # which is the supported route on those systems.
    if has apt-get; then
        note "Installing pipx via apt..."
        sudo apt-get update -qq && sudo apt-get install -y pipx && return 0
    elif has dnf; then
        note "Installing pipx via dnf..."
        sudo dnf install -y pipx && return 0
    elif has brew; then
        note "Installing pipx via Homebrew..."
        brew install pipx && return 0
    fi

    note "Installing pipx via pip..."
    if python3 -m pip install --user pipx 2>/dev/null; then
        return 0
    fi
    # Last resort on PEP 668 systems without a packaged pipx.
    python3 -m pip install --user --break-system-packages pipx
}

if ! has pipx; then
    install_pipx || {
        err "Could not install pipx automatically."
        warn "Install it with your package manager, then re-run install.sh:"
        warn "  apt install pipx   |   dnf install pipx   |   brew install pipx"
        exit 1
    }
    export PATH="$PATH:$HOME/.local/bin"
    if ! has pipx; then
        err "pipx installation succeeded but command not found on PATH."
        warn "Run:   export PATH=\"\$PATH:\$HOME/.local/bin\"   then re-run install.sh"
        exit 1
    fi
    pipx ensurepath >/dev/null
fi

# ----------------------------- repo clone ----------------------------------
if [[ ! -d "$REPO_DIR" ]]; then
    note "Cloning TIL repository to $REPO_DIR..."
    git clone https://github.com/kfet/til.git "$REPO_DIR"
else
    note "TIL repository already exists at $REPO_DIR, updating..."
    (cd "$REPO_DIR" && git pull --ff-only --quiet) || \
        warn "git pull failed; continuing with existing checkout"
fi

# ----------------------------- pipx install --------------------------------
note "Installing TIL CLI tool..."
(cd "$REPO_DIR/til_cli" && pipx install --force . >/dev/null)

# Make sure ``til`` is reachable for the configure step below.
PIPX_BIN="$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || echo "$HOME/.local/bin")"
export PATH="$PATH:$PIPX_BIN"

if ! has til; then
    err "'til' was installed by pipx but is not on PATH (looked under $PIPX_BIN)."
    warn "Add this to your shell rc and reopen the shell:"
    warn "  export PATH=\"\$PATH:$PIPX_BIN\""
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

# ----------------------------- post-install summary ------------------------
printf '\n'
ok "Installation complete."
printf '\n'
echo "TIL repository: $REPO_DIR"
echo "til binary:     $(command -v til)"
echo
echo "Try:"
echo "  til list              # list every skill"
echo "  til search git        # search for git-related skills"
echo "  til show <slug>       # view a skill (uses bat/glow if installed)"
echo "  til validate          # check skill format"
echo "  til update            # pull latest skills"
echo
if ! has glow && ! has bat; then
    warn "Neither 'glow' nor 'bat' is installed — \`til show\` will print"
    warn "plain text. Install one of them for syntax-highlighted output."
fi
