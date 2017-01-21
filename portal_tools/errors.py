# -*- coding:utf-8 -*-

class IdasNeedCaptcha(Exception):
    def __str__(self):
        return repr('Idas need captcha!')


class IdasUsrPwdError(Exception):
    def __str__(self):
        return repr('Username and Password are wrong!')
