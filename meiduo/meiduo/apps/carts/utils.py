from django.views import View
import pickle, base64
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request, response):
    """合并购物车的函数, 在登录的地方调用"""
    """".合并方向：cookie购物车数据合并到Redis购物车数据中。
    2.
    合并数据：购物车商品数据和勾选状态。
    3.
    合并方案：
    3.1
    Redis数据库中的购物车数据保留。
    3.2
    如果cookie中的购物车数据在Redis数据库中已存在，将cookie购物车数据覆盖Redis购物车数据。
    3.3
    如果cookie中的购物车数据在Redis数据库中不存在，将cookie购物车数据新增到Redis。
    3.4
    最终购物车的勾选状态以cookie购物车勾选状态为准。"""
    # 获取用户购物车的cookie信息
    cart_str = request.COOKIES.get('carts')
    # 判断是否有购物车信息
    if not cart_str:
        # 没有购物车直接返回
        return
    # 购物车转字典
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
    # 获取用户， 合并数据的前提是有用户, 则必须放到用户状态保持之后， 否则是匿名用户
    user = request.user
    if user.is_authenticated:
        # 登录用户
        redis_conn = get_redis_connection('carts')
        # 取数据
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)  # 二进制的数据
        selects_ids = redis_conn.smembers('selected_%s' % user.id)  # 元素是二进制的集合
        # 对cookie中购物车进行遍历， 逻辑核心代码
        pl = redis_conn.pipeline()
        for sku_id in cart_dict.keys():
            # 如果cook数据中有该项商品就替代，没有的话保持原来的hash字典,hash 不能一次存入一个字典， 故直接一个个存
            pl.hset('carts_%s' % user.id, sku_id, cart_dict[sku_id]['count'])
            # set数据类型也是可以存入， sku_id相同的不改变， 不同的值添加到集合中
            if cart_dict[sku_id]['selected']:
                # 如果cookie 中的商品是选中的状态， 也要保存
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
        pl.execute()
    else:
        return '代码逻辑错误'
    response.delete_cookie('carts')