# CLAUDE.md for TIL Repository

This repo holds my "Today I Learned" notes, now packaged as
[Agent Skills](https://agentskills.io/specification) under `skills/`.

## Commands
- Test: `python3 -m unittest test_til.py`
- Test single test: `python3 -m unittest test_til.TestTILTool.test_til_entry_parsing`
- Run the TIL CLI (uv launcher): `./til <command>`
- Re-run the one-shot migration script: `python3 tools/convert_to_skills.py`

Note: `test_til.py` and `til_cli/` still exercise the legacy TIL entry
format against synthetic fixtures. They have not yet been retargeted to
validate the new `skills/` tree, so `./til validate` will report
"Missing Summary section" against every skill — expected, not a real
failure.

## Code Style Guidelines
- Python: Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Error handling: Use try/except blocks with specific exceptions
- Variable naming: snake_case for variables and functions
- Class naming: PascalCase for classes
- Imports: Standard library first, then third-party, then local modules
- Docstrings: Multi-line docstrings with summary line, description, and args

## Skill Authoring Conventions
- Each skill lives at `skills/{topic}-{slug}/SKILL.md`
- Frontmatter has `name` (must equal the directory name, lowercase
  letters/digits/hyphens only, ≤64 chars) and `description` (≤1024
  chars; lead with the title, then a "Use when..." activation hint)
- Body is regular Markdown. Start with a level-1 heading describing
  the topic, use fenced code blocks with language tags, mark
  executable sections with "(executable)" in the heading

## File Organization
- All knowledge entries: `skills/{topic}-{specific_knowledge}/SKILL.md`
- Top-level non-skill files: `README.md`, `CLAUDE.md`, `TODO.md`,
  `install.sh`, `til` (CLI launcher), `til_cli/` (legacy CLI),
  `test_til.py`, `tools/` (migration scripts)
