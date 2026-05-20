# TIL CLI Tool

A self-contained command-line tool for managing Today I Learned (TIL) entries. Uses `uv` for dependency isolation.

## Installation

1. Ensure you have `uv` installed:
   ```
   pip install uv
   ```

2. Clone the repository and make the tool executable:
   ```
   git clone https://github.com/yourusername/til.git
   cd til
   chmod +x til
   ```

3. You can now run the tool from the repository directory:
   ```
   ./til [command]
   ```

4. Optionally, add the tool to your PATH for system-wide access:
   ```
   # Add to ~/.zshrc or ~/.bashrc
   export PATH="$PATH:/path/to/til"
   ```

## Features

- Search, list, and view TIL entries
- Execute code blocks from TIL entries
- Validate TIL entries for proper formatting

## Usage

```
./til [command] [options]
```

### Commands

- `list`: List all TIL entries

- `search TERM`: Search for TIL entries matching the given term

- `show ENTRY`: Show the content of a TIL entry
  - `ENTRY` can be a skill slug (`ghostty-config-term`), a repository
    path (`skills/ghostty-config-term/SKILL.md`), an absolute path, or
    the entry title

- `execute ENTRY SECTION`: Execute code blocks from a section marked as executable
  - `ENTRY`: skill slug, repository path, absolute path, or title
  - `SECTION`: Section name containing the executable code blocks

- `validate [ENTRY]`: Validate TIL entries for proper formatting
  - `ENTRY` (optional): skill slug or path (validates all entries if not specified)

- `version`: Show version information about the tool

## Entry Format

Entries are packaged as [Agent Skills](https://agentskills.io/specification)
under `skills/{topic}-{name}/SKILL.md`. Each file has YAML frontmatter
with `name` (must equal the directory name; `[a-z0-9-]{1,64}`) and
`description` (≤1024 chars), a level-1 heading, and standard Markdown
content. Mark executable code blocks by appending `(executable)` to the
containing `## Section` heading and tagging code fences with a language
(`bash`, `sh`, `python`).

## Examples

List all entries:
```
./til list
```

Search for entries related to git:
```
./til search git
```

Show a specific entry:
```
./til show git-git-configure
```

Execute the Install section of an entry:
```
./til execute python-til-tests Summary
```

Validate all entries:
```
./til validate
```
