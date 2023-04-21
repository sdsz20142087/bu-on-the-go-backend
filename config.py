import os


class Config:
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    PORT = os.environ.get('PORT') or 8080
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI') or open('SECRET', 'r').readlines()[1].strip() or None
