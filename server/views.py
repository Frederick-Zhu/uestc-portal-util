# -*- coding:utf-8 -*-
import werkzeug.datastructures
from flask import render_template, request, session

from server import app


@app.route('/')
def index_page():
    return render_template('index.html')


@app.route('/login', methods=['POST', ])
def login():
    form_data = request.form  # type: werkzeug.datastructures.ImmutableMultiDict

    if not form_data.has_key('username') and form_data.has_key('password'):
        raise ValueError

    session['username'] = form_data.get('username')
    session['password'] = form_data.get('password')

    return ''
