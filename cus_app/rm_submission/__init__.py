from flask import Blueprint
bp = Blueprint('rm_submission', __name__)
from . import routes
