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
from .utils import ManyUser


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

        user = User.objects.create_user(username=username, password=password, telephone=telephone)
        login(request, user)

        # 设置cookie，是竹叶的用户信息更新（vue.js会接受，然后渲染页面）
        # 注册成功后，重新定向到首页
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', username)
        return response


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


class IndexContents(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        #  目的：获取用户的登陆信息， 分析：前端是用form表单发送，post请求，需要返回的是http response
        # input 标签表单的name属性就是这个标签的key， value属性是值
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

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
        url = reverse('contents:index')
        if request.GET.get('next') == 'info':
            url = reverse('users:center')
        response = redirect(url)
        # 设置cooike带回username （不管以验证是么信息登录的都是显示用户名）
        response.set_cookie('username', user.username)
        return response


# 直接推出
class LogoutUser(View):
    def get(self, request):
        print('aaa')
        # 逻辑是这样，但是存储的不仅仅是kyy名
        # redis_conn = get_redis_connection('session')
        # redis_conn.delete(request.COOKIE['sessionid'])
        logout(request)

        response = redirect('users:login')
        response.delete_cookie('username')
        return response


class UserCenterInfo(View):
    def get(self, request):
        # 一个是经验的看request.user,,此为一类对象，导包无效，可以转字符串
        # print(request.user)
        # if str(request.user) == 'AnonymousUser':
        #     print(request.user)
        #     return redirect(reverse('users:login'))

        # django提供了快速的验证方法, 返回True/False
        if request.user.is_authenticated():
            return render(request, 'user_center_info.html')
        else:
            # 加入此项是为了回到来时的用户中心
            url = reverse('users:login') + '?next=info'
            return redirect(url)





