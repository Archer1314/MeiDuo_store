from django.conf.urls import url
from rest_framework.routers import SimpleRouter
from rest_framework_jwt.views import obtain_jwt_token
from .views.login_home_views import *
from .views.user_views import *
from .views.sku_views import *
from .views.spu_views import *
from .views.spec_views import *
from .views.specoption_views import *
from .views.image_views import *
from .views.chanel_views import *
from .views.brand_views import *
from .views.order_views import *
from .views.permission_views import *
from .views.group_permission_views import *
from .views.admins_views import *



urlpatterns = [
    url(r'^authorizations/$', Login.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),
    url(r'^statistical/goods_day_views/$', GoodVisitCountView.as_view()),
    url(r'^users/$', UserManageView.as_view()),
    # url(r'^skus/$', SkuGoodsManageView.as_view()),
    # 商品 分类
    url(r'^skus/categories/$', CategoryManageView.as_view()),
    # 商品名称
    url(r'^goods/simple/$', CategoryManageView.as_view()),
    # 商品 规格
    url(r'^goods/(?P<pk>\d+)/specs/$', SPUSpecView.as_view()),
    # 商品品牌
    url(r'^goods/brands/simple/$', GoodsBrandView.as_view()),

    # 商品一级分类
    url(r'^goods/channel/categories/$', CategoryView.as_view()),
    # 商品二级三级分类goods/channel/categories/33/
    url(r'^goods/channel/categories/(?P<pk>\d+)/$', CategoryView.as_view()),

    url(r'^goods/specs/$', SPUSecViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^goods/specs/(?P<pk>\d+)/$', SPUSecViewSet.as_view({'get': 'retrieve',
                                                              'put': 'update',
                                                              'delete': 'destroy'})),
    # specs/options/
    url(r'^specs/options/$', SpecOptionViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^specs/options/(?P<pk>\d+)/$', SpecOptionViewSet.as_view({'get': 'retrieve',
                                                                    'put': 'update',
                                                                    'delete': 'destroy'})),
    # skus/images/
    url(r'^skus/images/$', ImageViewSet.as_view({'get': 'list', 'post': 'create'})),
    url(r'^skus/images/(?P<pk>\d+)/$', ImageViewSet.as_view({'get': 'retrieve',
                                                             'put': 'update',
                                                             'delete': 'destroy'})),

    # 上传图片前获取商品id
    url(r'^skus/simple/$', SkuSimpleView.as_view()),

    # 上传规格选项前：获取所有规格
    url(r'^goods/specs/simple/$', SPUSpecSimpleView.as_view()),

    # 频道需要的一级分组
    url(r'^goods/categories/$', CategoryView.as_view()),
    # 频道需要的分组
    url(r'^goods/channel_types/$', GoodsChannelGroupView.as_view({'get': 'list'})),

    # 修改用户订单的状态
    # orders/20190720111331000000002/status/
    url(r'^orders/(?P<pk>\d+)/status/$', OrderViewSet.as_view({'patch': 'partial_update'})),
    # 获取权限类型列表
    # permission/content_types/
    url(r'^permission/content_types/$', PermissionListView.as_view()),
    # 权限列表
    # permission/simple/
    url(r'^permission/simple/$', PermissionSimpleView.as_view()),

    url(r'^permission/groups/simple/$', GroupSimpleView.as_view()),

]

router = SimpleRouter()
# skus 的增删该查
router.register(prefix='skus', viewset=SkuGoodsManageView, base_name='skus')
# 注册首页的增删该查
router.register(prefix='statistical', viewset=IndexManageMessage, base_name='statistical')
# 频道页
router.register(prefix='goods/channels', viewset=GoodsChannelViewSet, base_name='channels')
# 品牌管理
router.register(prefix='goods/brands', viewset=BrandViewSet, base_name='brand')
# spu管理
router.register(prefix='goods', viewset=SPUViewSet, base_name='goods')
# order管理
router.register(prefix='orders', viewset=OrderViewSet, base_name='orders')
# 权限管理
router.register(prefix='permission/perms', viewset=PermissionViewSet, base_name='permission')
# 组权限管理
router.register(prefix='permission/groups', viewset=GroupPermissionViewSet, base_name='groups')
# 管理员
router.register(prefix='permission/admins', viewset=AdminUserViewSet, base_name='admins')

urlpatterns += router.urls



