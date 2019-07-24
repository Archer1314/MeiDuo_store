import re
from django.contrib.auth.backends import ModelBackend
from .models import User
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings


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


def generate_verify_url(user):
    """生成用户激活邮箱url"""
    # 新建加密对象
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    # 准备加密数据
    data = {'user_id': user.id, 'email': user.email}
    # 加密,字节流转字符串
    token = serializer.dumps(data).decode()
    # 拼接激活url   'http://www.meiduo.site:8000/emails/verification/' + '?token=' + 'xxxxdfsajadsfljdlskaj'
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    print(verify_url)
    return verify_url



def check_verify_url(token):
    """传入token解密后查询用户"""
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    print(token)
    try:
        data = serializer.loads(token)
        user_id = data.get('user_id')
        email = data.get('email')
        try:
            user = User.objects.get(id=user_id, email=email)
            return user
        except User.DoesNotExist:
            return None
    except BadData:
        return None
    # # 新建加密对象
    # serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    # print(12)
    # try:
    #     data = serializer.loads(token)
    #     user_id = data.get('user_id')
    #     email = data.get('email')
    #     print(user_id, email)
    #     try:
    #         user = User.objects.get(id=user_id, email=email)
    #         return user
    #     except User.DoesNotExist:
    #         return None
    # except BadData:
    #     return None


def generate_access_token(user):
    # 新建加密对象
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    # 准备加密数据
    data = {'id': user.id, 'token': user.telephone}
    # 加密,得到字节流字符串
    data_bytes = serializer.dumps(data)
    # 返回字符串
    access_token = data_bytes.decode()
    # 返回
    return access_token


def check_access_token(access_token):
    # 新建加密对象
    serializer = Serializer(settings.SECRET_KEY, 3600 * 24)
    try:
        data = serializer.loads(access_token)
        mobile = data.get('token')
        id = data.get('id')
        try:
            user = User.objects.get(id=id, telephone=mobile)
            return user
        except User.DoesNotExist:
            return None
    except BadData:
        return None
