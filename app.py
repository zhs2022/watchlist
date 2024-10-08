from flask import Flask, url_for, render_template
from markupsafe import escape
name = 'ZHS'
movies = [
    {'title': 'My Neighbor Totoro', 'year': '1988'},
    {'title': 'Dead Poets Society', 'year': '1989'},
    {'title': 'A Perfect World', 'year': '1993'},
    {'title': 'Leon', 'year': '1994'},
    {'title': 'Mahjong', 'year': '1996'},
    {'title': 'Swallowtail Butterfly', 'year': '1996'},
    {'title': 'King of Comedy', 'year': '1999'},
    {'title': 'Devils on the Doorstep', 'year': '1999'},
    {'title': 'WALL-E', 'year': '2008'},
    {'title': 'The Pork of Music', 'year': '2012'},
]

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html', name=name, movies=movies)

@app.route('/hello')
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