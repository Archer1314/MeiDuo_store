from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.utils.user_pages import MyUserPagination
from meiduo_admin.serializers.image_serializer import *


class ImageViewSet(ModelViewSet):
    queryset = SKUImage.objects.all()
    serializer_class = ImageSerializer
    pagination_class = MyUserPagination

#     图片上传有问题， 应该是上传图片的路径而不是图片文件

class SkuSimpleView(ListAPIView):
    queryset = SKU.objects.all()
    serializer_class = SKUSimpleSerializer
