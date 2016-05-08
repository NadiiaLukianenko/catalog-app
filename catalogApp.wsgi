import sys
import logging
sys.path.insert(0, "/var/www/catalogApp/")

from catalogApp import app as application
from catalogApp import generate_csrf_token
application.secret_key = 'w58s7hVOVmRMmTXfqvo5PoDO'
application.config['SESSION_TYPE'] = 'filesystem'
application.jinja_env.globals['csrf_token'] = generate_csrf_token
application.debug = False
