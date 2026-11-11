from setuptools import setup, find_packages

setup(
    name="prontuario",
    version="2.8.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-login',
        'python-dotenv>=1.2.2,<2',
        'pycryptodome==3.23.0',
        'PyMuPDF==1.28.0',
    ],
)
