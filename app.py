import os
import sys
import click
from flask import Flask, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///' #windows 系统使用///
else:
    prefix = 'sqlite:////' #否则使用////


app = Flask(__name__)

#先加载配置，再实例化
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # 关闭对模型修改的监控
db = SQLAlchemy(app)

class User(db.Model): # 表名为user
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


@app.cli.command() #将以下的函数注册为flask命令，功能为初始化数据库
@click.option('--drop', is_flag=True, help='Create after drop.') 
def initdb(drop):
    #"Initialize the database"
    if drop:
        db.drop_all()
        click.echo('Successfully deleted the current database.')
    db.create_all()
    click.echo('Initialized database.')

@app.cli.command()#将以下的函数注册为flask命令，功能为添加虚拟数据
def forge():
    # Generate fake data
    db.create_all()
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
    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('Done.')

#模板上下文处理函数，使用字典来储存多个模板内都需要的变量
#设置该函数后，模板的视图函数中就不需要再指定对应的变量
#注意base template中的变量一定要使用模板上下文处理函数预先保存
@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user.name)

#主页
@app.route('/')
def index():
    #user = User.query.first()
    movies = Movie.query.all()

    return render_template('index.html', movies=movies)

#错误页面
@app.errorhandler(404)
def page_not_found(e):
    #user = User.query.first()
    return render_template('404.html'), 404



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