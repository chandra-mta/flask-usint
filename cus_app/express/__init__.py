from flask import Blueprint
bp = Blueprint('express', __name__)
from . import routes
