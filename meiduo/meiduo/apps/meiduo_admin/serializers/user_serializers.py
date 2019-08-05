from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from users.models import User


class UserDetailSerializers(serializers.ModelSerializer):
    # mobile = serializers.CharField(write_only=True, max_length=20)
    class Meta:
        model = User
        fields = ['id', 'username', 'telephone', 'email', 'password', ]
        extra_kwargs = {
            'username': {
                'max_length': 20,
                'min_length': 5
            },
            'password': {
                'max_length': 20,
                'min_length': 8,
                'write_only': True
            },
            'telephone': {'read_only': True}
        }

    def create(self, validated_data):
        """需求是对密码进行加密， 创建的应该是管理员"""
        # password = validated_data.get('password')
        # 进行加密
        # password = make_password(password)
        # 再保存validate_data--> 尽可能该数据而使用框架的逻辑
        # validated_data['telephone'] = validated_data.get('mobile')
        # validated_data[password] = password
        # validated_data['is_staff'] = True
        # 不自己创建：
        # user = User.objects.create(is_staff=True, **validated_data)

        # password = validated_data['password'] # 明文
        # validated_data['password'] = 密文
        # validated_data['password'] = make_password(password)
        # validated_data['is_staff'] = True
        # 有效数据中：1、明文该密文；2、添加is_staff=True

        # return super().create(validated_data)
        # 以上等价于： 创建超级用户的方法中内容
        return self.Meta.model.objects.create_superuser(**validated_data)



# 序列化嵌套