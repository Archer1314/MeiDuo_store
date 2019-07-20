from decimal import Decimal
from django.shortcuts import render
from meiduo.utils.views import LoginRequiredView
from meiduo.utils.response_code import RETCODE
from users.models import Addresses
from django_redis import get_redis_connection
import json
from goods.models import SKU, SPU
from .contants import Constants
from django import http
from .models import OrderInfo, OrderGoods
from django.utils import timezone
# Create your views here.


class OrderSettlementView(LoginRequiredView):
    """渲染提交订单的界面"""
    def get(self, request):
        # cart 模板中的a标签发出的请求，没有参数

        user = request.user
        # 直接查地址表
        addresses = Addresses.objects.filter(user=user, is_deleted=False)
        # 通过一查多进行查询
        # addresses = user.addresses.filter(is_deleted=False)
        redis_conn = get_redis_connection('carts')
        # 获取购物车数据
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        selected_ids = redis_conn.smembers('selected_%s' % user.id)
        # 遍历选择集合， 将要购买的商品跳出
        # 先定义个新的集合来装要购买的商品
        cart = {}   # {1:2, 2:2}
        for sku_id in selected_ids:
            cart[int(sku_id)] = int(redis_carts[sku_id])
        # 组织数据渲染
        # 取到所有的要购买商品模型
        skus = SKU.objects.filter(id__in=cart.keys())
        # 准备初始值, 计算总共要购买的商品
        total_count = 0
        total_amount = 0
        # 遍历是为了总数和总计
        for sku in skus:
            sku.count = cart[sku.id]
            sku.amount = sku.count * sku.price
            # 计算总数量和总金额
            total_count += sku.count
            total_amount += sku.count * sku.price
        context = {
            'addresses': addresses,
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'freight': Constants.freight,
            'payment_amount': total_amount + Constants.freight
        }
        return render(request, 'place_order.html', context)


class CreateOrderView(LoginRequiredView):
    def post(self, request):
        """提交订单"""
        # 核心就是要在两张表中创建记录
        # 接受请求参数
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')   # 前端会来1/2
        user = request.user
        # 校验参数信息
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('参数不全')
        try:
            Addresses.objects.get(id=address_id, user=user, is_deleted=False)
        except Addresses.DoesNotExist:
            return http.HttpResponseForbidden('参数不正确')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"], OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.HttpResponseForbidden('参数不正确')
        # 生成订单号, timezone.now()得到的是时间对象，具体到秒， 需要转成字符串， u
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        # 判断该订单状态 三目法
        status = (OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM["CASH"]
                  else OrderInfo.ORDER_STATUS_ENUM["UNPAID"])
        # 创建基础信息表
        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address_id=address_id,  # 是address_id对象还是id
            total_count=0,
            total_amount=Decimal('0.00'),
            freight=Constants.freight,
            pay_method=pay_method,
            status=status,
        )
        #创建具体的订单购买表的记录，一个订单要创建多条-->遍历
        redis_conn = get_redis_connection('carts')
        # 查出要购买的商品, 构造成字典
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        selected_ids = redis_conn.smembers('selected_%s' % user.id)
        cart = {}  # {1:2, 2:2}
        for sku_id in selected_ids:
            cart[int(sku_id)] = int(redis_carts[sku_id])
        # 遍历字典创建记录
        for sku_id in cart:
            # 修改库存和销量， 注意不能sku表中不能一次将商品选出(in=sku_ids)， 因为queryset有惰性执行和缓存行，
            # 用的时候可能已不是最新的数据， 数据错误可能行增加, 所以遍历执行
            sku = SKU.objects.get(id=sku_id, is_launched=True)
            # 判断库存是否足够，提前响应
            if sku.stock < cart[sku_id]:
                return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
            # 修改sku 和spu表
            sku.stock -= cart[sku_id]
            sku.sales += cart[sku_id]
            spu = sku.spu
            spu.sales += cart[sku_id]
            sku.save()
            spu.save()
            # 创建购买订单的商品表记录
            OrderGoods.objects.create(
                order=order,  # 外建， 给的是具体对象
                sku=sku,
                count=cart[sku_id],
                price=Decimal(str(sku.price)),
            )
            # 完善orderinfo表
            order.total_count += cart[sku_id]
            order.total_amount += (cart[sku_id] * sku.price)
        order.total_amount += Constants.freight
        order.save()
        # 删除购物车部分购买数据
        # 遍历、语言要购买的拼接字典
        pl = redis_conn.pipeline()
        pl.hdel('carts_%s' % user.id, *selected_ids)
        # for sku_id in cart:
        #     pl.hdel('carts_%s' % user.id, sku_id)
        #  删除选择的有多种方法， 删掉整个key（del）， 逐一删（srem）
        # pl.srem('selected_%s' % user.id, *selected_ids)
        pl.delete('selected_%s' % user.id)
        pl.execute()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'ok', 'order_id': order_id})


class OrderSuccessView(LoginRequiredView):
    def get(self, request):
        return render(request, 'order_success.html')