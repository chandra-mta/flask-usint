"""
**cus_app/__init__.py**: Initialize the CUS Flask Application

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 13, 2025

"""
from datetime import datetime
from itertools import zip_longest
from flask import Flask, render_template
from setup_logging import application_logging_setup

#: Import Flask Extensions from sibling module.
#: Flask Extensions expand functionality for the application
from .extensions import db, login, web_session_instance, bootstrap
from .auth import init_login

from .supple.helper_functions import rank_ordr, approx_equals, get_more, IterateRecords, coerce_from_json

#: Import Flask Blueprints (sets of webpages) from the rest of the application
from .errors import bp as errors_bp #: Error Pages
from .ocatdatapage import bp as odp_bp #: OCAT data page for submitting revisions
from .orupdate import bp as oru_bp #: Parameter signoff status pages
from .express import bp as exp_bp #: Express approval pages
from .chkupdata import bp as cup_bp #: Read individual revision request data and status page
from .rm_submission import bp as rmv_bp #: Remove accidental revision submission
from .scheduler import bp as sch_bp #: TOO POC duty scheduler


from sqlalchemy.engine import Engine
from sqlalchemy import event
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    SQLite can use Foreign Key Constraints to make row references between tables very convenient.
    - https://sqlite.org/foreignkeys.html
    For backwards compatibility, SQLite database connections do not start with this setting available.
    This functions is an event listener for any database connection, turning foreign keys on before 
    any transaction is performed.

    :NOTE: If needed, this can implement other PRAGMA settings for every database connection.
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

#: Small Python convenience functions for use in the Jinja Templates
function_dict = {
    'zip_longest': zip_longest,
    'set': set,
    'str': str,
    'rank_ordr': rank_ordr,
    'enumerate': enumerate,
    'approx_equals': approx_equals,
    'zip': zip,
    'datetime': datetime,
    'coerce_notes': lambda x: coerce_from_json(x) or {},
    'get_more': get_more,
    'IterateRecords': IterateRecords
}
def create_app(config_object='baseconfig.BaseConfig'):
    """
    Function for instantiating the entire application.

    :NOTE: The call for the app.app_context().push() makes the application context available for the later steps of registering webpage blueprints.
    This is done to make the database available for the scheduler to fetch TOO users, but will make the context available for all webpages.
    Therefore in future development, it's possible for functional inclusion to be made which require the application context, but the developer is not aware.
    Be mindful of editing or removing this function call and verify that which web pages require the application context in order to be registered
        - Scheduler Page
    https://flask.palletsprojects.com/en/stable/appcontext/

    :NOTE: The Usint database interface is supported by a set of interworking interfaces which require an understanding of PRG design approaches.
    This ensures that database writes are formatted successfully and not repeated upon new or refreshed requests.
        - PRG: https://en.wikipedia.org/wiki/Post/Redirect/Get
        - ACA Team Sybase Interface: https://github.com/sot/ska_dbi/blob/master/ska_dbi/sqsh.py
    
    # Is this true?
    The SQLite database interface libraries share a single "database" session per web request so that all users operate with the same data.
    This differs from a "web" session which stores data for the user in between web requests where common usage means they submit multiple web requests in a single sitting.

    Flask-Session commits to the usint database following every edit of the server-side cookie, which will also commit any pending transaction in the 
    SQLAlchemy database interface used for recording ocat revision information. This has the benefit of ensuring all web application processes are cleanly
    applied on the user side, at the expense of requiring careful monitoring of development work to ensure SQLAlchemy transactions and Flask-Session cookie updates
    occur separately during processing.
        - https://flask-session.readthedocs.io/en/latest/
        - https://flask-sqlalchemy.readthedocs.io/en/stable/
        - https://flask.palletsprojects.com/en/stable/api/#flask.session
    
    :NOTE: When testing the application, refreshing the web browser can sometimes retain previous form selections in rendering the webpage, even if the FlaskForm
    is altered to render the webpage differently or display different starting data in the form. It's most reliable to close the webpage entirely and reopen to test changes.

    :NOTE: Wherever form input is required, use the PRG design pattern (https://en.wikipedia.org/wiki/Post/Redirect/Get)

    """
    #: Instance 
    app = Flask(__name__, instance_relative_config=True)
    #: Import the configuration class listed as an argument from the application root baseconfig.py module.
    app.config.from_object(config_object)
    #: Read this installation's specific instance folder for configuration overrides. Relative pathing from the instance_relative_config argument.
    app.config.from_pyfile('config.py', silent=True)

    #: Bind the imported Flask Extensions to the initialized application.
    bind_flask_extensions(app)

    #: Define convenient minor functions in Jinja templates for rendering HTML files.
    app.jinja_env.globals.update(function_dict)

    #: Register the login handler functions.
    init_login()

    #app.app_context().push() #: Suspect. Investigate more.

    #: Register all subpages stored in the Flask Blueprints as URL routes
    register_blueprints(app)
    
    #: Register Main Usint Page as URL route
    @app.route("/")
    def index():
        """
        Render the Default Usint page
        """
        return render_template("index.html")
    
    #: Setup Application logging handlers
    application_logging_setup(app)

    return app

def bind_flask_extensions(app):
    """
    Flask Extensions are additional libraries which expand the functionality of an application,
    such as a user login manager and SQLite database connection handler.

    :NOTE: **SESSIONS:** A session is a temporary stateful exchange of information between a user and an application.
        This application uses TWO distinct sessions.

        - web_session: Part of Flask. This stores user input data and used to render web pages. For example, the OCAT data page
                    stores a new Z-offset user input value in the web_session so that the confirmation page can read and display.
                    web_session is client specific, relatively temporary, and only for storing data across multiple web pages.

                    For convenience, we use the flask_session library to write this data to the Usint SQLite database in the flask_sessions table.
                    While still recording data in the same file, this is not our permanent revision database. This is a server-side session
                    matched to a client-side cookie with a session-id to allocate intermediary data.
                    https://flask-session.readthedocs.io/en/latest/introduction.html#client-side-vs-server-side-sessions
        
        - db.session: Part of SQLAlchemy. This stores data to be injected into or fetch from the Usint SQLite database. Revision request data,
                    signoff statuses, TOO POC schedule, etc. This session exists for basic database mechanics to handle multiple simultaneous transactions
                    without overwriting other data. While technically a temporary data location, this contains data meant to be more permanent on the shared
                    Usint Database so that other users can read it.
    """
    #: Bootstrap is a front-end template, which means it provides helper functions
    #: to the Jinja templates for easily writing and rendering HTML files.
    bootstrap.init_app(app)

    #: Login provides helper functions to pull information on the logged-in user.
    #: WE DO NOT USE THIS FOR USER AUTHENTICATION. Login is done by the main web server
    #: using Apache LDAP and we just fetch the REMOTE_USER variable for the logged in user.
    login.init_app(app)

    #: To use server-side sessions, we bind the database connection as our web_session data file.
    app.config['SESSION_SQLALCHEMY'] = db #: Must set after connection construction but before binding extensions to the app.
    db.init_app(app)
    web_session_instance.init_app(app)

def register_blueprints(app):
    """
    Flask Blueprints are a way to containerize Flask application components and endpoints (webpages) into
    reusable sets of modules. For Flask Usint, we just use them to organize different Usint tasks together,
    i.e. the Ocat Revision pages in one directory, the parameter status pages in another.
    https://flask.palletsprojects.com/en/stable/blueprints/
    """
    app.register_blueprint(errors_bp) #: Error Pages
    app.register_blueprint(odp_bp, url_prefix="/ocatdatapage") #: OCAT data page for submitting revisions
    app.register_blueprint(oru_bp, url_prefix="/orupdate") #: Parameter signoff status pages
    app.register_blueprint(exp_bp, url_prefix="/express") #: Express approval pages
    app.register_blueprint(cup_bp, url_prefix="/chkupdata") #: Read individual revision request data and status page
    app.register_blueprint(rmv_bp, url_prefix="/rm_submission") #: Remove accidental revision submission
    app.register_blueprint(sch_bp, url_prefix="/scheduler") #: TOO POC duty scheduler

