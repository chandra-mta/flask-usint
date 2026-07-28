# Usint Flask Application

This repository contains the Python Flask application supporting the [Usint Website](https://cxc.cfa.harvard.edu/wsgi/cus/usint/).

For information related to the web server backend, support, and development of this application, consult the **Flask/Usint** folder in the MTA shared drive.

## Gunicorn Server

This is the server process startup command, running under Syshelp control, using the usint.py entrypoint.
https://flask.palletsprojects.com/en/stable/deploying/gunicorn/#running
```
gunicorn -c <server_config_name>.conf.py usint:application
```

The gunicorn server configuration file handles settings to allow the cxc web servers to send requests to the application server.
Flask application specific settings, such as database connections and email settings, exists as flask config files, and thus within MTA file ownership.

## Installation of an application

In this context, installation is a loose term in which the USINT admin updates/edits the application root directory so that it contains the application source code.
An application root directory should contain the following files from the Github Repo.
The file copies can also be performed by using the `install.sh` bash script using predetermined application roots.

- cli
- cus_app
- __create_tables.py
- baseconfig.py
- cli.py
- README.md
- setup_logging.py
- usint.py

Then, following the copy of the application source code files, a few additional setup tasks should be done to ensure that the particular installation is ready.

- Create the `instance` subdirectory for containing files pertaining to the installation. In this instance subdirectory, you should consider creating the following files and subdirectories
  - `config.py` (Configuration values which override the baseconfig.py file. This is good for changing the default dev behavior to official testing or production behavior.)
    - SQLALCHEMY_DATABASE_URI
    - HTTP_ADDRESS
    - MAIL_SUPPRESS_SEND
    - TEST_DATABASE
    - SECRET_KEY
  - log subdirectories (For containing the rotating log files)
    - `log/access`
    - `log/error`
    - `log/operation`

- Activate the conda environment supporting the app installation (`/proj/sot/mta/envs`) and run the __create_tables.py script to ensure data tables and flask session tables are instantiated in the database configured for this install.

## Supplemental Scripts
Using the CLI, we also run a set of support scripts and commands to performs tasks such as database backups, maintenance, and retaining legacy data files. The Cronjobs to run these supplemental tasks are written in the cronjobs.md file

## Logging

Syshelp uses a separate setup for processing logs which relate to their Apache web server operations. For Flask Usint on the Gunicorn sever,
this differs to provided more direct access to compartmentalized logs for each application installation.
Starting at the root folder of the application, `/proj/web-cxc/wsgi-scripts/cus` for example, there is an `instance/logs` directory which contains three types of logs

- **access:** This contains a log of the HTTP requests made to the server. Here you can see what URL's are requested by which user and other HTTP request header information
- **error:** This contains runtime errors for both the gunicorn server running the flask application, and runtime errors within the flask application.
- **operation:** This is a log for normal operational messages, such as a revision being submitted, or a signoff being performed.

## Structure

The top level of this project is the application root, containing the server entrypoint modules, base configuration settings, the instance directory containing file relevant to this application installation's specific runtime, and the cus_app package containing our source code.

* **`usint.py`**  
  Python module entrypoint for the gunicorn server which determine application creation and configuration.
  By acting as an entrypoint, MTA can perform file edits to the application configuration and creation without necessarily requiring a
  gunicorn server restart. Conceptually, the application could still run if gunicorn called the cus_app package create_app() function directly.
  

* **`baseconfig.py`**  
  Configuration file.

* **`instance/`**  
  Instance folder for storing application-specific files such as logs and the `usint.db` database.

* **`cus_app/`**  
  Main Flask application folder containing relevant page generation scripts:

  * **`__init__.py`** — Application instantiation script
  * **`emailing.py`** — Email-related functions for notifications
  * **`models.py`** — SQLAlchemy ORM models for interfacing with the Usint Revision database
  * **`extensions.py`** - Module for instantiating the Flask Extension class instances.

  ### Submodules

  * **`chkupdata/`** — Parameter check page scripts
  * **`errors/`** — Error handler scripts
  * **`express/`** — Express sign-off page scripts
  * **`ocatdatapage/`** — Ocat data page scripts
  * **`orupdate/`** — Parameter status page scripts
  * **`scheduler/`** — TOO duty scheduler page scripts
  * **`supple/`** — Supplemental Python scripts

  ### Static Files (`static/`)

  * `color.json` — Maps color names to RGB values
  * `labels.json` — Maps Ocat parameters to visual labels
  * `parameter_selections.json` — Parameter group mappings used across the application
  * `usint.js` — javascript library for the Ocat data page
  * `ocat_style.css` — CSS styles
  * `ocatdatapage/` — Static files for the Ocat data page
  * `orupdate/` — Static files for the parameter status page
  * `scheduler/` — Static files for the scheduler page

  ### Templates (`templates/`)

  * `base.html` -  Base template block for general web pages.
  * `app_base.html` — Base template for application pages (mainly CSS differences)
  * `index.html` — Main index page
  * Additional page-specific templates (see sections below)

***

## chkupdata

Displays original, requested, and current parameter values for a given `<obsid>.<rev>`.

### Files

* `routes.py` — Main logic
* `forms.py` — WTForms definitions
* `__init__.py` — Module setup

### Templates

* `index.html` — Main page
* `provide_obsidrev.html` — Shown when `<obsid>.<rev>` is not found
* `macros.html` — Template macros

***

## errors

Application error handling.

### Files

* `handlers.py` — Main error handling logic
* `__init__.py` — Module setup

### Templates

* `404.html` — Not found page
* `500.html` — Server error page

***

## express

Express sign-off / approval workflow.

### Files

* `routes.py` — Main logic
* `forms.py` — WTForms definitions
* `__init__.py` — Module setup

### Templates

* `index.html` — Main page
* `confirm.html` — Confirmation page
* `macros.html` — Template macros

***

## ocatdatapage

Ocat data page used for updating parameter values.

### Files

* `routes.py` — Main logic
* `forms.py` — WTForms definitions
* `format_ocat_data.py` — Data formatting utilities
* `__init__.py` — Module setup

### Additional Data

* `<obs_ss>/mp_long_term` — Planned roll angle from MP site
* `<obs_ss>/scheduled_obs_list` — Scheduled observations

### Templates

* `index.html` — Main update page
* `macros.html` — Template macros
* `confirm.html` — Update confirmation page
* `finalize.html` — Job completion page
* `provide_obsid.html` — Shown when `<obsid>` is not found

***

## orupdate

Target parameter status page.

### Files

* `routes.py` — Main logic
* `forms.py` — WTForms definitions
* `__init__.py` — Module setup

### Templates

* `index.html` — Main page
* `macros.html` — Template macros

> **Note:**  
> This page refreshes every 3 minutes to display the latest data. This ensures consistency when multiple users are updating the database simultaneously.

***

## rm\_submission

Remove accidental submissions.

### Files

* `routes.py` — Main logic
* `forms.py` — WTForms definitions
* `__init__.py` — Module setup

### Templates

* `index.html` — Main page
* `macros.html` — Template macros

***

## scheduler

POC duty sign-up sheet.

### Files

* `routes.py` — Main logic
* `forms.py` — WTForms definitions
* `__init__.py` — Module setup

### Templates

* `index.html` — Main page
* `macros.html` — Template macros

***

## supple

Supplemental scripts used across the application.

### Files

* `database_interface.py` — SQLAlchemy interface for the Usint Revision SQLite database
* `helper_functions.py` — General helper utilities
* `read_ocat_data.py` — Fetches and formats Ocat Sybase data via the `ska_dbi SQSH` interface

### Data Sources

* **CXC Ocat Sybase database** (via `read_ocat_data.py`)
* **Usint Revision SQLite database** (via `database_interface.py`)