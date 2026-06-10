"""
Usint Flask Application Entrypoint
=================================

This module serves as the entrypoint for the Flask Usint application when
run under a WSGI server such as Gunicorn.

Gunicorn loads this module and imports the `application` object:

    gunicorn -c <server_config_name>.conf.py usint:application

This triggers execution of this file and instantiation of the Flask app
via `create_app()`.

- https://flask.palletsprojects.com/en/stable/deploying/gunicorn/#running

Config
------

This entrypoint is controlled by MTA.
By modifying this file or related configuration modules, MTA can:

- Change which configuration profile is used (e.g., test vs production)
- Redirect database connections such as test usint database vs live usint database
- Adjust application-level behavior without modifying Gunicorn or Apache configs

Runtime Behavior
----------------------------

Gunicorn imports this module once per worker process. Therefore:

- Changes to this file do NOT affect already running workers immediately
- Changes take effect only when:
    - the Gunicorn process is restarted, or
    - workers are reloaded (if supported by the deployment)

To enable more dynamic configuration without restart, prefer:
- configuration files loaded at runtime (e.g., instance/config.py)

Design
------

Because server-level configuration is controlled externally (SysHelp),
this entrypoint provides an application-level mechanism for configuring
runtime behavior with minimal reliance on system-level changes.
"""

#: Normal startup for app configuration and creation
from cus_app import create_app
application = create_app()