from django.conf.urls import url, include
from users import views
urlpatterns = [
    # 注册网页路由
    url(r'^register/$', views.Users.as_view()),
    # 用户名（json）是否重复的校验
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernamecodeView.as_view()),
    # 手机号码（json）是否重复的校验
    url(r'^mobiles/(?P<mobile>[0-9A-Za-z]{8,20})/count/$', views.telephonecodeView.as_view()),
    # 用户登陆页面请求和校验登陆信息
    url(r'^login/$', views.IndexContents.as_view(), name='login'),
    # 用户退出
    url(r'^logout/$', views.LogoutUser.as_view()),
    # 用户中心
    url(r'^info/$', views.UserCenterInfo.as_view(), name='center'),
]