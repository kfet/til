---
name: linux-fixed-timezone
description: "Pin a host (or a whole tailnet fleet) to a fixed permanent UTC-7 offset with no DST. TIL note about linux/macos timezone setup. Use when setting a box timezone, wanting year-round Pacific time with no daylight-saving switch, or rolling tz across many hosts via a jumpbox."
---

# Fixed permanent timezone (UTC-7, no DST)

Pin a box — or a whole tailnet fleet — to **permanent UTC-7 with no daylight-saving
switch** (the year-round Pacific offset BC observes). Use the fixed zone
`Etc/GMT+7`, not `America/Vancouver` (which still springs forward / falls back).

## Gotchas

- **`Etc/GMT+7` is UTC-7**, not +7 — POSIX inverts the sign in `Etc/GMT*` zones.
  It renders as `-07` / `-0700` with no DST transitions.
- There is **no zone named "PT"**. A fixed-offset zone is the honest way to get a
  single offset all year; accept the `-07` label.
- `timedatectl set-timezone` often needs interactive polkit auth and fails under
  ssh. The symlink method below works with plain `sudo -n`.

## Linux (per box)

```bash
sudo ln -sf /usr/share/zoneinfo/Etc/GMT+7 /etc/localtime
echo "Etc/GMT+7" | sudo tee /etc/timezone
date            # verify: ... -07 ...
```

The clock updates immediately, but long-running services that cached the zone at
startup (loggers, cron jobs) should be restarted to pick it up.

## macOS

Use the proper API (needs interactive sudo — no passwordless-ssh path):

```bash
sudo systemsetup -settimezone Etc/GMT+7
```

If `systemsetup -listtimezones` rejects `Etc/GMT+7`, symlink `/etc/localtime` to
`/usr/share/zoneinfo/Etc/GMT+7` interactively instead.

## Fleet fan-out via a jumpbox

Enumerate hosts, then set each one. Key placement decides the ssh form:

```bash
tailscale status                      # list peers; skip offline/phones
```

- Host's key is on **your** machine → ProxyJump works:
  `ssh -J <jumpbox> <host> '<cmd>'`
- Host's key lives **on the jumpbox** → run ssh *on* the jumpbox so its own
  identity is used: `ssh <jumpbox> 'ssh <host> "<cmd>"'`
  (ProxyJump would authenticate with your origin key and get
  `Permission denied (publickey)`).

Per-host command:

```bash
sudo -n ln -sf /usr/share/zoneinfo/Etc/GMT+7 /etc/localtime
echo "Etc/GMT+7" | sudo -n tee /etc/timezone >/dev/null
date
```

Skip iOS/Android peers and any host `tailscale status` shows as `offline`. Hosts
that time out during banner exchange are down/overloaded — note them and move on
rather than blocking the fan-out.

## References

- [tz database — Etc/GMT* fixed-offset zones](https://en.wikipedia.org/wiki/Tz_database#Area)
