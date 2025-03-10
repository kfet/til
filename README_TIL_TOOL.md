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
- Create new TIL entries with correct formatting

## Usage

```
./til [command] [options]
```

### Commands

- `list`: List all TIL entries

- `search TERM`: Search for TIL entries matching the given term

- `show ENTRY`: Show the content of a TIL entry
  - `ENTRY` can be a file path or a name/title

- `execute ENTRY SECTION`: Execute code blocks from a section marked as executable
  - `ENTRY`: File path or name/title of the TIL entry
  - `SECTION`: Section name containing the executable code blocks

- `validate [ENTRY]`: Validate TIL entries for proper formatting
  - `ENTRY` (optional): File path or name/title (validates all entries if not specified)

- `create TITLE [--dir DIRECTORY]`: Create a new TIL entry
  - `TITLE`: Title of the new entry
  - `--dir DIRECTORY`: Directory to create the entry in (optional)

- `version`: Show version information about the tool

## Entry Format

TIL entries follow a standardized format:

1. Start with H1 title
2. Include metadata as key-value pairs
3. Use standardized sections with H2 headings
4. Mark executable code blocks with the "(executable)" tag

See `til-format.md` for the full format specification.

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
./til show git/git_configure.md
```

Execute the Install section of an entry:
```
./til execute shell/jq_basics.md Install
```

Validate all entries:
```
./til validate
```

Create a new entry:
```
./til create "Using grep with context" --dir shell
```