import base64, pickle
import json
from django_redis import get_redis_connection
from django import http
from django.shortcuts import render
from django.views import View
from goods.models import SKU
# Create your views here.
import logging
from meiduo.utils.response_code import RETCODE
from django.shortcuts import redirect, reverse
logger = logging.getLogger('django')


class CartsView(View):
    """购物车"""
    def post(self, request):
        """添加购物车数据"""
        # 1、接受请求体中的数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2. 校验数据
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id 不存在')
        try:
            count = int(count)   # int 转字符串‘1’不会报错， 转‘1.5’就会报错
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('参数类型有误')
        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('参数类型有误')

        # 3. 获取当前的请求user
        user = request.user
        # 判断当前是否是登录用户
        if user.is_authenticated:
            # 如果是登录用户就把购物车数据添加到redis
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 使用hincrby指令添加hash数据,如果添加的key已存在,会对value做累加操作
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            # 使用sadd 把勾选的商品sku_id添加到set集合中
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            pl.execute()
            # 响应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        # 3.2 如果是未登录用户就把购物车数据添加到cookie中
        # 获取cookie购物车数据
        cart_str = request.COOKIES.get('carts')
        # 判断是否获取到cookie购物车数据
        if cart_str:
            # 有cookie购物车数据,就把它从字符串转换到字典
            cart_str_bytes = cart_str.encode()
            cart_bytes = base64.b64decode(cart_str_bytes)
            cart_dict = pickle.loads(cart_bytes)
            # cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            # 判断本次添加到的商品之前是否已经添加过,如果添加过,就把count进行累加
            if sku_id in cart_dict:
                # 获取它原有的购买数量
                origin_count = cart_dict[sku_id]['count']
                count += origin_count
        else:

            # 没有cookie购物车数据,准备一个空的新字典,为后面添加购物车数据准备
            cart_dict = {}

        #  添加or修改
        cart_dict[sku_id] = {
            'count': count,
            'selected': selected
        }

        # 将购物车数据设置到cookie之前需要先将字典转换成字符串
        cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
        # 创建响应对象
        # gAN9cQAoSwN9cQEoWAUAAABjb3VudHECSwNYCAAAAHNlbGVjdGVkcQOIdUsBfXEEKFgFAAAAY291bnRxBUsDWAgAAABzZWxlY3RlZHEGiHV1Lg
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        # 设置cookie
        response.set_cookie('carts', cart_str)
        # 响应
        return response

    def get(self, request):
        """展示购物车数据"""
        # 先获取请求对象中的user
        user = request.user
        # 判断用户是否登录
        if user.is_authenticated:
            # 登录用户获取redis的购物车数据
            # 创建redis连接对象
            redis_conn = get_redis_connection('carts')
            # 获取hash 中的数据,得到的是field--sku_id和value_count的字典
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 获取set集合的数据,得到的是sku_id
            selects_ids = redis_conn.smembers('selected_%s' % user.id)
            # 把redis 购物车数据格式转换成cooike 的购物车数据格式
            # {商品1(sku_id)：{数量1：值， 选择2：值(T/F)}，
            # 商品2：{数量1：值， 选择2：值}，
            # }
            cart_dict = {}
            for sku_id in redis_carts:
                cart_dict[int(sku_id)] = {
                    'count': int(redis_carts[sku_id]),
                    'selected':(sku_id in selects_ids)
                }
        else:
            # 未登录用户获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 有cookie购物车数据就将它从字符串转为字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 未登录用户， 且购物车无数据，可以响应返回网页
                return render(request, 'cart.html')
        # 无论用户是否登录， 购物车都已转成字典格式
        # 查询购物车中的商品的模型
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        # 此列表来包装前段界面需要渲染的所有购物车数据
        cart_skus = []
        for sku in sku_qs:
            count = cart_dict[sku.id]['count']
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'selected': str(cart_dict[sku.id]['selected']),
                'amount': str(sku.price*count)
            })
        return render(request, 'cart.html', {'cart_skus':cart_skus})

    def put(self,request):
        """购物车修改(一次对一个商品进行修改)"""
        # 1.接收

        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 校验
        if not all([sku_id, count]):
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        try:
            count = int(count)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('参数类型不正确')
        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('参数类型不正确')

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hset('carts_%s' % user.id, sku_id, count)
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'selected': selected,   # js传过来的selected
                'amount': str(sku.price * count)
            }
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改成功', 'cart_sku': sku_dict})

        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected,
                }
            else:
                #  修改的前提是有
                return render(request, 'cart.html')
            # 把cookie的购物车字典转换成字符串
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            sku_dict = {
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': str(sku.price),
                'count': count,
                'selected': selected,   # js传过来的selected
                'amount': str(sku.price * count)
            }
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '修改成功', 'cart_sku': sku_dict})
            response.set_cookie('carts', cart_str)
            return response

    def delete(self, request):
        """删除购物车"""
        # 接受请求体中的数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        # 校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id 不存在')
        # 判断是否登录
        user = request.user
        if user.is_authenticated:
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hdel('carts_%s' % user.id, sku_id)
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.decode()))
            else:
                return render(request, 'cart.html')
            if sku_id in cart_dict:
                del cart_dict[sku_id]
            response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '删除成功'})

            # 删除了该商品后， 购物车为空
            if not cart_dict:
                response.delete_cookie('carts')
                return response
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).encode()

            response.set_cookie('carts', cart_str)
            return response


class CartsSelectAllView(View):
    def put(self, request):
        """购物车界面的全选和全不选"""
        # 获取前段传来的数据
        selected = json.loads(request.body.decode()).get('selected')
        # if not selected: # 判断是否要全选  这里是理解取消全选时直接退出， 不进行改变
        #     return redirect(reverse('carts:carts'))
        # 校验前段传来数据
        if not isinstance(selected, bool):
            return http.JsonResponse({'code': RETCODE.PARAMERR, 'errmsg': '参数类型错误'})
        # 获取用户对象，判断是否登录
        user = request.user
        if user.is_authenticated:
            # 登录用户操作redis数据库
            redis_conn = get_redis_connection('carts')
            # 获取该用户的购物车数据
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            selects_ids = redis_conn.smembers('selected_%s' % user.id)
            # 判断是要全选还是全不选
            if selected:
                # 全选
                # for sku_id in redis_carts:     # 可以简写， 取消遍历
                #     if sku_id not in selects_ids:
                #         redis_conn.sadd('selected_%s' % user.id, sku_id)
                """取hash的字典， 然后取所有keys，得到一个每个元素类型为二进制的列表， 再进行解包"""
                redis_conn.sadd('selected_%s' % user.id, *redis_carts.keys)
            else:
                # 全取消
                # 删掉redis中储存选择的集合即可
                redis_conn.delete('selected_%s' % user.id)
            # 响应js请求
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})

        # 非登录用户
        # 获取用户的购物车cookie数据
        cart_str = request.COOKIES.get('carts')
        # 判断购物车有无数据
        if cart_str:
            # 核心业务逻辑
            # 字符串转字典
            cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            # 遍历重新按照要求的全选或全不选修改数据：一个是在原有的字典上修改， 直接重置selected属性，
            for sku_id in cart_dict:   # 整个商品重写太多了， 还有count属性， 故
                cart_dict[sku_id]['selected'] = selected
            # 2、新键一个字典来重新装，缺点是需要多定义一个变量
            # cart_dict1 = {}
            # for sku_id in cart_dict:
            #     cart_dict1[sku_id] = {
            #         'count': cart_dict[sku_id]['count'],
            #         'selected': selected
            #     }
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
        else:
            # 没有页也可以点， 所以不能禁止， 先返回就ok
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})
        # 响应
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '全选成功'})
        response.set_cookie('carts', cart_str)
        return response


class CartsSimpleView(View):
    def get(self, request):
        # 未传参数,不需要获取和校验
        # 所以直接进行是否登录校验
        user = request.user
        if user.is_authenticated:
            # 登录用户， 操作redis数据库
            # 创建redis连接， 需指定连接的库别名
            redis_conn = get_redis_connection('carts')
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)   # 元素是二进制字节流的字典
            selects_ids = redis_conn.smembers('selected_%s' % user.id)  # 元素是二进制的集合
            # 建立一个新的字典， 用来改造成和非登录用户的购物车格式一样
            cart_dict = {}
            for sku_id in redis_carts:
                cart_dict[int(sku_id)] = {
                    # 二进制字节流转为整数类型
                    'count': int(redis_carts[sku_id]),
                    'selected': (sku_id in selects_ids)
                }
        else:
            # 未登录用户获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 有cookie购物车数据就将它从字符串转为字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 未登录用户， 且购物车无数据，可以响应返回网页
                return render(request, 'cart.html')
        # 无论用户是否登录， 购物车都已转成字典格式
        # 查询购物车中的商品的模型
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        # 此列表来包装前段界面需要渲染的所有购物车数据
        # 响应
        cart_skus = []
        for sku in sku_qs:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'count': cart_dict[sku.id]['count'],

            })
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK',  'cart_skus': cart_skus})


