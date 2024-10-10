from flask import render_template
from Watchlist import app

#错误页面
@app.errorhandler(404)
def page_not_found(e):
    #user = User.query.first()
    return render_template('errors/404.html'), 404