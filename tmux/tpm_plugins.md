## Common tpm plugins and configuration to add

See [tpm_install.md](tpm_install.md) for installing tmux plugin manager tpm.

This TIL is for tpm plugins.

`cat ~/.tmux.conf`
```
set -g @plugin 'b0o/tmux-autoreload'
set -g @plugin 'dracula/tmux'

# Dracula theme settings
set -g @dracula-plugins "ram-usage cpu-usage network weather"
set -g @dracula-cpu-usage-label "|"
set -g @dracula-ram-usage-label "|"
set -g @dracula-show-fahrenheit false
```
