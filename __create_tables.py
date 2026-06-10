#!/usr/bin/env python
"""
All database tables must exists before the server starts.
Otherwise, the error log will pollute with failed table creation statements as every worker tries to create any missing tables

If the database tables have been manipulated in some way, or the server-side session table dropped,
then run this script which creates a single application context to generate the tables for this installation.
"""
from cus_app.extensions import db
from cus_app import create_app

app = create_app()
with app.app_context():
    db.create_all()