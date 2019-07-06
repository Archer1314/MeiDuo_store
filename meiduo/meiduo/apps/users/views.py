from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django import http
from django_redis import get_redis_connection
# Create your views here.
import re
from .models import User
from meiduo.utils.response_code import RETCODE
from django.views.generic.base import View


class Users(View):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        query_dict = request.POST
        username = query_dict.get('username', '')
        password = query_dict.get('password', '')
        password2 = query_dict.get('password2', '')
        telephone = query_dict.get('mobile', '')
        #  图形验证码只是用来防止恶意大量注册使用,
        #  逻辑是填完校验码后点击获取手机验证码时将填的校验码发到后端进行比较,
        #  确认一致才发送短信(短信收费),所以不需要作为个人信息进行校验和保险到数据库
        # image_code = query_dict.get('image_code', '')
        sms_code = query_dict.get('sms_code', '')
        allow = query_dict.get('allow', '')

        # 校验有无选项为空,checkbox标签在提交时默认提供None/on, 或用value属性指定提交的信息
        # 此处register.html使用默认,以下all可判断是否勾选,无需进行其他校验.
        if not all(query_dict.dict().values()):
            return http.HttpResponseForbidden('非法注册,部分为空')
        # if not all([username, password, password2, telephone, sms_code, allow]):
        #     return http.HttpResponseForbidden('非法注册,部分为空')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('非法注册,用户名不符合规范')
        if not re.match(r'^[[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('非法注册,密码不符合规范')
        if not password == password2:
            return http.HttpResponseForbidden('非法注册,密码两次输入不一致')
        if not re.match(r'^1[345789]\d{9}$', telephone):
            return http.HttpResponseForbidden('非法注册,手机号不符合规范')

        # 后边补全手机验证码校验
        redis_conn = get_redis_connection('verifications')
        redis_sms_code = redis_conn.get('sms_code_%s' % telephone)
        # 保证每个手机验证码只能使用一次
        # 且前端无防护此项
        redis_conn.delete(redis_sms_code)
        if redis_sms_code is None:
            return http.HttpResponseForbidden('验证码已过期')     # 正常逻辑是json局部刷新,但此为form请求,暂时用
        if redis_sms_code.decode() != sms_code:
            return http.HttpResponseForbidden('手机验证码不正确')   # 前端给的是form表单请求,不能返回json


        user = User.objects.create_user(username=username, password=password, telephone= telephone)
        login(request, user)

        return redirect('http://www.baidu.com')


class UsernamecodeView(View):
    def get(self, request, username):
        username = username
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'err_msg': 'OK', 'count': count})


class telephonecodeView(View):
    def get(self, request, mobile):
        telephone = mobile
        count = User.objects.filter(telephone=telephone).count()
        return http.JsonResponse({'code': RETCODE.OK, 'err_msg': 'OK', 'count': count})


