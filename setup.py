#!/usr/bin/env python3

import sys
import os

with open("README.rst", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    requirements = [l.strip() for l in f if l.strip()]

if len(sys.argv) > 1 and sys.argv[1] == "freeze":
    sys.argv[1] = "build"
    from cx_Freeze import setup, Executable
    target_name = ENTRYPOINT
    if sys.platform == "win32":
        target_name += ".exe"

    extra_kwargs = {
        "executables": [
            Executable(
                os.path.join("siriai", "_cxfreeze_main.py"),
                targetName=target_name,
            ),
        ],
    }
else:
    from setuptools import setup
    extra_kwargs = {}

setup(
    name="siriai",
    version="0.9",
    description="Embed image in ASS subtitle",
    long_description=long_description,
    author="Joe Hu (SAPikachu)",
    author_email="i@sapika.ch",
    url="https://github.com/SAPikachu/siriai",
    packages=["siriai"],
    install_requires=requirements,
    entry_points={
        "console_scripts": ["siriai = siriai.__main__:main"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.3",
        "Topic :: Multimedia :: Video",
    ],
    **extra_kwargs
)
