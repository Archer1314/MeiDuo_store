from django import http
from django.shortcuts import render
from django.views import View
from .models import Content, ContentCategory
from goods.models import GoodsChannel
from .utils import get_goods_channel

# Create your views here.
class IndexContents(View):
    # 请求首页
    def get(self, request):
        # 获取商品频道分类
        """
        # categories = {}  # 存放所有分组信息
        # # 获取第一层分组, 所有都是一级分类， 但是有分组（手机、运营商、数码）， 和显示的顺序
        # goods_channel_qs = GoodsChannel.objects.all().order_by('group_id', 'sequence')
        # for goods_channel in goods_channel_qs:
        #     group_id = goods_channel.group_id
        #     # 判断当前的组号在字典中是否存在
        #     if group_id not in categories:
        #         # 不存在,包装一个当前组的准备数据()相当于商品频道的每一行
        #         categories[group_id] = {'channels': [], 'sub_cats': []}  # chanel 是商品中的手机
        #     # 获取一级类别数据  得到1,2,3...37  又对象转1d
        #     cat1 = goods_channel.category
        #     # 将频道中的url绑定给一级类型对象  # 跳转到一类的东西的广告界面:www.jiaju.jd.com
        #     cat1.url = goods_channel.url
        #     # 将id加入到字典的chanels字段中
        #     categories[group_id]['channels'].append(cat1)
        #     # 获取当前一组下面的所有二级数据， 隐士外建查找
        #     cat2_qs = cat1.subs.all()
        #     # 遍历二级数据查询集
        #     for cat2 in cat2_qs:
        #         cat3_qs = cat2.subs.all()  # 获取当前二级下面的所有三级 得到三级查询集
        #         cat2.sub_cats = cat3_qs  # 把二级下面的所有三级绑定给cat2对象的sub_cats属性
        #         categories[group_id]['sub_cats'].append(cat2)
                categories = get_goods_channel()
        """
        categories = get_goods_channel()
        # # 获取广告数据
        # 具体的广告
        contents = {}
        # 类别
        content_category = ContentCategory.objects.all()
        for category in content_category:
            # content表建立时外建时没有给contentcategory 的隐士外建指定别名，故
            # 返回的广告数据类型:{类别： 该类的所有具体广告对象的qs,
            contents[category.key] = category.content_set.filter(status=True).order_by('sequence')
        context = {
            # 此处要返回啥， 需要看前端怎么渲染
            'categories': categories,
            'contents': contents
        }
        return render(request, 'index.html', context)


