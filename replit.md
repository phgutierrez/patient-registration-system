# Patient Registration System (Sistema de Registro de Pacientes)

## Overview
A patient management and surgery request system built with Flask. Supports patient registration, surgery scheduling, and PDF generation for surgery requests.

## Current State
- Running on Replit with Python 3.11
- SQLite database (stored in `instance/prontuario.db`)
- Default admin credentials: username `admin`, password `admin123`

## Project Architecture
- **Framework**: Flask 2.3.3
- **Database**: SQLite via SQLAlchemy 1.4.41
- **Auth**: Flask-Login
- **Forms**: Flask-WTF / WTForms
- **Migrations**: Flask-Migrate / Alembic
- **PDF**: ReportLab, PyPDF2, FillPDF

## Project Structure
```
├── run.py                 # Entry point, runs Flask on 0.0.0.0:5000
├── src/
│   ├── app.py             # Flask app factory
│   ├── config.py           # Configuration (DB URI, secret key)
│   ├── extensions.py       # Flask extensions (db, login, csrf, migrate)
│   ├── models/             # SQLAlchemy models (User, Patient, SurgeryRequest)
│   ├── routes/             # Blueprints (auth, main, patients, surgery)
│   ├── forms/              # WTForms form classes
│   ├── templates/          # Jinja2 templates
│   └── static/             # CSS, JS, PDF files
├── migrations/             # Alembic migrations
├── instance/               # SQLite database (auto-created)
├── init_db.py              # Database initialization script
└── requirements.txt        # Python dependencies
```

## Recent Changes
- 2026-02-19: Initial Replit setup
  - Fixed Werkzeug/Flask-WTF version compatibility (Werkzeug 2.3.7, Flask-WTF 1.2.1)
  - Fixed init_db.py to include required `full_name` parameter for User model
  - Cleaned up duplicate entries in requirements.txt

## User Preferences
- Language: Portuguese (Brazilian) - the app UI is in Portuguese
