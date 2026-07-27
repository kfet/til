import re
from pathlib import Path

from setuptools import setup, find_packages

HERE = Path(__file__).resolve().parent

# Single source of truth for the version: til_cli/__init__.py. Keeping a
# second literal here is how 1.0.0/1.1.0 drifted apart and made
# ``til version`` report a stale number.
VERSION = re.search(
    r'^__version__\s*=\s*["\']([^"\']+)["\']',
    (HERE / "til_cli" / "__init__.py").read_text(),
    re.MULTILINE,
).group(1)

# README.md lives at the repository root, one level up — it is NOT part
# of this package directory, so it is absent when building from an sdist
# or when the packaging step moves files around (see the note in
# homebrew/til.rb.template). Degrade gracefully rather than crashing the
# install.
_readme = HERE.parent / "README.md"
LONG_DESCRIPTION = _readme.read_text() if _readme.is_file() else \
    "TIL CLI Tool - Manage Today I Learned entries"

setup(
    name="til-cli",
    version=VERSION,
    description="TIL CLI Tool - Manage Today I Learned entries",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="kfet",
    license="MIT",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "til=til_cli.__main__:main",
        ],
    },
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
