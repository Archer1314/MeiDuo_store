# from django.conf.urls import url, include
from django.conf.urls import url
from . import views
urlpatterns = [
    # ‘/’ 根路由不能写，否则路由进不来， 默认前段补上
    url(r'^$', views.IndexContents.as_view(), name='index')
]
