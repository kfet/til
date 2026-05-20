# Bash completion for the `til` CLI.
#
# Install:
#     # one-shot:
#     source /path/to/til/completions/til.bash
#     # persistent (bash-completion v2):
#     ln -s /path/to/til/completions/til.bash \
#           ~/.local/share/bash-completion/completions/til

_til() {
    local cur prev cmd
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Find the subcommand (first non-option argument).
    local i
    cmd=""
    for ((i=1; i<COMP_CWORD; i++)); do
        local w="${COMP_WORDS[i]}"
        case "$w" in
            --repo-path|--repo-path=*) ;;
            -*) ;;
            *)
                if [[ -z "$cmd" ]]; then
                    cmd="$w"
                fi
                ;;
        esac
    done

    # Honour --repo-path so completion targets the right repo.
    local repo_args=()
    for ((i=1; i<COMP_CWORD; i++)); do
        if [[ "${COMP_WORDS[i]}" == "--repo-path" && $((i+1)) -lt COMP_CWORD ]]; then
            repo_args=(--repo-path "${COMP_WORDS[i+1]}")
        elif [[ "${COMP_WORDS[i]}" == --repo-path=* ]]; then
            repo_args=(--repo-path "${COMP_WORDS[i]#*=}")
        fi
    done

    # Complete the option value for --repo-path with directories.
    if [[ "$prev" == "--repo-path" ]]; then
        COMPREPLY=( $(compgen -d -- "$cur") )
        return 0
    fi

    # Subcommand slot.
    if [[ -z "$cmd" ]]; then
        local cmds
        cmds="$(til _complete commands 2>/dev/null)"
        COMPREPLY=( $(compgen -W "$cmds --repo-path" -- "$cur") )
        return 0
    fi

    case "$cmd" in
        show|validate)
            local slugs
            slugs="$(til "${repo_args[@]}" _complete slugs 2>/dev/null)"
            COMPREPLY=( $(compgen -W "$slugs" -- "$cur") )
            ;;
        execute)
            # Argument position within the execute command: 1 = entry, 2 = section.
            local exec_argc=0 j
            for ((j=1; j<COMP_CWORD; j++)); do
                if [[ "${COMP_WORDS[j]}" == "execute" ]]; then
                    exec_argc=$((COMP_CWORD - j - 1))
                    break
                fi
            done
            if (( exec_argc <= 0 )); then
                local slugs
                slugs="$(til "${repo_args[@]}" _complete slugs 2>/dev/null)"
                COMPREPLY=( $(compgen -W "$slugs" -- "$cur") )
            elif (( exec_argc == 1 )); then
                # Section for the previously-given entry.
                local entry="${COMP_WORDS[COMP_CWORD-1]}"
                local sections
                sections="$(til "${repo_args[@]}" _complete sections "$entry" 2>/dev/null)"
                COMPREPLY=( $(compgen -W "$sections" -- "$cur") )
            fi
            ;;
        config)
            # Argument is a directory path.
            COMPREPLY=( $(compgen -d -- "$cur") )
            ;;
        *)
            COMPREPLY=()
            ;;
    esac
    return 0
}

complete -F _til til
