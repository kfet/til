# TIL CLI Tool

A command-line tool for managing Today I Learned entries.

## Features

- List TIL entries with
- Search TIL entries by keyword
- Display TIL entries
- Execute code blocks in TIL entries
- Validate TIL entries against formatting requirements
- Create new TIL entries with templates
- Update repository with latest changes
- Configure repository location

## Installation

### Option 1: Quick Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/kfet/til.git
cd til

# Run the installer script
./til_cli/install.sh
```

The installer script will:
1. Install pipx if not already installed
2. Clone the repository to ~/.til-repo
3. Install the TIL CLI tool globally
4. Configure the repository location

### Option 2: Manual Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/til.git
cd til

# Install with pipx (recommended for CLI tools)
pipx install ./til_cli

# Configure the repository location
til config /path/to/til/repo
```

### Option 3: Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/til.git
cd til

# Install in development mode
pip install -e ./til_cli

# Configure the repository location
til config $(pwd)
```

## Usage

```bash
# List all TIL entries
til list

# Search for entries
til search "git commit"

# Show an entry
til show git/git_worktree.md

# Execute a section in a TIL entry
til execute git/git_worktree.md "Setup"

# Create a new entry
til create "Git Stash" --dir git

# Validate all entries
til validate

# Update the repository
til update

# Show version information
til version

# Configure repository location
til config /path/to/til/repo

# Use a custom repository path for a single command
til --repo-path /path/to/til/repo list
```

## Configuration

The repository path can be set using any of these methods (in order of precedence):

1. Command-line argument: `til --repo-path /path/to/repo list`
2. Environment variable: `export TIL_REPO_PATH=/path/to/repo`
3. Config file: `~/.tilconfig`
4. Current directory (fallback)

To set the config file:

```bash
til config /path/to/til/repo
```

## License

This project is licensed under the BSD 3-Clause License - see the LICENSE.md file for details.
