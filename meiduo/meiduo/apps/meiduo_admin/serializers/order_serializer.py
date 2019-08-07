from rest_framework import serializers
from orders.models import OrderInfo, OrderGoods
from goods.models import SKU


class SKUSimpleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ['name', 'default_image']


class OrderGoodsModelSerializer(serializers.ModelSerializer):
    sku = SKUSimpleModelSerializer()

    class Meta:
        model = OrderGoods
        fields = ['count', 'price', 'sku']


class OrderModelDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    skus = OrderGoodsModelSerializer(many=True)

    class Meta:
        model = OrderInfo
        exclude = [
            'address',
            'update_time',
        ]


class OrderModelSimpleSerializer(serializers.ModelSerializer):
    """简单展示的序列化器"""
    class Meta:
        model = OrderInfo
        fields = ['order_id', 'create_time']


class OrderModelSerializer(serializers.ModelSerializer):
    """保存状态的"""
    class Meta:
        model = OrderInfo
        fields = ['status']
