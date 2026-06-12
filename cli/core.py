"""
Core components for the CLI interface.
"""

import sys
from functools import wraps

def _import_fail(error):
    """
    Internal warning for not activating the runtime application conda environment
    """
    print("Failed to start CLI due to import error.\n")
    print(str(error))
    print("Check that you have conda activated the environment running this application installation.")
    print(f"Python: {sys.executable}")
    sys.exit(1)

#: Define core variables from app context.
try:
    #: If fails, likely not running the correct conda environment.
    from cus_app import create_app
    from cus_app.extensions import db
    from cus_app.models import User
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
        app = create_app()
        with app.app_context():
            return f(*args, **kwargs)
    return wrapper
