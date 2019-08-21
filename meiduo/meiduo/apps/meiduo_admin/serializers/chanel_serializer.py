from rest_framework import serializers
from goods.models import GoodsChannel, GoodsChannelGroup, GoodsCategory


class GoodsChanelSerializer(serializers.ModelSerializer):
    group = serializers.StringRelatedField()
    group_id = serializers.IntegerField()
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    class Meta:
        model = GoodsChannel
        fields = '__all__'


class ChannelGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsChannelGroup
        fields = ['id', 'name']


# class SKUCategorySerializer(serializers.ModelSerializer):
#     """三级分类"""
#     class Meta:
#         model = GoodsCategory
#         fields = ['id', 'name']