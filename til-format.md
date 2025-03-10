# TIL Entry Format

## Summary

This document describes the standardized format for Today I Learned (TIL) entries to make them both human-readable and machine-parsable for automated tools.

## Structure

Each TIL entry should follow this structure:

1. Start with H1 title
2. Include metadata as key-value pairs
3. Use standardized sections with H2 headings
4. Mark executable code blocks with the "(executable)" tag

## Template

```markdown
# Title of TIL Entry


## Summary

Brief one or two sentence description of what this TIL entry covers.

## Details

Main content of the TIL entry goes here, using standard markdown formatting.

## Install (executable)

```bash
# Installation commands
brew install example
```

## Configure (executable)

```bash
# Configuration commands
example --configure setting value
```

## Usage

How to use the tool or command in practice.

## References

- [Reference 1](https://example.com)
- [Reference 2](https://example.com)
```

## Python Implementation

The accompanying Python tool will:

1. Parse metadata from key-value pairs
2. Extract executable blocks from sections tagged with "(executable)"
3. Build search index on content
4. Provide commands to search, display, and execute configurations

## Validation

A GitHub Action will validate that each TIL entry:

1. Starts with an H1 title
2. Has a Summary section
3. Uses proper markdown formatting
4. Has code blocks with language specifiers