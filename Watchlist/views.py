
from flask import request, redirect, render_template, url_for, flash
from flask_login import current_user, login_user, login_required, logout_user
from Watchlist import app, db #注意这里可能会导致循环依赖？
from Watchlist.models import User, Movie

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