# src/models/user.py

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from src.app import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'  # Explicitly set table name

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

    full_name = db.Column(db.String(100), nullable=False, server_default='')
    cns = db.Column(db.String(15), nullable=True, unique=True,
                    info={'unique_constraint_name': 'uq_user_cns'})
    crm = db.Column(db.String(20), nullable=True, unique=True,
                    info={'unique_constraint_name': 'uq_user_crm'})

    def __init__(self, username, password, full_name, role='user', cns=None, crm=None):
        self.username = username
        self.set_password(password)
        self.full_name = full_name
        self.role = role
        self.cns = cns
        self.crm = crm

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'
