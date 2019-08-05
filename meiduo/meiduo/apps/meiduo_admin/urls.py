from django.conf.urls import url
from rest_framework.routers import SimpleRouter
from rest_framework_jwt.views import obtain_jwt_token
from .views.login_home_views import *
from .views.user_views import *


urlpatterns = [
    url(r'^authorizations/$', Login.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^statistical/goods_day_views/$', GoodVisitCountView.as_view()),
    url(r'^users/$', UserManageView.as_view()),

    ]

router = SimpleRouter()
router.register(prefix='statistical', viewset=IndexManageMessage, base_name='statistical')
urlpatterns += router.urls
