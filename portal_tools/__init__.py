# -*- coding:utf-8 -*-

import bs4
import requests

from portal_tools import errors


class IdasSession(requests.Session):
    def __init__(self, username, password):
        super(IdasSession, self).__init__()

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
