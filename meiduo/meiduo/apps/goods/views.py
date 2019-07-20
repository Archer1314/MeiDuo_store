import json

from django.shortcuts import render
from django.utils import timezone
from django.views import View
from .models import GoodsCategory, SKU
from django.db import DatabaseError
from django import http
from contents.utils import get_breadcrumb, get_goods_channel
from django.core.paginator import Paginator
from meiduo.utils.response_code import RETCODE
from .models import GoodsVisitCount
from meiduo.utils.views import LoginRequiredView
from django_redis import get_redis_connection
# Create your views here.


class GoodsListView(View):
    def get(self, request, category_id, page_num):
        # 没渲染数据，未渲染无法返回,报错无参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('未知参数')
        # 获得面包屑
        breadcrumb = get_breadcrumb(category_id)
        # 获得商品频道数据
        categories = get_goods_channel()
        # 获得排序字段
        sort = request.GET.get('sort')
        if sort == 'price':
            chose_sort = 'price'
        elif sort == 'hot':
            chose_sort = '-sales'
        else:
            sort = 'default'
            chose_sort = 'create_time'
        # 获取所有具体商品sku, 已知三级分类，获取商品，根据表的隐士外键
        goods_skus = category.sku_set.filter(is_launched=True, stock__gt=0).order_by(chose_sort)
        # 根据分页显示，有django的模块
        # 生成分页器,两个参数必传， 需要分页的容器， 分页数量
        paginator = Paginator(goods_skus, 5)
        # 获得第page_num页的商品数据
        page_skus = paginator.page(page_num)
        # 计算总页数
        total_page = paginator.num_pages

        context = {
            'categories': categories,  # 频道分类
            'breadcrumb': breadcrumb,  # 面包屑导航
            'sort': sort,  # 排序字段
            'category': category,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request, 'list.html', context)


class HotGoodsView(View):
    def get(self, request, category_id):

        # 先判断category_id 是否正确
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('未知参数')
        # 取出商品sku表中， 按照sales排序， 取两个
        goods_sku = category.sku_set.filter(is_launched=True, stock__gt=0).order_by('-sales')[:2]

        # 查看前端vue， 知道存放商品的是hot——skus， vue中赋予每个对象一个url，应该是后边的商品详情连接，暂时用不上
        # htlm 中只是遍历取出， 需要用到的字段有图片、id、name,price
        hot_skus = []
        for sku in goods_sku:
            sku1 = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            }
            hot_skus.append(sku1)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': hot_skus})


class DetailGoodView(View):
    def get(self, request, sku_id):
        # 校验sku_id
        try:
            sku = SKU.objects.get(id=sku_id)
        except GoodsCategory.DoesNotExist:
            return render(request, '404.html')
        # 获取频道分类
        # 先根据sku——id取category_id，再调用封装好的方法
        category_id = sku.category.id

        # # 查询当前sku所对应的spu
        spu = sku.spu

        """1.准备当前商品的规格选项列表 [8, 11]"""
        # 获取出当前正显示的sku商品的规格选项id列表
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_option_ids = []  # [8, 11]
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)

        """2.构造规格选择仓库
        {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        """
        # 构造规格选择仓库
        temp_sku_qs = spu.sku_set.all()  # 获取当前spu下的所有sku
        # 选项仓库大字典
        spec_sku_map = {}  # {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        for temp_sku in temp_sku_qs:
            # 查询每一个sku的规格数据
            temp_spec_qs = temp_sku.specs.order_by('spec_id')
            temp_sku_option_ids = []  # 用来包装每个sku的选项值
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id

        """3.组合 并找到sku_id 绑定"""
        spu_spec_qs = spu.specs.order_by('id')  # 获取当前spu中的所有规格

        for index, spec in enumerate(spu_spec_qs):  # 遍历当前所有的规格
            spec_option_qs = spec.options.all()  # 获取当前规格中的所有选项
            temp_option_ids = current_sku_option_ids[:]  # 复制一个新的当前显示商品的规格选项列表
            for option in spec_option_qs:  # 遍历当前规格下的所有选项
                temp_option_ids[index] = option.id  # [8, 12]
                option.sku_id = spec_sku_map.get(tuple(temp_option_ids))  # 给每个选项对象绑定下他sku_id属性

            spec.spec_options = spec_option_qs  # 把规格下的所有选项绑定到规格对象的spec_options属性上
        context = {
            'categories': get_goods_channel(),  # 商品分类
            'breadcrumb': get_breadcrumb(category_id),  # 面包屑导航
            'sku': sku,  # 当前要显示的sku模型对象
            'category': sku.category,  # 当前的显示sku所属的三级类别
            'spu': spu,  # sku所属的spu
            'spec_qs': spu_spec_qs,  # 当前商品的所有规格数据
        }
        # context = {
        #     'categories': get_goods_channel(),  # 频道分类
        #     'breadcrumb': get_breadcrumb(category_id),  # 面包屑导航
        #     'sku': sku
        # }
        return render(request, 'detail.html', context)
        pass


class DetailVisitCount(View):
    def post(self, request, category_id):
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('未知参数')

        date_now = timezone.now()
        # date_now = timezone.localtime()
        try:
            category_visit = GoodsVisitCount.objects.get(category_id=category_id, date=date_now)
        except GoodsVisitCount.DoesNotExist:
            category_visit = GoodsVisitCount(category=category)
        category_visit.count += 1
        category_visit.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})



class BrowseHistoriesView(View):
    """需要用View， 否则非登录用户会转到登录界面"""
    def post(self, request):
        """存储商品浏览记录"""
        # 获取商品id
        sku_id = json.loads(request.body.decode()).get('sku_id')
        # 校验参数
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数错误'})
        user = request.user
        # 判断用户是否登录
        if not user.is_authenticated:
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '非登录用户'})
        # 存储浏览记录
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        # 不能重复， 去重
        pl.lrem('history_%s' % user.id, 0, sku_id)
        # 插入首位，最新浏览最靠前
        pl.lpush('history_%s' % user.id, sku_id)
        # 截取5个数据，因为前端只展示5个数据， 后端保存5个即可
        pl.ltrim('history_%s' % user.id, 0, 4)
        pl.execute()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """用户中心展示浏览记录"""

        # 必须做一次用户是否登录判断
        user = request.user
        if not user.is_authenticated:
            return http.HttpResponseForbidden('请先登录')
        # 获取数据

        redis_conn = get_redis_connection('history')
        redis_skus = redis_conn.lrange('history_%s' % user.id, 0, -1)
        skus = []
        # 用循环保证取出顺序和保存到给前端的数据一样
        for sku_id in redis_skus:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url,
            }
            skus.append(sku_dict)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': skus})





