from django.shortcuts import render
from .utils import get_goods_channel
from .models import ContentCategory
import os
from django.conf import settings



def generate_static_index_html():
    """将动态页面转换成静态html文件"""
    # 获取商品分类
    categories = get_goods_channel()
    # # 获取广告数据
    # 具体的广告
    contents = {}
    # 类别
    content_category = ContentCategory.objects.all()
    for category in content_category:
        # content表建立时外建时没有给content category 的隐士外建指定别名，故
        # 返回的广告数据类型:{类别： 该类的所有具体广告对象的qs,
        contents[category.key] = category.content_set.filter(status=True).order_by('sequence')
    context = {
        # 此处要返回啥， 需要看前端怎么渲染
        'categories': categories,
        'contents': contents
    }
    response = render(None, 'index.html', context)
    html_data = response.content.decode()
    # 存放生成的html文件的存放路径
    file_name = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_name, 'w', encoding='utf-8') as w:
        w.write(html_data)

