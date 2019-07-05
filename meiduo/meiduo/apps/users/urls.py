from django.conf.urls import url, include
from . import views
urlpatterns = [

    url(r'^register/$', views.Users.as_view()),
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernamecodeView.as_view()),
    url(r'^mobiles/(?P<mobile>[0-9A-Za-z]{8,20})/count/$', views.telephonecodeView.as_view()),
]