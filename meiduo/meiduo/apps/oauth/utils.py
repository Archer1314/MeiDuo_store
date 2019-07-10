from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings

class BaseModel(models.Model):
    # 给基类添加两个字段，记录用户的信息
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True   # (数据库迁移时不会产生一个数据库)


def generate_openid_encrypt(openid):
    '''对openid数据进行加密'''
    # 创建一个加密/解密对象  settings.SECRET_KEY 是混淆， 600是这个混淆的有效时间
    serializer_objects = Serializer(settings.SECRET_KEY, 600)
    # 准备要加密的数据，数据要准备成字典格式，真正要加密的是放在value位置
    data = {'openid': openid}
    # 对数据进行加密，返回得到的是字节流数据
    openid_secret = serializer_objects.dumps(data)
    # 要再转回字符串需要解析
    return openid_secret.decode()


def check_openid_singnature(openid_secret):
    # 创建一个加密/解密对象  settings.SECRET_KEY 是混淆， 600是这个混淆的有效时间
    serializer_objects = Serializer(settings.SECRET_KEY, 600)
    try:
        # 可能会报错， 有可能是混淆不正确 返回的是之前加密密的data字典， 可以将
        openid = serializer_objects.loads(openid_secret)['openid']
    except BadData:
        return None
    else:
        return openid