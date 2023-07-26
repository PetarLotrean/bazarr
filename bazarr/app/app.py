# coding=utf-8

from flask import Flask, redirect

from flask_compress import Compress
from flask_cors import CORS
from flask_socketio import SocketIO

from .database import database
from .get_args import args
from .config import settings, base_url

socketio = SocketIO()


def create_app():
    # Flask Setup
    app = Flask(__name__)
    app.config['COMPRESS_ALGORITHM'] = 'gzip'
    Compress(app)
    app.wsgi_app = ReverseProxied(app.wsgi_app)

    app.config["SECRET_KEY"] = settings.general.flask_secret_key
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.config['JSON_AS_ASCII'] = False

    app.config['RESTX_MASK_SWAGGER'] = False

    if settings.get('cors', 'enabled'):
        CORS(app)

    if args.dev:
        app.config["DEBUG"] = True
    else:
        app.config["DEBUG"] = False

    socketio.init_app(app, path=base_url.rstrip('/')+'/api/socket.io', cors_allowed_origins='*',
                      async_mode='threading', allow_upgrades=False, transports='polling')

    @app.errorhandler(404)
    def page_not_found(_):
        return redirect(base_url, code=302)

    # This hook ensures that a connection is opened to handle any queries
    # generated by the request.
    @app.before_request
    def _db_connect():
        database.begin()

    # This hook ensures that the connection is closed when we've finished
    # processing the request.
    @app.teardown_request
    def _db_close(exc):
        database.close()

    return app


class ReverseProxied(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        scheme = environ.get('HTTP_X_FORWARDED_PROTO')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)
