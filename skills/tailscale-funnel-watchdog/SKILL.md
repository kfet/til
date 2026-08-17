---
name: tailscale-funnel-watchdog
description: "Detect and auto-repair a Tailscale Funnel that has silently died -- public TLS handshakes fail while `tailscale funnel status` still says Funnel on. TIL note about tailscale. Use when working with tailscale and the user mentions funnel, a bot/service unreachable from the internet but fine on the tailnet, TLS handshake failures, SSL_ERROR_SYSCALL, or serve config."
---

# Tailscale Funnel watchdog (silent ingress death)

## Summary

A Funnel can stop serving the public internet while every local check says it
is healthy. Public TLS handshakes die; the tailnet path keeps working. This is
upstream bug [#14182](https://github.com/tailscale/tailscale/issues/14182)
(open and untriaged since Nov 2024). The only known recovery is an off/on
toggle. This TIL installs a small watchdog that detects it from the public side
and repairs itself.

## Details

### Symptom

- From the internet: TCP connects, then TLS dies immediately after ClientHello.
  `curl: SSL_ERROR_SYSCALL` / `unexpected eof while reading`, http code `000`.
- On the node: `tailscale funnel status` says **Funnel on**, cert valid,
  serve config intact, node Online, funnel nodeAttr present. Everything lies.
- Over the tailnet the same URL works fine.

### Why it happens

Public TLS is terminated **on your node** -- Tailscale's ingress boxes are
SNI-routed TCP forwarders that reach you over DERP. For that to work, the
ingress fleet must know where your node is.

The node advertises `Hostinfo.IngressEnabled` **edge-triggered** -- only when it
*changes*. There is no periodic re-assertion. If the ingress fleet drops the
node (it was offline/disconnected long enough), the node never re-announces,
because from its side nothing changed. Local status reports *intent*, not
reality. Toggling funnel off/on manufactures the state transition that
re-announces it.

### Diagnosing it (the important trick)

From a tailnet member, `curl https://<node>.ts.net/...` resolves via MagicDNS to
the node's `100.x` address and **never touches the Funnel ingress** -- so normal
monitoring is structurally blind to this failure. You must force the public path:

```bash
host=<node>.<tailnet>.ts.net
for ip in $(dig +short @1.1.1.1 $host A); do
  echo -n "$ip -> "
  curl -s -o /dev/null -w '%{http_code}\n' --max-time 15 \
       --resolve $host:443:$ip https://$host/
done
```

Any HTTP code = ingress healthy. `000` on every IP = ingress is dead.
Compare against a known-good node on the same tailnet to confirm.

### ⚠️ The landmine

`tailscale funnel --https=443 off` **wipes the entire serve config** -- every
path, not just the funnel flag. There is no "toggle" verb. Always capture
`tailscale serve status --json` first and replay the handlers. The watchdog
below does exactly that, and refuses to wipe if it cannot read the config back.

### Ruling out the other cause

Tailscale **1.102.1** shipped a real Funnel regression with an identical external
symptom (PR #20561 denied capabilities to `UnsignedPeerAPIOnly` peers, but
Funnel ingress nodes are unsigned by design, so every connection got 403'd).
Fixed in **1.102.2** by PR #20745. Distinguish them in the node's log:

- `peerapi: ingress: denied; no ingress cap` present → the cap bug, upgrade to ≥1.102.2.
- no such lines at all → connections never arrive → the #14182 registration bug, use this watchdog.

## Install (executable)

```bash
mkdir -p ~/.local/bin
cat > ~/.local/bin/funnel-watchdog <<'SCRIPT_EOF'
#!/usr/bin/env python3
"""Detect and repair a silently dead Tailscale Funnel ingress.

Upstream bug: tailscale/tailscale#14182. After the node is offline/disconnected
for a while, Tailscale's Funnel ingress fleet forgets it. The node never
re-announces, because from its side nothing changed: Hostinfo.IngressEnabled is
edge-triggered, not reconciled. So `tailscale funnel status` still says
"Funnel on", the TLS cert is still valid, the tailnet path still works -- and
every public request dies in the TLS handshake. Only an off/on toggle
re-announces it.

Healthy  = the public ingress completes TLS and returns ANY http status.
Broken   = TLS handshake fails (curl exit 35, http_code 000).

Nothing is hardcoded: the hostname comes from tailscale status, the ingress IPs
from public DNS (they change), the handlers from the live serve config (so the
repair replays whatever is actually configured).
"""

import json
import os
import subprocess
import sys
import time

STATE = os.path.expanduser("~/.cache/funnel-watchdog.state")
FAILS_BEFORE_REPAIR = 2      # consecutive bad probes before acting
MIN_REPAIR_INTERVAL = 900    # seconds; never thrash the toggle


def log(msg):
    print(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}", flush=True)


def run(*args, timeout=60):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except Exception:
        return {"fails": 0, "last_repair": 0}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w") as f:
        json.dump(s, f)


def public_ips(host):
    """Resolve via DoH so we bypass MagicDNS (which would return the 100.x).

    curl, not urllib: python's urllib stalls reaching 1.1.1.1 on macOS.
    """
    for resolver in ("https://1.1.1.1/dns-query?name={}&type=A",
                     "https://dns.google/resolve?name={}&type=A"):
        p = run("curl", "-s", "-m", "15", "-H", "Accept: application/dns-json",
                resolver.format(host), timeout=25)
        try:
            data = json.loads(p.stdout)
        except Exception:
            continue
        ips = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
        if ips:
            return ips
    return []


def repair(serve):
    """Replay the live config to force the IngressEnabled edge.

    `funnel off` wipes the ENTIRE serve config, so the caller must have
    captured it first.
    """
    handlers = []
    for hostport, cfg in (serve.get("Web") or {}).items():
        for path, h in (cfg.get("Handlers") or {}).items():
            if h.get("Proxy"):
                handlers.append((path, h["Proxy"]))
    if not handlers:
        log("ABORT no proxy handlers found; refusing to wipe config")
        return False

    log(f"REPAIR toggling funnel, replaying {len(handlers)} handler(s)")
    run("tailscale", "funnel", "--https=443", "off")
    time.sleep(2)
    for path, proxy in handlers:
        r = run("tailscale", "funnel", "--bg", "--https=443",
                f"--set-path={path}", proxy)
        if r.returncode != 0:
            log(f"  ERROR {path} -> {proxy}: {r.stderr.strip()[:200]}")
        else:
            log(f"  restored {path} -> {proxy}")
    return True


def main():
    st = run("tailscale", "status", "--json")
    if st.returncode != 0:
        log("SKIP tailscale status failed")
        return 0
    status = json.loads(st.stdout)
    if status.get("BackendState") != "Running":
        log(f"SKIP BackendState={status.get('BackendState')}")
        return 0
    host = status["Self"]["DNSName"].rstrip(".")

    sc = run("tailscale", "serve", "status", "--json")
    try:
        serve = json.loads(sc.stdout)
    except Exception:
        serve = {}
    if not serve.get("AllowFunnel"):
        log("SKIP no funnel configured")
        return 0

    if "--repair" in sys.argv:
        log("manual repair requested")
        return 0 if repair(serve) else 1

    try:
        ips = public_ips(host)
    except Exception as e:
        log(f"SKIP public DNS lookup failed: {e}")
        return 0
    if not ips:
        log(f"BROKEN-DNS {host} has no public A records "
            "(control is not publishing them) -- toggle will not help")
        return 1

    ok = False
    for ip in ips:
        p = run("curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "--max-time", "15", "--resolve", f"{host}:443:{ip}",
                f"https://{host}/")
        if p.stdout.strip() not in ("", "000"):
            ok = True
            break

    state = load_state()
    if ok:
        if state["fails"]:
            log(f"OK recovered after {state['fails']} bad probe(s)")
        state["fails"] = 0
        save_state(state)
        return 0

    state["fails"] += 1
    log(f"FAIL public TLS handshake dead on all {len(ips)} ingress IP(s) "
        f"(consecutive={state['fails']})")

    if state["fails"] < FAILS_BEFORE_REPAIR:
        save_state(state)
        return 1
    if time.time() - state["last_repair"] < MIN_REPAIR_INTERVAL:
        log("HOLD repaired too recently, not toggling again")
        save_state(state)
        return 1

    # Repair: replay the live config to force the IngressEnabled edge.
    if not repair(serve):
        save_state(state)
        return 1

    state["last_repair"] = time.time()
    state["fails"] = 0
    save_state(state)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"ERROR {type(e).__name__}: {e}")
        sys.exit(1)
SCRIPT_EOF
chmod +x ~/.local/bin/funnel-watchdog
~/.local/bin/funnel-watchdog && echo "healthy (silence is good)"
```

### macOS -- launchd, every 5 min (executable)

```bash
cat > ~/Library/LaunchAgents/dev.kfet.funnel-watchdog.plist <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>dev.kfet.funnel-watchdog</string>
  <key>ProgramArguments</key>
  <array><string>$HOME/.local/bin/funnel-watchdog</string></array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
  </dict>
  <key>StartInterval</key><integer>300</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/funnel-watchdog.log</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/funnel-watchdog.log</string>
</dict>
</plist>
PLIST
launchctl unload ~/Library/LaunchAgents/dev.kfet.funnel-watchdog.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/dev.kfet.funnel-watchdog.plist
launchctl list | grep funnel-watchdog
```

`PATH` matters: launchd gives no login shell, and the `tailscale` CLI lives in
`/usr/local/bin` on macOS.

### Linux -- systemd user timer, every 5 min (executable)

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/funnel-watchdog.service <<UNIT
[Unit]
Description=Repair silently dead Tailscale Funnel ingress (tailscale#14182)

[Service]
Type=oneshot
ExecStart=%h/.local/bin/funnel-watchdog
UNIT
cat > ~/.config/systemd/user/funnel-watchdog.timer <<UNIT
[Unit]
Description=Run funnel-watchdog every 5 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
UNIT
systemctl --user daemon-reload
systemctl --user enable --now funnel-watchdog.timer
systemctl --user list-timers funnel-watchdog.timer
```

If the funnel is owned by system `tailscaled` and the user cannot toggle it,
install the same unit under `/etc/systemd/system/` instead and drop `--user`.

## Usage

```bash
funnel-watchdog            # one probe; silent + exit 0 when healthy
funnel-watchdog --repair   # force the toggle now (safe: replays live config)
tail -f ~/Library/Logs/funnel-watchdog.log     # macOS
journalctl --user -u funnel-watchdog -f        # Linux
```

Behaviour: probes the public ingress every 5 min. Requires **2 consecutive**
failures before acting, and will not repair more than once per 15 min. It skips
entirely when tailscaled is not `Running`, when no funnel is configured, or when
public DNS has no A records (a different failure -- a toggle will not fix it).
It logs only when something is wrong, so an empty log is good news.

## Do not "simplify" this

- Do not hardcode ingress IPs. They change (`185.40.234.55/.75/.198` →
  `.37/.172/.210` within a week).
- Do not hardcode the handler list. The repair replays whatever the live serve
  config holds, which is what makes the wipe survivable.
- Do not probe over MagicDNS / the `100.x` address. That path stays healthy
  during this failure and will report all-clear while the bot is dark.
- Do not check for a specific HTTP status. Any status means TLS completed,
  which is the only thing being tested.

## References

- [#14182 funnel stops working after tailscaled stays offline for too long](https://github.com/tailscale/tailscale/issues/14182)
- [#20739 Funnel not working with Tailscale 1.102.1](https://github.com/tailscale/tailscale/issues/20739)
- [PR #20745 allow the ingress peer capability for unsigned peers](https://github.com/tailscale/tailscale/pull/20745)
