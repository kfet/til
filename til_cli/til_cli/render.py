"""Markdown rendering for ``til show``.

Auto-detects an installed Markdown renderer (``glow``, ``bat``) and
shells out to it when stdout is a TTY and the user hasn't opted out.
Falls back to plain text in every "this would be unsafe to colorise"
condition (non-TTY, ``NO_COLOR``, ``--plain``, ``TIL_RENDERER=plain``,
missing renderer).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import List, Optional, Sequence

# Order in which we try to auto-pick a renderer when ``TIL_RENDERER`` is
# unset or ``auto``. ``glow`` first because it formats Markdown; ``bat``
# is a syntax highlighter for the raw source, which is still pleasant.
_AUTO_ORDER: Sequence[str] = ("bat", "glow")


def _renderer_argv(name: str) -> Optional[List[str]]:
    """Return the argv for ``name`` if the binary is on PATH."""
    bin_path = shutil.which(name)
    if not bin_path:
        return None
    if name == "glow":
        # ``-s auto`` picks light/dark from terminal background; ``-p``
        # would page — we leave paging to the user's shell pipeline.
        return [bin_path, "-s", "dracula", "-"]
    if name == "bat":
        return [
            bin_path,
            "--language=md",
            "--style=grid",
            "--paging=never",
            "--color=always",
        ]
    return None


def pick_renderer(
    *,
    plain: bool = False,
    tty: Optional[bool] = None,
    env: Optional[dict] = None,
) -> Optional[List[str]]:
    """Decide which renderer to use, or ``None`` for plain output.

    Pure: no side effects, used both by ``render`` and tests.
    """
    env = env if env is not None else os.environ
    if tty is None:
        tty = sys.stdout.isatty()

    if plain or not tty:
        return None
    if env.get("NO_COLOR"):
        return None

    choice = env.get("TIL_RENDERER", "auto").lower()
    if choice in ("", "plain", "none", "off"):
        return None
    if choice == "auto":
        for name in _AUTO_ORDER:
            argv = _renderer_argv(name)
            if argv:
                return argv
        return None
    return _renderer_argv(choice)


def render(content: str, *, plain: bool = False) -> int:
    """Render ``content`` to stdout. Returns a shell-style exit code."""
    argv = pick_renderer(plain=plain)
    if argv is None:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
        return 0
    try:
        proc = subprocess.run(argv, input=content, text=True)
        return proc.returncode
    except (OSError, subprocess.SubprocessError):
        # Renderer launch failure: fall back to plain text rather than
        # crashing on the user.
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
        return 0
