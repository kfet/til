# CLAUDE.md for TIL Repository

## Commands
- Test: `python -m unittest test_til.py`
- Test single test: `python -m unittest test_til.TestTILTool.test_til_entry_parsing`
- Validate entries: `python -m til_cli.til_cli validate`
- Run the TIL CLI: `python -m til_cli.til_cli <command>`

## Code Style Guidelines
- Python: Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Error handling: Use try/except blocks with specific exceptions
- Variable naming: snake_case for variables and functions
- Class naming: PascalCase for classes
- Imports: Standard library first, then third-party, then local modules
- Docstrings: Multi-line docstrings with summary line, description, and args

## Markdown Formatting Conventions
- Use descriptive filenames in lowercase with underscores (e.g., `git_configure.md`)
- Start each TIL file with a level 1 heading describing the topic
- Use code blocks with backticks (```) for commands and code snippets
- Specify language for syntax highlighting where applicable
- Mark executable sections with "(executable)" in the heading

## File Organization
- Group related TILs in topic-specific directories
- Follow the pattern: `topic/specific_knowledge.md`
- Include a Summary section in every TIL entry