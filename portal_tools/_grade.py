# -*- coding:utf-8 -*-
import bs4

import portal_tools


def getGrade(username, password, semester_id=123):
    session = portal_tools.IdasSession(username, password)

    get_grade = session.get('http://eams.uestc.edu.cn/eams/teach/grade/course/person!search.action',
                            params={'semesterId': semester_id, 'projectType': ''})

    grade_form = bs4.BeautifulSoup(get_grade.content, 'html.parser').find(name='table')

    grade_list = list()

    for tr in grade_form.find(name='tbody').find_all(name='tr'):
        grade_info = dict()
        td = tr.find_all(name='td')

        grade_info['year'] = td[0].text.strip()
        grade_info['code'] = td[1].text.strip()
        grade_info['sn'] = td[2].text.strip()
        grade_info['name'] = td[3].text.strip()
        grade_info['type'] = td[4].text.strip()
        grade_info['credit'] = td[5].text.strip()
        grade_info['score'] = td[6].text.strip()
        grade_info['resit'] = td[7].text.strip()
        grade_info['total'] = td[8].text.strip()
        grade_info['gpa'] = td[9].text.strip()

        grade_list.append(grade_info)

    return grade_list
