# GrimoireLab Toolkit [![Build Status](https://github.com/chaoss/grimoirelab-toolkit/workflows/tests/badge.svg)](https://github.com/chaoss/grimoirelab-toolkit/actions?query=workflow:tests+branch:master+event:push) [![Coverage Status](https://img.shields.io/coveralls/chaoss/grimoirelab-toolkit.svg)](https://coveralls.io/r/chaoss/grimoirelab-toolkit?branch=master)

Toolkit of common functions used across GrimoireLab projects.

This package provides a library composed by functions widely used in other
GrimoireLab projects. These function deal with date handling, introspection,
URIs/URLs, among other topics.

## Requirements

 * Python >= 3.8

You will also need some other libraries for running the tool, you can find the
whole list of dependencies in [pyproject.toml](pyproject.toml) file.

## Installation

There are several ways to install GrimoireLab Toolkit on your system: packages or source 
code using Poetry or pip.

### PyPI

GrimoireLab Toolkit can be installed using pip, a tool for installing Python packages. 
To do it, run the next command:
```
$ pip install grimoirelab-toolkit
```

### Source code

To install from the source code you will need to clone the repository first:
```
$ git clone https://github.com/chaoss/grimoirelab-toolkit
$ cd grimoirelab-toolkit
```

Then use pip or Poetry to install the package along with its dependencies.

#### Pip
To install the package from local directory run the following command:
```
$ pip install .
```
In case you are a developer, you should install GrimoireLab Toolkit in editable mode:
```
$ pip install -e .
```

#### Poetry
We use [poetry](https://python-poetry.org/) for dependency management and 
packaging. You can install it following its [documentation](https://python-poetry.org/docs/#installation).
Once you have installed it, you can install GrimoireLab Toolkit and the dependencies in 
a project isolated environment using:
```
$ poetry install
```
To spaw a new shell within the virtual environment use:
```
$ poetry shell
```

## License

Licensed under GNU General Public License (GPL), version 3 or later.
