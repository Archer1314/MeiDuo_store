from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.utils.user_pages import MyUserPagination
from meiduo_admin.serializers.chanel_serializer import *


class GoodsChannelViewSet(ModelViewSet):
    queryset = GoodsChannel.objects.all()
    serializer_class = GoodsChanelSerializer
    pagination_class = MyUserPagination


class GoodsChannelGroupView(ModelViewSet):
    queryset = GoodsChannelGroup.objects.all()
    serializer_class = ChannelGroupSerializer
