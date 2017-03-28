# -*- coding:utf-8 -*-

from flask import render_template

from server import app


@app.route('/')
def index_page():
    return render_template('index.html')
