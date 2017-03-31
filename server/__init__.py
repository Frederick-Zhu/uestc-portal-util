# -*- coding:utf-8 -*-

import gevent.monkey

gevent.monkey.patch_all()

from flask import Flask

app = Flask(__name__)
app.config.from_pyfile('flask_config.py')

from server import views
from server import views_api_v0_1
