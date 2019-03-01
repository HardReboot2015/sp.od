# import os
# import logging
# from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app=app)
migrate = Migrate(app=app, db=db)
login = LoginManager(app=app)
login.login_view = '/'


# if not app.debug:
#     if not os.path.exists('logs'):
#         os.mkdir('logs')
#     file_handler = RotatingFileHandler('logs/sp.log', maxBytes=10240, backupCount=10)
#     file_handler.setFormatter(logging.Formatter(
#         '\n-------------------------------------\n%(asctime)s %(levelname)s: %(message)s [in %(pathname)s: %(lineno)d]\n-------------------------------------\n'))
#     file_handler.setLevel(logging.INFO)
#     app.logger.addHandler(file_handler)
#
#     app.logger.setLevel(logging.INFO)
#     app.logger.info('SP startup')

from app import routes, models, errors