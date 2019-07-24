from django.conf.urls import url, include
from users import views
urlpatterns = [
    # 注册网页路由
    url(r'^register/$', views.RegisterView.as_view()),
    # 用户名（json）是否重复的校验
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernamecountView.as_view()),
    # 手机号码（json）是否重复的校验
    url(r'^mobiles/(?P<mobile>[0-9A-Za-z]{8,20})/count/$', views.telephonecountView.as_view()),
    # 用户登陆页面请求和校验登陆信息
    url(r'^login/$', views.LoginView.as_view(), name='login'),
    # 用户退出
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
    # 用户中心
    url(r'^info/$', views.UserCenterInfoView.as_view(), name='center'),
    # 用户中心中用户绑定邮箱
    # this.host + '/emails/'
    url(r'^emails/$', views.UserCenterEmailView.as_view(), name='email'),
    # 用户中心 邮箱激活
    url(r'^emails/verifications/$', views.UserEmailActiveView.as_view(), name='active_email'),
    # 用户中心用户收货地址页面
    url(r'^addresses/$', views.UserCenterAreasView.as_view()),
    # 用户中心用户收货地址添加
    # var url = this.host + '/addresses/create/';
    url(r'^addresses/create/$', views.UserAreasCreateView.as_view()),
    # 修改收货地址post请求  \删除地址也是这个url delete请求
    # /addresses/(?P<address_id>\d+)/
    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 设置默认收货地址
    # /addresses/(?P<address_id>\d+)/default/
    url(r'^addresses/(?P<address_id>\d+)/default/$', views.SetDefaultAddressView.as_view()),
    # 修改地址标题
    # this.host + '/addresses/' + this.addresses[index].id + '/title/';
    url(r'^addresses/(?P<address_id>\d+)/title/$', views.AddressChangeTitleView.as_view()),
    # 修改密码
    url(r'^password/$', views.ChangePasswordView.as_view()),
    # 找回密码
    url(r'^find_password/$', views.FindPassword.as_view()),
    # 找回密码第一次请求密码
    url(r'^accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/sms/token/$', views.FindPasswordUniqueMake.as_view()),
    #     第二次请求前的获取短信 sms_codes/
    url(r'^sms_codes/$', views.FindPasswordSmsCode.as_view()),
    # 找回密码第二次请求密码
    url(r'^accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/password/token/$', views.FindPasswordCheckMsg.as_view()),
    # 找回密码第三次请求密码
    url(r'^users/(?P<user_id>\d+)/password/$', views.InstandPassword.as_view()),

    # this.host + '/users/'+ this.user_id +'/password/'
]