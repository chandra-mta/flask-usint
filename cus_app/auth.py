"""
This module compartmentalizes the Apache LDAP user authentication into the Flask login handler.
Note that no authentication measures, like password checking, occur in this module.
This only ties together the Apache web server authentication interface with the Flask User interface.
"""

import os
#from flask_login import current_user
from .extensions import login, db
from .models import User

def init_login():
    """
    Explicity register the authentication hooks with Flask-Login
    """
    @login.user_loader
    def load_user(id):
        """
        Session-based user loading.
        Flask-Login decorator for pairing a logged-in user to the Usint database.
        """
        return db.session.get(User,int(id))

    @login.request_loader
    def load_user_request(req):
        """
        Request-based user loading (Apache REMOTE_USER)
        """
        #: If already loaded via session, skip
        #if current_user.is_authenticated:
        #    return current_user
        #: Request environment is the Apache Web Server Context with LDAp authentication
        #: OS environment is the server process environment (localhost testing user definition)
        username = req.environ.get("REMOTE_USER") or os.environ.get("REMOTE_USER")
        
        if not username:
            raise Exception("Username is None in both request and server environment")

        user = db.session.execute(
            db.select(User).where(User.username == username)
            ).scalar()
        return user