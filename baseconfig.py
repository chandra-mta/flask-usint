"""
This python modules contains the base configurations available to every installation of the application.
This means that defining a variable in BaseConfig is meant to be available to localhost, cxc-0web, cxc-test, etc.

This is used in the cus_app/__init__.py application generator function...
- `app.config.from_object(config_object)`
for configurations available to all installations of the app.

As of 2026-06-03, only the BaseConfig is available to all installations.

Installation specific configurtation options, handling the differences between localhost, cxc-web, cxc-test,
will be stored in instance config.py files which override the BaseConfig.
- `app.config.from_pyfile('config.py', silent=True)`

See cus_app/configurations/memo.md for more details.

"""

import os
from datetime import timedelta

sqlalchemy_echo = bool(os.getenv('SQLALCHEMY_ECHO'))

class BaseConfig(object):
    """
    Base Class for the configuration of the Usint application
    """
    #remove need for this
    #CONFIGURATION_NAME = "baseconfig"

    # find way to depend on flask app context variables instead.
    HTTP_ADDRESS = "http://127.0.0.1:8888"

    # store config external to usint app so that startup will also have error handling.
    #ADMINS = ["william.aaron@cfa.harvard.edu"]

    TEST_NOTIFICATIONS = True
    TEST_DATABASE = True
    #
    # --- Database and CSRF secret key
    #
    SECRET_KEY = 'secret_key_for_test'
    #
    # --- SQLAlchemy
    #
    #: With relative database URI's Flask_SQLAlchemy will automatically path the database URI to the instance folder.
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_usint.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'echo': sqlalchemy_echo,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 10
        }
    #
    # --- Session Settings
    #
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_REFRESH_EACH_REQUEST = True
    SESSION_TYPE = 'sqlalchemy' #: Must set SQLAlchemy instance for session once database connection is instantiated
    #
    # --- Directory Pathing
    #
    OBS_SS = "/data/mta4/obs_ss/"

    #: Flask Mail Parameters
    MAIL_DEFAULT_SENDER = "cus@cfa.harvard.edu"
    #: HEAD system hosts all run locally trusted mail-transfer-agents
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    #: Unsecured protocol usage since security implemented by HEAD system host MTA's
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_SUPPRESS_SEND = True
    