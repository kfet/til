# Manage venv and dependencies using pipenv

[pipenv](https://pipenv.pypa.io/en/latest/) uses Pipfile and Pipfile.lock to manage dependencies, including hashes, instead of requirements.txt.

install:
```bash
pip install pipenv
```

add dependency (e.g. `requests`):
```
pipenv install requests
```

configure direnv
```
echo 'layout pipenv' >> .envrc
```
