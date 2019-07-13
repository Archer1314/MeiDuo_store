from django.db import models

# Create your models here.


class Areas(models.Model):
    name = models.CharField(max_length=20, verbose_name='名称')
    # on_delete=models.SET_NULL 外建默认有保护，不能为空， 普通的设置null=True还不够， 要加上这一句，使用技巧：自连接表
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, related_name='subs', null=True, blank=True, verbose_name='编号', )

    class Meta:
        db_table = 'tb_areas'
        verbose_name = '省市区三级地址'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name