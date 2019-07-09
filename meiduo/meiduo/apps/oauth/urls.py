from django.conf.urls import url
from . import  views

urlpatterns = [
    # 前端点击qq图标时， 向后台发送请求获取qq登录的连接https://graph.qq.com/oauth2.0/authorize
    # var url = this.host + '/qq/authorization/?next=' + next;
    url('^qq/authorization/$', views.OAuthQQURL.as_view()),
    # qq  返回的回调地址
    # http://www.meiduo.site:8000/oauth_callback?code=3CDB4F347C5872EEBC17AE3B61FC6E66&state=info
    url('^oauth_callback$', views.OAuthUserView.as_view())
]