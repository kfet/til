from setuptools import setup, find_packages

setup(
    name="til-cli",
    version="1.0.0",
    description="TIL CLI Tool - Manage Today I Learned entries",
    long_description=open("../README.md").read(),
    long_description_content_type="text/markdown",
    author="kfet",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "til=til_cli.__main__:main",
        ],
    },
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
)