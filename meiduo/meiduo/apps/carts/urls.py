from django.conf.urls import url
from . import views



urlpatterns = [
    # 添加购物车路由
    # this.host + '/carts/'
    url(r'^carts/$', views.CartsView.as_view(), name='carts'),
    # 购物车的商品全选
    # /carts/selection/
    url(r'^carts/selection/$', views.CartsSelectAllView.as_view()),
    ]