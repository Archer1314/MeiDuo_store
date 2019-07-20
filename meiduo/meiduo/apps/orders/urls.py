from django.conf.urls import url
from . import views



urlpatterns = [
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),

    # /orders/commit/
    url(r'^orders/commit/$', views.CreateOrderView.as_view()),
    # /orders/success/
    url(r'^orders/success/$', views.OrderSuccessView.as_view()),
]