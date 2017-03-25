# -*- coding:utf-8 -*-
import types

import bs4
from requests import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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

        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55' \
                                '.0.2883.87 Safari/537.36'

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
        if not self.session:
            self.session = _IdasSession(username=username, password=password)

    def getTotalGpa(self):
        get_all_grade = self.session.post(
            'http://eams.uestc.edu.cn/eams/teach/grade/course/person!historyCourseGrade.action',
            params={'projectType': 'MAJOR'})

        grade_sum_table = bs4.BeautifulSoup(get_all_grade.content, 'html.parser').find_all(name='table')[0]

        return grade_sum_table.find_all(name='tr')[-2].find_all(name='th')[-1].text.strip()
