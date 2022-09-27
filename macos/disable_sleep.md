# Disable sleep of macOs

This disables sleep even if not connected to power or lid of laptop is down.

Disable sleep:
```bash
sudo pmset -b disablesleep 1
```

Check curtent setting, look for SleepDisabled
```bash
pmset -g
```

Re-enable sleep
```bash
sudo pmset -b disablesleep 0
```
