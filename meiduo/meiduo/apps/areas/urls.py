from django.conf.urls import url
from . import views

urlpatterns = [
    # this.host + '/areas/';
    url(r'^areas/$', views.AreasView.as_view())
]