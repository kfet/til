#!/usr/bin/env python3

"""
TIL CLI Tool - Manage Today I Learned entries

Command-line interface for the TIL CLI Tool.
"""
import argparse
import logging
import os
import sys
import subprocess
from pathlib import Path
import platform as sys_platform  # Rename to avoid conflicts

# Import core functionality
from til_cli.til import (
    TILCollection,
    execute_code_block,
    validate_entry,
    get_til_repo_path,
    check_for_repo_updates
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("til")


def auto_update_repository(repo_path, command):
    """Automatically update repository if needed based on command type"""
    if command != 'update':
        # Only force update for commands that depend on content
        force_update = command in ['list', 'search', 'show', 'execute']
        check_for_repo_updates(repo_path, force=force_update)


def main():
    """Main entry point for the TIL CLI tool"""
    try:
        # Set up argument parser
        parser = argparse.ArgumentParser(description="TIL CLI Tool")
        subparsers = parser.add_subparsers(
            dest='command', help='Command to run')

        # List command
        subparsers.add_parser('list', help='List TIL entries')

        # Search command
        search_parser = subparsers.add_parser(
            'search', help='Search TIL entries')
        search_parser.add_argument('term', help='Search term')

        # Show command
        show_parser = subparsers.add_parser('show', help='Show a TIL entry')
        show_parser.add_argument('entry', help='Entry path or name')

        # Execute command
        exec_parser = subparsers.add_parser(
            'execute', help='Execute a TIL entry section')
        exec_parser.add_argument('entry', help='Entry path or name')
        exec_parser.add_argument('section', help='Section name to execute')

        # Validate command
        validate_parser = subparsers.add_parser(
            'validate', help='Validate TIL entries')
        validate_parser.add_argument(
            'entry', nargs='?', help='Entry path (or all if not specified)')

        # Version command
        subparsers.add_parser('version', help='Show version information')

        # Config command
        config_parser = subparsers.add_parser(
            'config', help='Configure TIL repository location')
        config_parser.add_argument(
            'path', nargs='?', help='Path to TIL repository')

        # Update command
        subparsers.add_parser(
            'update', help='Update TIL repository with latest changes')

        # Add global repo-path argument
        parser.add_argument('--repo-path', help='Path to TIL repository')

        # Parse args
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return 0

        # Get repository path
        if hasattr(args, 'repo_path') and args.repo_path:
            root_dir = Path(args.repo_path)
        else:
            root_dir = get_til_repo_path()

        # Handle config command (This must be handled before initializing the collection)
        if args.command == 'config':
            config_path = Path.home() / '.tilconfig'
            if args.path:
                repo_path = Path(args.path).resolve()

                if not repo_path.is_dir():
                    logger.error(f"Error: Not a valid directory: {repo_path}")
                    return 1

                config_path.write_text(str(repo_path))
                print(f"TIL repository path set to: {repo_path}")
                return 0

            elif config_path.exists():
                repo_path = Path(config_path.read_text().strip())
                print(f"TIL repository path: {repo_path}")
                return 0

        # Automatically update repository if needed
        auto_update_repository(root_dir, args.command)

        # Initialize TIL collection
        collection = TILCollection(root_dir)

        # Execute command
        if args.command == 'list':
            entries = collection.entries

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
                logger.error(
                    f"Section '{args.section}' is not marked as executable")
                return 1

            blocks = entry.get_executable_blocks(args.section)
            if not blocks:
                logger.error(
                    f"No executable code blocks found in section '{args.section}'")
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

        elif args.command == 'update':
            repo_path = root_dir
            print(f"Updating TIL repository at: {repo_path}")
            try:
                # Check if it's a git repository
                git_dir = repo_path / '.git'
                if not git_dir.is_dir():
                    logger.error(f"Error: Not a git repository: {repo_path}")
                    return 1

                # Run git pull
                result = subprocess.run(
                    ['git', 'pull'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(f"Successfully updated:\n{result.stdout}")
                    return 0
                else:
                    logger.error(
                        f"Error updating repository:\n{result.stderr}")
                    return 1
            except Exception as e:
                logger.error(f"Error updating repository: {e}")
                return 1

        elif args.command == 'version':
            from til_cli import __version__
            print(f"TIL CLI Tool v{__version__}")
            print(f"Python: {sys.version.split()[0]}")
            print(f"Platform: {sys_platform.system()}")
            print(f"Repository path: {root_dir}")

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
