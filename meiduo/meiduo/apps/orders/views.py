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
from django.db import transaction
# Create your views here.
import logging

logger = logging.error('django')

class OrderSettlementView(LoginRequiredView):
    """渲染提交订单的界面"""
    def get(self, request):
        # cart 模板中的a标签发出的请求，没有参数

        user = request.user
        # 直接查该用户所有地址
        addresses = Addresses.objects.filter(user=user, is_deleted=False)
        # 通过一查多进行查询
        # addresses = user.addresses.filter(is_deleted=False)
        redis_conn = get_redis_connection('carts')
        # 获取购物车数据
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        selected_ids = redis_conn.smembers('selected_%s' % user.id)
        # 遍历redis选择集合， 将要购买的商品挑出
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
    """提交订单"""
    """
    def post(self, request):
        
        # 核心就是要在两张表中创建记录
        # 接收请求参数
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')   # 前端传来地址的id 1,2,3,4
        pay_method = json_dict.get('pay_method')   # 前端会来1/2
        user = request.user
        # 校验参数信息
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('参数不全')
        try:
            Addresses.objects.get(id=address_id, user=user, is_deleted=False)
        except Addresses.DoesNotExist:
            return http.HttpResponseForbidden('地址参数不正确')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"], OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.HttpResponseForbidden('支付方式参数不正确')
        
        # 生成订单号, timezone.now()得到的是时间对象，具体到秒， 需要转成字符串
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
        # 创建具体的订单购买表的记录，一个订单要创建多条-->遍历
        redis_conn = get_redis_connection('carts')
        # 查出要购买的商品, 构造成字典
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        selected_ids = redis_conn.smembers('selected_%s' % user.id)
        cart = {}  # {1:2, 2:2}
        for sku_id in selected_ids:
            cart[int(sku_id)] = int(redis_carts[sku_id])
        # 遍历字典创建购买的具体商品记录
        for sku_id in cart:
            # 修改库存和销量， 注意不能sku表中不能一次将商品选出(in=sku_ids)， 因为queryset有惰性执行和缓存，
            # 用的时候可能已不是最新的数据， 数据错误可能行增加, 所以遍历执行，用一条取一条
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
        """

    def post(self, request):
        # 核心就是要在两张表中创建记录
        # 接收请求参数
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')  # 前端传来地址的id 1,2,3,4
        pay_method = json_dict.get('pay_method')  # 前端会来1/2
        user = request.user
        # 校验参数信息
        if not all([address_id, pay_method]):
            return http.HttpResponseForbidden('参数不全')
        try:
            Addresses.objects.get(id=address_id, user=user, is_deleted=False)
        except Addresses.DoesNotExist:
            return http.HttpResponseForbidden('地址参数不正确')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"], OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.HttpResponseForbidden('支付方式参数不正确')

        # 生成订单号, timezone.now()得到的是时间对象，具体到秒， 需要转成字符串
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        # 判断该订单状态 三目法
        status = (OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM["CASH"]
                  else OrderInfo.ORDER_STATUS_ENUM["UNPAID"])

        # 创建基础信息表
        # 开始手动管理事物管理（表的引擎是innodb）
        with transaction.atomic():
            # 创建最初保存点（原始点）
            save_id = transaction.savepoint()
            # 如果程序中途报错， 走不到回滚点1，或者回滚点1 后的代码有报错， 也需要将SPU、sku等4张表的可能修改都回滚点2
            try:
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
                # 创建具体的订单购买表的记录，一个订单要创建多条-->遍历
                redis_conn = get_redis_connection('carts')
                # 查出要购买的商品, 构造成字典
                redis_carts = redis_conn.hgetall('carts_%s' % user.id)
                selected_ids = redis_conn.smembers('selected_%s' % user.id)
                cart = {}  # {1:2, 2:2}
                for sku_id in selected_ids:
                    cart[int(sku_id)] = int(redis_carts[sku_id])
                # 遍历字典创建购买的具体商品记录
                for sku_id in cart:
                    i = 0
                    # 可能真的有人刚好在用， 给三次机会
                    while i < 3:
                        # 修改库存和销量， 注意不能sku表中不能一次将商品选出(in=sku_ids)， 因为queryset有惰性执行和缓存，
                        # 用的时候可能已不是最新的数据， 数据错误可能行增加, 所以遍历执行，用一条取一条
                        sku = SKU.objects.get(id=sku_id, is_launched=True)
                        # 判断库存是否足够，提前响应
                        if sku.stock < cart[sku_id]:
                            # 库存不足， 前边建的订单info表无效， 需要回滚点1
                            # 不指定回滚点时，默认放弃此次事物（创建的文件副本）修改
                            transaction.savepoint_rollback(save_id)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})
                        # 修改sku 和spu表,次种修改未考虑并发的情况， 即sku.stock可能已不是最新的了
                        # sku.stock -= cart[sku_id]
                        # sku.sales += cart[sku_id]
                        # spu = sku.spu
                        # spu.sales += cart[sku_id]
                        # sku.save()
                        # spu.save()
                        # 修改成单独
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        new_stock = origin_stock - cart[sku_id]
                        new_sales = origin_sales + cart[sku_id]
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if result == 0:
                            i += 1
                            continue
                        spu = sku.spu
                        spu.sales += cart[sku_id]
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
                        break
                order.total_amount += Constants.freight
                order.save()
            except Exception as e:
                # logger.error(e)
                transaction.savepoint_rollback(save_id)
                # 能走到这说明没有问题可以提交mysql数据库事物, 必须要有要提交的最近点（按照git的思想理解一下）
            transaction.savepoint_commit(save_id)
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
        # 获取参数
        query_dict = request.GET
        order_id = query_dict.get('order_id')
        payment_amount = query_dict.get('payment_amount')
        pay_method = query_dict.get('pay_method')
        # 校验参数
        if not all([order_id, pay_method, payment_amount]):
            return http.HttpResponseForbidden('参数不全')
        try:
             OrderInfo.objects.get(order_id=order_id, total_amount=payment_amount, pay_method=pay_method)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('参数有误')

        # 拼接返回给前端的渲染
        context = {
            'payment_amount': payment_amount,
            'order_id': order_id,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)