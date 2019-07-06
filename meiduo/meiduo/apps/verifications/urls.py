from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.Verifications.as_view()),
    # 此处url 只匹配资源路径,查询字符集不算在此处url内,所以要加上$
    url(r'^sms_codes/(?P<mobile>1[3-9][0-9]{9})/$', views.SmsCode.as_view()),
]