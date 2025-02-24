#!/usr/bin/env -S uv run --script --quiet

# /// script
# requires-python = ">=3.12"
# ///

"""
TIL CLI Tool - Manage Today I Learned entries

A self-contained tool for working with TIL (Today I Learned) entries.
Uses uv for dependency isolation.
"""
import argparse
import datetime
import logging
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import shutil
import platform as sys_platform  # Rename to avoid conflicts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("til")


class TILEntry:
    """Class representing a TIL entry with metadata and executable sections"""
    
    def __init__(self, path: Path):
        self.path = path
        self.title = ""
        self.metadata = {}
        self.sections = {}
        self.executable_sections = set()
        self._parse()
    
    def _parse(self):
        """Parse the TIL entry file to extract metadata and sections"""
        try:
            content = self.path.read_text()
            
            # Extract title (first H1)
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            if title_match:
                self.title = title_match.group(1).strip()
            
            # Extract metadata (key-value pairs after title)
            metadata_pattern = r'^([A-Za-z]+):\s*(.+)$'
            for line in content.split('\n'):
                match = re.match(metadata_pattern, line)
                if match:
                    key, value = match.groups()
                    if key == 'Tags':
                        self.metadata[key] = [tag.strip() for tag in value.split(',')]
                    else:
                        self.metadata[key] = value.strip()
            
            # Extract sections and executable sections
            section_pattern = r'^## (.+?)( \(executable\))?$'
            current_section = None
            section_content = []
            
            for line in content.split('\n'):
                match = re.match(section_pattern, line)
                if match:
                    # Save previous section if it exists
                    if current_section:
                        self.sections[current_section] = '\n'.join(section_content)
                    
                    # Start new section
                    current_section = match.group(1).strip()
                    section_content = []
                    
                    # Check if executable
                    if match.group(2):
                        self.executable_sections.add(current_section)
                elif current_section:
                    section_content.append(line)
            
            # Save last section
            if current_section:
                self.sections[current_section] = '\n'.join(section_content)
                
        except Exception as e:
            print(f"Error parsing {self.path}: {e}", file=sys.stderr)
    
    def get_executable_blocks(self, section_name: str) -> List[Tuple[str, str]]:
        """Extract executable code blocks from a section"""
        if section_name not in self.executable_sections:
            return []
        
        content = self.sections.get(section_name, "")
        blocks = []
        
        # Find code blocks with language specifier
        pattern = r'```(\w+)\n(.*?)```'
        for match in re.finditer(pattern, content, re.DOTALL):
            language, code = match.groups()
            blocks.append((language, code.strip()))
        
        return blocks
    
    def matches_search(self, term: str) -> bool:
        """Check if the TIL entry matches a search term"""
        term = term.lower()
        
        # Check title
        if term in self.title.lower():
            return True
        
        # Check metadata
        for key, value in self.metadata.items():
            if isinstance(value, list):
                if any(term in item.lower() for item in value):
                    return True
            elif term in str(value).lower():
                return True
        
        # Check section content
        for content in self.sections.values():
            if term in content.lower():
                return True
        
        # Check filename
        if term in self.path.stem.lower():
            return True
        
        return False
    
    def __str__(self) -> str:
        tags = self.metadata.get('Tags', [])
        date = self.metadata.get('Date', 'N/A')
        platform = self.metadata.get('Platform', 'all')
        
        return f"{self.title} ({self.path.relative_to(Path.cwd())})\n" \
               f"Date: {date}, Platform: {platform}\n" \
               f"Tags: {', '.join(tags) if isinstance(tags, list) else tags}"


class TILCollection:
    """Class for managing a collection of TIL entries"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.entries = []
        self._load_entries()
    
    def _load_entries(self):
        """Load all TIL entries from the repository"""
        md_files = self.root_dir.glob('**/*.md')
        
        for file_path in md_files:
            # Skip certain files like README.md, TODO.md, etc.
            if file_path.name in ('README.md', 'TODO.md', 'CLAUDE.md', 'til-format.md'):
                continue
                
            entry = TILEntry(file_path)
            if entry.title:  # Only add valid entries with a title
                self.entries.append(entry)
    
    def search(self, term: str) -> List[TILEntry]:
        """Search for TIL entries matching the given term"""
        return [entry for entry in self.entries if entry.matches_search(term)]
    
    def get_entry(self, path_or_name: str) -> Optional[TILEntry]:
        """Get a TIL entry by path or name"""
        # Try as path first
        try:
            path = Path(path_or_name)
            if not path.is_absolute():
                path = self.root_dir / path
            
            for entry in self.entries:
                if entry.path == path:
                    return entry
        except:
            pass
        
        # Try as title or partial match
        name_lower = path_or_name.lower()
        for entry in self.entries:
            if entry.title.lower() == name_lower:
                return entry
            
        # Try partial match on title or filename
        for entry in self.entries:
            if name_lower in entry.title.lower() or name_lower in entry.path.stem.lower():
                return entry
        
        return None
    
    def get_tags(self) -> Set[str]:
        """Get all unique tags from the collection"""
        tags = set()
        for entry in self.entries:
            entry_tags = entry.metadata.get('Tags', [])
            if isinstance(entry_tags, list):
                tags.update(entry_tags)
            else:
                tags.add(entry_tags)
        return tags
    
    def get_platforms(self) -> Set[str]:
        """Get all unique platforms from the collection"""
        platforms = set()
        for entry in self.entries:
            platform = entry.metadata.get('Platform', '')
            if ',' in platform:
                platforms.update(p.strip() for p in platform.split(','))
            else:
                platforms.add(platform)
        return platforms


def execute_code_block(language: str, code: str) -> int:
    """Execute a code block based on its language"""
    # Create a temporary script file
    temp_dir = Path(os.environ.get('TMPDIR', '/tmp'))
    
    if language == 'bash' or language == 'sh':
        script_file = temp_dir / 'til_exec.sh'
        interpreter = '/bin/bash'
    elif language == 'python':
        script_file = temp_dir / 'til_exec.py'
        interpreter = sys.executable
    else:
        print(f"Unsupported language: {language}", file=sys.stderr)
        return 1
    
    try:
        script_file.write_text(code)
        script_file.chmod(0o755)
        
        # Show the commands about to be executed
        print(f"Executing {language} code:")
        for line in code.split('\n'):
            print(f"  {line}")
        
        confirm = input("Continue with execution? [y/N] ")
        if confirm.lower() != 'y':
            print("Execution cancelled")
            return 0
        
        # Execute the script
        return subprocess.call([interpreter, str(script_file)])
    except Exception as e:
        print(f"Error executing code: {e}", file=sys.stderr)
        return 1
    finally:
        # Clean up
        if script_file.exists():
            script_file.unlink()


def validate_entry(entry: TILEntry) -> List[str]:
    """Validate a TIL entry against formatting requirements"""
    errors = []
    
    # Check title
    if not entry.title:
        errors.append("Missing H1 title")
    
    # Check required metadata
    for field in ['Date', 'Tags', 'Platform']:
        if field not in entry.metadata:
            errors.append(f"Missing {field} metadata")
    
    # Check Summary section
    if 'Summary' not in entry.sections:
        errors.append("Missing Summary section")
    
    # Check code blocks have language specifiers
    for section, content in entry.sections.items():
        if '```' in content:
            # Using regex to find complete code blocks with start and end delimiters
            code_blocks = re.findall(r'```(\w*)(.*?)```', content, re.DOTALL)
            for lang, _ in code_blocks:
                if not lang:
                    errors.append(f"Code block in section '{section}' missing language specifier")
    
    return errors


def main():
    """Main entry point for the TIL CLI tool"""
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description="TIL CLI Tool")
        subparsers = parser.add_subparsers(dest='command', help='Command to run')
        
        # List command
        list_parser = subparsers.add_parser('list', help='List TIL entries')
        list_parser.add_argument('--tag', help='Filter by tag')
        list_parser.add_argument('--platform', help='Filter by platform')
        
        # Search command
        search_parser = subparsers.add_parser('search', help='Search TIL entries')
        search_parser.add_argument('term', help='Search term')
        
        # Show command
        show_parser = subparsers.add_parser('show', help='Show a TIL entry')
        show_parser.add_argument('entry', help='Entry path or name')
        
        # Execute command
        exec_parser = subparsers.add_parser('execute', help='Execute a TIL entry section')
        exec_parser.add_argument('entry', help='Entry path or name')
        exec_parser.add_argument('section', help='Section name to execute')
        
        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate TIL entries')
        validate_parser.add_argument('entry', nargs='?', help='Entry path (or all if not specified)')
        
        # Tags command
        subparsers.add_parser('tags', help='List all tags')
        
        # Platforms command
        subparsers.add_parser('platforms', help='List all platforms')
        
        # Create command
        create_parser = subparsers.add_parser('create', help='Create a new TIL entry')
        create_parser.add_argument('title', help='Title of the entry')
        create_parser.add_argument('--dir', help='Directory to create the entry in')
        
        # Version command
        subparsers.add_parser('version', help='Show version information')
        
        # Parse args
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return 0
            
        # Initialize TIL collection
        root_dir = Path.cwd()
        collection = TILCollection(root_dir)
        
        # Execute command
        if args.command == 'list':
            entries = collection.entries
            
            if args.tag:
                entries = [e for e in entries if isinstance(e.metadata.get('Tags', []), list) and 
                          args.tag in e.metadata.get('Tags', []) or 
                          args.tag == e.metadata.get('Tags')]
            
            if args.platform:
                entries = [e for e in entries if args.platform in e.metadata.get('Platform', '').split(',')]
            
            for entry in sorted(entries, key=lambda e: e.title):
                print(entry)
        
        elif args.command == 'search':
            results = collection.search(args.term)
            if results:
                print(f"Found {len(results)} matching entries:")
                for entry in results:
                    print(entry)
            else:
                print("No matching entries found")
        
        elif args.command == 'show':
            entry = collection.get_entry(args.entry)
            if entry:
                # Display full content of the entry
                print(entry.path.read_text())
            else:
                logger.error(f"Entry not found: {args.entry}")
                return 1
        
        elif args.command == 'execute':
            entry = collection.get_entry(args.entry)
            if not entry:
                logger.error(f"Entry not found: {args.entry}")
                return 1
            
            if args.section not in entry.executable_sections:
                logger.error(f"Section '{args.section}' is not marked as executable")
                return 1
            
            blocks = entry.get_executable_blocks(args.section)
            if not blocks:
                logger.error(f"No executable code blocks found in section '{args.section}'")
                return 1
            
            for language, code in blocks:
                result = execute_code_block(language, code)
                if result != 0:
                    return result
        
        elif args.command == 'validate':
            if args.entry:
                entry = collection.get_entry(args.entry)
                if not entry:
                    logger.error(f"Entry not found: {args.entry}")
                    return 1
                
                entries = [entry]
            else:
                entries = collection.entries
            
            all_valid = True
            for entry in entries:
                errors = validate_entry(entry)
                if errors:
                    all_valid = False
                    print(f"Validation errors in {entry.path}:")
                    for error in errors:
                        print(f"  - {error}")
            
            if all_valid:
                print("All entries valid!")
            else:
                return 1
        
        elif args.command == 'tags':
            tags = collection.get_tags()
            print("Available tags:")
            for tag in sorted(tags):
                print(f"  {tag}")
        
        elif args.command == 'platforms':
            platforms = collection.get_platforms()
            print("Available platforms:")
            for platform in sorted(platforms):
                print(f"  {platform}")
        
        elif args.command == 'create':
            try:
                # Determine directory
                if args.dir:
                    directory = root_dir / args.dir
                    if not directory.exists():
                        directory.mkdir(parents=True)
                else:
                    directory = root_dir
                
                # Create filename from title
                filename = args.title.lower().replace(' ', '_') + '.md'
                filepath = directory / filename
                
                # Don't overwrite existing files
                if filepath.exists():
                    logger.error(f"Error: File already exists: {filepath}")
                    return 1
                
                # Get current date in ISO format
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                
                # Create file content from template
                current_platform = sys_platform.system().lower()
                content = f"""# {args.title}

Date: {today}
Tags: 
Platform: {current_platform}

## Summary

Brief summary goes here.

## Details

Details go here.

"""
                
                # Write file
                filepath.write_text(content)
                print(f"Created new TIL entry: {filepath}")
            except Exception as e:
                logger.error(f"Error creating TIL entry: {e}")
                return 1
                
        elif args.command == 'version':
            print(f"TIL CLI Tool v1.0.0")
            print(f"Python: {sys.version.split()[0]}")
            print(f"Platform: {sys_platform.system()}")
            
        else:
            parser.print_help()
        
        return 0
        
    except KeyboardInterrupt:
        logger.error("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if os.environ.get("TIL_DEBUG"):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())