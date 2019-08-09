from django.contrib.auth.hashers import make_password
from rest_framework import serializers
# from django.contrib.auth.models import User
from django.contrib.auth.models import Group
from users.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id',
                  'username',
                  'password',
                  'email',
                  'telephone',
                  'groups',
                  'user_permissions']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        attrs['is_staff'] = True
        attrs['password'] = make_password(attrs.get('password'))
        return attrs
    # def create(self, validated_data):
    #     validated_data['is_staff'] = True
    #     return self.Meta.model.objects.create_superuser(**validated_data)
    #
    # def update(self, instance, validated_data):
    #     validated_data['is_staff'] = True
    #     instance(**validated_data)
    #         instance.save()
    #     return instance


class GroupSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


