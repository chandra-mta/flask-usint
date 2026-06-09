"""
Gunicorn and Flask contain certain default logging class instances which are referenced by both libraries directly in their internal handling.
This means that the easiest way for us to configure logging altogether is to grab the existing loggers and reconfigure them.
https://docs.python.org/3/library/logging.html#logging.getLogger

This module handles the setup of three distinct python loggers for each distinct installation of the gunicorn server and application.

- access.log: This logger named `gunicorn.access` is instantiated by the gunicorn server process for logging HTTP requests to the server.
    
    For our needs, we want to allow greater configuration and implement file rotation, which is not possible in standard gunicorn configuration modules.
    As such, this module fetches the default `gunicorn.access` logger and reconfigures the handlers inside the server_logging_setup() function.

    :NOTE: In order for this to function, the gunicorn server must contain a configuration option which instantiates this logger for us to grab and reconfigure.
    This is easily done by setting `accesslog='-'` to log to stdout in the <server_name>.conf.py module.
    https://gunicorn.org/reference/settings/#accesslog

- error.log: This logger named `gunicorn.access` is instantiated by the gunicorn server process for handling errors encounter by the server process.
    
    For our needs, we want to allow greater configuration options, implement file rotation, and include the flask application error logs as well.
    As such, this module fetches the default `gunicorn.access` logger and reconfigures the handlers inside the server_logging_setup() function.

    In the application_logging_setup() function, this logger is fetched again to assign it to the flask app instance. Flask creates a default logger accessible by the
    `app.logger` attribute when referencing an application instance. We override the handlers in this logging class and map them to our gunicorn server logging handlers.
    By doing so, Flask will automatically route web application errors to the same location as server process errors.

    :NOTE: In order for this to function, the gunicorn server must contain a configuration option which instantiates this logger for us to grab and reconfigure.
    This is easily done by setting `errorlog='-'` to log to stderr in the <server_name>.conf.py module.
    https://gunicorn.org/reference/settings/#errorlog

- operation.log: This logger named `operations` is instantiated or fetched during the flask application creation. This logger exists specifically for logging normal operations
    of the Flask Usint application. For example, anytime a revision is submitted, this logger is access and written to log the obsid, revision number, and submitting user.
"""

import os
import logging
#: This logger is very similar to the native RotatingFileHandler class,
#: but implements multi-process handling, necessary due to multiple server workers.
from logging.handlers import RotatingFileHandler

def build_rotating_handler(path, level):
    handler = RotatingFileHandler(
        path,
        maxBytes=100 * 1024, # 100KB
        backupCount=4
    )

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
    )
    handler.setFormatter(formatter)
    handler.setLevel(level)

    return handler

def server_logging_setup(app_root):
    """
    This function reconfigures the existing gunicorn server loggers to our application needs.
    The `app_root` pathing argument is used to configured logs to be written to the application installation's instance folder.
    """
    log_dir = os.path.join(app_root, "instance", "logs")
    access_dir = os.path.join(log_dir, "access")
    error_dir = os.path.join(log_dir, "error")

    os.makedirs(access_dir, exist_ok=True)
    os.makedirs(error_dir, exist_ok=True)

    #: Gunicorn access logger
    gunicorn_access = logging.getLogger("gunicorn.access")
    gunicorn_access.handlers.clear()
    access_handler = build_rotating_handler(
            os.path.join(access_dir, "access.log"),
            logging.INFO
        )
    access_handler.set_name('access')
    gunicorn_access.addHandler(access_handler)
    gunicorn_access.setLevel(logging.INFO)

    #: Gunicorn error logger
    #: Log level set to info as gunicorn server startup events are always routed to stderr.
    #: Setting the level to ERROR would hide those.
    gunicorn_error = logging.getLogger("gunicorn.error")
    gunicorn_error.handlers.clear()
    error_handler = build_rotating_handler(
            os.path.join(error_dir, "error.log"),
            logging.INFO
        )
    error_handler.set_name('error')
    gunicorn_error.addHandler(error_handler)
    gunicorn_error.setLevel(logging.INFO)

def application_logging_setup(app):
    """
    This function reconfigures a created Flask application to use the gunicorn server logger
    for errors, and fetches / creates a logger for normal operations.
    """

    operation_dir = os.path.join(app.instance_path, "logs", "operation")
    os.makedirs(operation_dir, exist_ok=True)

    #: Route default Flask logger into gunicorn server error logs.
    gunicorn_error = logging.getLogger("gunicorn.error")

    if gunicorn_error.handlers:
        #: Running in a Gunicorn Server. Configure default application logger to use gunicorn error handlers
        app.logger.handlers = gunicorn_error.handlers
        app.logger.setLevel(gunicorn_error.level)
        app.logger.propagate = False
    else:
        #: No Gunicorn Server error logger. Test run in which error -> stderr
        pass
    
    #: Initialize the operations flask logger.
    #: Note that this logger is not accessible by any internal flask library functions.
    #: This is only accessible with the app.op_logger or current_app.op_logger attributes
    
    operations_logger = logging.getLogger("operations")
    
    #: If the fetched logger exists, then it will have a configured handler. Otherwise, create one.
    if not operations_logger.handlers:
        operations_logger.setLevel(logging.INFO)

        operations_handler = build_rotating_handler(
            os.path.join(operation_dir, "operations.log"),
            logging.INFO
        )
        operations_handler.set_name("operation")
        operations_logger.addHandler(operations_handler)
    
    app.op_logger = operations_logger
