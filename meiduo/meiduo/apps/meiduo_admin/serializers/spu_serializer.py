from rest_framework import serializers
from goods.models import SPU, Brand, GoodsCategory


class SPUDetailSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    brand_id = serializers.IntegerField()
    category1_id = serializers.IntegerField()
    category2_id = serializers.IntegerField()
    category3_id = serializers.IntegerField()
    # serializers.CharField(allow_blank=True)

    class Meta:
        model = SPU
        # 为啥这样会导致包装、描述字段变成必填项
        exclude = ['category1', 'category2', 'category3']
        extra_kwargs = {
            'desc_detail': {'allow_blank': True},
            'desc_pack': {'allow_blank': True},
            'desc_service': {'allow_blank': True},
        }




class GoodsBrandSerializer(serializers.ModelSerializer):
    """商品名称"""
    class Meta:
        model = Brand
        fields = ['id', 'name']


class SKUCategorySerializer(serializers.ModelSerializer):
    """三级分类"""
    class Meta:
        model = GoodsCategory
        fields = ['id', 'name']
