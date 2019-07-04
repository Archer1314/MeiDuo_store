from django.conf.urls import url, include
from . import views
urlpatterns = [

    url(r'^register/$', views.Users.as_view()),
    url(r'^usernames/[a-zA-Z0-9_-]{5,20}/count/$', views.Users.as_view()),
]