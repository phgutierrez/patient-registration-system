from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
csrf = CSRFProtect()
migrate = Migrate()

# ISSUE 2 FIX: SQLite performance optimization for LAN deployment
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Apply SQLite performance pragmas for better LAN performance."""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # WAL mode for better concurrent access
        cursor.execute("PRAGMA journal_mode=WAL")
        # Normal synchronous mode (safer than OFF, faster than FULL)
        cursor.execute("PRAGMA synchronous=NORMAL")
        # Keep temp data in memory for speed
        cursor.execute("PRAGMA temp_store=MEMORY")
        # Increase cache size for better performance
        cursor.execute("PRAGMA cache_size=10000")
        cursor.close()
