from rest_framework import serializers
from goods.models import Brand
from fdfs_client.client import Fdfs_client
from django.conf import settings


class BrandModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'

    def validate(self, attrs):
        """更正图片字段的数据类型， 图片数据转地址"""
        # 通用于更新和创建过程
        conn = Fdfs_client(settings.FASTFDS_CONF_PATH)
        # 获取图片数据内容
        logo = attrs.pop('logo')
        logo_content = logo.read()
        # 上传
        res = conn.upload_by_buffer(logo_content)
        # 判断上传结果
        if not res or res.get('Status') != 'Upload successed.':
            raise serializers.ValidationError('上传失败')

        # 前段传来的attrs更正为fdfs图片存储路径
        attrs['logo'] = res.get('Remote file_id')

        return super().validate(attrs)