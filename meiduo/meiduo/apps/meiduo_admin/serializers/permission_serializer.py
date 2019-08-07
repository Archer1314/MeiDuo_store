from rest_framework import serializers
from django.contrib.auth.models import Permission, ContentType


class PermissionModelSerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()
    # 新建时提醒缺少该字段
    content_type_id = serializers.IntegerField()

    class Meta:
        model = Permission
        fields = '__all__'


class ContentTypeModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ContentType
        # 为何看模型类没有这个name属性， 还可以用
        fields = ['name', 'id']
