# 公用一个路由， 两个方法get、post 对象列表和新建
# 如果不写路由就用model
from rest_framework.pagination import PageNumberPagination
from meiduo_admin.utils.user_pages import MyUserPagination
from rest_framework.generics import GenericAPIView, ListAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import status
from users.models import User
from meiduo_admin.serializers.user_serializers import UserDetailSerializers

# 导出到utils工具中， 方便重复调用
# class MyUserPagination(PageNumberPagination):
#     page_size = 10
#     page_size_query_param = 'pagesize'
#     max_page_size = 10
#     page_query_param = 'page'


# class UserManageView(GenericAPIView):
#     """手动分页返回数据"""
#     # 使用GenericAPIView
#     pagination_class = MyUserPagination
#     queryset = User.objects.filter(is_staff=True)
#     serializer_class = UserDetailSerializers
#
#     def get_queryset(self):
#         """ 解决有查询用户的， 不插入分页影响逻辑"""
#         keyword = self.request.query_params.get('keyword')
#         # 如果有查询
#         if keyword:
#             return self.queryset.filter(username__contains=keyword)
#         return self.queryset.all()
#
#     def get(self, request):
#         """获取用户信息 包含分页情况"""
#         # 获得查询级
#         query_set = self.get_queryset()
#
#         # genericAPIView 根据超级用户查询集进行分类, 根据查询字符串和分页器返回一页数据
#         page = self.paginate_queryset(query_set)
#         if page:
#             # 序列化真正需要的用户信息
#             serializer = self.get_serializer(page, many=True)
#
#             # return Response(
#             #     {
#             #         'counts': self.queryset.count(),
#             #         'lists': serializer.data,
#             #         'page': self.request.query_params['page'],
#             #         # 'pages': self.paginator.num_pages,
#             #         'pagesize':self.request.query_params['pagesize'],
#             #     }
#             # )
#             # 重构分页器的返回方法， 可以方便组织返回数据
#             # 传入分页后的子集的序列化结果，返回的是分页返回响应对象
#             return self.get_paginated_response(serializer.data)
#
#         # 序列化全部管理员用户信息
#         serializer = self.get_serializer(query_set, many=True)
#         # 返回用户信息
#         # return Response(data=serializer.data)  # 不符合要返回前端的数据要求
#         return Response(
#             {
#                 'counts': self.queryset.count(),
#                 'lists': serializer.data,
#             }
#         )


class UserManageView(ListAPIView, CreateAPIView):
    """继承ListAPIView， 自带分页返回功能; CreateAPIView 自带创建用户的逻辑"""
    pagination_class = MyUserPagination
    queryset = User.objects.filter(is_staff=True)
    serializer_class = UserDetailSerializers


    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(username__contains=keyword)
        return self.queryset.all()

# class SuperUserCreateView(CreateAPIView):
#     queryset = User.objects.filter(is_staff=True)
#     serializer_class = UserDetailSerializers