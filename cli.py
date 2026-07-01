#!/usr/bin/env python
"""
Python script to act as the command line interface for this flask-usint application installation.
Note that the commands are installation specific, and will affect only what this directory's application can control.

Note that this script requires the conda environment supporting this directory's application to be activate.
The current conda environments supporting the different application installations can be found at 
```
/proj/sot/mta/envs
```
"""
from cli.main import cli
if __name__ == "__main__":
    cli()