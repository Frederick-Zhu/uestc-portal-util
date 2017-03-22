# -*- coding:utf-8 -*-
import portal_tools
from portal_tools import _course_table
from portal_tools import _grade


def grade(**kwargs):
    if kwargs.has_key('session'):
        session = kwargs['session']
    elif kwargs.has_key('username') and kwargs.has_key('password'):
        session = portal_tools.IdasSession(kwargs['username'], kwargs['password'])
    else:
        raise ValueError

    course_table_list = _course_table.getCourseTable(semester_id=123, session=session)

    grade_list = _grade.getGrade(semester_id=123, session=session)

    grade_dict = dict()
    for grade_info in grade_list:
        grade_dict[grade_info['sn']] = grade_info

    for course in course_table_list:
        if course['sn'] in grade_dict.keys():
            print course['name'], grade_dict[course['sn']]
