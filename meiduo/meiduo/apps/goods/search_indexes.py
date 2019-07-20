# 文件名一个字符都不能错
from haystack import indexes
from .models import SKU   # 对该表建立索引


class SKUIndex(indexes.SearchIndex, indexes.Indexable):
    """SKU索引数据模型类， 类名可以修改"""
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        """返回建立索引的模型类， ， 对不同表的索引要修改返回的东西"""
        # return SPU
        return SKU

    def index_queryset(self, using=None):
        """返回要建立索引的数据查询集,返回的是SKU的0个或n个实例对象， 就是查询结果"""
        return self.get_model().objects.filter(is_launched=True)