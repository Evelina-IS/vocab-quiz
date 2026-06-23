import os
from flask import Flask, send_from_directory
from config import Config
from models import db
from routes import api

def create_app():
    app = Flask(__name__,
                static_folder='static',
                static_url_path='/static')
    app.config.from_object(Config)
    app.permanent_session_lifetime = 3600 * 24 * 30

    db.init_app(app)
    app.register_blueprint(api, url_prefix='/api')

    with app.app_context():
        db.create_all()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
