#数据库模型
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from Watchlist import db # 注意这里可能会导致循环依赖？

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