from rest_framework import serializers
from goods.models import SKUImage, SKU


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKUImage
        fields = ['id', 'sku', 'image']


class SKUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = ['id', 'name']