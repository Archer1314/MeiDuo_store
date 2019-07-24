from django import http
from django.shortcuts import render
from meiduo.libs.captcha.captcha import captcha
# Create your views here.
from django.views.generic.base import View
from django_redis import get_redis_connection
from meiduo.utils.response_code import RETCODE
from random import randint
# from meiduo.libs.yuntongxun.sms import CCP
import logging
from .constans import Constans
from celery_tasks.sms.tasks import sms_code_send   # 引入的是任务函数


class Verifications(View):
    def get(self, request, uuid):
        name, txt, image = captcha.generate_captcha()
        redis_conn = get_redis_connection(alias='verifications')
        redis_conn.setex(uuid, 300, txt)
        return http.HttpResponse(content=image, content_type='image/jpg')


class SmsCode(View):

    def get(self, request, mobile):
        # (3)、优化电话请求短信2
        redis_conn = get_redis_connection('verifications')
        count = redis_conn.get('sending_flag_%s' % mobile)
        if count:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'err_msg': '频繁访问'})

        # 1. 根据请求方式确定三个参数的获取
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        # 校验
        if not all([image_code, uuid]):
            return http.HttpResponseForbidden('缺少参数')

        # 尝试取出之前保存的图形验证码信息
        redis_image_code = redis_conn.get(uuid)
        # 判断该uuid是否在redis中,排除该redis是否过期
        if not redis_image_code:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形验证码过期'})

        # 优化1 避免同一个uuid-图形验证码被使用多次
        # 注前端可以利用点击获取短信验证码时刷新图形验证码请求-uuid避免
        redis_conn.delete(uuid)

        # 判断是否填对图形验证码
        if redis_image_code.decode().lower() != image_code.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形码输入不正确'})

        # 生成验证码信息
        sms_code = '%06d' % randint(0, 999999)
        # 中断显示验证码，性能
        logging.info(sms_code)
        print(sms_code)
        # 保存手机验证码的和手机号
        # 保存手机发送验证码的状态信息
        pl = redis_conn.pipeline()
        pl.setex('sms_code_%s' % mobile, Constans.SMS_CODE_EXPIRE_REDIS, sms_code)
        pl.setex('sending_flag_%s' % mobile, Constans.MOBILE_REQUEST_EXPIRE_REDIS, 1)
        pl.execute()

        # 利用第三方容联云发短信 ,比较花费时间，造成后边返回前台的阻塞
        # CCP().send_template_sms('15029014304', [sms_code, Constans.SMS_CODE_EXPIRE_REDIS//60], 1)

        # 利用celery
        sms_code_send.delay(mobile, sms_code)
        return http.JsonResponse({'code': RETCODE.OK, 'ess_sms': 'ok'})





