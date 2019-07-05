from django import http
from django.shortcuts import render
from meiduo.libs.captcha.captcha import captcha
# Create your views here.
from django.views.generic.base import View
from django_redis import get_redis_connection
from meiduo.utils.response_code import RETCODE

class Verifications(View):
    def get(self, request, uuid):
        name, txt, image = captcha.generate_captcha()
        redis_conn = get_redis_connection(alias='verifications')
        redis_conn.setex(uuid, 300, txt)
        return http.HttpResponse(content=image, content_type='image/jpg')


