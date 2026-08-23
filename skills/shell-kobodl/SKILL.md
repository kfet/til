---
name: shell-kobodl
description: "Download DRM-free EPUBs of books you own from the Kobo store with kobodl. Use when the user mentions kobodl, kobo-book-downloader, fetching or exporting Kobo ebooks, or finding their most recent Kobo purchase."
---

# kobodl — download your Kobo books as DRM-free EPUBs

## Summary

[`kobodl`](https://github.com/subdavis/kobo-book-downloader) exports books you
own from the Kobo store as plain EPUBs. It authenticates with the same
**device activation** flow a physical Kobo e-reader uses, so there is no
password prompt, no captcha, and no browser automation to keep working.

## Details

Pure Python, no native dependencies — identical setup on macOS and
Linux/ARM. Credentials land in `~/.config/kobodl.json` (device id, user key,
access/refresh tokens) and are reused indefinitely.

That file is a **secret**. Never commit it or paste it anywhere. Copying it to
another host is a legitimate way to skip re-activation there; `kobodl user add`
again to rotate.

## Install (executable)

```bash
uv tool install kobodl
```

Or with pipx:

```bash
pipx install kobodl
```

## Configure (executable)

```bash
kobodl user add
```

This prints a short activation code. Open <https://www.kobo.com/activate> on
any device, sign in, enter the code — the CLI polls until activation completes
and then saves the account.

Verify:

```bash
kobodl user list
kobodl book list
```

Installed via pipx or uv, the binary lives in `~/.local/bin`. That is often
absent from the `PATH` of a non-interactive or background shell, so scripts and
agents should call `~/.local/bin/kobodl` by full path.

## Usage

Download one book by its revision id:

```bash
kobodl book get -u <account-email> -o <output-dir> <RevisionId>
```

The output filename is `{Author} - {Title} {ShortRevisionId}.epub`.

### Finding the newest purchase

`kobodl book list` sorts **alphabetically** and prints no dates, so it cannot
show what you just bought. The underlying API does carry the entitlement date —
export the raw library and sort on it:

```bash
kobodl book list --read --export-library /tmp/kobolib.json
python3 - <<'PY'
import json

rows = []
for entry in json.load(open('/tmp/kobolib.json')):
    new = entry.get('NewEntitlement')
    if not new:
        continue
    ent, meta = new['BookEntitlement'], new['BookMetadata']
    added = ent.get('ActivePeriod', {}).get('From') or ent.get('Created') or ''
    rows.append((added, meta.get('Title', ''), meta.get('RevisionId', '')))

rows.sort(reverse=True)
for row in rows[:10]:
    print(*row)
PY
```

The top row is the most recent addition; feed its `RevisionId` to `book get`.

## References

- [kobo-book-downloader](https://github.com/subdavis/kobo-book-downloader)
- [Kobo device activation](https://www.kobo.com/activate)
