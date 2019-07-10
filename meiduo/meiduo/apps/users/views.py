import json
from django.contrib.auth import login
from django.contrib.auth import logout

from django.shortcuts import render, redirect
from django import http
from django.urls import reverse
from django_redis import get_redis_connection
# Create your views here.
import re
from .models import User
from meiduo.utils.response_code import RETCODE
from django.views.generic.base import View
from django.contrib.auth import authenticate    # 已经被ManyUser继承
from .utils import ManyUser, generate_verify_url
from django.conf import settings
from meiduo.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email

class RegisterView(View):
    def get(self, request):
        '''提供注册界面'''
        return render(request, 'register.html')

    def post(self, request):
        """注册逻辑"""
        # 接收请求体数据
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
        if  password != password2:
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

        user = User.objects.create_user(username=username, password=password, telephone=telephone)
        login(request, user)

        # 设置cookie，主页的用户信息更新（vue.js会接受，然后渲染页面）
        # 注册成功后，重新定向到首页
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', username, max_age=settings.SESSION_COOKIE_AGE)
        return response


class UsernamecountView(View):
    """判断用户名是否重复注册"""
    def get(self, request, username):
        username = username
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'err_msg': 'OK', 'count': count})


class telephonecountView(View):
    """判断手机是否重复注册"""
    def get(self, request, mobile):
        telephone = mobile
        count = User.objects.filter(telephone=telephone).count()
        return http.JsonResponse({'code': RETCODE.OK, 'err_msg': 'OK', 'count': count})


class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        #  目的：获取用户的登陆信息， 分析：前端是用form表单发送，post请求，需要返回的是http response
        # input 标签表单的name属性就是这个标签的key， value属性是值
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        if not all([username, password]):
            return http.HttpResponseForbidden('账号或密码不全')

        # 校验，如果不正确，再次返回登陆页面，并提示错误信息
        # filter不行，得到的是queryset，不能进行check_password方法
        # user = User.objects.filter(username=username)
        # if user.check_password(password):
        #     return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # return render(request, 'index.html')

        # try:
        #     user = User.objects.get(username=username)
        # except User.DoesnotExist:
        #     return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        #
        # if not user.check_password(password):
        #     return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 比较繁琐，django有做好该认证工作
        # user = authenticate(username=username, password=password)
        # 但是只能满足账号的username，手机号bu满足
        # 改善2  看源代码，将校验的内容根据输入动态的从username改为mobile
        user = ManyUser.authenticate(request, username=username, password=password)

        if not user:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})

        # 优花1
        # 保持用户状态  默认会保持14天
        # 浏览器关闭后还会存在14天（cookie存在14天，服务器上的session信息保存14天）
        # 如果要修改，本质是要修改保存的session保存时间,login中的session保存時間用的是全局設置中（global。setting中）的SESSION_COOKIE_AVG設置
        login(request, user)

        # 如果用户选择不记录，则是需要关闭浏览器后就没有session信息
        if remembered != 'on':
            request.session.set_expiry(0)
        # 设置cookie，是主页的用户信息更新（vue.js会接受，然后渲染页面）
        response = redirect(request.GET.get('next') or reverse('users:center'))
        # 设置cooike带回username （不管以验证是么信息登录的都是显示用户名）
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE if remembered else None)
        return response


# 直接推出
class LogoutView(View):
    def get(self, request):
        print('aaa')
        # 逻辑是这样，但是存储的不仅仅是kyy名
        # redis_conn = get_redis_connection('session')
        # redis_conn.delete(request.COOKIE['sessionid'])
        logout(request)

        response = redirect('users:login')
        response.delete_cookie('username')
        return response


class UserCenterInfoView(View):
    def get(self, request):
        # 一个是经验的看request.user,此为一类对象，导包无效，可以转字符串
        # print(request.user)
        # if str(request.user) == 'AnonymousUser':
        #     print(request.user)
        #     return redirect(reverse('users:login'))

        # django提供了快速的验证方法, 返回True/False
        if request.user.is_authenticated:
            return render(request, 'user_center_info.html')
        else:
            # 加入此项是为了回到来时的用户中心
            url = reverse('users:login') + '?next=info'
            return redirect(url)


class UserCenterEmailView(LoginRequiredView):
    def put(self, request):
        # 接收数据：email
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')
        # 校验
        # 1、非空
        if not email:
            return http.HttpResponseForbidden('缺少必传参数email')
        # 2、匹配格式
        if re.match('r[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮箱格式不正确')
        # 业务逻辑
        # 1、获取对象,request的user属性封装着真正的一个模型类对象
        user = request.user
        # 2、更新数据库的字段
        # 此类更新会更新数据库中的最近一次修改时间， 但是前段代码有问题，会随着重新发送邮箱时重复设置邮箱
        # user.email = email
        # user.save()
        # 此类更新不会更新数据表中的最近一次修改时间
        User.objects.filter(id=user.id).update(email=email)   # 邮箱只要设置成功了，此代码都是无效的修改
        
        # from django.core.mail import send_mail
        # # send_mail(subject='主题', message='邮件普通正文，是纯文本', from_email='发件人', recipient_list=[email], html_message='超文本的邮件内容')
        # html_message='<li><a href="/info/" class="active">· 个人信息</a></li>'
        # send_mail(subject='defult', message='hello, welcome', from_email=settings.EMAIL_HOST_USER, recipient_list=[email], html_message=html_message)
        verify_url = generate_verify_url(user)
        send_verify_email.delay(email, verify_url)
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '已发送邮件'})
#
#
#
#
#
#
# 1、获取对象
# 2、更新数据库的字段
# # 发送一个验证邮箱（和手机验证码时机是相同的）
# # 响应


