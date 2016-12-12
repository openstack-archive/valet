# /var/www/valet/app.wsgi
from valet.api.app import load_app

application = load_app(config_file='/var/www/valet/config.py')