"""
TIL CLI Tool core functionality - Manage Today I Learned entries

Core classes and functions for the TIL CLI Tool.
"""
import argparse
import logging
import os
import re
import sys
import subprocess
import time
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
        platform = self.metadata.get('Platform', 'all')
        
        return f"{self.title} ({self.path.relative_to(self.path.parent.parent)})\n" \
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
            if file_path.name in ('README.md', 'TODO.md', 'CLAUDE.md', 'til-format.md', 'til-installable.md'):
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
    # Create a temporary script file with unique name
    import tempfile
    import uuid
    
    temp_dir = Path(os.environ.get('TMPDIR', '/tmp'))
    unique_id = uuid.uuid4().hex[:8]
    
    if language == 'bash' or language == 'sh':
        script_file = temp_dir / f'til_exec_{unique_id}.sh'
        interpreter = '/bin/bash'
    elif language == 'python':
        script_file = temp_dir / f'til_exec_{unique_id}.py'
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
    for field in ['Tags', 'Platform']:
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

def get_til_repo_path():
    """
    Get the TIL repository path using the following priority order:
    1. Command line argument
    2. Environment variable
    3. Config file
    4. Current directory (fallback)
    """
    # Check environment variable
    env_path = os.environ.get('TIL_REPO_PATH')
    if env_path and Path(env_path).is_dir():
        return Path(env_path)
        
    # Check config file in user's home directory
    config_path = Path.home() / '.tilconfig'
    if config_path.exists():
        try:
            config = config_path.read_text().strip()
            if Path(config).is_dir():
                return Path(config)
        except:
            pass
            
    # Fallback to current directory
    return Path.cwd()


def check_for_repo_updates(repo_path: Path, force: bool = False) -> bool:
    """
    Check if the TIL repository needs updating and update if necessary.
    Returns True if an update was performed.
    """
    try:
        # Skip if not a git repository
        git_dir = repo_path / '.git'
        if not git_dir.is_dir():
            return False
            
        # Get last update check timestamp
        timestamp_file = Path.home() / '.til_last_update'
        current_time = time.time()
        
        # Check if we should update based on timestamp (every 12 hours)
        if not force and timestamp_file.exists():
            try:
                last_update = float(timestamp_file.read_text().strip())
                if current_time - last_update < 43200:  # 12 hours in seconds
                    return False
            except (ValueError, OSError):
                # Invalid timestamp, continue with update check
                pass
                
        # Check if update is needed using git
        try:
            # Fetch the latest changes
            subprocess.run(
                ['git', 'fetch', '--quiet'],
                cwd=repo_path,
                capture_output=True,
                check=True,
                timeout=5  # 5 second timeout to prevent hanging
            )
            
            # Check if we're behind remote
            result = subprocess.run(
                ['git', 'rev-list', 'HEAD..@{upstream}', '--count'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=2
            )
            
            # If behind remote (result > 0), perform update
            if int(result.stdout.strip()) > 0:
                update_result = subprocess.run(
                    ['git', 'pull', '--quiet'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if update_result.returncode == 0:
                    # Update timestamp
                    timestamp_file.write_text(str(current_time))
                    logger.info("TIL repository updated to latest version.")
                    return True
                else:
                    # Update failed but not critical, continue
                    return False
            else:
                # No update needed, still update timestamp
                timestamp_file.write_text(str(current_time))
                return False
                
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            # Git command failed or timed out, log but continue
            logger.debug(f"Git update check failed: {e}")
            return False
            
    except Exception as e:
        # Any other error, log but continue
        logger.debug(f"Repository update check failed: {e}")
        return False
    
    # Default: no update
    return False


