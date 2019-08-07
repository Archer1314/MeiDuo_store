from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django.db.models import Q
from meiduo_admin.serializers.brand_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class BrandViewSet(ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandModelSerializer
    pagination_class = MyUserPagination