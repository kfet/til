# Git in Bash prompt

How to see git repository status in your bash prompt (see the .sh file for zsh instructions)

Save [git-prompt.sh](https://raw.githubusercontent.com/git/git/master/contrib/completion/git-prompt.sh) in `~/.bash/`

Add to `.bashrc`:

```
source ~/.bash/git-prompt.sh # Show git branch name at command prompt
export GIT_PS1_SHOWCOLORHINTS=true # Option for git-prompt.sh to show branch name in color

 # Include git branch, use PROMPT_COMMAND (not PS1) to get color output (see git-prompt.sh for more)
 export PROMPT_COMMAND='__git_ps1 "\u@\h \W" "\\\$ "' # Git branch (relies on git-prompt.sh)
```

```
# Set these to non-empty to enable by defaut. See git-prompt.sh for more.
export GIT_PS1_SHOWDIRTYSTATE="Y"
export GIT_PS1_SHOWSTASHSTATE="Y"
export GIT_PS1_SHOWUNTRACKEDFILES="Y"
```
