---
name: jupyter-venv
description: "Create a kernel running in a python venv. TIL note about jupyter. Use when working with jupyter and the user mentions venv or related topics."
---

# Create a kernel running in a python venv

Activate the venv, and then run the following (customize name as needed):
```bash
python -m ipykernel install --user --name myenv --display-name "Python (myenv)"
```

Then run `jupyter notebook` anywhere, and create a notebook using the new kernel - it will be running inside the venv used to create it.

Resource: [IPython - Kernels for different environments](https://ipython.readthedocs.io/en/stable/install/kernel_install.html#kernels-for-different-environments)
