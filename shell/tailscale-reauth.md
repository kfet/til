# Re-authenticate tailscale node with one line

Extend the node key expiry, or disable then enable key expiry on the node, which effectively extends it for another 30m.

Generate a one-use auth key on the console:
https://login.tailscale.com/admin/settings/keys

Run on the node
```sh
sudo tailscale up --force-reauth --accept-risk=lose-ssh --authkey <the-new-key>
```

Verify on the Machines tab of the console:
https://login.tailscale.com/admin/machines

