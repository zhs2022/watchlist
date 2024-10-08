import os
import sys
import click
#request对象为请求出发后的产生的对象，其中包含了请求信息
from flask import Flask, url_for, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from markupsafe import escape

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///' #windows 系统使用///
else:
    prefix = 'sqlite:////' #否则使用////


app = Flask(__name__)
#定义签名所需的密钥，加密会话数据，以确保flash函数传递的闪现消息的安全
app.config['SECRET_KEY'] = 'dev' 
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
#默认情况下，页面只能处理get请求，可以使用methods关键字修改
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        #获取表单数据
        title = request.form.get('title').strip()#传入参数是表单对应字段的name
        year = request.form.get('year').strip()
        #验证数据
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input') #显示错误提示
            return redirect(url_for('index')) #重定向回到主页
        #数据合法，存入数据库
        movie = Movie(title=title, year=year) #创建记录
        db.session.add(movie)
        db.session.commit()
        flash('Item created') #显示成功创建的提示
        return redirect(url_for('index'))

    movies = Movie.query.all()

    return render_template('index.html', movies=movies)

#编辑电影条目
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == "POST":
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面
        movie.title = title  # 更新标题
        movie.year = year  # 更新年份
        db.session.commit()  # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index'))  # 重定向回主页
    return render_template('edit.html', movie=movie)

# 删除电影条目
@app.route('/movie/delete/<int:movie_id>', methods=['POST'])  # 限定只接受 POST 请求
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)  # 获取电影记录
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index'))  # 重定向回主页

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