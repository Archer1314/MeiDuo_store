from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.permission_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class PermissionViewSet(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionModelSerializer
    pagination_class = MyUserPagination

    def create(self, request, *args, **kwargs):
        request.data['content_type_id'] = request.data.get('content_type')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """修改： 问题在于只能修改一个分类"""
        # TODO 增加名称的修改, 改进成id的
        codename = request.data.get('codename')
        content_type_id = Permission.objects.get('codename').id
        request.data['content_type_id'] = request.data.get('content_type')
        return super().update(request, *args, **kwargs)


class PermissionListView(ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeModelSerializer

#     为何用permission返回的列表也同样的效果
# class PermissionListView(ListAPIView):
#     queryset = Permission.objects.all()
#     serializer_class = PermissionModelSerializer