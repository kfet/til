#!/usr/bin/env python3
"""Convert TIL markdown entries into Agent Skills format (agentskills.io/specification).

One-shot migration tool. Walks the repo's top-level topic dirs, finds `*.md`
entries, and writes each one to `skills/{category}-{basename}/SKILL.md` with
the frontmatter format used across the committed skills/ tree.
"""
from __future__ import annotations
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

# Top-level files / dirs that are NOT TIL entries.
EXCLUDE_DIRS = {".git", "__pycache__", "til_cli", "tools", "skills"}
EXCLUDE_FILES = {
    "README.md", "TODO.md", "CLAUDE.md",
    "til-format.md", "til-installable.md", "README_TIL_TOOL.md",
}


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def make_name(category: str, basename: str) -> str:
    return slugify(f"{category}-{basename}")[:64].strip("-")


def extract_title_and_body(md: str) -> tuple[str, str]:
    """Return (title, body_after_h1). Body falls back to the whole file when no H1."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip(), "\n".join(lines[i + 1:]).lstrip("\n")
    return "", md


def topic_phrase(basename: str) -> str:
    """Filename → human-ish topic phrase used in the description."""
    # Preserve original casing (e.g. "config TERM" stays uppercase).
    return basename.replace("_", " ").replace("-", " ").strip()


def build_description(title: str, category: str, basename: str) -> str:
    topic = topic_phrase(basename)
    desc = (
        f"{title}. TIL note about {category}. "
        f"Use when working with {category} and the user mentions {topic} or related topics."
    )
    if len(desc) > 1024:
        desc = desc[:1020].rstrip() + "..."
    return desc


def write_skill(name: str, description: str, title: str, body: str) -> Path:
    skill_dir = SKILLS_DIR / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    desc_escaped = description.replace('"', '\\"')
    content = (
        "---\n"
        f"name: {name}\n"
        f'description: "{desc_escaped}"\n'
        "---\n\n"
        f"# {title}\n\n"
        f"{body}".rstrip() + "\n"
    )
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


def main() -> None:
    SKILLS_DIR.mkdir(exist_ok=True)
    converted = 0
    for path in sorted(ROOT.rglob("*.md")):
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        if len(parts) == 1 and parts[0] in EXCLUDE_FILES:
            continue
        if len(parts) < 2:
            continue  # Top-level .md not in exclude list — skip to be safe.
        category = parts[0]
        basename = path.stem
        title, body = extract_title_and_body(path.read_text())
        if not title:
            title = basename.replace("_", " ").replace("-", " ").title()
        name = make_name(category, basename)
        description = build_description(title, category, basename)
        out = write_skill(name, description, title, body)
        print(f"  {rel} -> {out.relative_to(ROOT)}")
        converted += 1
    print(f"\nConverted {converted} TIL entries into skills/")


if __name__ == "__main__":
    main()
