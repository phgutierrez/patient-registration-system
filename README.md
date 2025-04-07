# filepath: /patient-registration-system/patient-registration-system/README.md

# Patient Registration System

This project is a basic patient registration system with login functionality for doctors, managers, and administrators. It uses a Flask backend and an SQLite database to manage user and patient data.

## Features

- User authentication for doctors, managers, and administrators
- Patient registration and management
- Dashboard for logged-in users
- Responsive HTML frontend

## Project Structure

```
patient-registration-system
├── src
│   ├── static
│   │   ├── css
│   │   │   └── styles.css
│   │   └── js
│   │       └── main.js
│   ├── templates
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   └── registration.html
│   ├── models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── patient.py
│   ├── routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── patients.py
│   ├── database
│   │   └── schema.sql
│   ├── config.py
│   ├── app.py
│   └── utils.py
├── tests
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_patients.py
├── requirements.txt
└── README.md
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd patient-registration-system
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Set up the database by running the SQL schema:
   ```
   sqlite3 database/schema.sql
   ```
2. Start the application:
   ```
   python src/app.py
   ```
3. Access the application in your web browser at `http://localhost:5000`.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.