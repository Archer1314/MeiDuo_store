from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from django.db.models import Q
from meiduo_admin.serializers.sku_serializers import *
from meiduo_admin.utils.user_pages import *


class SkuGoodsManageView(ModelViewSet):
    """Sku商品的增删改查实现"""
    queryset = SKU.objects.filter()
    serializer_class = SkuModelSerializers
    pagination_class = MyUserPagination

    def get_queryset(self):
        # ?keyword = < 名称 | 副标题 > & page = < 页码 > & page_size = < 页容量 >
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(Q(name__contains=keyword)|Q(caption__contains=keyword))
        return self.queryset.all()


class CategoryManageView(ListAPIView):
    """sku新增的一级分类列表选项"""
    queryset = GoodsCategory.objects.all()
    serializer_class = SKUCategorySimpleSerializer

    def get_queryset(self):
        return self.queryset.filter(parent=None)


class SPUMangeView(ListAPIView):
    """sku新增的spu信息列表选项"""
    queryset = SPU.objects.all()
    serializer_class = SPUSimpleSerializer


class SPUSpecView(ListAPIView):
    """SPU商品的规格及选项详细"""
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecDetailSerializer

    def get_queryset(self):
        spu_id = self.kwargs.get('pk')
        if spu_id:
            return self.queryset.filter(spu_id=spu_id)
        # all()是为了保证获取的是最新的数据操作集
        return self.queryset.all()
