from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler
from goods.models import GoodsVisitCount


class UserModelSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        # 校验账号密码
        user = authenticate(**attrs)
        if user is None:
            raise serializers.ValidationError('用户名或密码错误')

        token = jwt_encode_handler(payload=jwt_payload_handler(user))
        return {
            'user': user,
            'token': token
        }


class GoodsVisitCountSerializers(serializers.ModelSerializer):
    # 重写不符合数据要求的字段
    category = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GoodsVisitCount
        # 指定模型类要序列化的字段
        fields = ['category', 'count']
        extra_kwargs = {
            'count': {'min_value': 0}
        }