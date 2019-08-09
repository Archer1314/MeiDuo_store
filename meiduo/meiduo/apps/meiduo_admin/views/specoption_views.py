from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.specoption_serializer import *
from meiduo_admin.utils.user_pages import MyUserPagination
from goods.models import SKUSpecification


class SpecOptionViewSet(ModelViewSet):
    queryset = SpecificationOption.objects.all()
    serializer_class = SpecOptionSerializer
    pagination_class = MyUserPagination

    def destroy(self, request, *args, **kwargs):
        option_id = self.kwargs['pk']
        SKUSpecification.objects.filter(option_id=option_id).delete()
        return super().destroy(self, request, *args, **kwargs)


class SPUSpecSimpleView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer
