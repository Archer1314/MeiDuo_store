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

# 一级分组
# class CategoryView(ListAPIView):
#     """商品的三级分类列表选项"""
#     queryset = GoodsCategory.objects.all()
#     serializer_class = SKUCategorySerializer
#
#     def get_queryset(self):
#         parent_id = self.kwargs.get('pk')
#         if parent_id:
#             return self.queryset.filter(parent_id=parent_id)
#         return self.queryset.filter(parent=None)
