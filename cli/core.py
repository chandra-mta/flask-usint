"""
Core components for the CLI interface.
"""

__all__ = [
    "create_app",
    "db",
    "models",
    "mail",
    "emailing"
]

import sys
from functools import wraps

def _import_fail(error):
    """
    Internal warning for not activating the runtime application conda environment
    """
    print("Failed to start CLI due to import error.\n", file=sys.stderr)
    print(str(error), file=sys.stderr)
    print("Check that you have conda activated the environment before running this app installation CLI.", file=sys.stderr)
    print(f"Python: {sys.executable}", file=sys.stderr)
    raise SystemExit(1)

#: Define core variables from app context.
try:
    #: If fails, likely not running the correct conda environment.
    from cus_app import create_app, emailing
    from cus_app.extensions import db, mail
    #: Imports everything to ensure full model registration for SQLAlchemy
    import cus_app.models as models
    import cus_app.supple as supple
except ImportError as e:
    _import_fail(e)


#: Define app context function decorator
def with_app_context(f):
    """
    Add the line
    `@with_app_context`
    above any CLI defined function in order to provided the application context to the tool.
    
    This means that an instance of this installation's application will be generated for use by our commands.
    E.g. We can inject a new user into the database connection created by the application.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        app = create_app(logging_mode='console')
        #: Add additional configuration to the CLI invocation of the app creator
        #: to handle processing requests without the information of an incoming web request.
        #: Paths via this installation's specific instance folder. Relative pathing from the instance_relative_config argument.
        app.config.from_pyfile('cli_config.py', silent=True)
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper

def add_additional_cli_error_context(e):
    """
    If the python exception has certain commonly encountered problems,
    add additional notes for the developer
    """
    if "SERVER_NAME" in str(e):
        e.add_note(
            "Possible CLI configuration issue. Check that the SERVER_NAME variable is defined in the instance/cli_config.py module."
        )
    return e