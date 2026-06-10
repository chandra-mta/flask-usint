from flask import Blueprint
bp = Blueprint('chkupdata', __name__)
from . import routes
