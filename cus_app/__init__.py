"""
**cus_app/__init__.py**: Initialize the CUS Flask Application

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: Mar 13, 2025

"""
import logging.handlers
import os
from datetime import datetime
from itertools import zip_longest
import logging
from flask import Flask, render_template

#: Import Flask Extensions from sibling module.
#: Flask Extensions expand functionality for the application
from .extensions import db, login, web_session_instance, bootstrap

from .supple.helper_functions import rank_ordr, approx_equals, get_more, IterateRecords, coerce_from_json

#: Import Flask Blueprints from the rest of the application
from .errors import bp as errors_bp #: Error Pages
from .ocatdatapage import bp as odp_bp #: OCAT data page for submitting revisions
from .orupdate import bp as oru_bp #: Parameter signoff status pages
from .express import bp as exp_bp #: Express approval pages
from .chkupdata import bp as cup_bp #: Read individual revision request data and status page
from .rm_submission import bp as rmv_bp #: Remove accidental revision submission
from .scheduler import bp as sch_bp #: TOO POC duty scheduler

#
# --- SQLAlchemy event handler to turn on Foreign Key Constraints for every engine connection.
#
from sqlalchemy.engine import Engine
from sqlalchemy import event

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


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
    #: Read this installation's specific instance folder for configuration overrides. Relative pathing from the instance_realtive_config argument.
    app.config.from_pyfile('config.py', silent=True)

    #: Bind the imported Flask Extensions to the initialized application.
    bootstrap.init_app(app)
    login.init_app(app)

    #: This application stores user session data inside the Usint SQLite database using the flask_session library.
    #: This means that user input into a revision is temporarily stored inside the flask_session database table as they navigate multiple web pages.
    #: Once a user is finished with their revision, the application performs the official database transaction,
    #: such as adding an obsid to the approved list, by writing to the revisions table.
    #: The corresponding session data column in the flask_session database table is then cleared by the application with clear_session_data() function.
    #: https://flask-session.readthedocs.io/en/latest/introduction.html#client-side-vs-server-side-sessions

    app.config['SESSION_SQLALCHEMY'] = db #: Must set the SQLAlchemy database for server-side session data after construction
    db.init_app(app)
    web_session_instance.init_app(app)
    #: Note that this application uses both an SQLite database session for writing to the database more permanently,
    #: and a web application session for short-term client interactions. These will be labels explicitly as
    #: web_session and db.session
    
    app.jinja_env.globals.update(function_dict)

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
    #
    # --- Setup file logger for UsintErrorHandler if not using the Werkzeug Browser Debugger
    #
    if not app.debug:
        #
        # --- keep last 10 error logs
        #
        log_dir = app.config.get("LOG_DIR") or os.path.join(app.instance_path, 'logs')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, "ocat.log"),
            maxBytes=51200,
            backupCount=10,
        )
        file_handler.name = "Error-Info"
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

    return app


def register_blueprints(app):
    """
    Flask Blueprints are a way to containerize Flask application components and endpoints (webpages) into
    reusable sets of modules. For Flask Usint, we just use them to organize different Usint tasks together,
    i.e. the Ocat Revision pages in one directory, the paramter status pages in another.
    https://flask.palletsprojects.com/en/stable/blueprints/
    """
    app.register_blueprint(errors_bp) #: Error Pages
    app.register_blueprint(odp_bp, url_prefix="/ocatdatapage") #: OCAT data page for submitting revisions
    app.register_blueprint(oru_bp, url_prefix="/orupdate") #: Parameter signoff status pages
    app.register_blueprint(exp_bp, url_prefix="/express") #: Express approval pages
    app.register_blueprint(cup_bp, url_prefix="/chkupdata") #: Read individual revision request data and status page
    app.register_blueprint(rmv_bp, url_prefix="/rm_submission") #: Remove accidental revision submission
    app.register_blueprint(sch_bp, url_prefix="/scheduler") #: TOO POC duty scheduler

