"""Agentic dispatch for ``til run``.

Hands a whole skill document to an AI coding agent via
[airan](https://github.com/kfet/airan), wrapped in an imperative telling
the agent to *apply* the TIL to the current host rather than merely read
it.

airan is a soft dependency, discovered with ``shutil.which`` — the same
optional-external-binary pattern ``til_cli.render`` uses for glow/bat.
Backend resolution is deliberately left to airan (``$AIRAN_BACKEND``,
then ``airan config NAME``): backend dispatch belongs in exactly one
place, and it is not here.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

AIRAN_INSTALL_HINT = (
    "  curl -fsSL https://raw.githubusercontent.com/kfet/airan/main/install.sh | sh"
)

# Prepended to the skill body. Without it the agent receives a bare
# reference document and has to guess whether it is being asked to read,
# explain, or do.
IMPERATIVE = """\
Apply the following TIL note to the current host.

Do the work described below: install what is missing, apply the
configuration, and adapt the steps to this machine (its OS, shell,
package manager and existing config) where the note assumes otherwise.
Do not overwrite existing configuration without preserving a backup.

Then verify the result using the commands given in the note, and report
concisely what you changed, what was already in place, and anything you
could not do.

--- BEGIN TIL NOTE ---
"""

IMPERATIVE_FOOTER = "\n--- END TIL NOTE ---\n"


def find_airan() -> str | None:
    """Absolute path to the ``airan`` binary, or ``None`` if not on PATH."""
    return shutil.which("airan")


def build_prompt(content: str) -> str:
    """Wrap a skill document in the apply-to-this-host imperative."""
    if not content.endswith("\n"):
        content += "\n"
    return IMPERATIVE + content + IMPERATIVE_FOOTER


def missing_airan_message() -> str:
    """The actionable error shown when airan is not installed."""
    return (
        "til: `run` needs airan (not found on PATH)\n" + AIRAN_INSTALL_HINT
    )


def run_with_airan(content: str, *, slug: str = "skill") -> int:
    """Dispatch ``content`` through airan. Returns a shell exit code.

    The prompt is written to a temp file because airan accepts a FILE
    argument only. ``subprocess.run`` (not ``os.execvp``) is used
    deliberately: exec would replace this process and leave the temp file
    behind forever, while subprocess still inherits the TTY that these
    interactive agent backends need.
    """
    airan = find_airan()
    if not airan:
        print(missing_airan_message(), file=sys.stderr)
        return 1

    fd, temp_path = tempfile.mkstemp(prefix=f"til_run_{slug}_", suffix=".md")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(build_prompt(content))
        try:
            proc = subprocess.run([airan, temp_path])
        except OSError as exc:
            print(f"til: could not run airan: {exc}", file=sys.stderr)
            return 1
        return proc.returncode
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
