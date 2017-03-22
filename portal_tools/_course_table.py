# -*- coding:utf-8 -*-
import re

import bs4

import portal_tools

_idsPattern = ur'if\(jQuery\("#courseTableType"\)\.val\(\)=="std"\){\s*bg\.form\.addInput\(form,"ids","(\d+)"\);\s*}e' \
              ur'lse{\s*bg\.form\.addInput\(form,"ids","(\d+)"\);\s*}'


def getCourseTable(semester_id, **kwargs):
    if kwargs.has_key('session'):
        session = kwargs['session']
    elif kwargs.has_key('username') and kwargs.has_key('password'):
        session = portal_tools.IdasSession(kwargs['username'], kwargs['password'])
    else:
        raise ValueError

    get_course_table_for_std = session.get('http://eams.uestc.edu.cn/eams/courseTableForStd.action')

    ids = re.compile(pattern=_idsPattern).search(string=get_course_table_for_std.content).groups()

    post_course_table_for_std = session.post('http://eams.uestc.edu.cn/eams/courseTableForStd!courseTable.action',
                                             data={'ignoreHead': 1, 'setting.kind': 'std', 'startWeek': 1,
                                                   'semester.id': semester_id, 'ids': ids[0]})

    course_table_for_std_table = \
        bs4.BeautifulSoup(post_course_table_for_std.content, 'html.parser').find_all(name='table')[1]

    course_table_list = list()

    for tr in course_table_for_std_table.find(name='tbody').find_all(name='tr'):
        course_info = dict()
        td = tr.find_all(name='td')

        course_info['code'] = td[1].text.strip()
        course_info['name'] = td[2].text.strip()
        course_info['credit'] = td[3].text.strip()
        course_info['sn'] = td[4].text.strip()
        course_info['teacher'] = td[5].text.strip()

        course_table_list.append(course_info)

    return course_table_list
