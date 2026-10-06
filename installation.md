# Installation
Installation of the Usint Flask application consists of a few key build commands followed by a preconfigured rsync of the application source code files.
The procedure involves steps run as the development user and steps run as the `cus` user in order for file ownership to be properly assigned.

# Required Files in GitHub Repo for installation
- cli
- cus_app
- __create_tables.py
- baseconfig.py
- cli.py
- README.md
- setup_logging.py
- usint.py

# Procedure

1. Update the version.conf file as your final development step, following the semantic versioning paradigm. https://semver.org
    This is crucial for keeping track of operating versions. This will typically involve incrementing the patch number following a bug fix.

2. Sign in as the `cus` user
```
su cus
# or
ssh cus@r2d2-v
```

3. Run the `install.sh` bash script with a predetermined application root argument.
```
./install.sh <prod|test|r2d2|home>
```

4. Following the copy of the application source code files, check the  `$APP_ROOT/instance` subdirectory, with the app root selected during the installation.
    The following files and configurations settings are necessary for each installation of the application, though it's likely you will use the already existing instance for each installation.
    - `config.py` (Configuration values which override the baseconfig.py file. This is good for changing the default dev behavior to official testing or production behavior.)
        - SQLALCHEMY_DATABASE_URI
        - HTTP_ADDRESS
        - MAIL_SUPPRESS_SEND
        - TEST_DATABASE
        - SECRET_KEY
    - `cli_config.py` (Configuration values used whenever the CLI tool is used. Necessary for certain settings which are only in a web request not present from the command line)
        - SERVER_NAME
        - PREFERRED_URL_SCHEME
        - MAIL_DEFAULT_SENDER
    - log subdirectories (For containing the rotating log files). Set these directories to the `gunicorn_cus` group and full read-write-execute permissions. `chmod 777`
        - `logs/<web_server_machine>/access`
        - `logs/<web_server_machine>/error`
        - `logs/<web_server_machine>/operation`
    - Symlinks to the Usint databases. The following is a workable example
        - test_usint.db -> /data/mta4/CUS/Data_v2.1/test_usint.db
        - usint.db -> /data/mta4/CUS/Data_v2.1/usint.db