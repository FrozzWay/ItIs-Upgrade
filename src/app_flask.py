from flask import (Flask, render_template, send_from_directory)
from blueprints.api import bp as api_bp
import os
import mimetypes
import re

mimetypes.init()
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('image/svg+xml', '.svg')

app = Flask(
    __name__,
    template_folder=os.path.join(os.getcwd(), 'templates'),

    static_folder=os.path.join(os.getcwd(), 'static')
)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploaded')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
APP_DIRECTORY = os.getcwd()
app.config['APP_DIRECTORY'] = APP_DIRECTORY
STATIC_FOLDER = os.path.join(os.getcwd(), 'static')


app.register_blueprint(api_bp, url_prefix="/api")


@app.get('/')
def index_page():
    return render_template('index.html')


@app.get('/<path:page>')
def fallback(page):
    if check_for_static_files(page):
        return send_from_directory(STATIC_FOLDER, page)

    return render_template('index.html')


def check_for_static_files(page):
    # regex = re.match(r"^.*(\.js|\.css|\.ico)$")
    regex = re.match(r"^.*(\..+)$", page)
    if regex:
        return True

