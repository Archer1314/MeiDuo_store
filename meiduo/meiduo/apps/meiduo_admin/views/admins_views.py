from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.admins_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination
from rest_framework.response import Response


class AdminUserViewSet(ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = AdminUserSerializer
    pagination_class = MyUserPagination

    # 为了解决数据库是telephone，前端是mobile， 重写展示的方法
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            admin_user_list = serializer.data
            for one_user_dict in admin_user_list:
                one_user_dict['mobile'] = one_user_dict.pop('telephone')
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        admin_user_list = serializer.data
        for one_user_dict in admin_user_list:
            one_user_dict['mobile'] = one_user_dict.pop('telephone')
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        request.data['telephone'] = request.data.pop('mobile')
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        request.data['telephone'] = request.data.pop('mobile')
        return super().update(request, *args, **kwargs)


class GroupSimpleView(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = GroupSimpleSerializer
