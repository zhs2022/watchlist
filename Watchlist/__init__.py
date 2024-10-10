import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///' #windows 系统使用///
else:
    prefix = 'sqlite:////' #否则使用////

app = Flask(__name__)

# 定义签名所需的密钥，加密会话数据，以确保flash函数传递的闪现消息的安全
app.config['SECRET_KEY'] = 'dev'
# os.path.dirname()将返回传入路径对应的文件或文件夹的上一级
# 把 app.root_path 添加到 os.path.dirname() 中
# 以便把文件定位到项目根目录
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

@login_manager.user_loader
# 设置这个函数的目的是
# 当程序运行后，如果用户已登录，current_user 变量的值会是当前用户的用户模型类记录
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    from Watchlist.models import User
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象

login_manager.login_view = 'login' #若未登录用户访问了使用@login_required保护的功能，则回重定向到登录页面
#模板上下文处理函数，使用字典来储存多个模板内都需要的变量
#设置该函数后，模板的视图函数中就不需要再指定对应的变量
#注意base template中的变量一定要使用模板上下文处理函数预先保存

@app.context_processor
def inject_user():
    from .models import User
    user = User.query.first() #读取将User数据库表中的第一行记录对象
    # 此处应令变量user指向对象user，而非传入对象user的name
    # 因为user可能是个空对象，python对于空对象调用属性会抛出type error，但JinJa2不会，只会返回空字符串
    # 因此无需担心JinJa2中传入空对象的问题
    return dict(user=user)

from Watchlist import views, errors, commands