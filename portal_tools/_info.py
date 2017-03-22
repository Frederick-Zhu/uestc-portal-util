# -*- coding:utf-8 -*-
import bs4

import portal_tools


def getClassId(**kwargs):
    if kwargs.has_key('session'):
        session = kwargs['session']
    elif kwargs.has_key('username') and kwargs.has_key('password'):
        session = portal_tools.IdasSession(kwargs['username'], kwargs['password'])
    else:
        raise ValueError

    get_info = session.get('http://eams.uestc.edu.cn/eams/stdDetail.action')

    info_table = bs4.BeautifulSoup(get_info.content, 'html.parser').find_all(name='table')[0]
    class_id = info_table.find_all(name='tr')[12].find_all(name='td')[1].text.strip()

    return class_id
