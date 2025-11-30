import os
import time
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from database.Database import Database

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_CSRF_CHECK_FORM'] = False
    app.config['JWT_CSRF_IN_COOKIES'] = False
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    
    if test_config:
        app.config.update(test_config)
        
    JWTManager(app)
    CORS(app)

    database = Database(database_url='sqlite:///wordlewise.db')

    @app.before_request
    def before_request_func():
        time.sleep(0)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        database.session.remove()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.scores import scores_bp
    from routes.users import users_bp
    from routes.groups import groups_bp
    from routes.wordle import wordle_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(scores_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(wordle_bp)
    app.register_blueprint(admin_bp)

    # Store database instance in app config for route access
    app.config['database'] = database

    return app
