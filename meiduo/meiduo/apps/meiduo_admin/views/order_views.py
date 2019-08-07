from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import UpdateAPIView
from meiduo_admin.serializers.order_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class OrderViewSet(ModelViewSet):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderModelDetailSerializer
    pagination_class = MyUserPagination

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(order_id__contains=keyword)
        return self.queryset.all()


# class PartialUpdateView(UpdateAPIView):
#     queryset = 局部更新

