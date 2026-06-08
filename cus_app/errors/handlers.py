"""
Error Handlers
==============

**errors/handlers.py**: Error Redirection Handlers

:Author: T. Isobe (tisobe@cfa.harvard.edu)
:Maintainer: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 02, 2025

"""
from flask      import render_template
from cus_app.errors import bp
from cus_app.extensions import db
from cus_app.emailing import send_error_email
#
#--- use blueprint error handler to take care the error
#
@bp.app_errorhandler(404)
def not_found_error(error):
    """
    Error Handling for URL Not Found Error.
    """
    return render_template('errors/404.html'), 404


@bp.app_errorhandler(500)
def internal_error(error):
    """
    Error Handling for Interval Server Error.
    """
    db.session.rollback()
    send_error_email()
    return render_template('errors/500.html'), 500
