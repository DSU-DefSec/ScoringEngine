from flask import Flask

app = Flask(__name__)
app.secret_key = 'this is a secret'

from .routes import blueprints
for blueprint in blueprints:
    app.register_blueprint(blueprint)

from .routes.auth import login_manager
login_manager.init_app(app)
