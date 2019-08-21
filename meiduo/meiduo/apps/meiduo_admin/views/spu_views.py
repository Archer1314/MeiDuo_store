from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from goods.models import SPU, Brand
from meiduo_admin.serializers.spu_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class SPUViewSet(ModelViewSet):
    queryset = SPU.objects.all()
    serializer_class = SPUDetailSerializer
    pagination_class = MyUserPagination

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()


class GoodsBrandView(ListAPIView):
    """商品品牌"""
    queryset = Brand.objects.all()
    serializer_class = GoodsBrandSerializer


class CategoryView(ListAPIView):
    """商品的三级分类列表选项"""
    queryset = GoodsCategory.objects.all()
    serializer_class = SKUCategorySerializer

    def get_queryset(self):
        parent_id = self.kwargs.get('pk')
        if parent_id:
            return self.queryset.filter(parent_id=parent_id)
        return self.queryset.filter(parent=None)

