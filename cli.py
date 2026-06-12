#!/usr/bin/env python
"""
Python script to act as the command line interface for this flask-usint application installation.
Note that the commands are installation specific, and will affect only what this directory's application can control.
"""
from cli.main import cli
if __name__ == "__main__":
    cli()