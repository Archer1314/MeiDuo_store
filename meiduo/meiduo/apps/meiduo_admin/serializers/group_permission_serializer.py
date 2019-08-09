from rest_framework import serializers
from django.contrib.auth.models import Permission, ContentType, Group


class GroupPermissionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class PermissionSimpleSerializer(serializers.ModelSerializer):
    content_type = serializers.StringRelatedField()

    class Meta:
        model = Permission
        fields = ['id', 'name', 'content_type']


