from flask import Flask, url_for
from markupsafe import escape
app = Flask(__name__)

@app.route('/')
def hello():
    return 'hello'

@app.route('/user/<name>')
#视图函数名可以任意修改
#使用flask.url_for()函数可以根据视图函数名返回对应的URL
def user_page(name):
    return f'{escape(name)}, welcome'

@app.route('/test')
def test_url_for():
    print(url_for('hello'))
    print(url_for('user_page', name = 'zhs'))
    print(url_for('user_page', name = '233'))
    print(url_for('test_url_for'))
    print(url_for('test_url_for', num=2))
    return 'Test page'

#if __name__ == '__main__':
    #app.run(debug=True)