#!/bin/bash
# TIL Tool Installer Script
#
# Installs the `til` CLI via pipx, clones (or updates) the skills
# repository, optionally drops shell completion into the right place,
# and prints a clear post-install summary with PATH guidance.

set -euo pipefail

# ----------------------------- arguments -----------------------------------
INSTALL_COMPLETION="ask"   # ask | yes | no
for arg in "$@"; do
    case "$arg" in
        --completion=yes|--completion) INSTALL_COMPLETION=yes ;;
        --completion=no|--no-completion) INSTALL_COMPLETION=no ;;
        --help|-h)
            cat <<'USAGE'
Usage: install.sh [--completion=yes|no]

  --completion=yes     install shell completion non-interactively
  --completion=no      skip the completion prompt
  (default: prompt when running interactively, skip otherwise)

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

# Banner
printf '\n=============================================\n'
printf '  Installing TIL CLI Tool\n'
printf '=============================================\n\n'

# ----------------------------- pipx ----------------------------------------
if ! has pipx; then
    note "Installing pipx..."
    pip install --user pipx
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
            [[ "$yn" =~ ^[Yy]$ ]] || { note "Skipping completion install."; return 0; }
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
