from django.core.files.storage import Storage
from django.conf import settings
from goods.models import GoodsChannel, GoodsCategory


def get_goods_channel():
    """封装商品的分类导航"""
    categories = {}
    # 按照分组的顺序和每组的展示顺序获得商品频道一级标签
    # 重要的是知道取出了一级标签，37个 ，每个对象5个字段
    goods_channels = GoodsChannel.objects.all().order_by('group_id', 'sequence')
    for goods_channel in goods_channels:
        # 取得该一级标签的所属分组， （共11组，后续展示的依据）
        group_id = goods_channel.group_id
        # 给categories 加标签， 总共会加11个， 展示11行，这个key其实的内容不重要，只是用来划分11行
        # 赋上的值是一二三级产品频道的信息， 重要的了解其中的数据结构， chnnels 的值是所有一级标签， sub_cats的值是所有二级的标签，每个二级还会包含所有三级标签
        # categories[group_id] = {'channels': [一级分类], 'sub_cats': [二级分类的属性'sub_cats':[三级分类]]}
        if group_id  not in categories:
            # 如果没有此判断， 每次创建会被刷新导致数据丢失，
            # 这也是为何容器选用字典而不是列表的原因， 内部二级需要分二级和三级还是用字典，三级就没有关系了， 列表简单用列表
            categories[group_id] = {'channels': [], 'sub_cats': []}

        # 获取自连接表中的一级分类对象 (同样是37个) 此处cat1 只有id、name、parent三个字段
        cat1 = goods_channel.category
        # 将为37 个一级标签的准备的url还给另一张表
        # 给对象临时新增一个字段， 不能保存到数据库，仅作为传递给模板渲染使用
        cat1.url = goods_channel.url

        # 利用列表的可变类型特性添加一级分类
        categories[group_id]['channels'].append(cat1)
        # 查二级标签， 已知一级， 属于一查多， 用隐士外键
        cat2_qs = cat1.subs.all()
        for cat2 in cat2_qs:
            # 查寻三级分类
            cat3 = cat2.subs.all()
            # 将三级分类封装进二级标签的subs_cats属性
            cat2.sub_cats = cat3
            # 再将二级标签封进将被渲染的数据
            categories[group_id]['sub_cats'].append(cat2)
    return categories


def get_breadcrumb(category_id):
    # 获得三级分类对象
    category = GoodsCategory.objects.get(id=category_id)
    # 属于多找一，直接用外键
    cat1 = category.parent.parent
    # 给一级标签指定一个url， 和首页指定的网页相同
    # 需要访问GoodsChannel 表，外键在chnnel表， 故根据goodschannel_set访
    # 必须用all()才能取到具体的qs对象集合
    cat1.url = cat1.goodschannel_set.all()[0].url
    breadcrumb = {
        'cat1': cat1,
        'cat2': category.parent,
        'cat3': category,
    }
    return breadcrumb


class ImgFastStorage(Storage):
    def _open(self):
        """开发者的打开文件的方法， 名义上私有"""
        pass

    def _save(self):
        """开发者的保存文件的方法， 名义上私有"""
        pass

    def url(self, name):
        """重写url方法"""
        # '192.168.234.129:8888/'http://192.168.234.129:8888/
        return 'http://192.168.234.129:8888/' + name
