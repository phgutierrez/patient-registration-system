from flask import Blueprint

auth = Blueprint('auth', __name__)
main = Blueprint('main', __name__)
patients = Blueprint('patients', __name__)
surgery = Blueprint('surgery', __name__)
