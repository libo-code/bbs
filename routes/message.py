from flask import (
    render_template,
    request,
    redirect,
    url_for,
    Blueprint,
)

from routes import *
import config
from models.message import Messages, send_mail

main = Blueprint('message', __name__)

a = {}
@main.route("/add", methods=["POST"])
def add():
    form = request.form.to_dict()
    u = current_user()
    receiver_id = int(form['receiver_id'])
    # 发邮件
    Messages.send(
        title=form['title'],
        content=form['content'],
        sender_id=u.id,
        receiver_id=receiver_id
    )

    return redirect(url_for('.index'))


@main.route("/reset/send", methods=["POST"])
def reset_send():
    form = request.form.to_dict()
    username = form['username']
    u = User.one(username=username)
    token = str(uuid.uuid4())
    key = 'xiugai_{}'.format(token)
    cache.set(key, u.id)
    subject = '点击链接'
    author = config.admin_mail
    to = u.email
    content = 'http://129.28.154.236/message/reset/view?token={}'.format(token)
    send_mail(subject, author, to, content)
    return render_template('chakan.html')


@main.route("/reset/view")
def reset_view():
    if 'token' not in request.args:
        return redirect(url_for('index.index'))
    else:
        return render_template('reset_view.html', token=request.args['token'])


@main.route('/reset/update/<token>', methods=["POST"])
def reset_update(token):
    form = request.form.to_dict()
    # k = 'replied_topic_{}'.format(user_id)
    # if cache.exists(k):
    #     v = cache.get(k)
    #     ts = json.loads(v)
    #     return ts
    k = 'xiugai_{}'.format(token)
    if cache.exists(k):
        v = cache.get(k)
        u = User.one(id=int(v))
        password = User.salted_password(form['password'])
        User.update(u.id, password=password)
        return redirect(url_for('index.index'))


@main.route('/')
def index():
    u = current_user()

    send = Messages.all(sender_id=u.id)
    received = Messages.all(receiver_id=u.id)

    t = render_template(
        'mail/index.html',
        send=send,
        received=received,
    )
    return t




@main.route('/view/<int:id>')
def view(id):
    message = Messages.one(id=id)
    u = current_user()
    # if u.id == mail.receiver_id or u.id == mail.sender_id:
    if u.id in [message.receiver_id, message.sender_id]:
        return render_template('mail/detail.html', message=message)
    else:
        return redirect(url_for('.index'))
