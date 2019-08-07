from rest_framework.viewsets import ModelViewSet
from goods.models import SPUSpecification
from meiduo_admin.serializers.spec_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class SPUSecViewSet(ModelViewSet):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer
    pagination_class = MyUserPagination

