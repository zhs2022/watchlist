import unittest

from Watchlist import app, db
from Watchlist.models import Movie, User
from Watchlist.commands import forge, initdb

class WatchlistTestCase(unittest.TestCase):
    def setUp(self): #该方法在每个测试方法执行之前被调用
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI='sqlite:///memory:' #此处使用 SQLite 内存型数据库，不会干扰开发时使用的数据库文件
        )
        self.app_context = app.app_context()  # 创建应用上下文
        self.app_context.push()  # 激活应用上下文
        #创建数据库和表
        db.create_all()
        #创建测试数据，一个用户记录对象，一个电影条目
        user = User(name='Test', username='test')
        user.set_password('123')

        movie = Movie(title='Test Movie Title', year='2019')
        db.session.add_all([user, movie])
        db.session.commit()

        self.client = app.test_client() #创建测试客户端，可以通过调用它的get和post方法来模拟客户端的对应请求
        self.runner = app.test_cli_runner() #创建测试命令运行器

    def tearDown(self): #该方法在每个测试方法执行之后被调用
        db.session.remove() #清除数据库会话
        db.drop_all() #删除数据库表
        self.app_context.pop()  # 弹出应用上下文
    
    #测试程序实例是否存在
    def test_app_exist(self):
        self.assertIsNotNone(app)
    
    #测试程序是否处于测试模式
    def test_app_is_testing(self):
        self.assertTrue(app.config['TESTING'])

    # 测试404页面
    def test_404_page(self):
        response = self.client.get('/nothing')#response指向一个flask.Response 对象，包含了响应的所有信息，如状态码、响应数据、头部等
        data = response.get_data(as_text=True)
        self.assertIn('Page Not Found - 404', data)
        self.assertIn('Go Back', data)
        self.assertEqual(response.status_code, 404)  # 判断响应状态码
    
    # 测试主页
    def test_index_page(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertIn('Test\'s Watchlist', data)
        self.assertIn('Test Movie Title', data)
        self.assertEqual(response.status_code, 200)

    
    # 辅助方法，用于登入用户
    def login(self):
        self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
    
    # 测试创建条目
    def test_create_item(self):
        self.login() #先登录

        #客户端发送一个合法的表单数据
        response = self.client.post('/', data=dict(
            title='New Movie',
            year = '2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item created.', data)
        self.assertIn('New Movie', data)

        #客户端发送不合法的表单数据，电影标题为空
        response = self.client.post('/', data=dict(
            title='',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

        #客户端发送不合法的表单数据，电影年份为空
        response = self.client.post('/', data=dict(
            title='New Movie',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item created.', data)
        self.assertIn('Invalid input.', data)

    #测试更新条目
    def test_update_item(self):
        self.login()

        #测试更新页面
        response = self.client.get('/movie/edit/1')
        data = response.get_data(as_text=True)
        self.assertIn('Edit item', data)
        self.assertIn('Cancel', data)
        self.assertIn('Test Movie Title', data)
        self.assertIn('2019', data)

        #测试更新操作，发送合法的表单数据
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item updated.', data)
        self.assertIn('New Movie Edited', data)

        #测试更新操作，电影标题为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='',
            year='2019'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertIn('Invalid input.', data)

        #测试更新操作，电影年份为空
        response = self.client.post('/movie/edit/1', data=dict(
            title='New Movie Edited Again',
            year=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Item updated.', data)
        self.assertNotIn('New Movie Edited Again', data)
        self.assertIn('Invalid input.', data)

    # 测试删除条目操作
    def test_delete_item(self):
        self.login()

        response = self.client.post('/movie/delete/1', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Item deleted.', data)
        self.assertNotIn('Test Movie Title', data)

    # 测试登录保护，即对于未登录的用户，主页中不应该出现某些功能按钮
    def test_login_protect(self):
        response = self.client.get('/')
        data = response.get_data(as_text=True)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('<form method="post">', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)

    # 测试登录
    def test_login(self):
        response = self.client.post('/login', data=dict(
            username='test',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Login success.', data)
        self.assertIn('Logout', data)
        self.assertIn('Settings', data)
        self.assertIn('Delete', data)
        self.assertIn('Edit', data)
        self.assertIn('<form method="post">', data)

        # 测试使用错误的密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password='456'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)
    
        # 测试使用错误的用户名登录
        response = self.client.post('/login', data=dict(
            username='wrong',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid username or password.', data)

        # 测试使用空用户名登录
        response = self.client.post('/login', data=dict(
            username='',
            password='123'
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

        # 测试使用空密码登录
        response = self.client.post('/login', data=dict(
            username='test',
            password=''
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Login success.', data)
        self.assertIn('Invalid input.', data)

    # 测试登出，用户登出后，页面被重定向到主页
    def test_logout(self):
        self.login()

        response = self.client.get('/logout', follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Goodbye.', data)
        self.assertNotIn('Logout', data)
        self.assertNotIn('Settings', data)
        self.assertNotIn('Delete', data)
        self.assertNotIn('Edit', data)
        self.assertNotIn('<form method="post">', data)
    
    # 测试设置
    def test_settings(self):
        self.login()

        # 测试设置页面
        response = self.client.get('/settings')
        data = response.get_data(as_text=True)
        self.assertIn('Your Name', data)
        self.assertIn('Settings', data)

        # 测试更新设置
        response = self.client.post('/settings', data=dict(
            name="ZHS"
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertIn('Setting updated.', data)
        self.assertIn('ZHS', data)

        # 测试更新设置，传入空名称
        response = self.client.post('/settings', data=dict(
            name=""
        ), follow_redirects=True)
        data = response.get_data(as_text=True)
        self.assertNotIn('Setting updated.', data)
        self.assertIn('Invalid input.', data)
    
    #测试自定义的命令行命令
    # 这部分的主要逻辑在于执行命令后，数据库是否按照预期变化
    # 测试增加虚拟数据
    def test_forge_command(self):
        result = self.runner.invoke(forge) #self.runner指向一个命令运行器对象，对其调用 invoke() 方法可以执行命令
        self.assertIn('Done.', result.output)
        self.assertNotEqual(Movie.query.count(), 0)
    
    # 测试初始化数据库
    def test_initdb_command(self):
        result = self.runner.invoke(initdb)
        self.assertIn('Initialized database.', result.output)

    # 测试生成管理员账户
    def test_admin_command(self):
        db.drop_all()
        db.create_all()
        #invoke() 方法可以传入传入命令函数对象，或是使用 args 关键字直接给出命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'zhs', '--password', '123'])
        self.assertIn('Creating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'zhs')
        self.assertTrue(User.query.first().validate_password('123'))

    # 测试更新管理员账户
    def test_admin_command_update(self):
        # 使用 args 参数给出完整的命令参数列表
        result = self.runner.invoke(args=['admin', '--username', 'peter', '--password', '456'])
        self.assertIn('Updating user...', result.output)
        self.assertIn('Done.', result.output)
        self.assertEqual(User.query.count(), 1)
        self.assertEqual(User.query.first().username, 'peter')
        self.assertTrue(User.query.first().validate_password('456'))
    
if __name__ == '__main__':
    unittest.main()

