"""
TIL CLI Tool core functionality - Manage Today I Learned entries

Core classes and functions for the TIL CLI Tool.
"""
import logging
import os
import re
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Tuple

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
        self.frontmatter = {}
        self.sections = {}
        self.executable_sections = set()
        self._parse()

    @staticmethod
    def _split_frontmatter(content: str) -> Tuple[dict, str]:
        """Strip a leading ``---``-delimited YAML-ish frontmatter block.

        Returns ``(frontmatter_dict, remaining_body)``. Only ``key: value``
        pairs on single lines are recognised — enough for SKILL.md, no
        dependency on PyYAML.
        """
        if not content.startswith('---\n') and not content.startswith('---\r\n'):
            return {}, content
        # Locate the closing fence on its own line.
        fm_match = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n?', content, re.DOTALL)
        if not fm_match:
            return {}, content
        raw = fm_match.group(1)
        body = content[fm_match.end():]
        fm: dict = {}
        for line in raw.splitlines():
            kv = re.match(r'^([A-Za-z_][\w-]*):\s*(.*)$', line)
            if not kv:
                continue
            key, value = kv.group(1), kv.group(2).strip()
            # Drop surrounding matching quotes.
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
                value = value[1:-1]
            fm[key] = value
        return fm, body

    def _parse(self):
        """Parse the TIL entry file to extract metadata and sections"""
        try:
            content = self.path.read_text()

            # Frontmatter (skill format).
            self.frontmatter, body = self._split_frontmatter(content)

            # Title cascade: first H1 in body, else description lead phrase,
            # else slug. Skills with valid frontmatter but no H1 still get a
            # usable display title.
            title_match = re.search(r'^# (.+)$', body, re.MULTILINE)
            if title_match:
                self.title = title_match.group(1).strip()
            elif self.frontmatter.get('description'):
                # Lead phrase of the description, terminated by ``.`` or ``;``.
                desc = self.frontmatter['description']
                lead = re.split(r'[.;]\s', desc, maxsplit=1)[0].strip()
                self.title = lead or self.slug
            else:
                self.title = self.slug

            # Legacy ``Key: value`` metadata (after the optional H1).
            metadata_pattern = r'^([A-Za-z]+):\s*(.+)$'
            for line in body.split('\n'):
                match = re.match(metadata_pattern, line)
                if match:
                    key, value = match.groups()
                    self.metadata[key] = value.strip()

            # Extract sections and executable sections from the body.
            section_pattern = r'^## (.+?)( \(executable\))?$'
            current_section = None
            section_content: List[str] = []

            for line in body.split('\n'):
                match = re.match(section_pattern, line)
                if match:
                    if current_section:
                        self.sections[current_section] = '\n'.join(
                            section_content)
                    current_section = match.group(1).strip()
                    section_content = []
                    if match.group(2):
                        self.executable_sections.add(current_section)
                elif current_section:
                    section_content.append(line)

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

        # Check slug. (Skill files all share the stem ``SKILL``, so a
        # ``path.stem`` check would match every skill for any substring of
        # ``skill`` — the slug is the only useful identifier.)
        if term in self.slug.lower():
            return True

        return False

    @property
    def slug(self) -> str:
        """Stable identifier for this entry.

        For skill entries (``skills/<slug>/SKILL.md``) this is the
        containing directory name. For legacy single-file entries it
        falls back to the file stem.
        """
        if self.path.name == 'SKILL.md':
            return self.path.parent.name
        return self.path.stem

    def __str__(self) -> str:
        return f"{self.title} ({self.slug})"


class TILCollection:
    """Class for managing a collection of TIL entries"""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.entries = []
        self._load_entries()

    def _load_entries(self):
        """Load TIL entries from the repository.

        Only ``skills/<slug>/SKILL.md`` is recognised — everything else
        (README, LICENSE, tool docs, stray Markdown) is ignored.
        """
        pattern = 'skills/*/SKILL.md'
        for file_path in sorted(self.root_dir.glob(pattern)):
            entry = TILEntry(file_path)
            self.entries.append(entry)

    def search(self, term: str) -> List[TILEntry]:
        """Search for TIL entries matching the given term"""
        return [entry for entry in self.entries if entry.matches_search(term)]

    def get_entry(self, path_or_name: str) -> Optional[TILEntry]:
        """Get a TIL entry by slug, repository path, or title."""
        requested = path_or_name.strip()
        if not requested:
            return None
        name_lower = requested.lower()

        # 1) Exact slug.
        for entry in self.entries:
            if entry.slug.lower() == name_lower:
                return entry

        # 2) Path match. Accept absolute paths, repository-relative paths
        #    (``skills/<slug>/SKILL.md``), and trailing-component matches
        #    (``<slug>/SKILL.md``) since older search output omitted the
        #    leading ``skills/`` directory.
        req_path = Path(requested)
        req_parts = req_path.parts
        for entry in self.entries:
            if req_path.is_absolute():
                try:
                    if entry.path.resolve() == req_path.resolve():
                        return entry
                except OSError:
                    pass
                continue
            try:
                rel_parts = entry.path.relative_to(self.root_dir).parts
            except ValueError:
                rel_parts = entry.path.parts
            if rel_parts == req_parts:
                return entry
            if len(req_parts) > 1 and rel_parts[-len(req_parts):] == req_parts:
                return entry

        # 3) Exact title.
        for entry in self.entries:
            if entry.title.lower() == name_lower:
                return entry

        # 4) Partial match on slug or title. (``path.stem`` is intentionally
        #    excluded: skill files all share the stem ``SKILL``, so a stem
        #    check would resolve any substring of ``skill`` — including ``s``,
        #    ``kil``, ``ll`` — to the first skill alphabetically. ``slug``
        #    is the right identifier; for legacy single-file entries the
        #    slug equals the stem anyway, so no coverage is lost.)
        for entry in self.entries:
            if (name_lower in entry.slug.lower()
                    or name_lower in entry.title.lower()):
                return entry

        return None


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
    """Validate a TIL entry against the Agent Skill spec.

    Applies to ``skills/<slug>/SKILL.md`` files. Legacy single-file entries
    keep the older "must have an H1 and a Summary section" checks.
    """
    errors: List[str] = []
    is_skill = entry.path.name == 'SKILL.md'

    # Read the file once; subsequent checks reuse ``raw``/``body``.
    try:
        raw = entry.path.read_text()
    except OSError as exc:
        errors.append(f"Cannot read file: {exc}")
        raw = ''
    _, body = TILEntry._split_frontmatter(raw)

    if is_skill:
        # Frontmatter must exist for skill entries.
        if not entry.frontmatter:
            errors.append("Missing frontmatter block (--- ... ---)")
        else:
            name = entry.frontmatter.get('name', '')
            description = entry.frontmatter.get('description', '')
            dir_name = entry.path.parent.name

            if not name:
                errors.append("Frontmatter missing 'name'")
            else:
                if name != dir_name:
                    errors.append(
                        f"Frontmatter 'name' ({name!r}) must match the "
                        f"directory name ({dir_name!r})")
                if not re.fullmatch(r'[a-z0-9-]{1,64}', name):
                    errors.append(
                        "Frontmatter 'name' must be lowercase letters, "
                        "digits, or hyphens (\u22641\u201364 characters)")

            if not description:
                errors.append("Frontmatter missing 'description'")
            elif len(description) > 1024:
                errors.append(
                    f"Frontmatter 'description' is too long "
                    f"({len(description)} chars; limit is 1024)")

        # The body must start with a level-1 heading per the skill spec.
        # "Start with" = the first non-empty line of the body is ``# ...``;
        # leading blank lines are OK, prose before the heading is not.
        first_nonempty = next(
            (line for line in body.splitlines() if line.strip()),
            '',
        )
        if not re.match(r'^# .+', first_nonempty):
            errors.append("Body must start with a level-1 heading (# ...)")
    else:
        # Legacy single-file entry: keep the older sanity checks.
        if not entry.title:
            errors.append("Missing H1 title")
        if 'Summary' not in entry.sections:
            errors.append("Missing Summary section")

    # Common: code blocks must have a language specifier. Walk fences
    # line-by-line so a stray backtick inside a code block can't mask
    # the opening fence.
    in_block = False
    open_lang: Optional[str] = None
    for line in body.splitlines():
        m = re.match(r'^```([A-Za-z0-9_-]*)\s*$', line)
        if not m:
            continue
        if not in_block:
            in_block = True
            open_lang = m.group(1)
        else:
            in_block = False
            if not open_lang:
                errors.append("Code block missing language specifier")
            open_lang = None
    if in_block:
        errors.append("Unclosed code block (missing closing ```)")

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
