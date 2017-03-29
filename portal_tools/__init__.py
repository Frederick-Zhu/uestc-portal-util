# -*- coding:utf-8 -*-
import datetime
import re

import bs4
import types
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Optional, Union, Dict, List

from portal_tools import errors


class _IdasSession(Session):
    _timeout = 10
    _max_retries = 10

    def __init__(self, username, password):
        super(_IdasSession, self).__init__()

        _retry = Retry(_IdasSession._max_retries, status_forcelist=[500, ], backoff_factor=0.2)
        _http_adapter = HTTPAdapter(max_retries=_retry)

        self.mount('http://', _http_adapter)
        self.mount('https://', _http_adapter)

        # 判断是否需要输入验证码
        get_need_captcha = self.get('http://idas.uestc.edu.cn/authserver/needCaptcha.html',
                                    params={'username': str(username)})

        # 如果需要则报错
        if 'true' in get_need_captcha.content:
            raise errors.IdasNeedCaptcha

        # 获得登陆表格
        get_login_form = self.get(
            'http://idas.uestc.edu.cn/authserver/login?service=http%3A%2F%2Fportal.uestc.edu.cn%2F')

        # 解析登陆表格内容
        login_form = bs4.BeautifulSoup(get_login_form.content, 'html.parser').find(name='form', id='casLoginForm')

        # 登陆表格字典
        login_form_data = dict()

        # 将登陆表格中所有input加入登录表格字典中
        for item in login_form.find_all(name='input'):
            login_form_data[item.get('name')] = item.get('value')

        # 写入用户名和密码
        login_form_data[u'username'] = unicode(username)
        login_form_data[u'password'] = unicode(password)

        # 发送登陆表格
        post_login_from = self.post(
            'http://idas.uestc.edu.cn/authserver/login?service=http%3A%2F%2Fportal.uestc.edu.cn%2F',
            data=login_form_data)

        # 通过重定向网址判断是否登陆成功
        if post_login_from.url != 'http://portal.uestc.edu.cn/':
            raise errors.IdasUsrPwdError

    def __del__(self):
        self.get('http://idas.uestc.edu.cn/authserver/logout')

    def request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                json=None):

        if isinstance(headers, types.NoneType):
            headers = dict()

        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/5' \
                                '5.0.2883.87 Safari/537.36'

        return super(_IdasSession, self).request(method=method, url=url, params=params, data=data, headers=headers,
                                                 cookies=cookies, files=files, auth=auth,
                                                 timeout=timeout or _IdasSession._timeout,
                                                 allow_redirects=allow_redirects, proxies=proxies, hooks=hooks,
                                                 stream=stream, verify=verify, cert=cert, json=json)

    def get(self, url, **kwargs):
        ret = super(_IdasSession, self).get(url, **kwargs)
        ret.raise_for_status()
        return ret

    def post(self, url, data=None, json=None, **kwargs):
        ret = super(_IdasSession, self).post(url=url, data=data, json=json, **kwargs)
        ret.raise_for_status()
        return ret


class PortalUtil(object):
    session = None

    def __init__(self, username, password):
        # type: (str, str) -> None
        if not self.session:
            self.session = _IdasSession(username=username, password=password)

    def getClassId(self):
        # type: () -> str
        """Get user's class id."""
        get_info = self.session.get('http://eams.uestc.edu.cn/eams/stdDetail.action')

        info_table = bs4.BeautifulSoup(get_info.content, 'html.parser').find_all(name='table')[
            0]  # type: bs4.BeautifulSoup
        class_id = info_table.find_all(name='tr')[12].find_all(name='td')[1].text.strip()

        return class_id

    def getMajorId(self):
        # type: () -> str
        """Get user's major id."""
        return self.getClassId()[:-2]

    def getTotalGpa(self):
        # type: () -> str
        get_all_grade = self.session.post(
            'http://eams.uestc.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action',
            params={'projectType': 'MAJOR'})

        grade_sum_table = bs4.BeautifulSoup(get_all_grade.content, 'html.parser').find_all(name='table')[0]

        return grade_sum_table.find_all(name='tr')[-2].find_all(name='th')[-1].text.strip()

    def getCourseTable(self, semester_id):
        # type: (int) -> List[Dict[str, str]]
        _idsPattern = ur'if\(jQuery\("#courseTableType"\)\.val\(\)=="std"\){\s*bg\.form\.addInput\(form,"ids","(\d+)' \
                      ur'"\);\s*}else{\s*bg\.form\.addInput\(form,"ids","(\d+)"\);\s*}'

        get_course_table_for_std = self.session.get('http://eams.uestc.edu.cn/eams/courseTableForStd.action')

        ids = re.compile(pattern=_idsPattern).search(string=get_course_table_for_std.content).groups()

        post_course_table_for_std = self.session.post(
            'http://eams.uestc.edu.cn/eams/courseTableForStd!courseTable.action',
            data={'ignoreHead': 1,
                  'setting.kind': 'std',
                  'startWeek': 1,
                  'semester.id': semester_id, 'ids': ids[0]})

        course_table_for_std_table = \
            bs4.BeautifulSoup(post_course_table_for_std.content, 'html.parser').find_all(name='table')[1]

        course_table_list = list()

        for tr in course_table_for_std_table.find(name='tbody').find_all(name='tr'):
            course_info = dict()  # type: Dict[str, str]
            td = tr.find_all(name='td')

            course_info['code'] = td[1].text.strip()
            course_info['name'] = td[2].text.strip()
            course_info['credit'] = td[3].text.strip()
            course_info['sn'] = td[4].text.strip()
            course_info['teacher'] = td[5].text.strip()

            course_table_list.append(course_info)

        return course_table_list

    def getAllGrade(self):
        # type: () -> list
        get_all_grade = self.session.post(
            'http://eams.uestc.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action',
            params={'projectType': 'MAJOR'})

        all_grade_table = bs4.BeautifulSoup(get_all_grade.content, 'html.parser').find_all(name='table')[1]

        all_grade_list = list()

        for tr in all_grade_table.find(name='tbody').find_all(name='tr'):
            grade_info = dict()
            td = tr.find_all(name='td')

            grade_info['year'] = td[0].text.strip()
            grade_info['code'] = td[1].text.strip()
            grade_info['sn'] = td[2].text.strip()
            grade_info['name'] = td[3].text.strip()
            grade_info['type'] = td[4].text.strip()
            grade_info['credit'] = td[5].text.strip()
            grade_info['score'] = td[6].text.strip()
            grade_info['total'] = td[7].text.strip()

            all_grade_list.append(grade_info)

        return all_grade_list

    def getGrade(self, semester_id):
        # type: (int) -> list
        get_grade = self.session.get('http://eams.uestc.edu.cn/eams/teach/grade/course/person!search.action',
                                     params={'semesterId': semester_id,
                                             'projectType': ''})

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

    def grade(self, semester_id=123):
        # type: (int) -> None
        course_table_list = self.getCourseTable(semester_id=semester_id)

        grade_list = self.getGrade(semester_id=semester_id)  # type: list

        grade_dict = dict()
        for grade_info in grade_list:
            grade_dict[grade_info['sn']] = grade_info

        for course in course_table_list:
            if course['sn'] in grade_dict.keys():
                print course['name'], grade_dict[course['sn']]

    def getCourseFinalExamTime(self, semester_id, course_id):
        # type: (int, str) -> Optional[Dict[str, Union[str, int, datetime.datetime]]]
        finalExamTimePattern = ur'第(\d+)周\s星期[一二三四五六日]\((\d{4})(\d{2})(\d{2})\)\s(\d{2}):(\d{2})-(\d{2}):(\d' \
                               ur'{2})'
        post_public_search_data = {'lesson.project.id': '1',
                                   'lesson.no': str(course_id),
                                   'lesson.course.name': '',
                                   'lesson.teachDepart.id': '...',
                                   'limitGroup.depart.id': '...',
                                   'teacher.name': '',
                                   'fake.teacher.null': '...',
                                   'limitGroup.grade': '',
                                   'fake.weeks': '',
                                   'startWeekSchedule': '',
                                   'endWeekSchedule': '',
                                   'fake.time.weekday': '...',
                                   'fake.time.unit': '',
                                   'lesson.campus.id': '...',
                                   'lesson.courseType.id': '...',
                                   'examType.id': '1',
                                   'lesson.semester.id': 'undefined'}

        self.session.post('http://eams.uestc.edu.cn/eams/publicSearch!index.action',
                          data={'semester.id': semester_id})

        post_public_search = self.session.post('http://eams.uestc.edu.cn/eams/publicSearch!search.action',
                                               data=post_public_search_data)

        post_public_search_soup = bs4.BeautifulSoup(post_public_search.content, 'lxml').find(name='tbody').find(
            name='tr').find_all(name='td')  # type: bs4.BeautifulSoup

        final_exam_time_re_search = re.compile(pattern=finalExamTimePattern).search(
            string=post_public_search_soup[10].text)

        ret = dict()

        if final_exam_time_re_search is not None:
            course_name = post_public_search_soup[2].text  # type: str
            week = int(final_exam_time_re_search.group(1))  # type: int
            year = int(final_exam_time_re_search.group(2))  # type: int
            month = int(final_exam_time_re_search.group(3))  # type: int
            day = int(final_exam_time_re_search.group(4))  # type: int
            begin_hour = int(final_exam_time_re_search.group(5))  # type: int
            begin_minute = int(final_exam_time_re_search.group(6))  # type: int
            end_hour = int(final_exam_time_re_search.group(7))  # type: int
            end_minute = int(final_exam_time_re_search.group(8))  # type: int
            ret = {'courseName': course_name,
                   'examWeek': week,
                   'examBegin': datetime.datetime(year, month, day, begin_hour, begin_minute),
                   'examEnd': datetime.datetime(year, month, day, end_hour, end_minute)}
        return ret

    def getFinalExamTime(self, semester_id):
        # type: (int) -> List[Dict[str, Union[str, int, datetime.datetime]]]
        course_list = self.getCourseTable(semester_id=semester_id)  # type: List[Dict[str, str]]

        course_sn_list = list()  # type: List[str]
        for course in course_list:
            course_sn_list.append(course.get('sn'))

        final_exam_time_list = list()  # type: List[Dict[str, Union[str, int, datetime.datetime]]]

        for course_sn in course_sn_list:
            final_exam_time = self.getCourseFinalExamTime(semester_id=semester_id, course_id=course_sn)
            if final_exam_time:
                final_exam_time_list.append(final_exam_time)

        final_exam_time_list.sort(key=lambda course: course['examBegin'])

        return final_exam_time_list
