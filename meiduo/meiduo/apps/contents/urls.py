# from django.conf.urls import url, include
from django.conf.urls import url
from . import views
urlpatterns = [
    url(r'^$', views.IndexContents.as_view(), name='index')
]
