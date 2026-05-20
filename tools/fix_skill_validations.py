"""One-shot helper to add language tags to fenced code blocks in skill files.

For every ``skills/*/SKILL.md`` with an untagged code fence, infer the
language from the first non-empty line of the block and rewrite the
opening fence to include it. Also promotes a leading ``## `` heading to
``# `` when the body has no level-1 heading.

This script is meant to be reviewed via ``git diff`` after running.
"""
import re
import sys
from pathlib import Path


def infer_language(code: str, file_slug: str) -> str:
    """Guess the language for a code block from its content and file slug."""
    lines = [line for line in code.splitlines() if line.strip()]
    if not lines:
        return "text"
    first = lines[0].lstrip()

    # Shebangs win outright.
    if first.startswith("#!/bin/sh") or first.startswith("#!/usr/bin/env sh"):
        return "sh"
    if first.startswith("#!"):
        if "bash" in first:
            return "bash"
        if "python" in first:
            return "python"
        if "node" in first:
            return "javascript"
        return "sh"

    joined = " \n".join(lines).lower()

    # vimrc style (the only vim file we have starts with a vim comment ``"``).
    if first.startswith('"') and (
            "vimruntime" in joined or "syntax enable" in joined
            or "filetype" in joined or "setfiletype" in joined):
        return "vim"

    # ghostty / tmux / helix style config — ``key = value`` or ``set -g`` /
    # ``bind`` directives with no shell command.
    config_signals = (
        "keybind =", "theme =", "macos-option-as-alt", "background =",
        "foreground =", "font-family", "macos-titlebar",
    )
    if any(sig in joined for sig in config_signals):
        return "conf"

    # tmux conf — top-level comments, ``set -g``, ``bind``, ``setw``.
    if file_slug.startswith("tmux-") and (
            re.search(r"^\s*(set|bind|setw|run)\b", code, re.MULTILINE)
            or first.startswith("#")):
        return "tmux"

    # helix / TOML-ish.
    if file_slug.startswith("hx-") and "=" in first:
        return "toml"

    # Linux device-tree style boot config.
    if "dtparam" in joined or "dtoverlay" in joined:
        return "conf"

    # Everything else with shell command signals.
    shell_cmd_starts = (
        "ssh ", "sudo ", "git ", "brew ", "apt ", "pipx ", "pip ", "pip3 ",
        "bun ", "ffmpeg ", "ls ", "cat ", "echo ", "date ", "go ", "gs ",
        "lsof ", "jupyter ", "tldr ", "tmux ", "infocmp", "tic ",
        "mkdir ", "cd ", "python3 ", "python ", "rm ", "mv ", "cp ",
        "xattr ", "OUT=", "ghostty ", "direnv", "if [", "pv ", "$ ",
        "source ", "export ", "nvim", "vim", "llm ",
    )
    if any(first.startswith(s) for s in shell_cmd_starts):
        return "bash"
    if "plugins=" in first or "@plugin" in first:
        return "bash"

    # ``<prefix>:list-keys`` style snippets are tmux commands, but they
    # aren't shell — treat as plain text.
    if first.startswith("<prefix>"):
        return "text"

    # Default conservative fallback.
    return "bash"


def fix_file(path: Path) -> tuple[int, bool]:
    """Returns (blocks_tagged, h1_promoted)."""
    text = path.read_text()
    slug = path.parent.name

    # Split out frontmatter to leave it untouched.
    fm_match = re.match(r'^(---\r?\n.*?\r?\n---\r?\n?)', text, re.DOTALL)
    if fm_match:
        head = fm_match.group(1)
        body = text[fm_match.end():]
    else:
        head, body = "", text

    # Promote a leading ``## `` to ``# `` when no top-level heading exists.
    h1_promoted = False
    if not re.search(r'^# .+', body, re.MULTILINE):
        new_body, n = re.subn(r'^## ', '# ', body, count=1, flags=re.MULTILINE)
        if n:
            body = new_body
            h1_promoted = True

    # Walk fences in order; rewrite ``` (no lang) to ```<lang>.
    out_chunks: list[str] = []
    last = 0
    blocks_tagged = 0
    open_re = re.compile(r'^```([A-Za-z0-9_-]*)\n', re.MULTILINE)
    close_re = re.compile(r'^```\s*$', re.MULTILINE)
    pos = 0
    while True:
        m = open_re.search(body, pos)
        if not m:
            break
        lang = m.group(1)
        # Find the matching closing fence.
        close = close_re.search(body, m.end())
        if not close:
            break
        code = body[m.end():close.start()]
        if lang:
            pos = close.end()
            continue
        new_lang = infer_language(code, slug)
        # Splice in the language tag.
        body = body[:m.start()] + f"```{new_lang}\n" + body[m.end():]
        blocks_tagged += 1
        # Re-find the close because the body shifted.
        close = close_re.search(body, m.end() + len(new_lang))
        if not close:
            break
        pos = close.end()

    if blocks_tagged or h1_promoted:
        path.write_text(head + body)
    return blocks_tagged, h1_promoted


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    total_blocks = 0
    total_h1 = 0
    touched: list[str] = []
    for skill in sorted(repo.glob("skills/*/SKILL.md")):
        b, h1 = fix_file(skill)
        if b or h1:
            touched.append(f"  {skill.relative_to(repo)}  blocks={b} h1={int(h1)}")
            total_blocks += b
            total_h1 += int(h1)
    print(f"Updated {len(touched)} files; {total_blocks} fences tagged, "
          f"{total_h1} H1 headings promoted.")
    for line in touched:
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
