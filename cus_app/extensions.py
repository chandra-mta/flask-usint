"""
Flask extensions are extra Python packages which expand the core Flask framework with a variety of desireable features.
In our case, we make use of a login handler, SQLAlchemy database transations matching web requests,
session data transferable to multiple web pages, and the Bootstrap templater.

This module intitializes these extensions independently, allowing their registration whenever the application is created in
the __init__.create_app() function. Structuring in this way helps avoid circular import errors for 
submodules which use extensions, allowing them to be referenced from this module.

https://flask.palletsprojects.com/en/stable/extensions/
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_session import Session
from flask_bootstrap import Bootstrap5

db = SQLAlchemy()
login = LoginManager()
web_session = Session()
bootstrap = Bootstrap5()