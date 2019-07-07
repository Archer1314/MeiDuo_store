import re
from django.contrib.auth.backends import ModelBackend
from .models import User

def get_use(username):
    try:
        if re.match(r'^1[3-9]\d{9}$', username):
            user = User.objects.get(telephone=username)
        else:
            user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None
    else:
        return user


class ManyUser(ModelBackend):
    # 重写该方法，其他正常使用
    # 根据现有内容、username password
    @staticmethod
    def authenticate(request, username=None, password=None, **kwargs):
        user = get_use(username)
        if user and user.check_password(password):
            return user
