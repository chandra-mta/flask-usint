# Usint CLI Interface

For supporting the day-to-day operation of an installation of the Usint Flask application, for example the live installation served by the main cxc web servers and installed at `/proj/web-cxc/wsgi-scripts/cus`, we have a few CLI tools which can update or fetch from that installation's database.

## General Usage

Use of the CLI tools requires two conditions for correct operation.
1. The user CLI terminal must have the flask-usint conda web environment invoked for library dependencies. This could be either invoking the direct environment running the application installation `TO BE DETERMINED`, or creating the conda yourself using the `python-server-configs/environment.yml` chandra-mta github repository file.
2. The terminal must have the current working directory set to the application installation's root directory. For example, the live application has all code files located in the `/proj/web-cxc/wsgi-scripts/cus` application root directory. This is just to avoid any pathing issues which might arise due to our need to determine an installation by a specific directory path.

Once done, run the the `cli.py` python script package entry point for the local python package, followed by the category of command, and the command an args themselves.
The local CLI package will contain `--help` options to document each command.
```
(test_python_web_apps) [waaron@scrapper-12:19:flask-usint]$ pwd
/home/waaron/git/flask-usint
(test_python_web_apps) [waaron@scrapper-12:20:flask-usint]$ cli.py <category> <command> --args
```

## User Category

These commands edit the user database.

```
(test_python_web_apps) [waaron@scrapper-12:21:flask-usint]$ cli.py user --help
Usage: cli.py user [OPTIONS] COMMAND [ARGS]...

  User management commands

Options:
  --help  Show this message and exit.

Commands:
  create  Create a new user in the database.
  groups  Change the group assignments for a user.
  search  Query the database for a specific user.
```

## Schedule Category

These commands edit the TOO duty schedule table.
Some commands are called via a cronjob, such as the maintain schedule command which injects additional time period table entries to maintain a rolling schedule horizon.

```
(test_python_web_apps) [waaron@scrapper-15:33:flask-usint]$ cli.py schedule maintain-schedule --help
Usage: cli.py schedule maintain-schedule [OPTIONS]

  Inject additional schedule time period entries into the schedule table up to
  a point in the future

Options:
  --help  Show this message and exit.

#: Example Cronjob
0 2 * * * cd /proj/web-cxc/wsgi-scripts/cus; /proj/sot/mta/envs/python_web_apps/bin/python cli.py schedule maintain-schedule
```