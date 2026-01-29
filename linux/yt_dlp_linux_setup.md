# Install and Configure yt-dlp on Linux

Install using `uv`:

```bash
uv tool install yt-dlp
```

Configure yt-dlp:

```bash
$ cat ~/yt-dlp.conf
--js-runtimes bun
--remote-components ejs:npm
--extractor-args "youtube:player-client=mweb"
```

More details about configuration options:
* https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#configuration
