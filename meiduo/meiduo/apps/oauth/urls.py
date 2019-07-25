from django.conf.urls import url
from . import  views

urlpatterns = [
    # 前端点击qq图标时， 向后台发送请求获取qq登录的连接https://graph.qq.com/oauth2.0/authorize
    # var url = this.host + '/qq/authorization/?next=' + next;
    url('^qq/login/$', views.OAuthQQURL.as_view()),
    # qq  返回的回调地址
    # http://www.meiduo.site:8000/oauth_callback?code=3CDB4F347C5872EEBC17AE3B61FC6E66&state=info
    url('^oauth_callback/$', views.OAuthUserView.as_view()),

    # 前端点击微信图标时， 向后台发送请求获取qq登录的连接https://api.weibo.com/oauth2/authorize
    # '/sina/login/?next=' + next;
    url('^sina/login/$', views.OAuthWeiBoUrl.as_view()),
    # 返回的回调地址
    # sina_callback
    url('^sina_callback/$', views.OAuthWeiBoView.as_view()),
    # /oauth/sina/user/
    # 绑定用户
    # url('^oauth/sina/user/$', views.OAuthWeiBoUserView.as_view()),

    # '/sms_codes/' + this.mobile + '/?text=' + this.image_code+'&image_code_id='+ this.image_code_id
    # url('^sms_codes/(?P<mobile>1[3-9][0-9]{9})/$', views.OAuthSendSms.as_view()),

]