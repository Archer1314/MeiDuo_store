from rest_framework import serializers
from goods.models import SKU, SKUSpecification, GoodsCategory, SPU, SPUSpecification, SpecificationOption


class SKUSpecSimpleSerializer(serializers.ModelSerializer):
    spec_id = serializers.IntegerField()
    option_id = serializers. IntegerField()

    class Meta:
        model = SKUSpecification
        fields = ['spec_id', 'option_id']



class SkuModelSerializers(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    # 代表就是与当前sku主表对象关联的多有从表（Spec）对象集(多个)
    specs = SKUSpecSimpleSerializer(many=True)

    class Meta:
        model = SKU
        fields = '__all__'

    def create(self, validated_data):
        # 取出
        specs = validated_data.pop('specs')
        # 创建sku对象
        # spu = SPU.objects.get(id=validated_data.pop('spu_id'))
        # validated_data['spu'] = spu
        # 重新调用create要按照字典的格式传入， 不能用**validated_data, 否则会报spu_id\category_id 等字段的错误
        sku = super().create(validated_data)
        # 创建从表SKU——spec的数据
        for spec in specs:
            SKUSpecification.objects.create(sku_id=sku.id, **spec)
        return sku

    def update(self, instance, validated_data):
        specs = validated_data.pop('specs')
        SKUSpecification.objects.filter(sku_id=instance.id).delete()
        for spec in specs:
            SKUSpecification.objects.create(sku_id=instance.id, **spec)
        return super().update(instance, validated_data)
    # 级联， 会将从表的外建数据也删除


class SKUCategorySimpleSerializer(serializers.ModelSerializer):
    """三级分类"""
    class Meta:
        model = GoodsCategory
        fields = ['id', 'name']


class SPUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = ['id', 'name']


class SpecSimpleView(serializers.ModelSerializer):
    spec = serializers.StringRelatedField()

    class Meta:
        model = SpecificationOption
        fields = ['id', 'value', 'spec']


class SPUSpecDetailSerializer(serializers.ModelSerializer):
    """商品的规格表"""
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    options = SpecSimpleView(many=True)

    class Meta:
        model = SPUSpecification
        fields = ['id', 'name', 'spu', 'spu_id', 'options']

