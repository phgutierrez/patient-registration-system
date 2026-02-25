from setuptools import setup, find_packages

setup(
    name="prontuario",
    version="2.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-sqlalchemy',
        'flask-login',
        'python-dotenv',
    ],
)