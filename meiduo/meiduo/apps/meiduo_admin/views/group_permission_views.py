from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.group_permission_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class GroupPermissionViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupPermissionModelSerializer
    pagination_class = MyUserPagination
    # 为何创建时能在auth_group\auth_group_permission 两张表创建对象


class PermissionSimpleView(ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = PermissionSimpleSerializer


