# -*- coding:utf-8 -*-
from functools import wraps

import arrow
import werkzeug.datastructures
from flask import render_template, request, session, url_for, redirect, flash, g
from typing import List, Dict, Union

import portal_tools
import portal_tools.errors
from server import app


def need_login(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if session.has_key('username') and session.has_key('password'):
            try:
                g.portal = portal_tools.PortalUtil(username=session.get('username'),
                                                   password=session.get('password'))  # type: portal_tools.PortalUtil
                return func(*args, **kwargs)
            except:
                return redirect(url_for('index_page'))
        else:
            return redirect(url_for('index_page'))

    return decorated_view


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
@need_login
def final_exam_time():
    final_exam_time_list = g.portal.getFinalExamTime(
        semester_id=143)  # type: List[Dict[str, Union[str, int, arrow.Arrow]]]

    final_exam_time_list.sort(key=lambda course: course['examBegin'])

    for course in final_exam_time_list:
        course['examBegin'] = course.get('examBegin').format('YYYY-M-D HH:mm')
        course['examEnd'] = course.get('examEnd').format('YYYY-M-D HH:mm')

    return render_template('final_exam_time.html',
                           final_exam_time_list=final_exam_time_list)


@app.route('/grade_analyze')
@need_login
def grade_analyze():
    total_gpa = g.portal.getTotalGpa()
    grade_list = g.portal.getGradeAnalyze()  # type:List[Dict[str, Union[str, float]]]

    grade_list.sort(key=lambda course: course.get('total'))
    grade_list.sort(key=lambda course: course.get('year'))
    grade_list.sort(key=lambda course: course.get('ratio'))
    grade_list.sort(key=lambda course: course.get('semester'))

    for course in grade_list:
        course['rmb_per_gpa'] = str(round(course.get('rmb_per_gpa'), 2)) if course.get('gpa') != 4.0 else ''
        course['rmb'] = str(course.get('rmb')) if course.get('gpa') != 4.0 else ''
        course['gpato4'] = str(round(course.get('gpato4'), 2)) if course.get('gpa') != 4.0 else ''
        course['ratio'] = str(course.get('ratio')) if course.get('gpa') != 4.0 else ''

    return render_template('grade_analyze.html',
                           total_gpa=total_gpa,
                           grade_list=grade_list)
