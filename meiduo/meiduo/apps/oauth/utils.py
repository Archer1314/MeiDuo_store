from django.db import models


class BaseModel(models.Model):
    # 给基类添加两个字段，记录用户的信息
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True   # (数据库迁移时不会产生一个数据库)