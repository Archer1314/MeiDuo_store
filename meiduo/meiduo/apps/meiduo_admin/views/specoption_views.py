from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.specoption_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination


class SpecOptionViewSet(ModelViewSet):
    queryset = SpecificationOption.objects.all()
    serializer_class = SpecOptionSerializer
    pagination_class = MyUserPagination


class SPUSpecSimpleView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer
