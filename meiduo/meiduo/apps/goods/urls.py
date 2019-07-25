from django.conf.urls import url
from . import views


urlpatterns = [
    # 获取商品列表
    # http://www.meiduo.site:8000/list/115/1/
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.GoodsListView.as_view()),
    # 获取热销商品数据， 使用vue请求
    # url = this.host + '/hot/' + this.category_id + '/';
    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),
    # 获取商品详情页
    # /detail/(?P<sku_id>\d+)/
    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailGoodView.as_view()),
    # 统计各个第三类商品的浏览量
    #     this.hots + '/visit/' + this.category_id + '/';
    url(r'^visit/(?P<category_id>\d+)/$', views.DetailVisitCount.as_view()),
    # 保存浏览记录
    # url = this.host + '/browse_histories/';
    url(r'^browse_histories/$', views.BrowseHistoriesView.as_view()),
    # 获取评价详情
    # /comments/'+ this.sku_id +'/'
    url(r'^comments/(?P<sku_id>\d+)/$', views.DetailGoodCommentView.as_view()),

]