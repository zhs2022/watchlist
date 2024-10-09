import os
import sys
import click
#request对象为请求出发后的产生的对象，其中包含了请求信息
from flask import Flask, url_for, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user#实现用户认证
from markupsafe import escape
from werkzeug.security import generate_password_hash, check_password_hash
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
login_manager = LoginManager(app) #实例化扩展类
login_manager.login_view = 'login' #若未登录用户访问了使用@login_required保护的功能，则回重定向到登录页面
@login_manager.user_loader
# 设置这个函数的目的是
# 当程序运行后，如果用户已登录，current_user 变量的值会是当前用户的用户模型类记录
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

#通过db创建数据库模型（每个单独的模型对应一张数据库表）
class User(db.Model, UserMixin): # 表名为user，继承UserMixin会让 User 类拥有几个用于判断认证状态的属性和方法
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128)) #密码散列值

    def set_password(self, password): #接收用户输入的密码，将其转换为散列值
        #类属性在实例方法中也可使用self来引用
        self.password_hash = generate_password_hash(password)
    def validate_password(self, password): #验证用户的密码是否与数据库中的散列值
        return check_password_hash(self.password_hash, password)
    
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

#创建管理员账户
@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password) #设置密码
        db.session.add(user)
    db.session.commit() #提交数据库会话
    click.echo('Done.')

#模板上下文处理函数，使用字典来储存多个模板内都需要的变量
#设置该函数后，模板的视图函数中就不需要再指定对应的变量
#注意base template中的变量一定要使用模板上下文处理函数预先保存
@app.context_processor
def inject_user():
    user = User.query.first() #读取将User数据库表中的第一行记录对象
    # 此处应令变量user指向对象user，而非传入对象user的name
    # 因为user可能是个空对象，python对于空对象调用属性会抛出type error，但JinJa2不会，只会返回空字符串
    # 因此无需担心JinJa2中传入空对象的问题
    return dict(user=user)

#主页
#默认情况下，页面只能处理get请求，可以使用methods关键字修改
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        if not current_user.is_authenticated: #对于未登录的用户，其is_authenticated属性为False
            return redirect(url_for('index'))  # 重定向到主页
        #获取表单数据
        title = request.form.get('title').strip()#传入参数是表单对应字段的name
        year = request.form.get('year').strip()
        #验证数据
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.') #显示错误提示
            return redirect(url_for('index')) #重定向回到主页
        #数据合法，存入数据库
        movie = Movie(title=title, year=year) #创建记录
        db.session.add(movie)
        db.session.commit()
        flash('Item created.') #显示成功创建的提示
        # 此处必须使用重定向，而不能直接渲染html页面
        # 后者会导致该html页面是由POST请求加载的，从而在刷新页面时，仍然发送了POST请求，导致表单重复提交
        return redirect(url_for('index')) 
    movies = Movie.query.all()

    return render_template('index.html', movies=movies)

#用户登录页面
@app.route('/login', methods=['GET', "POST"])
def login():
    if request.method == "POST":#接收表单传回的信息
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        user = User.query.first()
        #增加对数据库是否为空的判断
        if not user:
            flash('Error, the User Table is Empty.')
            return redirect(url_for('index')) #重定向到主页
        #验证输入的用户名和密码和数据库中保存的是否一致
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('index')) #重定向到主页
        
        #验证失败，重定向到登录页面
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    
    return render_template('login.html') #对于get请求，直接返回html页面

#用户登出
@app.route('/logout')
@login_required #用于视图保护，未登录用户不能执行此操作
def logout():
    logout_user() #登出用户
    flash('Goodbye.')
    return redirect(url_for('index')) #重定向回首页

#设置页面
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        #新名称不合法
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings')) #重定向
        # 新名称合法
        # 对于已登录的用户，current_user指向当前登录用户的数据库记录对象
        current_user.name = name #等价于user = User.query.first(); user.name = name
        db.session.commit()
        flash('Setting updated.')
        return redirect(url_for('index'))
    return render_template('settings.html')
    
#编辑电影条目
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required #用于视图保护，未登录用户不能执行此操作
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
@login_required
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