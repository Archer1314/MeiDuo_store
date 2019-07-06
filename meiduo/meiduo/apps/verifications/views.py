from django import http
from django.shortcuts import render
from meiduo.libs.captcha.captcha import captcha
# Create your views here.
from django.views.generic.base import View
from django_redis import get_redis_connection
from meiduo.utils.response_code import RETCODE
from random import randint
from meiduo.libs.yuntongxun.sms import CCP
import logging
from .constans import Constans

class Verifications(View):
    def get(self, request, uuid):
        name, txt, image = captcha.generate_captcha()
        redis_conn = get_redis_connection(alias='verifications')
        redis_conn.setex(uuid, 300, txt)
        return http.HttpResponse(content=image, content_type='image/jpg')


class SmsCode(View):

    def get(self, request, mobile):
        # 1. 根据请求方式确定三个参数的获取
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        if not all([image_code, uuid]):
            return http.HttpResponseForbidden('缺少参数')
        redis_conn = get_redis_connection('verifications')
        redis_image_code = redis_conn.get(uuid)
        print(redis_image_code)
        if not redis_image_code:   # 判断该uuid是否在redis中,排除该redis是否过期
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形验证码过期'})

        # 优化1 避免同一个uuid-图形验证码被使用多次
        # 注前端可以利用点击获取短信验证码时刷新图形验证码请求-uuid避免
        redis_conn.delete(uuid)

        if redis_image_code.decode().lower() != image_code.lower():  # 判断是否填对图形验证码
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'err_msg': '图形码输入不正确'})

        sms_code = '%06d' % randint(0, 999999)
        redis_conn.setex('sms_code_%s' % mobile, Constans.SMS_CODE_EXPIRE_REDIS, sms_code)

        logging.info(sms_code)

        # 利用第三方容联云发短信
        a = CCP().send_template_sms('15029014304', [sms_code, Constans.SMS_CODE_EXPIRE_REDIS//60], 1)
        sending_flag = True
        return http.JsonResponse({'code': RETCODE.OK, 'ess_sms': 'ok'})






