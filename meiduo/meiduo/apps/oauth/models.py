from django.db import models
from .utils import BaseModel
# Create your models here.


# 创建一个qq登录用户表， 存放登录用户信息
class OAuthUser(BaseModel):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=80, unique=True, db_index=True, verbose_name='open_id')

    class Meta:
        db_table = 'tb_qq_oauth'
        verbose_name = 'QQ登录用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.username



