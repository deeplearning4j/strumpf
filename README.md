# Strumpf - Skymind test resource management for paunchy files

Strumpf is a test resource management tool for very large files that fits into your git workflow.
Instead having to rely on git LFS, Strumpf keeps references to the actual test files and downloads
them on demand at test time. This way your test resource folder won't exceed size limits you want
to avoid.

---------

[![Build Status](https://jenkins.ci.skymind.io/buildStatus/icon?job=deeplearing4j/strumpf/master)](https://jenkins.ci.skymind.io/blue/organizations/jenkins/deeplearing4j%2Fstrumpf/activity)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/deeplearning4j/strumpf/blob/master/LICENSE)
[![PyPI version](https://badge.fury.io/py/strumpf.svg)](https://badge.fury.io/py/strumpf)

## Installation

Strumpf is on PyPI, so you can install it with `pip`:

```bash
pip install strumpf
```

Alternatively, you can build the project locally as follows:

```bash
git clone https://www.github.com/deeplearning4j/strumpf.git
cd strumpf
python setup.py install
```

## Strumpf command line interface (CLI)

Installing Strumpf exposes a command line tool called `strumpf`. You can use this tool to configure
your test environment. To initialize a new Strumpf configuration, type

```bash
strumpf init


███████╗████████╗██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗
██╔════╝╚══██╔══╝██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝
███████╗   ██║   ██████╔╝██║   ██║██╔████╔██║██████╔╝█████╗  
╚════██║   ██║   ██╔══██╗██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  
███████║   ██║   ██║  ██║╚██████╔╝██║ ╚═╝ ██║██║     ██║
╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝

...
```