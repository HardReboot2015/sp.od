import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL'] = "postgresql://{user}:{pw}@{url}/{db}".format(user="postgres", pw="1947bigg", url="localhost:5432", db="SP")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SECRET KEY') or 'this-is-very-secret-key'
    UPLOAD_FOLDER = '/static/upload/products/'
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])