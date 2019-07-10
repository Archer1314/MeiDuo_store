from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.conf import settings
from django.contrib.auth import mixins
import json

from .models import User
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url


class RegisterView(View):
    """注册"""

    def get(self, request):
        """提供注册界面"""
        return render(request, 'register.html')

    def post(self, request):
        """注册逻辑"""

        # 接收请求体表单数据
        query_dict = request.POST
        # 获取 username password password2 mobile sms_code allow
        username = query_dict.get('username')
        password = query_dict.get('password')
        password2 = query_dict.get('password2')
        mobile = query_dict.get('mobile')
        sms_code_client = query_dict.get('sms_code')
        allow = query_dict.get('allow')  # 没有指定复选框中的value时如果勾选 'on',  没勾选None  如果前端指定了value值勾选就传递的是value中的值

        # 校验
        # if all(query_dict.dict().values()):
        # 判断里面可迭代对象中的每个元素是否有为None '', {}, [], False,如果有就返回False
        if all([username, password, password2, mobile, sms_code_client, allow]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('两次密码输入的不一致')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')

        # 短信验证码校验后期补充
        # 创建redis连接对象
        redis_conn = get_redis_connection('verify_code')
        # 获取短信验证码
        sms_code_server = redis_conn.get('sms_code_%s' % mobile)
        # 让短信验证码只能用一次
        redis_conn.delete('sms_code_%s' % mobile)
        # 判断是否过期
        if sms_code_server is None:
            return http.HttpResponseForbidden('短信验证码过期')

        # 判断用户短信验证码是否输入正确
        if sms_code_client != sms_code_server.decode():
            return http.HttpResponseForbidden('短信验证码输入错误')

        # 创建一个新用户
        # user = User.objects.create(password=password)
        # user.set_password(password)
        # user.save()
        user = User.objects.create_user(username=username, password=password, mobile=mobile)
        # 状态保持(记录用户登录状态)
        login(request, user)

        response = redirect('/')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        # 用户注册成功即代表登录成功
        # 响应,重定向到首页
        # return http.HttpResponse('注册成功,跳转到首页')
        return response
        # http://127.0.0.1:8000/register/login/
        # http://127.0.0.1:8000/login/


class UsernameCountView(View):
    """判断用户是否是重复注册"""

    def get(self, request, username):
        # 以username查询user模型,再取它的count, 0:代表用户名没有重复, 1代表用户名重复
        count = User.objects.filter(username=username).count()
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    """判断手机号是否是重复注册"""

    def get(self, request, mobile):
        # 以mobile查询user模型,再取它的count, 0:代表用户名没有重复, 1代表用户名重复
        count = User.objects.filter(mobile=mobile).count()
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class LoginView(View):
    """用户登录"""

    def get(self, request):
        return render(request, 'login.html')

    """
    多账号登录不推荐版
    def post(self, request):

        # 接收前端传入的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        # 校验
        # user = User.objects.get(username=username)
        # user.check_password(password)
        # return user
        # 判断用户是否用手机号登录, 如果是的,认证时就用手机号查询
        if re.match(r'^1[3-9]\d{9}$', username):
            User.USERNAME_FIELD = 'mobile'


        # authenticate 用户认证
        user = authenticate(request, username=username, password=password)

        User.USERNAME_FIELD = 'username'  # 再改回去,不然其它用户登录可能会出问题
        # 判断用户是否通过认证
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 状态保持
        login(request, user)
        # # 如果用户没有记住登录
        if remembered != 'on':
            request.session.set_expiry(0)  # 把session的过期时间设置为0 表示会话结束后就过期
        # request.session.set_expiry((60 * 60 * 48) if remembered else 0)


        # 重定向到指定页
        return http.HttpResponse('登录成功,来到首页')
    """

    def post(self, request):
        # 接收前端传入的表单数据
        query_dict = request.POST
        username = query_dict.get('username')
        password = query_dict.get('password')
        remembered = query_dict.get('remembered')

        # 校验
        # authenticate 用户认证
        user = authenticate(request, username=username, password=password)

        # 判断用户是否通过认证
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 状态保持
        login(request, user)
        # # 如果用户没有记住登录
        if remembered != 'on':
            request.session.set_expiry(0)  # 把session的过期时间设置为0 表示会话结束后就过期
        # /login/?next=/info/
        # /login/
        # 用户如果有来源就重定向到来源,反之就去首页
        response = redirect(request.GET.get('next') or '/')  # 创建重定向响应对象   SESSION_COOKIE_AGE
        # response.set_cookie('username', user.username, max_age=(60 * 60 * 24 * 7 * 2) if remembered else None)
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE if remembered else None)
        # print(settings.SESSION_COOKIE_AGE)
        # 重定向到指定页
        # return http.HttpResponse('登录成功,来到首页')
        return response


class LogoutView(View):
    """退出登录"""

    def get(self, request):

        # 清除状态操持
        logout(request)

        # 创建响应对象
        response = redirect('/login/')
        # 删除cookie中的username
        response.delete_cookie('username')
        # 重定向到登录界面
        return response


# class InfoView(View):
#     """用户中心"""
#
#     def get(self, request):
#         # if isinstance(request.user, User):
#         if request.user.is_authenticated:  # 如果if 成立说明是登录用户
#             return render(request, 'user_center_info.html')
#         else:
#             return redirect('/login/?next=/info/')


class InfoView(mixins.LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        return render(request, 'user_center_info.html')


class EmailView(LoginRequiredView):
    """设置用户邮箱"""
    def put(self, request):
        # 接收数据
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验
        if email is None:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮件格式不正确')
        # 处理业务逻辑
        user = request.user
        # user.email = email  # 此写法,在当前场景会随着重新发送邮箱时,重复设置邮箱
        # user.save()
        User.objects.filter(id=user.id, email='').update(email=email)  # 邮箱只要设置成功了,此代码都是无效的修改

        # 在此顺带的发一个激活邮件出去
        # from django.core.mail import send_mail
        # send_mail(subject='主题', message='邮件普通正文', from_email='发件人', recipient_list='收件人,必须是列表',
        #       html_message='超文本的邮件内容')
        # verify_url = 'http://www.meiduo.site:8000/emails/verification/?token=3'
        # 生成激活url
        verify_url = generate_verify_email_url(user)
        # celery异步发邮件
        send_verify_email.delay(email, verify_url)
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
