import os
import uuid

from flask import (
    render_template,
    request,
    redirect,
    session,
    url_for,
    Blueprint,
    abort,
    send_from_directory,
    current_app)
from werkzeug.datastructures import FileStorage

from models.board import Board
from models.reply import Reply
from models.topic import Topic
from models.user import User
# from routes import current_user, cache
from routes import current_user, cache

import json

from utils import log

main = Blueprint('index', __name__)

"""
用户在这里可以
    访问首页
    注册
    登录

用户登录后, 会写入 session, 并且定向到 /profile
"""

# import gevent
import time



@main.route("/")
def index():

    # t = threading.Thread()
    # t.start()
    # gevent.spawn()
    return render_template("index1.html")


@main.route("/register", methods=['POST'])
def register():
    form = request.form.to_dict()
    # 用类函数来判断
    u = User.register(form)
    return redirect(url_for('.index'))


@main.route("/login", methods=['POST'])
def login():
    form = request.form
    u = User.validate_login(form)
    if u is None:
        return redirect(url_for('.index'))
    else:
        # session 中写入 user_id
        session_id = str(uuid.uuid4())
        key = 'session_id_{}'.format(session_id)
        log('index login key <{}> user_id <{}>'.format(key, u.id))
        cache.set(key, u.id)

        redirect_to_index = redirect(url_for('topic.index'))
        response = current_app.make_response(redirect_to_index)
        response.set_cookie('session_id', value=session_id)
        # 转到 topic.index 页面
        return response
        # session['user_id'] = u.id
        # return redirect(url_for('topic.index'))


def created_topic(user_id):
    # O(n)
    ts = Topic.all(user_id=user_id)
    return ts
    #
    # k = 'created_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     return ts
    # else:
    #     ts = Topic.all(user_id=user_id)
    #     v = json.dumps([t.json() for t in ts])
    #     cache.set(k, v)
    #     return ts


def replied_topic(user_id):
    # O(k)+O(m*n)
    rs = Reply.all(user_id=user_id)
    ts = []
    for r in rs:
        t = Topic.one(id=r.topic_id)
        ts.append(t)
    return ts
    #
    #     sql = """
    # select * from topic
    # join reply on reply.topic_id=topic.id
    # where reply.user_id=1
    # """
    # k = 'replied_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     return ts
    # else:
    #     rs = Reply.all(user_id=user_id)
    #     ts = []
    #     for r in rs:
    #         t = Topic.one(id=r.topic_id)
    #         ts.append(t)
    #
    #     v = json.dumps([t.json() for t in ts])
    #     cache.set(k, v)

        # return ts
    # ts = Topic.query\
    #     .join(Reply, Topic.id==Reply.topic_id)\
    #     .filter(Reply.user_id==user_id)\
    #     .all()
    # return ts


# @main.route('/profile')
# def profile():
#     print('running profile route')
#     u = current_user()
#     if u is None:
#         return redirect(url_for('.index'))
#     else:
#         created = created_topic(u.id)
#         replied = replied_topic(u.id)
#         return render_template(
#             'profile.html',
#             user=u,
#             created=created,
#             replied=replied
#         )


@main.route('/profile')
def profile():
    u = current_user()
    if u is None:
        return redirect(url_for('.index'))
    else:
        topics = created_topic(u.id)
        b = sorted(topics, key=lambda t: t.created_time, reverse=True)
        replies = replied_topic(u.id)
        replies_topics = sorted(replies, key=lambda t: t.created_time, reverse=True)
        return render_template('profile1.html', u=u, topics=b, ms=replies_topics)


@main.route('/setting_view')
def setting_view():
    board = int(request.args.get('board_id', -1))
    u = current_user()
    if u is None:
        return redirect(url_for('.index'))
    else:
        return render_template(
            'shezhi.html',
            user=u,
            bid=board
        )


@main.route('/setting_username', methods=['POST'])
def setting_username():
    form = request.form.to_dict()
    u = current_user()
    user_name = form['name']
    qianming = form['signature']
    User.update(u.id, username=user_name, qianming=qianming)
    return redirect(url_for('index.setting_view'))


@main.route('/setting_password', methods=['POST'])
def setting_password():
    form = request.form.to_dict()
    u = current_user()
    old_password = User.salted_password(form['old_pass'])
    if old_password != u.password:
        return redirect(url_for('index.setting_view'))
    else:
        new_password = User.salted_password(form['new_pass'])
        User.update(u.id, password=new_password)
        return redirect(url_for('index.index'))






@main.route('/user/<int:id>')
def user_detail(id):
    u = User.one(id=id)
    if u is None:
        abort(404)
    else:
        return render_template('profile.html', user=u)


@main.route('/image/add', methods=['POST'])
def avatar_add():
    file: FileStorage = request.files['avatar']
    # file = request.files['avatar']
    # filename = file.filename
    # ../../root/.ssh/authorized_keys
    # images/../../root/.ssh/authorized_keys
    # filename = secure_filename(file.filename)
    suffix = file.filename.split('.')[-1]
    if suffix not in ['gif', 'jpg', 'jpeg']:
        abort(400)
        log('不接受的后缀, {}'.format(suffix))
    else:
        filename = '{}.{}'.format(str(uuid.uuid4()), suffix)
        path = os.path.join('images', filename)
        file.save(path)

        u = current_user()
        User.update(u.id, image='/images/{}'.format(filename))

        return redirect(url_for('.profile'))


@main.route('/images/<filename>')
def image(filename):
    # 不要直接拼接路由，不安全，比如
    # http://localhost:3000/images/..%5Capp.py
    # path = os.path.join('images', filename)
    # print('images path', path)
    # return open(path, 'rb').read()
    # if filename in os.listdir('images'):
    #     return
    return send_from_directory('images', filename)
