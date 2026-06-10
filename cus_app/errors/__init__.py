from flask import Blueprint
#
#--- setting name of blueprint and the name of the base module
#
bp = Blueprint('errors', __name__)

from . import handlers
