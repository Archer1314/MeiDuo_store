from django.conf.urls import url
from . import views



urlpatterns = [
    # 添加购物车路由
    # this.host + '/carts/'
    url(r'^carts/$', views.CartsView.as_view()),
    ]