# -*- coding:utf-8 -*-

from server import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=1207, debug=True, use_reloader=True, threaded=True)
