from rest_framework import serializers
from goods.models import SpecificationOption, SPUSpecification


class SpecOptionSerializer(serializers.ModelSerializer):
    spec = serializers.StringRelatedField()
    spec_id = serializers.IntegerField()

    class Meta:
        model = SpecificationOption
        fields = '__all__'


class SPUSpecSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPUSpecification
        fields = ['id', 'name']


