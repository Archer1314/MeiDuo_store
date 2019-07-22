from django.shortcuts import render
from meiduo.utils.views import LoginRequiredView
from django import http
from meiduo.utils.response_code import RETCODE
from orders.models import OrderInfo
from alipay import AliPay
import os
from django.conf import settings
from .models import Payment
from django.db import transaction, DatabaseError

# Create your views here.

class PaymentView(LoginRequiredView):
    def get(self, request, order_id):
        # 获取对象
        user = request.user
        # 校验参数 order_id
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('参数不正确')

        # 拼接url路径
        # 创建支付宝支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # app_private_key_string=app_private_key_string,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            # alipay_public_key_string=alipay_public_key_string,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )

        # 生成登录支付宝连接
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城%s" % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


class PaymentSuccess(LoginRequiredView):
    def get(self, request):
        """支付成功重定向的返回路由
        http://www.meiduo.site:8000/payment/status/
        ?charset=utf-8
        &out_trade_no=20190721203010000000001
        &method=alipay.trade.page.pay.return
        &total_amount=6698.00
        &sign=XHJX5e%2FwB6asR%2FRiIbplHFAqKIpEbmh2cD8z7npRcSOTgGL%2BqmiNFm0Kxi9FMFh4TXUt8I50IPNs45HdFHautmHE3%2FYzRi55vpRuOhLR46psarL1s%2BZWKVrQE2Ln3Mp0vFgK6J%2Fxm3YIGQiwORFaVVIMPkqrgrj9EjS%2FjRd3kYvZRPh4T8XiEGWC%2FOCfH1ksOM19rad4F%2BSS48tRbptcUmgg1nYXGf%2BD54bI3zkJJBprmvpM5rtG7dMtSWBiiSIzo4mWgR6%2F1O%2FER904miWqmvZJDAPHdx53HoMqTDosyaU0pDty6t6MqjiM3c7SFVcLtKNzMMv%2F9bKPU80gXZb6fA%3D%3D
        &trade_no=2019072122001454531000006865
        &auth_app_id=2016101000651850
        &version=1.0
        &app_id=2016101000651850
        &sign_type=RSA2
        &seller_id=2088102178910007
        &timestamp=2019-07-21+21%3A47%3A42"""
        # 获取参数
        query_dict = request.GET

        # 转字典
        data = query_dict.dict()

        # 删除并获取sign 加密的数剧
        signature = data.pop('sign')

        # 校验数据
        # verify
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # app_private_key_string=app_private_key_string,
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            # alipay_public_key_string=alipay_public_key_string,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        success = alipay.verify(data, signature)
        if success:
            # 数据校验ok（非非法请求）， 修改数据库
            trade_id = data.get('trade_no')
            order_id = data.get('out_trade_no')
            # 多个数据库必须同时达到某一现象或同时回滚
            with transaction.atomic():
                save_id = transaction.savepoint()
                OrderInfo.objects.filter(order_id=order_id, total_amount=data['total_amount'], status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']).update(status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
                try:
                    Payment.objects.get(trade_id=trade_id)
                except Payment.DoesNotExist:
                    try:
                        Payment.objects.create(order_id=order_id, trade_id=trade_id)
                    except DatabaseError:
                        transaction.savepoint_rollback(save_id)
                        return http.HttpResponseForbidden('创建失败')
                transaction.savepoint_commit(save_id)
        else:
            return http.HttpResponseForbidden('参数有误')
        context = {
            'trade_id': trade_id
        }
        return render(request, 'pay_success.html', context)
