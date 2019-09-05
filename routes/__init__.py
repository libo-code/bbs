import uuid
from functools import wraps

import redis
import json
from flask import session, request, abort

from models.user import User
from utils import log


# def current_user():
#     if 'session_id' in request.cookies:
#         session_id = request.cookies['session_id']
#         s = Session.one_for_session_id(session_id=session_id)
#         key = 'session_id_{}'.format(session_id)
#         user_id = int(cache.get(key))
#         log('current_user key <{}> user_id <{}>'.format(key, user_id))
#         u = User.one(id=user_id)
#         return u
#     else:
#         return None

def current_user():
    # if 'session_id' in request.cookies:
    #     session_id = request.cookies['session_id']
    #     u = Session.find_user(session_id=session_id)
    #     return u
    # else:
    #     return User.guest()
    session_id = request.cookies['session_id']
    key = 'session_id_{}'.format(session_id)
    if cache.exists(key):
        v = cache.get(key)
        u = User.one(id=int(v))
        # type annotation
        # User u = User.one(id=uid)
        return u


def csrf_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args['token']
        u = current_user()
        # if cache.exists(k):
        #     v = cache.get(k)
        #     ts = json.loads(v)
        #     return ts
        k = 'wangye_token_{}'.format(token)
        if cache.exists(k) and int(cache.get(k)) == int(u.id):
            cache.delete(k)
            return f(*args, **kwargs)
        else:
            abort(401)

    return wrapper


def new_csrf_token():
    u = current_user()
    token = str(uuid.uuid4())
    k = 'wangye_token_{}'.format(token)
    cache.set(k, u.id)
    return token


cache = redis.StrictRedis()