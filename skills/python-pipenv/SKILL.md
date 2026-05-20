---
name: python-pipenv
description: "Manage venv and dependencies using pipenv. TIL note about python. Use when working with python and the user mentions pipenv or related topics."
---

# Manage venv and dependencies using pipenv

[pipenv](https://pipenv.pypa.io/en/latest/) uses Pipfile and Pipfile.lock to manage dependencies, including hashes, instead of requirements.txt.

install:
```bash
pip install pipenv
```

add dependency (e.g. `requests`):
```bash
pipenv install requests
```

configure direnv
```bash
echo 'layout pipenv' >> .envrc
```
