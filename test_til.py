#!/usr/bin/env python3
"""
Tests for the TIL CLI Tool
"""
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch, MagicMock
import sys

# Add the parent directory to sys.path so we can import the til module
sys.path.append(str(Path(__file__).parent))
from til_cli.til_cli.til import TILEntry, TILCollection, validate_entry, execute_code_block


class TestTILTool(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

        # Sample skill fixture — lives at skills/<slug>/SKILL.md, the only
        # layout the loader recognises.
        self.sample_dir = self.test_dir / "skills" / "sample"
        self.sample_dir.mkdir(parents=True)
        self.sample_file = self.sample_dir / "SKILL.md"
        self.sample_content = """---
name: sample
description: "Sample TIL. Use when testing the TIL CLI."
---

# Sample TIL

Date: 2024-02-24

## Summary

This is a sample TIL entry for testing.

## Details

More details about the sample.

## Install (executable)

```bash
echo "This is a test install command"
```

## Usage

How to use the sample.
"""
        self.sample_file.write_text(self.sample_content)

        # Invalid skill fixture — missing frontmatter, slug mismatch, no H1.
        self.invalid_dir = self.test_dir / "skills" / "invalid"
        self.invalid_dir.mkdir(parents=True)
        self.invalid_file = self.invalid_dir / "SKILL.md"
        self.invalid_content = """## No top-level heading

This file is missing frontmatter and a level-1 heading.
"""
        self.invalid_file.write_text(self.invalid_content)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_til_entry_parsing(self):
        # Test parsing a valid TIL entry
        entry = TILEntry(self.sample_file)
        
        # Check basic attributes
        self.assertEqual(entry.title, "Sample TIL")
        self.assertEqual(entry.metadata["Date"], "2024-02-24")
        
        # Check sections
        self.assertIn("Summary", entry.sections)
        self.assertIn("Details", entry.sections)
        self.assertIn("Install", entry.sections)
        self.assertIn("Usage", entry.sections)
        
        # Check executable sections
        self.assertIn("Install", entry.executable_sections)
        
        # Check executable blocks
        blocks = entry.get_executable_blocks("Install")
        self.assertEqual(len(blocks), 1)
        lang, code = blocks[0]
        self.assertEqual(lang, "bash")
        self.assertIn("echo", code)
    
    def test_til_collection(self):
        # Create a collection from the test directory
        collection = TILCollection(self.test_dir)

        # Check that entries were loaded (the two skills fixtures).
        self.assertEqual(len(collection.entries), 2)

        # Test search functionality
        results = collection.search("sample")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Sample TIL")

        # Test get_entry by slug
        entry = collection.get_entry("sample")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.title, "Sample TIL")

        # Test getting by absolute path
        entry = collection.get_entry(str(self.sample_file))
        self.assertIsNotNone(entry)

    def test_get_entry_does_not_match_skill_stem(self):
        """`til show <substring-of-SKILL>` must not return a random skill.

        ``skills/<slug>/SKILL.md`` files all share the stem ``SKILL``, so
        any partial-match clause that consulted ``path.stem`` would resolve
        single-character / short queries (``s``, ``sk``, ``kil``, ``ll``)
        to the first skill alphabetically. ``matches_search`` already
        avoids that; ``get_entry``'s partial-match fallback must too.
        """
        extra_dir = self.test_dir / "skills" / "zzz-other"
        extra_dir.mkdir(parents=True)
        (extra_dir / "SKILL.md").write_text(
            "---\nname: zzz-other\ndescription: \"Zzz. Use when.\"\n"
            "---\n\n# Zzz Other\n"
        )

        collection = TILCollection(self.test_dir)
        # Queries that are substrings of "skill" but appear in no slug,
        # title, or body content must return None, not a stem match.
        for query in ("kil", "ll", "sk", "skil"):
            found = collection.get_entry(query)
            self.assertIsNone(
                found,
                f"get_entry({query!r}) returned {found!r}; expected None "
                f"(query is a substring of SKILL.md stem only)")

        # Substring partial-match on slug must still work, so users keep
        # the "fuzzy slug" affordance even with the stem clause removed.
        # The setUp fixture lives at skills/sample/SKILL.md (slug=sample);
        # "ample" is a substring of the slug.
        found = collection.get_entry("ample")
        self.assertIsNotNone(found)
        self.assertEqual(found.slug, "sample")

    def test_search_does_not_match_skill_word_for_every_skill(self):
        """Searching for 'skill' must not return every skill via path.stem."""
        # ``path.stem`` for ``skills/<slug>/SKILL.md`` is always ``SKILL``.
        # Make sure that's no longer treated as searchable content.
        extra_dir = self.test_dir / "skills" / "ghostty-foo"
        extra_dir.mkdir(parents=True)
        (extra_dir / "SKILL.md").write_text(
            "---\nname: ghostty-foo\ndescription: \"Ghostty foo. Use when.\"\n"
            "---\n\n# Ghostty foo\n"
        )

        collection = TILCollection(self.test_dir)
        # ``skill`` must not blanket-match every entry: the two setUp
        # fixtures (``sample``, ``invalid``) and ``ghostty-foo`` are all
        # SKILL.md files, but none of their slugs/titles/content contain
        # the word "skill".
        hits = collection.search("skill")
        hit_slugs = {e.slug for e in hits}
        self.assertNotIn("ghostty-foo", hit_slugs)
        self.assertNotIn("sample", hit_slugs)
        self.assertNotIn("invalid", hit_slugs)

    def test_collection_ignores_non_skill_files(self):
        """Loader must only pick up skills/<slug>/SKILL.md."""
        # Top-level Markdown that isn't a skill.
        (self.test_dir / "README.md").write_text("# Project README\n")
        (self.test_dir / "LICENSE.md").write_text("# License\n")
        # Markdown in a sibling tool subdir.
        sub = self.test_dir / "til_cli"
        sub.mkdir()
        (sub / "README.md").write_text("# CLI README\n")
        (sub / "LICENSE.md").write_text("# CLI License\n")
        # Stray Markdown directly under skills/ that is not a SKILL.md.
        (self.test_dir / "skills" / "stray.md").write_text("# Stray\n")
        # Nested skill that doesn't match the skills/<slug>/SKILL.md shape.
        nested = self.test_dir / "skills" / "deep" / "nested"
        nested.mkdir(parents=True)
        (nested / "SKILL.md").write_text("# Nested\n")

        collection = TILCollection(self.test_dir)
        titles = {e.title for e in collection.entries}

        # Only the two fixtures created in setUp under skills/<slug>/SKILL.md.
        self.assertEqual(len(collection.entries), 2)
        for forbidden in ("Project README", "License", "CLI README",
                          "CLI License", "Stray", "Nested"):
            self.assertNotIn(forbidden, titles)

    def test_skill_without_h1_falls_back_to_description(self):
        """Skills whose body has no level-1 heading still appear in listings."""
        skill_dir = self.test_dir / "skills" / "vim-defaults"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(
            "---\n"
            "name: vim-defaults\n"
            "description: \"Vim Defaults. Use when configuring vim.\"\n"
            "---\n\n"
            "## My preferred VIM defaults\n\n"
            "Body without an H1.\n"
        )

        collection = TILCollection(self.test_dir)
        found = collection.get_entry("vim-defaults")
        self.assertIsNotNone(found)
        # No H1 -> title falls back to the description's lead phrase.
        self.assertEqual(found.title, "Vim Defaults")
    
    def test_slug_for_skill_entries(self):
        # Skill entries live at skills/<slug>/SKILL.md; slug must be the dir name.
        skill_dir = self.test_dir / "skills" / "shell-epoch-timestamp"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("# Convert epoch timestamp\n\nBody.\n")

        entry = TILEntry(skill_file)
        self.assertEqual(entry.slug, "shell-epoch-timestamp")
        self.assertEqual(str(entry), "Convert epoch timestamp (shell-epoch-timestamp)")

        # Legacy single-file entries fall back to the file stem.
        legacy = TILEntry(self.sample_file)
        self.assertEqual(legacy.slug, "sample")

        # Collection lookup by slug works for skills.
        collection = TILCollection(self.test_dir)
        found = collection.get_entry("shell-epoch-timestamp")
        self.assertIsNotNone(found)
        self.assertEqual(found.path, skill_file)

        # Repository-relative paths work.
        found = collection.get_entry("skills/shell-epoch-timestamp/SKILL.md")
        self.assertIsNotNone(found)
        self.assertEqual(found.path, skill_file)

        # Old search output omitted the leading skills/ directory; keep
        # accepting copied results from that output.
        found = collection.get_entry("shell-epoch-timestamp/SKILL.md")
        self.assertIsNotNone(found)
        self.assertEqual(found.path, skill_file)

    def test_validation(self):
        # Valid skill should pass cleanly.
        valid_entry = TILEntry(self.sample_file)
        self.assertEqual(validate_entry(valid_entry), [])

        # Invalid fixture is missing frontmatter and has no H1 — both
        # should be reported.
        invalid_entry = TILEntry(self.invalid_file)
        errors = validate_entry(invalid_entry)
        self.assertTrue(any("frontmatter" in e.lower() for e in errors),
                        f"expected a frontmatter error, got {errors!r}")

    def test_validation_skill_format(self):
        """Validator enforces the skills/<slug>/SKILL.md frontmatter spec."""
        # name mismatched with directory.
        skill_dir = self.test_dir / "skills" / "shell-foo"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: shell-bar\n"
            "description: \"Foo. Use when foo-ing.\"\n"
            "---\n\n"
            "# Foo\n"
        )
        errors = validate_entry(TILEntry(skill_dir / "SKILL.md"))
        self.assertTrue(any("name" in e.lower() and "match" in e.lower()
                            for e in errors),
                        f"expected name-mismatch error, got {errors!r}")

        # name contains invalid characters.
        bad_chars_dir = self.test_dir / "skills" / "Bad_Name"
        bad_chars_dir.mkdir(parents=True)
        (bad_chars_dir / "SKILL.md").write_text(
            "---\n"
            "name: Bad_Name\n"
            "description: \"Bad. Use when bad.\"\n"
            "---\n\n"
            "# Bad\n"
        )
        errors = validate_entry(TILEntry(bad_chars_dir / "SKILL.md"))
        self.assertTrue(any("lowercase" in e.lower() or "letters" in e.lower()
                            or "characters" in e.lower() for e in errors),
                        f"expected name-charset error, got {errors!r}")

        # description over the 1024-char limit.
        long_desc_dir = self.test_dir / "skills" / "long-desc"
        long_desc_dir.mkdir(parents=True)
        (long_desc_dir / "SKILL.md").write_text(
            "---\n"
            "name: long-desc\n"
            f"description: \"{'x' * 1100}\"\n"
            "---\n\n"
            "# Long\n"
        )
        errors = validate_entry(TILEntry(long_desc_dir / "SKILL.md"))
        self.assertTrue(any("1024" in e or "long" in e.lower() for e in errors),
                        f"expected description-length error, got {errors!r}")

        # Missing description.
        no_desc_dir = self.test_dir / "skills" / "no-desc"
        no_desc_dir.mkdir(parents=True)
        (no_desc_dir / "SKILL.md").write_text(
            "---\n"
            "name: no-desc\n"
            "---\n\n"
            "# No desc\n"
        )
        errors = validate_entry(TILEntry(no_desc_dir / "SKILL.md"))
        self.assertTrue(any("description" in e.lower() for e in errors),
                        f"expected missing-description error, got {errors!r}")

        # Code block with no language specifier.
        no_lang_dir = self.test_dir / "skills" / "no-lang"
        no_lang_dir.mkdir(parents=True)
        (no_lang_dir / "SKILL.md").write_text(
            "---\n"
            "name: no-lang\n"
            "description: \"No lang. Use when.\"\n"
            "---\n\n"
            "# No lang\n\n"
            "```\necho hi\n```\n"
        )
        errors = validate_entry(TILEntry(no_lang_dir / "SKILL.md"))
        self.assertTrue(any("language" in e.lower() for e in errors),
                        f"expected language-specifier error, got {errors!r}")

        # Stray backtick inside a tagged code block must not mask
        # detection of fence boundaries.
        stray_dir = self.test_dir / "skills" / "stray-tick"
        stray_dir.mkdir(parents=True)
        (stray_dir / "SKILL.md").write_text(
            "---\n"
            "name: stray-tick\n"
            "description: \"Stray. Use when.\"\n"
            "---\n\n"
            "# Stray\n\n"
            "```bash\nwget http://example.com/foo.tar.gz`\n```\n\n"
            "```\necho second\n```\n"
        )
        errors = validate_entry(TILEntry(stray_dir / "SKILL.md"))
        self.assertTrue(any("language" in e.lower() for e in errors),
                        f"stray backtick masked second-block detection: "
                        f"{errors!r}")

        # Unclosed code block must be reported.
        unclosed_dir = self.test_dir / "skills" / "unclosed"
        unclosed_dir.mkdir(parents=True)
        (unclosed_dir / "SKILL.md").write_text(
            "---\n"
            "name: unclosed\n"
            "description: \"Unclosed. Use when.\"\n"
            "---\n\n"
            "# Unclosed\n\n"
            "```bash\necho hi\n"
        )
        errors = validate_entry(TILEntry(unclosed_dir / "SKILL.md"))
        self.assertTrue(any("unclosed" in e.lower() for e in errors),
                        f"expected unclosed-fence error, got {errors!r}")

        # Body must START with a level-1 heading: paragraph text before
        # the first ``# `` is a spec violation, not just unusual.
        prose_first_dir = self.test_dir / "skills" / "prose-first"
        prose_first_dir.mkdir(parents=True)
        (prose_first_dir / "SKILL.md").write_text(
            "---\n"
            "name: prose-first\n"
            "description: \"Prose. Use when.\"\n"
            "---\n\n"
            "Stray paragraph before the heading.\n\n"
            "# Title\n"
        )
        errors = validate_entry(TILEntry(prose_first_dir / "SKILL.md"))
        self.assertTrue(any("start" in e.lower() and "level-1" in e.lower()
                            for e in errors),
                        f"expected body-must-start-with-H1 error, got "
                        f"{errors!r}")
    
    @patch('subprocess.call')
    @patch('builtins.input', return_value='y')
    def test_execute_code_block(self, mock_input, mock_subprocess_call):
        # Set up the mock to return a success status code
        mock_subprocess_call.return_value = 0
        
        # Test executing a bash code block
        result = execute_code_block('bash', 'echo "Hello, World!"')
        
        # Verify that the subprocess call was made
        mock_subprocess_call.assert_called_once()
        
        # Check that the script file path was passed to subprocess.call
        args, _ = mock_subprocess_call.call_args
        script_path = args[0][1]
        
        # Verify that a unique filename was generated (contains a random part)
        self.assertIn('til_exec_', script_path)
        self.assertRegex(script_path, r'til_exec_[a-f0-9]{8}\.sh$')
        
        # Verify the return value
        self.assertEqual(result, 0)


    def test_search_term_underscore_complete_not_hijacked(self):
        """`til search _complete` must search, not run the hidden helper."""
        import subprocess
        til_launcher = Path(__file__).parent / "til"
        # Use --repo-path so the test repo is targeted.
        proc = subprocess.run(
            [str(til_launcher), "--repo-path", str(self.test_dir),
             "search", "_complete"],
            capture_output=True, text=True,
        )
        # The search should run cleanly and report a real result line —
        # either matching entries or "No matching entries found" — not
        # emit the completion helper's slug list.
        out = proc.stdout
        self.assertTrue(
            "matching entries" in out or "No matching entries found" in out,
            f"`til search _complete` looks hijacked by the completion "
            f"helper. stdout=\n{out}")

    def test_help_does_not_leak_complete_helper(self):
        """`til --help` must not expose the hidden `_complete` subcommand."""
        import subprocess
        til_launcher = Path(__file__).parent / "til"
        out = subprocess.check_output(
            [str(til_launcher), "--help"], text=True,
            stderr=subprocess.STDOUT,
        )
        self.assertNotIn("_complete", out,
                         f"`_complete` leaked into --help:\n{out}")
        self.assertNotIn("SUPPRESS", out,
                         f"`SUPPRESS` sentinel leaked into --help:\n{out}")

    def test_completion_helper(self):
        """`til _complete` emits stable lists for shell completion."""
        import subprocess
        til_launcher = Path(__file__).parent / "til"

        def run(*extra: str) -> List[str]:
            out = subprocess.check_output(
                [str(til_launcher), "--repo-path", str(self.test_dir),
                 "_complete", *extra],
                text=True,
            )
            return [line for line in out.splitlines() if line]

        cmds = run("commands")
        self.assertIn("list", cmds)
        self.assertIn("show", cmds)
        self.assertIn("execute", cmds)
        # The helper itself stays hidden.
        self.assertNotIn("_complete", cmds)

        slugs = run("slugs")
        self.assertIn("sample", slugs)
        self.assertIn("invalid", slugs)

        sections = run("sections", "sample")
        self.assertIn("Install", sections)
        # Non-executable sections are not offered.
        self.assertNotIn("Summary", sections)

        # Unknown slug -> no output, no error.
        self.assertEqual(run("sections", "no-such-slug"), [])


class TestRenderer(unittest.TestCase):
    """Renderer selection rules for ``til show``."""

    def test_plain_flag_disables_renderer(self):
        from til_cli.til_cli.render import pick_renderer
        self.assertIsNone(pick_renderer(plain=True, tty=True, env={}))

    def test_non_tty_disables_renderer(self):
        from til_cli.til_cli.render import pick_renderer
        self.assertIsNone(pick_renderer(tty=False, env={}))

    def test_no_color_disables_renderer(self):
        from til_cli.til_cli.render import pick_renderer
        self.assertIsNone(
            pick_renderer(tty=True, env={"NO_COLOR": "1"}))

    def test_til_renderer_plain_disables_renderer(self):
        from til_cli.til_cli.render import pick_renderer
        for value in ("plain", "PLAIN", "none", "off", ""):
            self.assertIsNone(
                pick_renderer(tty=True, env={"TIL_RENDERER": value}),
                f"value={value!r} should yield plain output")

    def test_auto_picks_first_available(self):
        from til_cli.til_cli import render as render_mod
        # Force ``glow`` available, ``bat`` not — auto must pick glow.
        with patch.object(render_mod.shutil, "which",
                          side_effect=lambda n:
                          "/usr/bin/glow" if n == "glow" else None):
            argv = render_mod.pick_renderer(
                tty=True, env={"TIL_RENDERER": "auto"})
        self.assertIsNotNone(argv)
        self.assertEqual(argv[0], "/usr/bin/glow")

    def test_explicit_choice_returns_none_if_missing(self):
        from til_cli.til_cli import render as render_mod
        with patch.object(render_mod.shutil, "which", return_value=None):
            self.assertIsNone(render_mod.pick_renderer(
                tty=True, env={"TIL_RENDERER": "bat"}))

    def test_til_show_plain_flag_end_to_end(self):
        """`til show --plain` emits raw markdown to a pipe."""
        import subprocess
        til_launcher = Path(__file__).parent / "til"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            skill_dir = tmp_path / "skills" / "sample"
            skill_dir.mkdir(parents=True)
            content = (
                "---\nname: sample\n"
                "description: \"Sample. Use when.\"\n"
                "---\n\n# Sample\n\nBody text.\n"
            )
            (skill_dir / "SKILL.md").write_text(content)

            out = subprocess.check_output(
                [str(til_launcher), "--repo-path", str(tmp_path),
                 "show", "--plain", "sample"],
                text=True,
            )
        self.assertIn("# Sample", out)
        self.assertIn("Body text.", out)


if __name__ == "__main__":
    unittest.main()