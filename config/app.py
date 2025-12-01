import os
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

from database.Database import Database

load_dotenv()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///wordlewise.db')
    app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
    
    if app.config['FLASK_ENV'] == 'development':
        app.debug = True
    
    if test_config:
        app.config.update(test_config)

    JWTManager(app)
    CORS(app)

    database = Database(database_url=app.config['DATABASE_URL'])

    if not test_config or not test_config.get('TESTING'):
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            database.session.remove()

    # Register blueprints
    from routes.auth import auth_bp
    from routes.scores import scores_bp
    from routes.users import users_bp
    from routes.groups import groups_bp
    from routes.wordle import wordle_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(scores_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(groups_bp)
    app.register_blueprint(wordle_bp)

    # Store database instance in app config for route access
    app.config['database'] = database

    return app
