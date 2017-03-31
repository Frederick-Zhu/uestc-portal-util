# -*- coding:utf-8 -*-

from functools import wraps

import arrow
from flask import jsonify, request, g
from typing import List, Dict, Union

import portal_tools
from server import app


def need_login(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        form_data = request.form
        if form_data.has_key('username') and form_data.has_key('password'):
            try:
                g.portal = portal_tools.PortalUtil(username=form_data.get('username'),
                                                   password=form_data.get('password'))  # type: portal_tools.PortalUtil
                return func(*args, **kwargs)
            except:
                return jsonify('ERROR')
                # return func(*args, **kwargs)
        else:
            return jsonify('ERROR')

    return decorated_view


@app.route('/api/v0.1/final_exam_time', methods=['POST', ])
@need_login
def api_v0_1_final_exam_time():
    final_exam_time_list = g.portal.getFinalExamTime(
        semester_id=143)  # type: List[Dict[str, Union[str, int, arrow.Arrow]]]

    final_exam_time_list.sort(key=lambda course: course['examBegin'])

    for course in final_exam_time_list:
        course['examBegin'] = course.get('examBegin').for_json()
        course['examEnd'] = course.get('examEnd').for_json()

    return jsonify(final_exam_time_list)
