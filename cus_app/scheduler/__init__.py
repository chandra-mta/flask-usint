from flask import Blueprint
bp = Blueprint('scheduler', __name__)
from . import routes
