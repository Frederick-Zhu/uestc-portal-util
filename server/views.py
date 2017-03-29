# -*- coding:utf-8 -*-
import werkzeug.datastructures
from flask import render_template, request, session, url_for, redirect, flash, g

import portal_tools
import portal_tools.errors
from server import app


@app.before_request
def before_request():
    if request.method == 'GET' and request.path != url_for('index_page'):
        if session.has_key('username') and session.has_key('password'):
            try:
                g.portal = portal_tools.PortalUtil(username=session.get('username'),
                                                   password=session.get('password'))  # type: portal_tools.PortalUtil
            except:
                return redirect(url_for(index_page))
        else:
            return redirect(url_for('index_page'))


@app.route('/')
def index_page():
    if session.has_key('username') and session.has_key('password'):
        return render_template('index.html', login_vaild=True)
    else:
        return render_template('index.html', login_vaild=False)


@app.route('/login', methods=['POST', ])
def login():
    form_data = request.form  # type: werkzeug.datastructures.ImmutableMultiDict

    if not form_data.has_key('username') or not form_data.has_key('password'):
        flash('Form data ERROR!', 'danger')
        return redirect(url_for('index_page'))

    username = form_data.get('username')
    password = form_data.get('password')

    try:
        portal_tools.PortalUtil(username=username, password=password)
    except portal_tools.errors.IdasUsrPwdError:
        flash('Student ID or password wrong.', 'danger')
        return redirect(url_for('index_page'))
    except portal_tools.errors.IdasNeedCaptcha:
        flash('Need captcha.', 'danger')
        return redirect(url_for('index_page'))

    session['username'] = username
    session['password'] = password

    flash('Login success.', 'success')
    return redirect(url_for('index_page'))


@app.route('/logout')
def logout():
    session.pop('username')
    session.pop('password')
    flash('Logout success.', 'success')
    return redirect(url_for('index_page'))


@app.route('/final_exam_time')
def final_exam_time():
    final_exam_time_list = g.portal.getFinalExamTime(semester_id=143)

    final_exam_time_list.sort(key=lambda course: course['examBegin'])

    return render_template('final_exam_time.html',
                           final_exam_time_list=final_exam_time_list)
