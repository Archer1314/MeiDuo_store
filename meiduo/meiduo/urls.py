"""meiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # 用户应用
    url(r'^', include('users.urls', namespace='users')),
    # 图形验证码、短信验证码应用
    url(r'^', include('verifications.urls', namespace='verifications')),  # 为何没有路由屏蔽:a
    # 主页应用
    url(r'^', include('contents.urls', namespace='contents')),
    # qq 登录应用
    url(r'^', include('oauth.urls', namespace='oauth')),
    # 收货地址的应用
    url(r'^', include('areas.urls', namespace='areas')),
]
