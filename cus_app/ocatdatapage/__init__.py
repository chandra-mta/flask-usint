from flask import Blueprint
bp = Blueprint('ocatdatapage', __name__)
from . import routes
