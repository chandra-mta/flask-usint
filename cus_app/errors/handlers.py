"""
Error Handlers
==============

**errors/handlers.py**: Error Redirection Handlers

:Author: W. Aaron (william.aaron@cfa.harvard.edu)
:Last Updated: May 02, 2025

"""
from flask import render_template
from . import bp #: import the blueprint from error/__init__.py
from ..extensions import db

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
    return render_template('errors/500.html'), 500
