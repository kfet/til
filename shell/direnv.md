# Configure environment per directory

[direnv](https://direnv.net) is a self-contained binary tool, which allows setting-up shell environemnt per directory. It hooks into the shell prompt evaluation.

When you enter a directory it loads an `.env` or `.envrc` file, if present, and unloads it as you exit the directory. Supports also plugins for other actions per-directory, like activate/deactivate a Python pyenv.

----
Here's how to use direnv:

1. [Install direnv](https://direnv.net/docs/installation.html)
2. [Hook direnv into your shell](https://direnv.net/docs/hook.html)


Add environment to `.env` or `.envrc` in a directory
```
echo "export TEST=foo" > .envrc
```

Allow `direnv` to use it
```
direnv allow
```

Try it out
```
cd ..
echo $TEST
cd -
echo $TEST
```
