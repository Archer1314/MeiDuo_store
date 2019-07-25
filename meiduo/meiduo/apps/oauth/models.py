from django.db import models
from .utils import BaseModel
# Create your models here.



class OAuthUser(BaseModel):
    """QQ登录用户模型类"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=80, unique=True, db_index=True, verbose_name='open_id')

    class Meta:
        db_table = 'tb_qq_oauth'
        verbose_name = 'QQ登录用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.username


class OAuthWeiBoUser(BaseModel):
    """微博登录用户模型类"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    access_token = models.CharField(max_length=80, unique=True, db_index=True, verbose_name='access_token')

    class Meta:
        db_table = 'tb_weibo_oauth'
        verbose_name = '微博登录用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.user.username


